import json
import time
from pathlib import Path

from canker.action import Action


class Benchmark(Action):
    def before_run(self, tool):
        self._start_nanos = time.monotonic_ns()

    def after_run(self, tool):
        elapsed = (time.monotonic_ns() - self._start_nanos) // 1000

        bench_file = Path(self._config["output"])
        with bench_file.open("a") as io:
            bench_record = {"tool": tool.wrapped_tool(), "elapsed": elapsed}
            print(json.dumps(bench_record), file=io)
