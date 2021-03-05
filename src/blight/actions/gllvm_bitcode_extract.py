"""
The `GLLVMBitcodeExtract` action.
"""

import logging
import os

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class GLLVMBitcodeExtract(CompilerAction):
    """
    Compile and extract bitcode with GLLVM.
    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        if tool.lang in [Lang.C, Lang.Cxx]:
            # TODO(sonya): emits bitcode only (no binary)
            tool.args.extend(["-emit-llvm", "-c"])
            os.environ.update(
                {
                    "BLIGHT_WRAPPED_CC": "gclang",
                    "BLIGHT_WRAPPED_CXX": "gclang++",
                }
            )
        else:
            logger.debug("not extracting bitcode for an unknown language")
