import json
import shutil

from canker.actions import Record
from canker.tool import CC


def test_record(tmp_path):
    output = tmp_path / "record.jsonl"
    record = Record({"output": output})

    record.before_run(CC(["-fake", "-flags"]))

    record_contents = json.loads(output.read_text())
    assert record_contents["wrapped_tool"] == shutil.which("cc")
    assert record_contents["args"] == ["-fake", "-flags"]
