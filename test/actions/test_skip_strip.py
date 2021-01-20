import pytest

from blight.actions import SkipStrip
from blight.exceptions import SkipRun
from blight.tool import CC, STRIP


def test_skip_strip_before_run_raises():
    strip = STRIP(["--help"])
    skip_strip = SkipStrip({})

    with pytest.raises(SkipRun):
        skip_strip.before_run(strip)


def test_skip_strip(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "SkipStrip")
    monkeypatch.setenv("BLIGHT_WRAPPED_STRIP", "true")

    # SkipStrip causes strip runs to be skipped
    strip = STRIP([])
    assert SkipStrip in [a.__class__ for a in strip._actions]
    assert not strip._skip_run
    strip.run()
    assert strip._skip_run

    # SkipStrip doesn't affect other tools
    cc = CC(["-v"])
    assert SkipStrip in [a.__class__ for a in cc._actions]
    assert not cc._skip_run
    cc.run()
    assert not cc._skip_run
