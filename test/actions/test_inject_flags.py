import shlex

from blight.actions import InjectFlags
from blight.tool import CC, CXX


def test_inject_flags():
    inject_flags = InjectFlags(
        {"CFLAGS": "-more -flags", "CXXFLAGS": "-these -are -ignored", "CPPFLAGS": "-foo"}
    )
    cc = CC(["-fake", "-flags"])

    inject_flags.before_run(cc)

    assert cc.args == shlex.split("-fake -flags -more -flags -foo")


def test_inject_flags_cxx():
    inject_flags = InjectFlags(
        {"CFLAGS": "-these -are -ignored", "CXXFLAGS": "-more -flags", "CPPFLAGS": "-bar"}
    )
    cxx = CXX(["-fake", "-flags"])

    inject_flags.before_run(cxx)

    assert cxx.args == shlex.split("-fake -flags -more -flags -bar")


def test_inject_flags_unknown_lang():
    inject_flags = InjectFlags(
        {"CFLAGS": "-these -are -ignored", "CXXFLAGS": "-so -are -these", "CPPFLAGS": "-and -this"}
    )
    cxx = CXX(["-x", "-unknownlanguage"])

    inject_flags.before_run(cxx)

    assert cxx.args == shlex.split("-x -unknownlanguage")
