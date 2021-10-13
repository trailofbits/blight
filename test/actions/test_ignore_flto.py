import shlex

from blight.actions import IgnoreFlto
from blight.tool import CC


def test_ignore_werror():
    ignore_flto = IgnoreFlto({})
    cc = CC(["-Wall", "-Werror", "-flto", "-flto=thin", "-O3"])

    ignore_flto.before_run(cc)

    assert cc.args == shlex.split("-Wall -Werror -O3")
