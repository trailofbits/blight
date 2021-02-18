"""
The `SkipStrip` action.
"""


from blight.action import STRIPAction
from blight.exceptions import SkipRun
from blight.tool import STRIP


class SkipStrip(STRIPAction):
    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: STRIP) -> None:  # type: ignore
        raise SkipRun
