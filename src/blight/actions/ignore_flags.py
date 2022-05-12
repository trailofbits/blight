"""
The `IgnoreFlags` action.
"""

import logging
import shlex

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class IgnoreFlags(CompilerAction):
    """
    An action for ignoring specific flags passed to compiler
    commands (specifically, `cc` and `c++`).

    For example:

    ```bash
    export BLIGHT_WRAPPED_CC=clang
    export BLIGHT_ACTIONS="IgnoreFlags"
    export BLIGHT_ACTIONS_IGNOREFLAGS="FLAGS='-Werror -ffunction-sections'"
    make CC=blight-cc
    ```

    will cause blight to remove `-Werror` and `--ffunction-sections` arguments
    from each `clang` invocation.
    """

    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        ignore_flags = shlex.split(self._config.get("FLAGS", ""))
        if tool.lang in [Lang.C, Lang.Cxx]:
            tool.args = [a for a in tool.args if a not in ignore_flags]
        else:
            logger.debug("not ignoring flags for an unknown language")
