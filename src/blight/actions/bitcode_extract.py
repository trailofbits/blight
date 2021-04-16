"""
The `BitcodeExtract` action.
"""

import hashlib
import logging
import os
import subprocess
from pathlib import Path
from typing import List

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class BitcodeExtract(CompilerAction):
    """
    Compile and extract bitcode. The output bitcode file will be located placed in directory
    specified by `store=/some/dir/`. The setting is passed in the `FindActions` configuration.
    If `store` is not specified the action will error.
    """

    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        store = self._config.get("store")

        if store is None:
            logger.debug("not extracting bitcode to an unspecified location")  # pragma: no cover
            assert False  # pragma: no cover

        if tool.lang not in [Lang.C, Lang.Cxx]:
            logger.debug("not extracting bitcode for an unknown language")

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

            bitcode_flags = os.getenv("LLVM_BITCODE_GENERATION_FLAGS")
            if bitcode_flags:
                args.extend(bitcode_flags.split())

            subprocess.run([tool.wrapped_tool(), *args], env=tool._env)
