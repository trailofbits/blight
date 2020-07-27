"""
Helper utilities for blight.
"""

import contextlib
import fcntl
import os
import shlex
import sys
from typing import Any, List, Optional, Sequence

from blight.exceptions import BlightError


def die(message):
    """
    Aborts the program with a final message.

    Args:
        message (str): The message to print
    """
    print(f"Fatal: {message}", file=sys.stderr)
    sys.exit(1)


def rindex(items: Sequence[Any], needle: Any) -> Optional[int]:
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


def rindex_prefix(items: Sequence[str], prefix: str) -> Optional[int]:
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


def insert_items_at_idx(parent_items: Sequence[Any], idx: int, items: Sequence[Any]) -> List[Any]:
    """
    Inserts `items` at `idx` in `parent_items`.

    Args:
        parent_items (sequence of any): The parent sequence to insert within
        idx (int): The index to insert at
        items (sequence of any): The items to insert

    Returns:
        A new list containing both the parent and inserted items
    """

    def _insert_items_at_idx(parent_items, idx, items):
        for pidx, item in enumerate(parent_items):
            if pidx != idx:
                print(item)
                yield item
            else:
                for item in items:
                    yield item

    return list(_insert_items_at_idx(parent_items, idx, items))


@contextlib.contextmanager
def flock_append(filename):
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


def load_actions():
    """
    Loads any blight actions requested via the environment.

    Each action is loaded from the `BLIGHT_ACTIONS` environment variable,
    separated by colons.

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
    if action_names is None:
        return []

    actions = []
    for action_name in action_names.split(":"):
        action_class = getattr(blight.actions, action_name, None)
        if action_class is None:
            raise BlightError(f"Unknown action: {action_name}")

        action_config = os.getenv(f"BLIGHT_ACTION_{action_name.upper()}", None)
        if action_config is not None:
            action_config = shlex.split(action_config)
            action_config = dict(c.split("=") for c in action_config)
        else:
            action_config = {}

        actions.append(action_class(action_config))
    return actions
