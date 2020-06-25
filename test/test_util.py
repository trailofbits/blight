import pytest

from canker import util
from canker.actions import Record


def test_die():
    with pytest.raises(SystemExit):
        util.die(":(")


def test_rindex():
    assert util.rindex([1, 1, 2, 3, 4, 5], 1) == 1
    assert util.rindex([1, 1, 2, 3, 4, 5], 6) is None
    assert util.rindex([1, 1, 2, 3, 4, 5], 5) == 5


def test_load_actions(monkeypatch):
    monkeypatch.setenv("CANKER_ACTIONS", "Record")
    monkeypatch.setenv("CANKER_ACTION_RECORD", "key=value")

    actions = util.load_actions()
    assert len(actions) == 1
    assert actions[0].__class__ == Record
    assert actions[0]._config == {"key": "value"}


def test_load_actions_nonexistent(monkeypatch):
    monkeypatch.setenv("CANKER_ACTIONS", "ThisActionDoesNotExist")

    with pytest.raises(SystemExit):
        util.load_actions()


def test_load_actions_empty_config(monkeypatch):
    monkeypatch.setenv("CANKER_ACTIONS", "Record")

    actions = util.load_actions()
    assert len(actions) == 1
    assert actions[0].__class__ == Record
    assert actions[0]._config == {}
