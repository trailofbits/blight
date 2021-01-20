import logging
import os
import shlex
import shutil
import stat
import sys
import tempfile
from pathlib import Path

import click

import blight.tool
from blight.exceptions import BlightError
from blight.util import die, unswizzled_path

logging.basicConfig(level=os.environ.get("BLIGHT_LOGLEVEL", "INFO").upper())

# A mapping of shim name -> blight-{tool} for shim generation.
# fmt: off
SHIM_MAP = {
    # Standard build tool names.
    "cc": "cc",
    "c++": "c++",
    "cpp": "cpp",
    "ld": "ld",
    "as": "as",
    "ar": "ar",
    "strip": "strip",

    # GNU shims.
    "gcc": "cc",
    "g++": "c++",
    "gold": "ld",
    "gas": "as",

    # Clang shims.
    "clang": "cc",
    "clang++": "c++",
    "lld": "ld",
}
# fmt: on


def _unset(variable):
    print(f"unset {variable}")


def _export(variable, value):
    value = shlex.quote(value)
    print(f"export {variable}={value}")


def _export_guess_wrapped():
    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
        tool_path = shutil.which(tool)
        if tool_path is None:
            die(f"Couldn't locate {tool} on the $PATH")

        _export(f"BLIGHT_WRAPPED_{variable}", tool_path)


def _swizzle_path(stubs):
    blight_dir = Path(tempfile.mkdtemp(suffix=blight.util.SWIZZLE_SENTINEL))

    for shim, tool in SHIM_MAP.items():
        shim_path = blight_dir / shim
        with open(shim_path, "w+") as io:
            print("#!/bin/sh", file=io)
            print(f'blight-{tool} "${{@}}"', file=io)

        shim_path.chmod(shim_path.stat().st_mode | stat.S_IEXEC)

    for stub in stubs:
        stub_path = blight_dir / stub
        with open(stub_path, "w+") as io:
            print("#!/bin/sh", file=io)
            print("true", file=io)

        stub_path.chmod(stub_path.stat().st_mode | stat.S_IEXEC)

    _export("PATH", f"{blight_dir}:{unswizzled_path()}")


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
@click.option("--swizzle-path", help="Wrap via PATH swizzling", is_flag=True)
@click.option("--stub", help="Stub a command out while swizzling", multiple=True)
@click.option("--unset", help="Unset the tool variables instead of setting them", is_flag=True)
def env(unset, guess_wrapped, swizzle_path, stub):
    if guess_wrapped:
        _export_guess_wrapped()

    if swizzle_path:
        _swizzle_path(stub)

    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
        if unset:
            _unset(variable)
        else:
            _export(variable, f"blight-{tool}")


def tool():
    # NOTE(ww): Specifically *not* a click command!
    wrapped_basename = os.path.basename(sys.argv[0])

    tool_classname = blight.tool.BLIGHT_TOOL_MAP.get(wrapped_basename)
    if tool_classname is None:
        die(f"Unknown blight wrapper requested: {wrapped_basename}")

    tool_class = getattr(blight.tool, tool_classname)
    tool = tool_class(sys.argv[1:])
    try:
        tool.run()
    except BlightError as e:
        die(str(e))
