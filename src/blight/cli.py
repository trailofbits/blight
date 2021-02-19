import logging
import os
import shlex
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Iterator, List, Tuple

import click

import blight.tool
from blight.enums import BuildTool
from blight.exceptions import BlightError
from blight.util import die, unswizzled_path

logging.basicConfig(level=os.environ.get("BLIGHT_LOGLEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# A mapping of shim name -> tool name for default shim generation.
# Each shim will ultimately call `blight-{tool}`, completing the interposition.
# fmt: off
SHIM_MAP = {
    # Standard build tool names.
    "cc": BuildTool.CC.value,
    "c++": BuildTool.CXX.value,
    "cpp": BuildTool.CPP.value,
    "ld": BuildTool.LD.value,
    "as": BuildTool.AS.value,
    "ar": BuildTool.AR.value,
    "strip": BuildTool.STRIP.value,

    # GNU shims.
    "gcc": BuildTool.CC.value,
    "g++": BuildTool.CXX.value,
    "gold": BuildTool.LD.value,
    "gas": BuildTool.AS.value,

    # Clang shims.
    "clang": BuildTool.CC.value,
    "clang++": BuildTool.CXX.value,
    "lld": BuildTool.LD.value,
}
# fmt: on


def _unset(variable: str) -> None:
    print(f"unset {variable}")


def _export(variable: str, value: str) -> None:
    value = shlex.quote(value)
    print(f"export {variable}={value}")


def _guess_wrapped() -> Iterator[Tuple[str, str]]:
    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
        tool_path = shutil.which(tool)
        if tool_path is None:
            die(f"Couldn't locate {tool} on the $PATH")

        yield (f"BLIGHT_WRAPPED_{variable}", tool_path)


def _swizzle_path(stubs: List[str], shim_specs: List[str]) -> str:
    blight_dir = Path(tempfile.mkdtemp(suffix=blight.util.SWIZZLE_SENTINEL))

    for shim, tool in SHIM_MAP.items():
        shim_path = blight_dir / shim
        with open(shim_path, "w+") as io:
            print("#!/bin/sh", file=io)
            print(f'blight-{tool} "${{@}}"', file=io)

        shim_path.chmod(shim_path.stat().st_mode | stat.S_IEXEC)

    for shim_spec in shim_specs:
        try:
            (shim, tool) = shim_spec.split(":", 1)
        except ValueError:
            die(f"Malformatted custom shim spec: expected `shim:tool`, got {shim_spec}")

        # Sanity check: our requested tool should be a valid BuildTool.
        if tool not in list(BuildTool):
            die(
                f"Unknown tool requested for shim: {tool} "
                f"(supported tools: {[t.value for t in BuildTool]})"
            )

        if shim in SHIM_MAP:
            logger.warning(f"overriding default shim ({shim}) with custom tool ({tool})")

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

    return f"{blight_dir}:{unswizzled_path()}"


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
@click.option("--swizzle-path", help="Wrap via PATH swizzling", is_flag=True)
@click.option("--stub", "stubs", help="Stub a command out while swizzling", multiple=True)
@click.option("--shim", "shims", help="Add a custom shim while swizzling", multiple=True)
@click.option("--unset", help="Unset the tool variables instead of setting them", is_flag=True)
def env(unset, guess_wrapped, swizzle_path, stubs, shims):
    if guess_wrapped:
        for (variable, value) in _guess_wrapped():
            if variable not in os.environ:
                _export(variable, value)

    if swizzle_path:
        _export("PATH", _swizzle_path(stubs, shims))

    for variable, tool in blight.tool.TOOL_ENV_MAP.items():
        if unset:
            _unset(variable)
        else:
            _export(variable, f"blight-{tool}")


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
@click.option("--swizzle-path", help="Wrap via PATH swizzling", is_flag=True)
@click.option("--stub", "stubs", help="Stub a command out while swizzling", multiple=True)
@click.option("--shim", "shims", help="Add a custom shim while swizzling", multiple=True)
@click.argument("target")
@click.argument("args", nargs=-1)
def exec_(guess_wrapped, swizzle_path, stubs, shims, target, args):
    env = dict(os.environ)

    if guess_wrapped:
        env.update(
            {variable: value for (variable, value) in _guess_wrapped() if variable not in env}
        )

    if swizzle_path:
        env["PATH"] = _swizzle_path(stubs, shims)

    env.update(
        {variable: f"blight-{tool}" for (variable, tool) in blight.tool.TOOL_ENV_MAP.items()}
    )

    os.execvpe(target, [target, *args], env)


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
