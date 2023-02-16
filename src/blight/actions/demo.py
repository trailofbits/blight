"""
The `Demo` action.
"""

import sys

from blight.action import Action
from blight.tool import Tool


class Demo(Action):
    def before_run(self, tool: Tool) -> None:
        print(f"[demo] before-run: {tool.wrapped_tool()}", file=sys.stderr)

    def after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:
        print(f"[demo] after-run: {tool.wrapped_tool()}", file=sys.stderr)
