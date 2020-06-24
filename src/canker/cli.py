import os
import shlex
import sys

import click

import canker.tool
from canker.util import die, which


def _export(variable, value):
    print(f"export {variable}={shlex.quote(value)}")


def _export_guess_wrapped():
    for variable, tool in canker.tool.TOOL_ENV_MAP.items():
        if tool_path := which(tool):
            _export(f"CANKER_WRAPPED_{variable}", tool_path)
        else:
            die(f"Fatal: Couldn't locate {tool} on the $PATH")


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
def env(guess_wrapped):
    if guess_wrapped:
        _export_guess_wrapped()

    for variable, tool in canker.tool.TOOL_ENV_MAP.items():
        _export(variable, f"canker-{tool}")


# NOTE(ww): Specifically *not* a click command!
def tool():
    wrapped_basename = os.path.basename(sys.argv[0])

    if tool_classname := canker.tool.CANKER_TOOL_MAP.get(wrapped_basename):
        tool_class = getattr(canker.tool, tool_classname)
        tool = tool_class(sys.argv[1:])
        tool.run()
    else:
        die(f"Unknown canker wrapper requested: {wrapped_basename}")
