"""
The `Lint` action.
"""

import logging

from blight.action import CompilerAction
from blight.tool import CompilerTool

logger = logging.getLogger(__name__)


class Lint(CompilerAction):
    """
    A "linting" action for common command-line mistakes.

    At the moment, this catches mistakes like:

    * `-DFORTIFY_SOURCE=...` instead of `-D_FORTIFY_SOURCE=...`

    For example:

    ```bash
    export BLIGHT_WRAPPED_CC=clang
    export BLIGHT_ACTIONS="Lint"
    make CC=blight-cc
    ```
    """

    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: CompilerTool) -> None:  # type: ignore
        for name, _ in tool.defines:
            # TODO: Maybe do something more drastic here, like stopping the run.
            if name == "FORTIFY_SOURCE":
                logger.warning("found -DFORTIFY_SOURCE; you probably meant: -D_FORTIFY_SOURCE")
