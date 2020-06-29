import logging
import os
import shlex
import shutil
import sys

import click

import canker.tool
from canker.exceptions import CankerError
from canker.util import die

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())


def _export(variable, value):
    print(f"export {variable}={shlex.quote(value)}")


def _export_guess_wrapped():
    for variable, tool in canker.tool.TOOL_ENV_MAP.items():
        tool_path = shutil.which(tool)
        if tool_path is None:
            die(f"Couldn't locate {tool} on the $PATH")

        _export(f"CANKER_WRAPPED_{variable}", tool_path)


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
def env(guess_wrapped):
    if guess_wrapped:
        _export_guess_wrapped()

    for variable, tool in canker.tool.TOOL_ENV_MAP.items():
        _export(variable, f"canker-{tool}")


def tool():
    # NOTE(ww): Specifically *not* a click command!
    wrapped_basename = os.path.basename(sys.argv[0])

    tool_classname = canker.tool.CANKER_TOOL_MAP.get(wrapped_basename)
    if tool_classname is None:
        die(f"Unknown canker wrapper requested: {wrapped_basename}")

    tool_class = getattr(canker.tool, tool_classname)
    tool = tool_class(sys.argv[1:])
    try:
        tool.run()
    except CankerError as e:
        die(str(e))
