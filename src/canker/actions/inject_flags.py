"""
The `InjectFlags` action.
"""

import logging
import shlex

from canker.action import CompilerAction
from canker.enums import Lang

logger = logging.getLogger(__name__)


class InjectFlags(CompilerAction):
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
