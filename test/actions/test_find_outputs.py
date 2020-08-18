import json

from blight.actions import FindOutputs
from blight.actions.find_outputs import OutputKind
from blight.tool import CC


def test_find_outputs(tmp_path):
    output = tmp_path / "outputs.jsonl"

    find_outputs = FindOutputs({"output": output})
    cc = CC(["-o", "foo", "foo.c"])
    find_outputs.before_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs[OutputKind.Executable.value] == [str(cc.cwd / "foo")]


def test_find_outputs_multiple(tmp_path):
    fake_cs = [tmp_path / fake_c for fake_c in ["foo.c", "bar.c", "baz.c"]]
    [fake_c.touch() for fake_c in fake_cs]

    output = tmp_path / "outputs.jsonl"

    find_outputs = FindOutputs({"output": output})
    cc = CC(["-c", *[str(fake_c) for fake_c in fake_cs]])
    find_outputs.before_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs[OutputKind.Object.value] == [
        str(cc.cwd / fake_c.with_suffix(".o").name) for fake_c in fake_cs
    ]


def test_find_outputs_handles_a_out(tmp_path):
    output = tmp_path / "outputs.jsonl"

    find_outputs = FindOutputs({"output": output})
    cc = CC(["foo.c"])
    find_outputs.before_run(cc)

    outputs = json.loads(output.read_text())["outputs"]
    assert outputs[OutputKind.Executable.value] == [str(cc.cwd / "a.out")]
