import json
import shlex
import shutil

import pytest

from canker import tool
from canker.enums import CompilerStage, Lang, Std
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
    ("flags", "lang", "std", "stage"),
    [
        ("", Lang.C, Std.GnuUnknown, CompilerStage.AllStages),
        ("-x c++", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.AllStages),
        ("-ansi", Lang.C, Std.C89, CompilerStage.AllStages),
        ("-ansi -x c++", Lang.Cxx, Std.Cxx03, CompilerStage.AllStages),
        ("-std=c99", Lang.C, Std.C99, CompilerStage.AllStages),
        ("-x unknown", Lang.Unknown, Std.Unknown, CompilerStage.AllStages),
        ("-ansi -x unknown", Lang.Unknown, Std.Unknown, CompilerStage.AllStages),
        ("-std=cunknown", Lang.C, Std.CUnknown, CompilerStage.AllStages),
        ("-std=c++unknown", Lang.C, Std.CxxUnknown, CompilerStage.AllStages),
        ("-std=gnuunknown", Lang.C, Std.GnuUnknown, CompilerStage.AllStages),
        ("-std=gnu++unknown", Lang.C, Std.GnuxxUnknown, CompilerStage.AllStages),
        ("-std=nonsense", Lang.C, Std.Unknown, CompilerStage.AllStages),
        ("-v", Lang.C, Std.GnuUnknown, CompilerStage.Unknown),
        ("-###", Lang.C, Std.GnuUnknown, CompilerStage.Unknown),
        ("-E", Lang.C, Std.GnuUnknown, CompilerStage.Preprocess),
        ("-fsyntax-only", Lang.C, Std.GnuUnknown, CompilerStage.SyntaxOnly),
        ("-S", Lang.C, Std.GnuUnknown, CompilerStage.Assemble),
        ("-c", Lang.C, Std.GnuUnknown, CompilerStage.CompileObject),
    ],
)
def test_cc(flags, lang, std, stage):
    flags = shlex.split(flags)
    cc = tool.CC(flags)

    assert cc.wrapped_tool() == shutil.which("cc")
    assert cc.lang == lang
    assert cc.std == std
    assert cc.stage == stage
    assert repr(cc) == f"<CC {cc.wrapped_tool()} {cc.lang} {cc.std} {cc.stage}>"
    assert cc.asdict() == {
        "name": cc.__class__.__name__,
        "wrapped_tool": cc.wrapped_tool(),
        "args": flags,
        "lang": lang.name,
        "std": std.name,
        "stage": stage.name,
    }


@pytest.mark.parametrize(
    ("flags", "lang", "std", "stage"),
    [
        ("", Lang.Cxx, Std.GnuxxUnknown, CompilerStage.AllStages),
        ("-x c", Lang.C, Std.GnuUnknown, CompilerStage.AllStages),
        ("-std=c++17", Lang.Cxx, Std.Cxx17, CompilerStage.AllStages),
    ],
)
def test_cxx(flags, lang, std, stage):
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
