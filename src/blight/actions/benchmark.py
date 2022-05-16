"""
The `Benchmark` action.
"""

import time
from pathlib import Path

from pydantic import BaseModel

from blight.action import Action
from blight.tool import Tool
from blight.util import flock_append


class BenchmarkRecord(BaseModel):
    """
    Represents a single `Benchmark` record. Each record contains a representation
    of the tool invocation, the elapsed time between the `before_run`
    and `after_run` handlers (in milliseconds), and a flag indicating whether
    the underlying tool was actually run.
    """

    tool: Tool
    """
    The `Tool` invocation.
    """

    elapsed: int
    """
    The invocation's runtime, in milliseconds.
    """

    run_skipped: bool
    """
    Whether or not the tool was actually run.
    """

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {Tool: lambda t: t.asdict()}


class Benchmark(Action):
    def before_run(self, tool: Tool) -> None:
        self._start_nanos = time.monotonic_ns()

    def after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:
        elapsed = (time.monotonic_ns() - self._start_nanos) // 1000
        bench = BenchmarkRecord(tool=tool, elapsed=elapsed, run_skipped=run_skipped)

        if tool.is_journaling():
            self._result = bench.dict()
        else:
            bench_file = Path(self._config["output"])
            with flock_append(bench_file) as io:
                print(bench.json(), file=io)
