"""
The `BitcodeExtract` action.
"""

import logging
import os
import subprocess
from typing import List

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class BitcodeExtract(CompilerAction):
    """
    Compile and extract bitcode. The output bitcode file will be located in the same direcory
    as the output executable.
    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        if tool.lang in [Lang.C, Lang.Cxx]:
            args: List[str]
            if tool.outputs:
                args = ["-c", "-emit-llvm", "-o", tool.outputs[0] + ".bc", *tool.inputs]
            else:
                logger.debug(
                    "not extracting bitcode with unspecified output location"
                )  # pragma: no cover
                return # pragma: no cover

            bitcode_flags = os.getenv("LLVM_BITCODE_GENERATION_FLAGS")
            if bitcode_flags:
                args.extend(bitcode_flags.split())

            subprocess.run([tool.wrapped_tool(), *args], env=tool._env)
        else:
            logger.debug("not extracting bitcode for an unknown language")
