from typing import List

from typing_extensions import Protocol

from canker.enums import Lang


class ArgsProtocol(Protocol):
    @property
    def args(self) -> List[str]:
        ...  # pragma: no cover


class LangProtocol(Protocol):
    # NOTE(ww): This is a little silly, but neither inheriting from `ArgsProtocol`
    # nor `self: ArgsProtocol` for `lang` works.
    args: List[str]

    @property
    def lang(self) -> Lang:
        ...  # pragma: no cover
