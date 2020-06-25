import shutil

import pytest


@pytest.fixture(autouse=True)
def canker_env(monkeypatch):
    monkeypatch.setenv("CANKER_WRAPPED_CC", shutil.which("cc"))
    monkeypatch.setenv("CANKER_WRAPPED_CXX", shutil.which("c++"))
    monkeypatch.setenv("CANKER_WRAPPED_CPP", shutil.which("cpp"))
    monkeypatch.setenv("CANKER_WRAPPED_LD", shutil.which("ld"))
    monkeypatch.setenv("CANKER_WRAPPED_AS", shutil.which("as"))
