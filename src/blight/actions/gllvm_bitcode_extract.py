"""
The `GLLVMBitcodeExtract` action.
"""

import logging
import os

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool, Tool

logger = logging.getLogger(__name__)


class GLLVMBitcodeExtract(CompilerAction):
    """
    Compile and extract bitcode with GLLVM.
    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        if tool.lang in [Lang.C, Lang.Cxx]:
            os.environ.update(
                {
                    "BLIGHT_WRAPPED_CC": "gclang",
                    "BLIGHT_WRAPPED_CXX": "gclang++",
                    # NOTE(sonya): both WLLVM and GLLVM use WLLVM_BC_STORE
                    "WLLVM_BC_STORE": str(tool.cwd),
                }
            )

            # Update the environment so WLLVM_BC_STORE is defined
            tool._env = tool._fixup_env()
        else:
            logger.debug("not extracting bitcode for an unknown language")

    def after_run(self, tool: Tool, *, run_skipped: bool = False):
        # TODO(sonya): Change name of bitcode file to something besides
        #  the hash of the path to the original bitcode file
        pass
