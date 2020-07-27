"""
The `InjectFlags` action.
"""

import logging
import shlex

from blight.action import CompilerAction
from blight.enums import Lang

logger = logging.getLogger(__name__)


class InjectFlags(CompilerAction):
    """
    An action for injecting flags into compiler commands (specifically, `cc` and `c++`).

    This action takes `CFLAGS`, `CXXFLAGS`, and `CPPFLAGS` in its configuration and
    appends them (after shell-splitting) as appropriate.

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

    def before_run(self, tool):
        cflags = shlex.split(self._config.get("CFLAGS", ""))
        cxxflags = shlex.split(self._config.get("CXXFLAGS", ""))
        cppflags = shlex.split(self._config.get("CPPFLAGS", ""))

        if tool.lang == Lang.C:
            tool.args += cflags
            tool.args += cppflags
        elif tool.lang == Lang.Cxx:
            tool.args += cxxflags
            tool.args += cppflags
        else:
            logger.debug("not injecting flags for an unknown language")
