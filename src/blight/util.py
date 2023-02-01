"""
Helper utilities for blight.
"""

from __future__ import annotations

import argparse
import contextlib
import enum
import fcntl
import os
import shlex
import sys
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Iterator, NoReturn, Sequence

if TYPE_CHECKING:
    from blight.action import Action  # pragma: no cover
from blight.exceptions import BlightError

SWIZZLE_SENTINEL = "@blight-swizzle@"


@enum.unique
class OptionValueStyle(enum.Enum):
    """
    A collection of common option formatting styles in build tools.

    This enumeration is not exhaustive.
    """

    Space = enum.auto()
    """
    Options that look like `-O foo`.
    """

    Mash = enum.auto()
    """
    Options that look like `-Ofoo`.
    """

    MashOrSpace = enum.auto()
    """
    Options that look like `-Ofoo` or `-O foo`.
    """

    Equal = enum.auto()
    """
    Options that look like `-O=foo`.
    """

    EqualOrSpace = enum.auto()
    """
    Options that look like `-O=foo` or `-O foo`.
    """

    def permits_equal(self) -> bool:
        return self in [OptionValueStyle.Equal, OptionValueStyle.EqualOrSpace]

    def permits_mash(self) -> bool:
        return self in [OptionValueStyle.Mash, OptionValueStyle.MashOrSpace]

    def permits_space(self) -> bool:
        return self in [
            OptionValueStyle.Space,
            OptionValueStyle.MashOrSpace,
            OptionValueStyle.EqualOrSpace,
        ]


def die(message: str) -> NoReturn:
    """
    Aborts the program with a final message.

    Args:
        message (str): The message to print
    """
    print(f"Fatal: {message}", file=sys.stderr)
    sys.exit(1)


def assert_never(x: NoReturn) -> NoReturn:
    """
    A hint to the typechecker that a branch can never occur.
    """
    assert False, f"unhandled type: {type(x).__name__}"  # pragma: no cover


def collect_option_values(
    args: Sequence[str],
    option: str,
    *,
    style: OptionValueStyle = OptionValueStyle.MashOrSpace,
) -> list[tuple[int, str]]:
    """
    Given a list of arguments, collect the ones that look like options with values.

    Supports multiple option "styles" via `OptionValueStyle`.

    Args:
        args (sequence): The arguments to search
        option (str): The option prefix to search for
        style: (OptionValueStyle): The option style to search for

    Returns:
        A list of tuples of (index, value) for matching options. The index in each
        tuple is the argument index for the option itself.
    """

    # TODO(ww): There are a lot of error cases here. They should be thought out more.

    values: list[tuple[int, str]] = []
    for idx, arg in enumerate(args):
        if not arg.startswith(option):
            continue

        is_exact = arg == option
        if is_exact and style.permits_space():
            # -o foo is the only style that make sense here.
            values.append((idx, args[idx + 1]))
        elif not is_exact:
            # We have -oSOMETHING, where SOMETHING might be:
            # * A "mash", like `-Dfoo`
            # * An equals, like `-D=foo`
            if style.permits_mash():
                # NOTE(ww): Assignment to work around black's confusing formatting.
                suff = len(option)
                values.append((idx, arg[suff:]))
            elif style.permits_equal():
                values.append((idx, arg.split("=", 1)[1]))

    return values


def rindex(items: Sequence[Any], needle: Any) -> int | None:
    """
    Args:
        items (sequence): The items to search
        needle (object): The object to search for

    Returns:
        The rightmost index of `needle`, or `None`.
    """
    for idx, item in enumerate(reversed(items)):
        if item == needle:
            return len(items) - idx - 1
    return None


def rindex_prefix(items: Sequence[str], prefix: str) -> int | None:
    """
    Args:
        items (sequence of str): The items to search
        prefix (str): The prefix to find

    Returns:
        The rightmost index of the element that starts with `prefix`, or `None`
    """
    for idx, item in enumerate(reversed(items)):
        if item.startswith(prefix):
            return len(items) - idx - 1
    return None


def ritem_prefix(items: Sequence[str], prefix: str) -> str | None:
    """
    Args:
        items (sequence of str): The items to search
        prefix (str): The prefix to find

    Returns:
        The rightmost element that starts with `prefix`, or `None`
    """
    for item in reversed(items):
        if item.startswith(prefix):
            return item
    return None


def insert_items_at_idx(parent_items: Sequence[Any], idx: int, items: Sequence[Any]) -> list[Any]:
    """
    Inserts `items` at `idx` in `parent_items`.

    Args:
        parent_items (sequence of any): The parent sequence to insert within
        idx (int): The index to insert at
        items (sequence of any): The items to insert

    Returns:
        A new list containing both the parent and inserted items
    """

    def _insert_items_at_idx(
        parent_items: Sequence[Any], idx: int, items: Sequence[Any]
    ) -> Iterator[Any]:
        for pidx, item in enumerate(parent_items):
            if pidx != idx:
                print(item)
                yield item
            else:
                for item in items:
                    yield item

    return list(_insert_items_at_idx(parent_items, idx, items))


@contextlib.contextmanager
def flock_append(filename: os.PathLike) -> Iterator[IO]:
    """
    Open the given file for appending, acquiring an exclusive lock on it in
    the process.

    Args:
        filename (str): The file to open for appending

    Yields:
        An open fileobject for `filename`
    """
    with open(filename, "a") as io:
        try:
            fcntl.flock(io, fcntl.LOCK_EX)
            yield io
        finally:
            fcntl.flock(io, fcntl.LOCK_UN)


def unswizzled_path() -> str:
    """
    Returns a version of the current `$PATH` with any blight shim paths removed.
    """
    paths = os.getenv("PATH", "").split(os.pathsep)
    paths = [p for p in paths if not Path(p).name.endswith(SWIZZLE_SENTINEL)]

    return os.pathsep.join(paths)


def load_actions() -> list[Action]:
    """
    Loads any blight actions requested via the environment.

    Each action is loaded from the `BLIGHT_ACTIONS` environment variable,
    separated by colons. Duplicate actions are removed.

    For example, the following loads the `Record` and `Benchmark` actions:

    ```bash
    BLIGHT_ACTIONS="Record:Benchmark"
    ```

    Each action additionally receives a configuration dictionary from
    `BLIGHT_ACTION_{UPPERCASE_NAME}`. The contents of each of these variables
    is shell-quoted, in `key=value` format.

    For example, the following:

    ```bash
    BLIGHT_ACTION_RECORD="output=/tmp/whatever.jsonl"
    ```

    yields the following configuration dictionary:

    ```python
    {"output": "/tmp/whatever.jsonl"}
    ```

    Returns:
        A list of `blight.action.Action`s.
    """
    import blight.actions

    action_names = os.getenv("BLIGHT_ACTIONS")
    if not action_names:
        return []

    seen = set()
    actions = []
    for action_name in action_names.split(":"):
        if action_name in seen:
            continue
        seen.add(action_name)

        action_class = getattr(blight.actions, action_name, None)
        if action_class is None:
            raise BlightError(f"Unknown action: {action_name}")

        action_config_raw = os.getenv(f"BLIGHT_ACTION_{action_name.upper()}", None)
        if action_config_raw is not None:
            action_config = shlex.split(action_config_raw)
            action_config = dict(c.split("=", 1) for c in action_config)
        else:
            action_config = {}

        actions.append(action_class(action_config))
    return actions


def json_helper(value: Any) -> Any:
    """
    A `default` helper for Python's `json`, intended to facilitate
    serialization of blight classes.
    """

    if hasattr(value, "asdict"):
        return value.asdict()

    if isinstance(value, Path):
        return str(value)

    raise TypeError


class ArgumentParser(argparse.ArgumentParser):
    """
    A wrapper around `argparse.ArgumentParser` with non-exiting error behavior.

    Parsing errors raise `ValueError` instead.
    """

    def error(self, message: str) -> NoReturn:
        raise ValueError(message)

    def default_namespace(self) -> argparse.Namespace:
        """
        Returns a default `argparse.Namespace`, suitable for contexts where
        argument parsing fails completely.
        """
        defaults = {action.dest: self.get_default(action.dest) for action in self._actions}
        return argparse.Namespace(**defaults)
