import os
import shlex
import sys

import canker.actions


def die(message):
    print(f"Fatal: {message}", file=sys.stderr)
    sys.exit(1)


def rindex(items, needle):
    for idx, item in enumerate(reversed(items)):
        if item == needle:
            return len(items) - idx - 1
    return None


def load_actions():
    action_names = os.getenv("CANKER_ACTIONS")
    if action_names is None:
        return []

    actions = []
    for action_name in action_names.split(":"):
        action_class = getattr(canker.actions, action_name, None)
        if action_class is None:
            die(f"Unknown action: {action_name}")

        action_config = os.getenv(f"CANKER_ACTION_{action_name.upper()}", None)
        if action_config is not None:
            action_config = shlex.split(action_config)
            action_config = dict(c.split("=") for c in action_config)
        else:
            action_config = {}

        actions.append(action_class(action_config))
    return actions
