"""
Helper utilities for canker.
"""

import contextlib
import fcntl
import os
import shlex
import sys

from canker.exceptions import CankerError


def die(message):
    """
    Aborts the program with a final message.

    Args:
        message (str): The message to print
    """
    print(f"Fatal: {message}", file=sys.stderr)
    sys.exit(1)


def rindex(items, needle):
    """
    Args:
        items (iterator): The items to search
        needle (object): The object to search for

    Returns:
        The rightmost index of `needle`, or `None`.
    """
    for idx, item in enumerate(reversed(items)):
        if item == needle:
            return len(items) - idx - 1
    return None


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
    Loads any canker actions requested via the environment.

    Each action is loaded from the `CANKER_ACTIONS` environment variable,
    separated by colons.

    For example, the following loads the `Record` and `Benchmark` actions:

    ```bash
    CANKER_ACTIONS="Record:Benchmark"
    ```

    Each action additionally receives a configuration dictionary from
    `CANKER_ACTION_{UPPERCASE_NAME}`. The contents of each of these variables
    is shell-quoted, in `key=value` format.

    For example, the following:

    ```bash
    CANKER_ACTION_RECORD="output=/tmp/whatever.jsonl"
    ```

    yields the following configuration dictionary:

    ```python
    {"output": "/tmp/whatever.jsonl"}
    ```

    Returns:
        A list of `canker.action.Action`s.
    """
    import canker.actions

    action_names = os.getenv("CANKER_ACTIONS")
    if action_names is None:
        return []

    actions = []
    for action_name in action_names.split(":"):
        action_class = getattr(canker.actions, action_name, None)
        if action_class is None:
            raise CankerError(f"Unknown action: {action_name}")

        action_config = os.getenv(f"CANKER_ACTION_{action_name.upper()}", None)
        if action_config is not None:
            action_config = shlex.split(action_config)
            action_config = dict(c.split("=") for c in action_config)
        else:
            action_config = {}

        actions.append(action_class(action_config))
    return actions
