"""
The `Benchmark` action.
"""

import json
import time
from pathlib import Path

from canker.action import Action
from canker.util import flock_append


class Benchmark(Action):
    def before_run(self, tool):
        self._start_nanos = time.monotonic_ns()

    def after_run(self, tool):
        elapsed = (time.monotonic_ns() - self._start_nanos) // 1000

        bench_file = Path(self._config["output"])
        with flock_append(bench_file) as io:
            bench_record = {"tool": tool.wrapped_tool(), "elapsed": elapsed}
            print(json.dumps(bench_record), file=io)
