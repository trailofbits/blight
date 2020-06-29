import json
import shlex
import shutil

import pytest

from canker import tool
from canker.enums import CompilerStage, Lang, OptLevel, Std
from canker.exceptions import CankerError


def test_tool_doesnt_instantial():
    with pytest.raises(NotImplementedError):
        tool.Tool([])


def test_tool_missing_wrapped_tool(monkeypatch):
    monkeypatch.delenv("CANKER_WRAPPED_CC")
    with pytest.raises(CankerError):
        tool.CC.wrapped_tool()


def test_tool_run(monkeypatch, tmp_path):
    bench_output = tmp_path / "bench.jsonl"
    monkeypatch.setenv("CANKER_ACTIONS", "Benchmark")
    monkeypatch.setenv("CANKER_ACTION_BENCHMARK", f"output={bench_output}")

    cc = tool.CC(["-v"])
    cc.run()

    bench_record = json.loads(bench_output.read_text())
    assert bench_record["tool"] == cc.asdict()
    assert isinstance(bench_record["elapsed"], int)


@pytest.mark.parametrize(
    ("flags", "lang", "std", "stage", "opt"),
    [
        ("", Lang.C, Std.GnuUnknown, CompilerStage.AllStages, OptLevel.O0),
        ("-x c++ -O1", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.AllStages, OptLevel.O1),
        ("-ansi -O2", Lang.C, Std.C89, CompilerStage.AllStages, OptLevel.O2),
        ("-ansi -x c++ -O3", Lang.Cxx, Std.Cxx03, CompilerStage.AllStages, OptLevel.O3),
        ("-std=c99 -O4", Lang.C, Std.C99, CompilerStage.AllStages, OptLevel.O3),
        ("-x unknown -Ofast", Lang.Unknown, Std.Unknown, CompilerStage.AllStages, OptLevel.OFast),
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
        "lang": lang.name,
        "std": std.name,
        "stage": stage.name,
        "opt": opt.name,
    }


@pytest.mark.parametrize(
    ("flags", "lang", "std", "stage", "opt"),
    [
        ("", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.AllStages, OptLevel.O0),
        ("-x c", Lang.C, Std.GnuUnknown, CompilerStage.AllStages, OptLevel.O0),
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
        "lang": lang.name,
        "std": std.name,
        "stage": stage.name,
        "opt": opt.name,
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
        "lang": lang.name,
        "std": std.name,
    }


def test_ld():
    ld = tool.LD([])

    assert ld.wrapped_tool() == shutil.which("ld")
    assert repr(ld) == f"<LD {ld.wrapped_tool()}>"
    assert ld.asdict() == {
        "name": ld.__class__.__name__,
        "wrapped_tool": ld.wrapped_tool(),
        "args": [],
    }


def test_as():
    as_ = tool.AS([])

    assert as_.wrapped_tool() == shutil.which("as")
    assert repr(as_) == f"<AS {as_.wrapped_tool()}>"
    assert as_.asdict() == {
        "name": as_.__class__.__name__,
        "wrapped_tool": as_.wrapped_tool(),
        "args": [],
    }
