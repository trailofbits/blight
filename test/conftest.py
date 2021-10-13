import shutil

import pytest


@pytest.fixture(autouse=True)
def blight_env(monkeypatch):
    monkeypatch.setenv("BLIGHT_WRAPPED_CC", shutil.which("cc"))
    monkeypatch.setenv("BLIGHT_WRAPPED_CXX", shutil.which("c++"))
    monkeypatch.setenv("BLIGHT_WRAPPED_CPP", shutil.which("cpp"))
    monkeypatch.setenv("BLIGHT_WRAPPED_LD", shutil.which("ld"))
    monkeypatch.setenv("BLIGHT_WRAPPED_AS", shutil.which("as"))
    monkeypatch.setenv("BLIGHT_WRAPPED_AR", shutil.which("ar"))
    monkeypatch.setenv("BLIGHT_WRAPPED_STRIP", shutil.which("strip"))
    monkeypatch.setenv("BLIGHT_WRAPPED_INSTALL", shutil.which("install"))
