"""
The `ExtractBitcode` action.
"""

import hashlib
import logging
import shlex
import subprocess
from pathlib import Path
from typing import List

from blight.action import CompilerAction
from blight.enums import CompilerStage
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class ExtractBitcode(CompilerAction):
    """
    Action to compile and extract bitcode.

    The output bitcode file will be located placed in directory specified by `store=/some/dir/`.
    The setting is passed in the `FindActions` configuration. If `store` is not specified the
    action will produce not output. Similarly, if `llvm-bitcode-flags` is specified the
    corresponding flags will be passed when the bitcode is extracted.

    Example:

    ```bash
    export BLIGHT_ACTIONS="ExtractBitcode"
    BLIGHT_ACTION_BITCODEEXTRACT="store=/path/to/dst/dir llvm-bitcode-flags='-flto'"
    make CC=blight-cc

    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        store = self._config.get("store")
        bitcode_flags = shlex.split(self._config.get("llvm-bitcode-flags", ""))

        if store is None:
            logger.error("not extracting bitcode to an unspecified location")
            return

        if tool.stage not in [CompilerStage.AllStages, CompilerStage.CompileObject]:
            logger.debug(f"not extracting bitcode for compiler stage: {tool.stage}")
            return

        for inpt in tool.inputs:
            args: List[str]
            content_hash = hashlib.sha256(Path(inpt).read_bytes()).hexdigest()
            args = [
                "-c",
                "-emit-llvm",
                "-o",
                store + "/" + content_hash + ".bc",
                inpt,
            ]

            args.extend(bitcode_flags)

            subprocess.run([tool.wrapped_tool(), *args], env=tool._env)
