import pytest

from blight import action, tool


@pytest.mark.parametrize(
    ("action_class", "tool_class", "should_run_on"),
    [
        (action.Action, tool.CC, True),
        (action.CCAction, tool.CC, True),
        (action.CXXAction, tool.CC, False),
        (action.CompilerAction, tool.CC, True),
        (action.CPPAction, tool.CC, False),
        (action.LDAction, tool.CC, False),
        (action.ASAction, tool.CC, False),
    ],
)
def test_should_run_on(action_class, tool_class, should_run_on):
    action = action_class({})
    tool = tool_class([])

    assert action._should_run_on(tool) == should_run_on
