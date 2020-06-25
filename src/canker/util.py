import os
import sys
from pathlib import Path

from canker import actions


def die(message):
    print(f"Fatal: {message}", file=sys.stderr)
    sys.exit(1)


def load_actions():
    action_names = os.getenv("CANKER_ACTIONS")
    if action_names is None:
        return []

    action_objects = []
    for action_name in action_names.split(":"):
        if (action_class := getattr(actions, action_name, None)) is None:
            die(f"Unknown action: {action_name}")
        action_objects.append(action_class())
    return action_objects
