"""
Substructural typing protocols for blight.

These are, generally speaking, an implementation detail.
"""

from pathlib import Path
from typing import Dict, List

from typing_extensions import Protocol

from blight.enums import Lang


class CwdProtocol(Protocol):
    @property
    def cwd(self) -> Path:
        ...  # pragma: no cover


class ArgsProtocol(CwdProtocol, Protocol):
    @property
    def args(self) -> List[str]:
        ...  # pragma: no cover


class CanonicalizedArgsProtocol(ArgsProtocol, Protocol):
    @property
    def canonicalized_args(self) -> List[str]:
        ...  # pragma: no cover


class LangProtocol(CanonicalizedArgsProtocol, Protocol):
    @property
    def lang(self) -> Lang:
        ...  # pragma: no cover


class IndexedUndefinesProtocol(CanonicalizedArgsProtocol, Protocol):
    @property
    def indexed_undefines(self) -> Dict[str, int]:
        ...  # pragma: no cover
