import json
import os
from pathlib import Path

from blight.actions import FindInputs
from blight.enums import InputKind
from blight.tool import CC
from blight.actions.find_inputs import Input
from blight.util import json_helper

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


def test_find_inputs_journaling(monkeypatch, tmp_path):
    journal_output = tmp_path / "journal.jsonl"
    monkeypatch.setenv("BLIGHT_JOURNAL_PATH", str(journal_output))

    foo_input = (tmp_path / "foo.c").resolve()
    foo_input.touch()

    find_inputs = FindInputs({})
    cc = CC(["-c", str(foo_input), "-o", "foo"])
    find_inputs.before_run(cc)
    find_inputs.after_run(cc)

    inputs = find_inputs._result["inputs"]
    assert len(inputs) == 1
    assert inputs[0] == {
        "kind": InputKind.Source.value,
        "prenormalized_path": str(foo_input),
        "path": foo_input,
        "store_path": None,
        "content_hash": None,
    }

def test_serialize_input(tmp_path):
    journal_output = tmp_path / "journal.jsonl"
    foo_input = (tmp_path / "foo.c").resolve()
    input = Input(prenormalized_path="foo.c", kind=InputKind.Source, path=foo_input)
    with open(journal_output, "w") as io:  # type: ignore
        json.dump(input.dict(), io, default=json_helper)
        io.write("\n")
    
    kwargs = json.loads(journal_output.read_text())

    assert Input(**kwargs).dict() == input.dict()