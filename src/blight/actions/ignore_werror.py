"""
The `IgnoreWerror` action.
"""

import logging

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool

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

    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        if tool.lang in [Lang.C, Lang.Cxx]:
            tool.args = [a for a in tool.args if a != "-Werror"]
        else:
            logger.debug("not injecting flags for an unknown language")
