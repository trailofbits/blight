"""
The `EmbedBitcode` action.
"""

import logging

from blight.action import CompilerAction
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class EmbedBitcode(CompilerAction):
    """
    An action to embed bitcode in compiler tool outputs.

    This action assumes that the compiler toolchain is LLVM based, and supports
    the `-fembed-bitcode` option. It injects `-fembed-bitcode` into each invocation,
    and lets the compiler tools take care of the rest.

    Example:

    ```bash
    export BLIGHT_ACTIONS="EmbedBitcode"
    make CC=blight-cc
    ```
    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        # TODO(ww): It probably makes sense to sanity check the arguments here,
        # just in case the build is being run with some other flags that are
        # relevant to bitcode generation (e.g. `-emit-llvm` or `-flto`).
        tool.args = ["-fembed-bitcode", *tool.args]
