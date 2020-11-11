import shlex

from blight.actions import IgnoreWerror
from blight.tool import CC, CXX


def test_ignore_werror():
    ignore_werror = IgnoreWerror({})
    cc = CC(["-Wall", "-Werror", "-O3", "-Werror"])

    ignore_werror.before_run(cc)

    assert cc.args == shlex.split("-Wall -O3")


def test_ignore_werror_cxx():
    ignore_werror = IgnoreWerror({})
    cxx = CXX(["-Wall", "-Werror", "-O3", "-Werror"])

    ignore_werror.before_run(cxx)

    assert cxx.args == shlex.split("-Wall -O3")


def test_ignore_werror_unknown_lang():
    ignore_werror = IgnoreWerror({})
    cxx = CXX(["-x", "-unknownlanguage", "-Werror"])

    ignore_werror.before_run(cxx)

    assert cxx.args == shlex.split("-x -unknownlanguage -Werror")
