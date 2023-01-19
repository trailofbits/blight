"""
The different actions supported by blight.
"""

from typing import Any, Dict, Optional

import blight.tool
from blight.tool import Tool


class Action:
    """
    A generic action, run with every tool (both before and after the tool's execution).
    """

    def __init__(self, config: Dict[str, str]):
        self._config = config
        self._result: Optional[Dict[str, Any]] = None

    def _should_run_on(self, tool: Tool) -> bool:
        return True

    def before_run(self, tool: Tool) -> None:  # pragma: no cover
        """
        Invoked right before the underlying tool is run.

        Args:
            tool: The tool about to run
        """
        pass

    def _before_run(self, tool: Tool) -> None:
        if self._should_run_on(tool):
            self.before_run(tool)

    def after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:  # pragma: no cover
        """
        Invoked right after the underlying tool is run.

        Args:
            tool: The tool that just ran
        """
        pass

    def _after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:
        if self._should_run_on(tool):
            self.after_run(tool, run_skipped=run_skipped)

    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """
        Returns the result computed by this action, if there is one.
        """
        return self._result


class CCAction(Action):
    """
    A `cc` action, run whenever the tool is a `blight.tool.CC` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.CC)


class CXXAction(Action):
    """
    A `c++` action, run whenever the tool is a `blight.tool.CXX` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.CXX)


class CompilerAction(CCAction, CXXAction):
    """
    A generic compiler action, run whenever the tool is a `blight.tool.CC`
    or `blight.tool.CXX` instance.

    **NOTE:** Action writers should generally prefer this over `CCAction` and `CXXAction`,
    as messy builds may use `cc` to compile C++ sources (via `-x c`) and vice versa.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, (blight.tool.CC, blight.tool.CXX))


class CPPAction(Action):
    """
    A `cpp` action, run whenever the tool is a `blight.tool.CPP` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.CPP)


class LDAction(Action):
    """
    An `ld` action, run whenever the tool is a `blight.tool.LD` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.LD)


class ASAction(Action):
    """
    An `as` action, run whenever the tool is a `blight.tool.AS` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.AS)


class ARAction(Action):
    """
    An `ar` action, run whenever the tool is a `blight.tool.AR` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.AR)


class STRIPAction(Action):
    """
    A `strip` action, run whenever the tool is a `blight.tool.STRIP` instance.
    """

    def _should_run_on(self, tool: Tool) -> bool:
        return isinstance(tool, blight.tool.STRIP)
