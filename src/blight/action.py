"""
The different actions supported by blight.
"""

import blight.tool


class Action:
    """
    A generic action, run with every tool (both before and after the tool's execution).
    """

    def __init__(self, config):
        self._config = config

    def _should_run_on(self, tool):
        return True

    def before_run(self, tool):  # pragma: no cover
        """
        Invoked right before the underlying tool is run.

        Args:
            tool (`blight.tool.Tool`): The tool about to run
        """
        pass

    def _before_run(self, tool):
        if self._should_run_on(tool):
            self.before_run(tool)

    def after_run(self, tool):  # pragma: no cover
        """
        Invoked right after the underlying tool is run.

        Args:
            tool (`blight.tool.Tool`): The tool that just ran
        """
        pass

    def _after_run(self, tool):
        if self._should_run_on(tool):
            self.after_run(tool)


class CCAction(Action):
    """
    A `cc` action, run whenever the tool is a `blight.tool.CC` instance.
    """

    def _should_run_on(self, tool):
        return isinstance(tool, blight.tool.CC)


class CXXAction(Action):
    """
    A `c++` action, run whenever the tool is a `blight.tool.CXX` instance.
    """

    def _should_run_on(self, tool):
        return isinstance(tool, blight.tool.CXX)


class CompilerAction(CCAction, CXXAction):
    """
    A generic compiler action, run whenever the tool is a `blight.tool.CC`
    or `blight.tool.CXX` instance.

    **NOTE:** Action writers should generally prefer this over `CCAction` and `CXXAction`,
    as messy builds may use `cc` to compile C++ sources (via `-x c`) and vice versa.
    """

    def _should_run_on(self, tool):
        return isinstance(tool, blight.tool.CC) or isinstance(tool, blight.tool.CXX)


class CPPAction(Action):
    """
    A `cpp` action, run whenever the tool is a `blight.tool.CPP` instance.
    """

    def _should_run_on(self, tool):
        return isinstance(tool, blight.tool.CPP)


class LDAction(Action):
    """
    An `ld` action, run whenever the tool is a `blight.tool.LD` instance.
    """

    def _should_run_on(self, tool):
        return isinstance(tool, blight.tool.LD)


class ASAction(Action):
    """
    An `as` action, run whenever the tool is a `blight.tool.AS` instance.
    """

    def _should_run_on(self, tool):
        return isinstance(tool, blight.tool.AS)
