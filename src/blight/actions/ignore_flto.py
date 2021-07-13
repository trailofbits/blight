"""
The `IgnoreFlto` action.
"""

import logging

from blight.action import CompilerAction
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class IgnoreFlto(CompilerAction):
    """
    An action for ignoring the `-flto` flag passed to compiler
    commands (specifically, `cc` and `c++`). Related commands that
    control LTO (`-flto=...`) are also ignored.

    For example:

    ```bash
    export BLIGHT_WRAPPED_CC=clang
    export BLIGHT_ACTIONS="IgnoreFlto"
    make CC=blight-cc
    ```

    will cause blight to remove `-flto` arguments from each `clang`
    invocation.
    """

    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        tool.args = [a for a in tool.args if not a.startswith("-flto")]
