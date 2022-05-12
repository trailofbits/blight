"""
The `InjectFlags` action.
"""

import logging
import shlex

from blight.action import CompilerAction
from blight.enums import CompilerStage, Lang
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class InjectFlags(CompilerAction):
    """
    An action for injecting flags into compiler commands (specifically, `cc` and `c++`).

    This action takes the following flags in its configuration and appends them
    (after shell-splitting) as appropriate:
    - `CFLAGS`: Flags to append to every C compiler call
    - `CFLAGS_LINKER`: Flags to append to every C compiler call that runs the linking
     stage (i.e: no `-c`, `-e`, `-S`, etc. flags present)
    - `CXXFLAGS`: Same as `CFLAGS` but for C++
    - `CFLAGS_LINKER`: Same as `CFLAGS_LINKER`, but for C++
    - `CPPFLAGS`: Flags to append for the preprocessor stage

    For example:

    ```bash
    export BLIGHT_WRAPPED_CC=clang
    export BLIGHT_ACTIONS="InjectFlags"
    export BLIGHT_ACTION_INJECTFLAGS="CFLAGS='-g -O0' CPPFLAGS='-DWHATEVER'"
    make CC=blight-cc
    ```

    will cause blight to add `-g -O0 -DWHATEVER` to each `clang` invocation
    (unless it's a C++ invocation, e.g. via `-x c++`).
    """

    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        cflags = shlex.split(self._config.get("CFLAGS", ""))
        cflags_linker = shlex.split(self._config.get("CFLAGS_LINKER", ""))
        cxxflags = shlex.split(self._config.get("CXXFLAGS", ""))
        cxxflags_linker = shlex.split(self._config.get("CXXFLAGS_LINKER", ""))
        cppflags = shlex.split(self._config.get("CPPFLAGS", ""))

        if tool.lang == Lang.C:
            tool.args += cflags
            tool.args += cppflags
            if tool.stage is CompilerStage.AllStages:
                tool.args += cflags_linker
        elif tool.lang == Lang.Cxx:
            tool.args += cxxflags
            tool.args += cppflags
            if tool.stage is CompilerStage.AllStages:
                tool.args += cxxflags_linker
        else:
            logger.debug("not injecting flags for an unknown language")
