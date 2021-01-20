import pytest

from blight import action, tool


@pytest.mark.parametrize(
    ("action_class", "tool_class", "should_run_on"),
    [
        (action.Action, tool.CC, True),
        (action.CCAction, tool.CC, True),
        (action.CCAction, tool.CXX, False),
        (action.CXXAction, tool.CXX, True),
        (action.CXXAction, tool.CC, False),
        (action.CompilerAction, tool.CC, True),
        (action.CompilerAction, tool.CXX, True),
        (action.CompilerAction, tool.CPP, False),
        (action.CPPAction, tool.CC, False),
        (action.CPPAction, tool.CPP, True),
        (action.LDAction, tool.CC, False),
        (action.LDAction, tool.LD, True),
        (action.ASAction, tool.CC, False),
        (action.ASAction, tool.AS, True),
        (action.ARAction, tool.CC, False),
        (action.ARAction, tool.AR, True),
        (action.STRIPAction, tool.CC, False),
        (action.STRIPAction, tool.STRIP, True),
    ],
)
def test_should_run_on(action_class, tool_class, should_run_on):
    action = action_class({})
    tool = tool_class([])

    assert action._should_run_on(tool) == should_run_on
