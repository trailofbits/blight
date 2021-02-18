"""
The `Record` action.
"""

import json
from pathlib import Path

from blight.action import Action
from blight.tool import Tool
from blight.util import flock_append


class Record(Action):
    def after_run(self, tool: Tool, *, run_skipped: bool = False):
        record_file = Path(self._config["output"])

        # TODO(ww): Restructure this dictionary; it should be more like:
        # { run: {...}, tool: {...}}
        tool_record = tool.asdict()
        tool_record["run_skipped"] = run_skipped

        with flock_append(record_file) as io:
            print(json.dumps(tool_record), file=io)
