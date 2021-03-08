"""
The `BitcodeExtract` action.
"""

import logging
import subprocess

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
            bc_filename = tool.outputs[0] + ".bc" if tool.outputs else "a.out.bc"
            args = ["-S", "-emit-llvm", "-o", bc_filename, *tool.inputs]
            subprocess.run([tool.wrapped_tool(), *args], env=tool._env)
        else:
            logger.debug("not extracting bitcode for an unknown language")
