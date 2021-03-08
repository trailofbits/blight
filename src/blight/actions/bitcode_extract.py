"""
The `BitcodeExtract` action.
"""

import logging
import subprocess
from typing import List

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool, Tool

logger = logging.getLogger(__name__)


class BitcodeExtract(CompilerAction):
    """
    Compile and extract bitcode.
    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        if tool.lang in [Lang.C, Lang.Cxx]:
            args: List[str]
            if tool.outputs:
                args = ["-c", "-emit-llvm", "-o", tool.outputs[0] + ".bc", *tool.inputs]
            else:
                args = ["-c", "-emit-llvm", *tool.inputs]
            subprocess.run([tool.wrapped_tool(), *args], env=tool._env)
        else:
            logger.debug("not extracting bitcode for an unknown language")
