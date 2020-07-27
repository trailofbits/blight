"""
Substructural typing protocols for blight.

These are, generally speaking, an implementation detail.
"""

from typing import Dict, List

from typing_extensions import Protocol

from blight.enums import Lang


class ArgsProtocol(Protocol):
    @property
    def args(self) -> List[str]:
        ...  # pragma: no cover


class LangProtocol(ArgsProtocol, Protocol):
    @property
    def lang(self) -> Lang:
        ...  # pragma: no cover


class IndexedUndefinesProtocol(ArgsProtocol, Protocol):
    @property
    def indexed_undefines(self) -> Dict[str, int]:
        ...  # pragma: no cover
