import pytest

from blight import util
from blight.actions import Record
from blight.exceptions import BlightError


def test_die():
    with pytest.raises(SystemExit):
        util.die(":(")


def test_collect_option_values():
    args = ["foo", "-foo", "baz", "-fooquux", "-Dfoo"]

    assert util.collect_option_values(args, "-foo") == [(1, "baz"), (3, "quux")]
    assert util.collect_option_values(args, "-foo", style=util.OptionValueStyle.Mash) == [
        (3, "quux")
    ]
    assert util.collect_option_values(args, "-foo", style=util.OptionValueStyle.Space) == [
        (1, "baz")
    ]

    args = ["foo", "-foo=bar", "-foo", "baz"]
    assert util.collect_option_values(args, "-foo", style=util.OptionValueStyle.EqualOrSpace) == [
        (1, "bar"),
        (2, "baz"),
    ]


def test_rindex():
    assert util.rindex([1, 1, 2, 3, 4, 5], 1) == 1
    assert util.rindex([1, 1, 2, 3, 4, 5], 6) is None
    assert util.rindex([1, 1, 2, 3, 4, 5], 5) == 5


def test_load_actions(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "Record")
    monkeypatch.setenv("BLIGHT_ACTION_RECORD", "key=value key2='a=b'")

    actions = util.load_actions()
    assert len(actions) == 1
    assert actions[0].__class__ == Record
    assert actions[0]._config == {"key": "value", "key2": "a=b"}


def test_load_actions_dedupes(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "Record:Record")

    actions = util.load_actions()
    assert len(actions) == 1


def test_load_actions_preserves_order(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "Benchmark:Record:FindOutputs")

    actions = util.load_actions()
    assert [a.__class__.__name__ for a in actions] == ["Benchmark", "Record", "FindOutputs"]


def test_load_actions_nonexistent(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "ThisActionDoesNotExist")

    with pytest.raises(BlightError):
        util.load_actions()


def test_load_actions_empty_variable(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "")

    actions = util.load_actions()
    assert actions == []


def test_load_actions_empty_config(monkeypatch):
    monkeypatch.setenv("BLIGHT_ACTIONS", "Record")

    actions = util.load_actions()
    assert len(actions) == 1
    assert actions[0].__class__ == Record
    assert actions[0]._config == {}
