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
from blight.enums import BlightTool, BuildTool
from blight.exceptions import BlightError
from blight.util import die, unswizzled_path

logging.basicConfig(level=os.environ.get("BLIGHT_LOGLEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Particularly common clang version suffixes.
CLANG_VERSION_SUFFIXES = ["3.8", "7", "9", "10", "11", "12", "13", "14", "15"]

# A mapping of shim name -> tool name for default shim generation.
# Each shim will ultimately call `blight-{tool}`, completing the interposition.
# fmt: off
SHIM_MAP = {
    # Standard build tool names.
    "cc": BuildTool.CC,
    "c++": BuildTool.CXX,
    "cpp": BuildTool.CPP,
    "ld": BuildTool.LD,
    "as": BuildTool.AS,
    "ar": BuildTool.AR,
    "strip": BuildTool.STRIP,
    "install": BuildTool.INSTALL,

    # GNU shims.
    "gcc": BuildTool.CC,
    "g++": BuildTool.CXX,
    "gold": BuildTool.LD,
    "gas": BuildTool.AS,

    # Clang shims.
    "clang": BuildTool.CC,
    **{f"clang-{v}": BuildTool.CC for v in CLANG_VERSION_SUFFIXES},
    "clang++": BuildTool.CXX,
    **{f"clang++-{v}": BuildTool.CXX for v in CLANG_VERSION_SUFFIXES},
    "lld": BuildTool.LD,
}
# fmt: on


def _unset(variable: str) -> None:
    print(f"unset {variable}")


def _export(variable: str, value: str) -> None:
    value = shlex.quote(value)
    print(f"export {variable}={value}")


def _guess_wrapped() -> Iterator[Tuple[str, str]]:
    for tool in BuildTool:
        tool_path = os.getenv(tool.env)
        if tool_path is None:
            tool_path = shutil.which(tool.cmd)
            if tool_path is None:
                die(f"Couldn't locate {tool} on the $PATH")

        yield (tool.blight_tool.env, tool_path)


def _swizzle_path(stubs: List[str], shim_specs: List[str]) -> str:
    blight_dir = Path(tempfile.mkdtemp(suffix=blight.util.SWIZZLE_SENTINEL))

    for shim, tool in SHIM_MAP.items():
        shim_path = blight_dir / shim
        with open(shim_path, "w+") as io:
            print("#!/bin/sh", file=io)
            print(f'{tool.blight_tool.value} "${{@}}"', file=io)

        shim_path.chmod(shim_path.stat().st_mode | stat.S_IEXEC)

    for shim_spec in shim_specs:
        try:
            (shim, tool_name) = shim_spec.split(":", 1)
            tool = BuildTool(tool_name.upper())
        except ValueError:
            die(
                f"Malformatted custom shim spec: expected `shim:tool`, got {shim_spec} "
                f"(supported tools: {[t.value for t in BuildTool]})"
            )

        if shim in SHIM_MAP:
            logger.warning(f"overriding default shim ({shim}) with custom tool ({tool})")

        shim_path = blight_dir / shim
        with open(shim_path, "w+") as io:
            print("#!/bin/sh", file=io)
            print(f'{tool.blight_tool.value} "${{@}}"', file=io)

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
def env(
    unset: bool, guess_wrapped: bool, swizzle_path: bool, stubs: List[str], shims: List[str]
) -> None:
    if guess_wrapped:
        for variable, value in _guess_wrapped():
            if variable not in os.environ:
                _export(variable, value)

    if swizzle_path:
        _export("PATH", _swizzle_path(stubs, shims))

    for tool in BuildTool:
        if unset:
            _unset(tool.env)
        else:
            _export(tool.env, tool.blight_tool.value)


@click.command()
@click.option(
    "--guess-wrapped", help="Attempt to guess the appropriate programs to wrap", is_flag=True
)
@click.option("--swizzle-path", help="Wrap via PATH swizzling", is_flag=True)
@click.option(
    "--stub", "stubs", metavar="STUB", help="Stub a command out while swizzling", multiple=True
)
@click.option(
    "--shim", "shims", metavar="SHIM", help="Add a custom shim while swizzling", multiple=True
)
@click.option("--action", "actions", metavar="ACTION", help="Enable an action", multiple=True)
@click.option(
    "--journal-path",
    metavar="PATH",
    help="The path to use for action journaling",
    type=click.Path(dir_okay=False, exists=False, path_type=Path),
)
@click.argument("target")
@click.argument("args", nargs=-1)
def exec_(
    guess_wrapped: bool,
    swizzle_path: bool,
    stubs: List[str],
    shims: List[str],
    actions: List[str],
    journal_path: click.Path,
    target: str,
    args: List[str],
) -> None:
    env = dict(os.environ)

    if guess_wrapped:
        env.update(
            {variable: value for (variable, value) in _guess_wrapped() if variable not in env}
        )

    if swizzle_path:
        env["PATH"] = _swizzle_path(stubs, shims)

    if len(actions) > 0:
        env["BLIGHT_ACTIONS"] = ":".join(actions)

    if journal_path is not None:
        env["BLIGHT_JOURNAL_PATH"] = str(journal_path)

    env.update({tool.env: tool.blight_tool.value for tool in BuildTool})

    logger.debug(f"built environment: {env}")

    os.execvpe(target, [target, *args], env)


def tool() -> None:
    # NOTE(ww): Specifically *not* a click command!
    wrapped_basename = os.path.basename(sys.argv[0])

    try:
        blight_tool = BlightTool(wrapped_basename)
    except ValueError:
        die(f"Unknown blight wrapper requested: {wrapped_basename}")

    tool_class = getattr(blight.tool, blight_tool.build_tool.value)
    tool = tool_class(sys.argv[1:])
    try:
        tool.run()
    except BlightError as e:
        die(str(e))
