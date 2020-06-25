import os
import subprocess

from canker.util import die, load_actions

CANKER_TOOL_MAP = {
    "canker-cc": "CC",
    "canker-cxx": "CXX",
    "canker-cpp": "CPP",
    "canker-ld": "LD",
    "canker-as": "AS",
}

TOOL_ENV_MAP = {
    "CC": "cc",
    "CXX": "c++",
    "CPP": "cpp",
    "LD": "ld",
    "as": "as",
}

TOOL_ENV_WRAPPER_MAP = {
    "CC": "CANKER_WRAPPED_CC",
    "CXX": "CANKER_WRAPPED_CXX",
    "CPP": "CANKER_WRAPPED_CPP",
    "LD": "CANKER_WRAPPED_LD",
    "AS": "CANKER_WRAPPED_AS",
}


class Tool:
    @classmethod
    def wrapped_tool(cls):
        wrapped_tool = os.getenv(TOOL_ENV_WRAPPER_MAP[cls.__name__])
        if wrapped_tool is None:
            die(f"No wrapped tool found for {TOOL_ENV_MAP[cls.__name__]}")

    def __init__(self, args):
        if self.__class__ == Tool:
            raise TypeError(f"can't instantiate {self.__class__.__name__} directly")
        self.args = args
        self._actions = load_actions()

    def _before_run(self):
        for action in self._actions:
            action._before_run(self)

    def _after_run(self):
        for action in self._actions:
            action._after_run(self)

    def run(self):
        self._before_run()

        subprocess.run([self.wrapped_tool(), *self.args])

        self._after_run()


class CompilerTool(Tool):
    pass


class CC(CompilerTool):
    pass


class CXX(CompilerTool):
    pass


class CPP(Tool):
    pass


class LD(Tool):
    pass


class AS(Tool):
    pass
