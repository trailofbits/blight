"""
The `IgnoreWerror` action.
"""

import logging

from blight.action import CompilerAction
from blight.enums import Lang

logger = logging.getLogger(__name__)


class IgnoreWerror(CompilerAction):
    """
    An action for ignoring the `-Werror` flag passed to compiler
    commands (specifically, `cc` and `c++`).

    For example:

    ```bash
    export BLIGHT_WRAPPED_CC=clang
    export BLIGHT_ACTIONS="IgnoreWerror"
    make CC=blight-cc
    ```

    will cause blight to remove `-Werror` arguments from each `clang`
    invocation.
    """

    def before_run(self, tool):
        if tool.lang in [Lang.C, Lang.Cxx]:
            tool.args = [a for a in tool.args if a != "-Werror"]
        else:
            logger.debug("not injecting flags for an unknown language")
