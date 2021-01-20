"""
The `SkipStrip` action.
"""


from blight.action import STRIPAction
from blight.exceptions import SkipRun


class SkipStrip(STRIPAction):
    def before_run(self, tool):
        raise SkipRun
