import json
import os
from pathlib import Path

from blight.actions import FindInputs
from blight.enums import InputKind
from blight.tool import CC


def test_find_inputs(tmp_path):
    output = tmp_path / "outputs.jsonl"

    foo_input = (tmp_path / "foo.c").resolve()
    foo_input.touch()

    find_inputs = FindInputs({"output": output})
    cwd_path = Path(os.getcwd()).resolve()
    os.chdir(tmp_path)
    cc = CC(["-o", "foo", "foo.c"])
    os.chdir(cwd_path)
    find_inputs.before_run(cc)
    find_inputs.after_run(cc)

    inputs = json.loads(output.read_text())["inputs"]
    assert inputs == [
        {
            "kind": InputKind.Source.value,
            "prenormalized_path": "foo.c",
            "path": str(foo_input),
            "store_path": None,
            "content_hash": None,
        }
    ]


def test_find_outputs_journaling(monkeypatch, tmp_path):
    journal_output = tmp_path / "journal.jsonl"
    monkeypatch.setenv("BLIGHT_JOURNAL_PATH", str(journal_output))

    foo_input = (tmp_path / "foo.c").resolve()
    foo_input.touch()

    find_outputs = FindInputs({})
    cc = CC(["-c", str(foo_input), "-o", "foo"])
    find_outputs.before_run(cc)
    find_outputs.after_run(cc)

    inputs = find_outputs._result["inputs"]
    assert len(inputs) == 1
    assert inputs[0] == {
        "kind": InputKind.Source.value,
        "prenormalized_path": str(foo_input),
        "path": foo_input,
        "store_path": None,
        "content_hash": None,
    }
