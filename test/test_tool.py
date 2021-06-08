import json
import os
import shlex
import shutil

import pytest

from blight import tool, util
from blight.enums import CodeModel, CompilerStage, Lang, OptLevel, Std
from blight.exceptions import BlightError, BuildError


def test_tool_doesnt_instantiate():
    with pytest.raises(NotImplementedError):
        tool.Tool([])


def test_compilertool_doesnt_instantiate():
    with pytest.raises(NotImplementedError):
        tool.CompilerTool([])


def test_tool_missing_wrapped_tool(monkeypatch):
    monkeypatch.delenv("BLIGHT_WRAPPED_CC")
    with pytest.raises(BlightError):
        tool.CC.wrapped_tool()


def test_tool_fails(monkeypatch):
    monkeypatch.setenv("BLIGHT_WRAPPED_CC", "false")
    with pytest.raises(BuildError):
        tool.CC([]).run()


def test_tool_env_filters_swizzle_path(monkeypatch):
    path = os.getenv("PATH")
    monkeypatch.setenv("PATH", f"/tmp/does-not-exist-{util.SWIZZLE_SENTINEL}:{path}")

    cc = tool.CC(["-v"])

    env = cc.asdict()["env"]
    assert util.SWIZZLE_SENTINEL not in env["PATH"]


def test_tool_run(monkeypatch, tmp_path):
    bench_output = tmp_path / "bench.jsonl"
    monkeypatch.setenv("BLIGHT_ACTIONS", "Benchmark")
    monkeypatch.setenv("BLIGHT_ACTION_BENCHMARK", f"output={bench_output}")

    cc = tool.CC(["-v"])
    cc.run()

    bench_record = json.loads(bench_output.read_text())
    assert bench_record["tool"] == cc.asdict()
    assert isinstance(bench_record["elapsed"], int)


def test_tool_args_property():
    cpp = tool.CPP(["a", "b", "c"])

    assert cpp.args == ["a", "b", "c"]

    cpp.args.append("d")
    cpp.args += ["e"]

    assert cpp.args == ["a", "b", "c", "d", "e"]


def test_tool_inputs(tmp_path):
    foo_input = (tmp_path / "foo.c").resolve()
    foo_input.touch()

    bar_input = (tmp_path / "bar.c").resolve()
    bar_input.touch()

    cc = tool.CC([str(foo_input), str(bar_input), "-", "-o", "foo"])

    assert cc.inputs == [str(foo_input), str(bar_input), "-"]


def test_tool_output(tmp_path):
    assert tool.CC(["-ofoo"]).outputs == ["foo"]
    assert tool.CC(["-o", "foo"]).outputs == ["foo"]
    assert tool.CC(["foo.c"]).outputs == ["a.out"]
    assert tool.CC(["-E"]).outputs == ["-"]

    foo_input = (tmp_path / "foo.c").resolve()
    foo_input.touch()

    assert tool.CC(["-c", str(foo_input)]).outputs == [str(foo_input.with_suffix(".o").name)]
    assert tool.CC(["-S", str(foo_input)]).outputs == [str(foo_input.with_suffix(".s").name)]

    bar_input = (tmp_path / "bar.c").resolve()
    bar_input.touch()

    assert tool.CC(["-c", str(foo_input), str(bar_input)]).outputs == [
        str(foo_input.with_suffix(".o").name),
        str(bar_input.with_suffix(".o").name),
    ]
    assert tool.CC(["-S", str(foo_input), str(bar_input)]).outputs == [
        str(foo_input.with_suffix(".s").name),
        str(bar_input.with_suffix(".s").name),
    ]

    assert tool.CC([]).outputs == []
    assert tool.CC(["-v"]).outputs == []


def test_tool_response_file(tmp_path):
    response_file = (tmp_path / "args").resolve()
    response_file.write_text("-some -flags -O3")

    cc = tool.CC([f"@{response_file}"])
    assert cc.args == [f"@{response_file}"]
    assert cc.canonicalized_args == ["-some", "-flags", "-O3"]
    assert cc.opt == OptLevel.O3


def test_tool_response_file_nested(tmp_path):
    response_file1 = (tmp_path / "args").resolve()
    response_file1.write_text("-some -flags @args2 -more -flags")
    response_file2 = (tmp_path / "args2").resolve()
    response_file2.write_text("-nested -flags -O3")

    cc = tool.CC([f"@{response_file1}"])
    assert cc.args == [f"@{response_file1}"]
    assert cc.canonicalized_args == [
        "-some",
        "-flags",
        "-nested",
        "-flags",
        "-O3",
        "-more",
        "-flags",
    ]
    assert cc.opt == OptLevel.O3


def test_tool_response_file_invalid_file():
    cc = tool.CC(["@/this/file/does/not/exist"])

    assert cc.args == ["@/this/file/does/not/exist"]
    assert cc.canonicalized_args == []


def test_tool_response_file_recursion_limit(tmp_path):
    response_file = (tmp_path / "args").resolve()
    response_file.write_text(f"-foo @{response_file}")

    cc = tool.CC([f"@{response_file}"])
    assert cc.args == [f"@{response_file}"]
    assert cc.canonicalized_args == ["-foo"] * tool.RESPONSE_FILE_RECURSION_LIMIT


@pytest.mark.parametrize(
    ("flags", "defines", "undefines"),
    [
        ("-Dfoo -Dbar -Dbaz", [("foo", "1"), ("bar", "1"), ("baz", "1")], {}),
        ("-Dfoo -Ufoo -Dbar", [("bar", "1")], {"foo": 1}),
        ("-Dfoo -Dbar -Ufoo", [("bar", "1")], {"foo": 2}),
        ("-Ufoo -Dfoo", [("foo", "1")], {"foo": 0}),
        ("-U foo -Dfoo", [("foo", "1")], {"foo": 0}),
        ("-Ufoo -D foo", [("foo", "1")], {"foo": 0}),
        ("-Dkey=value", [("key", "value")], {}),
        ("-Dkey=value=x", [("key", "value=x")], {}),
        ("-Dkey='value'", [("key", "value")], {}),
        ("-Dkey='value=x'", [("key", "value=x")], {}),
        ("-D'FOO(x)=x+1'", [("FOO(x)", "x+1")], {}),
        ("-D 'FOO(x)=x+1'", [("FOO(x)", "x+1")], {}),
    ],
)
def test_defines_mixin(flags, defines, undefines):
    cc = tool.CC(shlex.split(flags))

    assert cc.defines == defines
    assert cc.indexed_undefines == undefines


@pytest.mark.parametrize(
    ("flags", "code_model"),
    [
        ("", CodeModel.Small),
        ("-mcmodel", CodeModel.Small),
        ("-mcmodel=small", CodeModel.Small),
        ("-mcmodel=medlow", CodeModel.Small),
        ("-mcmodel=medium", CodeModel.Medium),
        ("-mcmodel=medany", CodeModel.Medium),
        ("-mcmodel=large", CodeModel.Large),
        ("-mcmodel=kernel", CodeModel.Kernel),
        ("-mcmodel=unknown", CodeModel.Unknown),
    ],
)
def test_codemodel_mixin(flags, code_model):
    cc = tool.CC(shlex.split(flags))

    assert cc.code_model == code_model


@pytest.mark.parametrize(
    ("flags", "lang", "std", "stage", "opt"),
    [
        ("", Lang.C, Std.GnuUnknown, CompilerStage.Unknown, OptLevel.O0),
        ("-x c++ -O1", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.AllStages, OptLevel.O1),
        ("-xc++ -O1", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.AllStages, OptLevel.O1),
        ("-ansi -O2", Lang.C, Std.C89, CompilerStage.AllStages, OptLevel.O2),
        ("-ansi -x c++ -O3", Lang.Cxx, Std.Cxx03, CompilerStage.AllStages, OptLevel.O3),
        ("-std=c99 -O4", Lang.C, Std.C99, CompilerStage.AllStages, OptLevel.O3),
        ("-x unknown -Ofast", Lang.Unknown, Std.Unknown, CompilerStage.AllStages, OptLevel.OFast),
        ("-xunknown -Ofast", Lang.Unknown, Std.Unknown, CompilerStage.AllStages, OptLevel.OFast),
        (
            "-ansi -x unknown -Os",
            Lang.Unknown,
            Std.Unknown,
            CompilerStage.AllStages,
            OptLevel.OSize,
        ),
        ("-std=cunknown -Oz", Lang.C, Std.CUnknown, CompilerStage.AllStages, OptLevel.OSizeZ),
        ("-std=c++unknown -Og", Lang.C, Std.CxxUnknown, CompilerStage.AllStages, OptLevel.ODebug),
        (
            "-std=gnuunknown -Omadeup",
            Lang.C,
            Std.GnuUnknown,
            CompilerStage.AllStages,
            OptLevel.Unknown,
        ),
        ("-std=gnu++unknown -O", Lang.C, Std.GnuxxUnknown, CompilerStage.AllStages, OptLevel.O1),
        ("-std=nonsense", Lang.C, Std.Unknown, CompilerStage.AllStages, OptLevel.O0),
        ("-v", Lang.C, Std.GnuUnknown, CompilerStage.Unknown, OptLevel.O0),
        ("-###", Lang.C, Std.GnuUnknown, CompilerStage.Unknown, OptLevel.O0),
        ("-E", Lang.C, Std.GnuUnknown, CompilerStage.Preprocess, OptLevel.O0),
        ("-fsyntax-only", Lang.C, Std.GnuUnknown, CompilerStage.SyntaxOnly, OptLevel.O0),
        ("-S", Lang.C, Std.GnuUnknown, CompilerStage.Assemble, OptLevel.O0),
        ("-c", Lang.C, Std.GnuUnknown, CompilerStage.CompileObject, OptLevel.O0),
    ],
)
def test_cc(flags, lang, std, stage, opt):
    flags = shlex.split(flags)
    cc = tool.CC(flags)

    assert cc.wrapped_tool() == shutil.which("cc")
    assert cc.lang == lang
    assert cc.std == std
    assert cc.stage == stage
    assert cc.opt == opt
    assert repr(cc) == f"<CC {cc.wrapped_tool()} {cc.lang} {cc.std} {cc.stage}>"
    assert cc.asdict() == {
        "name": cc.__class__.__name__,
        "wrapped_tool": cc.wrapped_tool(),
        "args": flags,
        "canonicalized_args": flags,
        "cwd": str(cc.cwd),
        "lang": lang.name,
        "std": std.name,
        "stage": stage.name,
        "opt": opt.name,
        "env": dict(os.environ),
    }


@pytest.mark.parametrize(
    ("flags", "lang", "std", "stage", "opt"),
    [
        ("", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.Unknown, OptLevel.O0),
        ("-x c", Lang.C, Std.GnuUnknown, CompilerStage.AllStages, OptLevel.O0),
        ("-xc", Lang.C, Std.GnuUnknown, CompilerStage.AllStages, OptLevel.O0),
        ("-std=c++17", Lang.Cxx, Std.Cxx17, CompilerStage.AllStages, OptLevel.O0),
    ],
)
def test_cxx(flags, lang, std, stage, opt):
    flags = shlex.split(flags)
    cxx = tool.CXX(flags)

    assert cxx.wrapped_tool() == shutil.which("c++")
    assert cxx.lang == lang
    assert cxx.std == std
    assert cxx.stage == stage
    assert repr(cxx) == f"<CXX {cxx.wrapped_tool()} {cxx.lang} {cxx.std} {cxx.stage}>"
    assert cxx.asdict() == {
        "name": cxx.__class__.__name__,
        "wrapped_tool": cxx.wrapped_tool(),
        "args": flags,
        "canonicalized_args": flags,
        "cwd": str(cxx.cwd),
        "lang": lang.name,
        "std": std.name,
        "stage": stage.name,
        "opt": opt.name,
        "env": dict(os.environ),
    }


@pytest.mark.parametrize(
    ("flags", "lang", "std"),
    [
        ("", Lang.Unknown, Std.Unknown),
        ("-x c", Lang.C, Std.GnuUnknown),
        ("-ansi", Lang.Unknown, Std.Unknown),
    ],
)
def test_cpp(flags, lang, std):
    flags = shlex.split(flags)
    cpp = tool.CPP(flags)

    assert cpp.wrapped_tool() == shutil.which("cpp")
    assert cpp.lang == lang
    assert cpp.std == std
    assert cpp.std.is_unknown()
    assert repr(cpp) == f"<CPP {cpp.wrapped_tool()} {cpp.lang} {cpp.std}>"
    assert cpp.asdict() == {
        "name": cpp.__class__.__name__,
        "wrapped_tool": cpp.wrapped_tool(),
        "args": flags,
        "canonicalized_args": flags,
        "cwd": str(cpp.cwd),
        "lang": lang.name,
        "std": std.name,
        "env": dict(os.environ),
    }


def test_ld():
    ld = tool.LD([])

    assert ld.wrapped_tool() == shutil.which("ld")
    assert repr(ld) == f"<LD {ld.wrapped_tool()}>"
    assert ld.asdict() == {
        "name": ld.__class__.__name__,
        "wrapped_tool": ld.wrapped_tool(),
        "args": [],
        "canonicalized_args": [],
        "cwd": str(ld.cwd),
        "env": dict(os.environ),
    }


@pytest.mark.parametrize(
    ("flags", "output"),
    [
        ("", "a.out"),
        ("-o foo", "foo"),
        ("-ofoo", "foo"),
        ("--output foo", "foo"),
        ("--output=foo", "foo"),
    ],
)
def test_ld_output_forms(flags, output):
    ld = tool.LD(shlex.split(flags))

    assert ld.outputs == [output]


def test_as():
    as_ = tool.AS([])

    assert as_.wrapped_tool() == shutil.which("as")
    assert repr(as_) == f"<AS {as_.wrapped_tool()}>"
    assert as_.asdict() == {
        "name": as_.__class__.__name__,
        "wrapped_tool": as_.wrapped_tool(),
        "args": [],
        "canonicalized_args": [],
        "cwd": str(as_.cwd),
        "env": dict(os.environ),
    }


def test_ar():
    ar = tool.AR([])

    assert ar.wrapped_tool() == shutil.which("ar")
    assert repr(ar) == f"<AR {ar.wrapped_tool()}>"
    assert ar.asdict() == {
        "name": ar.__class__.__name__,
        "wrapped_tool": ar.wrapped_tool(),
        "args": [],
        "canonicalized_args": [],
        "cwd": str(ar.cwd),
        "env": dict(os.environ),
    }


@pytest.mark.parametrize(
    ("flags", "outputs"),
    [
        ("cr foo.a a.o b.o", ["foo.a"]),
        ("-X64_32 cr foo.a a.o b.o", ["foo.a"]),
        ("r foo.a bar.o", ["foo.a"]),
        ("ru foo.a bar.o", ["foo.a"]),
        ("d foo.a bar.o", ["foo.a"]),
        ("--help", []),
    ],
)
def test_ar_output_forms(flags, outputs):
    ar = tool.AR(shlex.split(flags))

    assert ar.outputs == outputs


def test_strip():
    strip = tool.STRIP([])

    assert strip.wrapped_tool() == shutil.which("strip")
    assert repr(strip) == f"<STRIP {strip.wrapped_tool()}>"
    assert strip.asdict() == {
        "name": strip.__class__.__name__,
        "wrapped_tool": strip.wrapped_tool(),
        "args": [],
        "canonicalized_args": [],
        "cwd": str(strip.cwd),
        "env": dict(os.environ),
    }


def test_install():
    install = tool.INSTALL([])

    assert install.wrapped_tool() == shutil.which("install")
    assert repr(install) == f"<INSTALL {install.wrapped_tool()}>"
    assert install.asdict() == {
        "name": install.__class__.__name__,
        "wrapped_tool": install.wrapped_tool(),
        "args": [],
        "canonicalized_args": [],
        "cwd": str(install.cwd),
        "env": dict(os.environ),
    }


@pytest.mark.parametrize(
    ("flags", "directory_mode", "inputs", "outputs"),
    [
        # Reasonable inputs.
        ("-d foo bar baz", True, [], ["foo", "bar", "baz"]),
        ("-d -g wheel -o root -m 0755 foo bar baz", True, [], ["foo", "bar", "baz"]),
        ("-c foo bar", False, ["foo"], ["bar"]),
        ("-c foo bar baz /tmp", False, ["foo", "bar", "baz"], ["/tmp/foo", "/tmp/bar", "/tmp/baz"]),
        (
            "-cv foo bar baz /tmp",
            False,
            ["foo", "bar", "baz"],
            ["/tmp/foo", "/tmp/bar", "/tmp/baz"],
        ),
        (
            "-c -v foo bar baz /tmp",
            False,
            ["foo", "bar", "baz"],
            ["/tmp/foo", "/tmp/bar", "/tmp/baz"],
        ),
        (
            "-cbCM foo bar baz /tmp",
            False,
            ["foo", "bar", "baz"],
            ["/tmp/foo", "/tmp/bar", "/tmp/baz"],
        ),
        (
            "-g wheel -o root -m 0755 foo bar baz /tmp",
            False,
            ["foo", "bar", "baz"],
            ["/tmp/foo", "/tmp/bar", "/tmp/baz"],
        ),
        # Broken inputs.
        ("", False, [], []),
        ("foo", False, [], []),
    ],
)
def test_install_inputs_and_outputs(flags, directory_mode, inputs, outputs):
    install = tool.INSTALL(shlex.split(flags))

    assert install.directory_mode == directory_mode
    assert install.inputs == inputs
    assert install.outputs == outputs
