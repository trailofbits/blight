"""
The `Record` action.
"""

import json
from pathlib import Path

from canker.action import Action
from canker.util import flock_append


class Record(Action):
    def before_run(self, tool):
        record_file = Path(self._config["output"])

        with flock_append(record_file) as io:
            print(json.dumps(tool.asdict()), file=io)
