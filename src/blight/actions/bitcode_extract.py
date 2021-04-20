"""
The `BitcodeExtract` action.
"""

import hashlib
import logging
import subprocess
from pathlib import Path
from typing import List

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class BitcodeExtract(CompilerAction):
    """
    Action to compile and extract bitcode.

    The output bitcode file will be located placed in directory specified by `store=/some/dir/`.
    The setting is passed in the `FindActions` configuration. If `store` is not specified the
    action will produce not output. Similarly, if `llvm-bitcode-flags` is specified the
    corresponding flags will be passed when the bitcode is extracted.

    Example:

    ```bash
    export BLIGHT_ACTIONS="BitcodeExtract"
    BLIGHT_ACTION_BITCODEEXTRACT="store=/path/to/dst/dir llvm-bitcode-flags='-flto'"
    make CC=blight-cc

    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        store = self._config.get("store")
        bitcode_flags = shlex.split(self._config.get("llvm-bitcode-flags", ""))

        if store is None:
            logger.error("not extracting bitcode to an unspecified location")
            return

        if tool.lang not in [Lang.C, Lang.Cxx]:
            logger.debug("not extracting bitcode for an unknown language")
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
