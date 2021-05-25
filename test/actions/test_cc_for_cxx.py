import shlex

from blight.actions import CCForCXX
from blight.tool import CC


def test_cc_for_cxx():
    cc_for_cxx = CCForCXX({})
    cc = CC(["-std=c++17", "foo.cpp"])

    cc_for_cxx.before_run(cc)

    assert cc.args == shlex.split("-x c++ -std=c++17 foo.cpp")


def test_cc_for_cxx_does_not_inject():
    cc_for_cxx = CCForCXX({})
    cc = CC(["-std=c99", "foo.c"])

    cc_for_cxx.before_run(cc)

    assert cc.args == shlex.split("-std=c99 foo.c")
