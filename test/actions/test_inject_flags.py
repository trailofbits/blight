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


def test_inject_linker_flags():
    inject_flags = InjectFlags(
        {
            "CFLAGS": "-cc-flags",
            "CFLAGS_LINKER": "-c-linker-flags",
            "CXXFLAGS": "-cxx-flags",
            "CXXFLAGS_LINKER": "-cxx-linker-flags",
        }
    )

    cc_nolink = CC(["-c"])
    cc_link = CC(["-fake", "-flags"])
    cxx_nolink = CXX(["-c"])
    cxx_link = CXX(["-fake", "-flags"])

    inject_flags.before_run(cc_nolink)
    inject_flags.before_run(cc_link)
    inject_flags.before_run(cxx_nolink)
    inject_flags.before_run(cxx_link)

    assert cc_nolink.args == shlex.split("-c -cc-flags")
    assert cc_link.args == shlex.split("-fake -flags -cc-flags -c-linker-flags")
    assert cxx_nolink.args == shlex.split("-c -cxx-flags")
    assert cxx_link.args == shlex.split("-fake -flags -cxx-flags -cxx-linker-flags")


def test_inject_flags_unknown_lang():
    inject_flags = InjectFlags(
        {"CFLAGS": "-these -are -ignored", "CXXFLAGS": "-so -are -these", "CPPFLAGS": "-and -this"}
    )
    cxx = CXX(["-x", "-unknownlanguage"])

    inject_flags.before_run(cxx)

    assert cxx.args == shlex.split("-x -unknownlanguage")
