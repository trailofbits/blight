import json
import shutil

from blight.actions import Record
from blight.tool import CC


def test_record(tmp_path):
    output = tmp_path / "record.jsonl"
    record = Record({"output": output})

    record.after_run(CC(["-fake", "-flags"]), run_skipped=False)

    record_contents = json.loads(output.read_text())
    assert record_contents["wrapped_tool"] == shutil.which("cc")
    assert record_contents["args"] == ["-fake", "-flags"]
    assert not record_contents["run_skipped"]
