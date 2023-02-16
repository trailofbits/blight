"""
The `Record` action.

`Record` produces a transcript of each tool's invocation. It supports
both journaling and a custom output path.

Configuration:

* `output`: a path on disk that each `Record` step's output will be written to

"""

import json
from pathlib import Path

from blight.action import Action
from blight.tool import Tool
from blight.util import flock_append


class Record(Action):
    def after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:
        # TODO(ww): Restructure this dictionary; it should be more like:
        # { run: {...}, tool: {...}}
        tool_record = tool.asdict()
        tool_record["run_skipped"] = run_skipped

        if tool.is_journaling():
            self._result = tool_record
        else:
            record_file = Path(self._config["output"])
            with flock_append(record_file) as io:
                print(json.dumps(tool_record), file=io)
