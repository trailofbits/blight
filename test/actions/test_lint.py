import shlex

import pretend
import pytest

from blight.actions import lint
from blight.tool import CC


@pytest.mark.parametrize(
    "macro", ["-DFORTIFY_SOURCE", "-D FORTIFY_SOURCE", "-DFORTIFY_SOURCE=1", "-D FORTIFY_SOURCE=2"]
)
def test_lint(monkeypatch, macro):
    logger = pretend.stub(warning=pretend.call_recorder(lambda s: None))
    monkeypatch.setattr(lint, "logger", logger)

    lint_ = lint.Lint({})
    cc = CC([*shlex.split(macro), "-std=c++17", "foo.cpp"])

    lint_.before_run(cc)
    assert logger.warning.calls == [
        pretend.call("found -DFORTIFY_SOURCE; you probably meant: -D_FORTIFY_SOURCE")
    ]
