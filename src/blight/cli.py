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
from blight.util import die

logging.basicConfig(level=os.environ.get("BLIGHT_LOGLEVEL", "INFO").upper())


def _export(variable, value, *, quote=True):
    if quote:
        value = shlex.quote(value)
    print(f"export {variable}={value}")


def _export_guess_wrapped():
    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
        tool_path = shutil.which(tool)
        if tool_path is None:
            die(f"Couldn't locate {tool} on the $PATH")

        _export(f"BLIGHT_WRAPPED_{variable}", tool_path)


def _swizzle_path():
    blight_dir = Path(tempfile.mkdtemp(prefix="blight"))

    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
        shim_path = blight_dir / tool
        with open(shim_path, "w+") as io:
            io.write(f'blight-{tool} "${{@}}"\n')

        st = shim_path.stat()
        shim_path.chmod(st.st_mode | stat.S_IEXEC)

    # NOTE(ww): No quotation, to allow $PATH to expand.
    _export("PATH", f"{blight_dir}:$PATH", quote=False)


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
@click.option("--swizzle-path", help="Wrap via PATH swizzling", is_flag=True)
def env(guess_wrapped, swizzle_path):
    if guess_wrapped:
        _export_guess_wrapped()

    if swizzle_path:
        _swizzle_path()

    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
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
