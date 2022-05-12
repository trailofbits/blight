import shlex

from blight.actions import IgnoreFlags
from blight.tool import CC, CXX


def test_ignore_flags():
    ignore_flags = IgnoreFlags({"FLAGS": "-Wextra -ffunction-sections"})

    for tool in [CC, CXX]:
        tool = CC(["-Wall", "-ffunction-sections", "-O3", "-ffunction-sections", "-Wextra"])
        ignore_flags.before_run(tool)
        assert tool.args == shlex.split("-Wall -O3")


def test_ignore_werror_unknown_lang():
    ignore_flags = IgnoreFlags({"FLAGS": "-Wextra -ffunction-sections"})
    cxx = CXX(["-x", "-unknownlanguage", "-Werror"])

    ignore_flags.before_run(cxx)

    assert cxx.args == shlex.split("-x -unknownlanguage -Werror")
