import time

from canker.action import Action


class Benchmark(Action):
    def before_run(self, tool):
        self._start_nanos = time.monotonic_ns()

    def after_run(self, tool):
        stop_millis = (time.monotonic_ns() - self._start_nanos) // 1000
        print(stop_millis)
