"""
Encapsulations of the tools supported by canker.
"""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from canker.enums import CompilerStage, Lang, OptLevel, Std
from canker.exceptions import CankerError
from canker.util import load_actions, rindex_prefix

logger = logging.getLogger(__name__)

CANKER_TOOL_MAP = {
    "canker-cc": "CC",
    "canker-c++": "CXX",
    "canker-cpp": "CPP",
    "canker-ld": "LD",
    "canker-as": "AS",
}

TOOL_ENV_MAP = {
    "CC": "cc",
    "CXX": "c++",
    "CPP": "cpp",
    "LD": "ld",
    "AS": "as",
}

TOOL_ENV_WRAPPER_MAP = {
    "CC": "CANKER_WRAPPED_CC",
    "CXX": "CANKER_WRAPPED_CXX",
    "CPP": "CANKER_WRAPPED_CPP",
    "LD": "CANKER_WRAPPED_LD",
    "AS": "CANKER_WRAPPED_AS",
}


class Tool:
    """
    Represents a generic tool wrapped by canker.

    `Tool` instances cannot be created directory; a specific subclass must be used.
    """

    @classmethod
    def wrapped_tool(cls) -> str:
        """
        Returns the executable name or path of the tool that this canker tool wraps.
        """
        wrapped_tool = os.getenv(TOOL_ENV_WRAPPER_MAP[cls.__name__])
        if wrapped_tool is None:
            raise CankerError(f"No wrapped tool found for {TOOL_ENV_MAP[cls.__name__]}")
        return wrapped_tool

    def __init__(self, args):
        if self.__class__ == Tool:
            raise NotImplementedError(f"can't instantiate {self.__class__.__name__} directly")
        self.args = args
        self._cwd = Path(os.getcwd()).resolve()
        self._actions = load_actions()

    def _before_run(self):
        for action in self._actions:
            action._before_run(self)

    def _after_run(self):
        for action in self._actions:
            action._after_run(self)

    def run(self):
        """
        Runs the wrapped tool with the original arguments.
        """
        self._before_run()

        subprocess.run([self.wrapped_tool(), *self.args])

        self._after_run()

    def asdict(self) -> Dict[str, Any]:
        """
        Returns:
            A dictionary representation of this tool
        """

        return {
            "name": self.__class__.__name__,
            "wrapped_tool": self.wrapped_tool(),
            "args": self.args,
            "cwd": str(self._cwd),
        }

    @property
    def cwd(self) -> Path:
        """
        Returns the directory that this tool was run in.
        """
        return self._cwd

    @property
    def inputs(self) -> List[str]:
        """
        Returns all explicit "inputs" to the tool. "Inputs" is subjectively
        defined to be the "main" inputs to a tool, i.e. source files and **not**
        additional files that *may* be passed in via options.

        Tools may further refine the behavior of this property
        by overriding it with their own, more specific behavior.

        **NOTE**: This property, more so than others, relies on heuristics.

        Returns:
            A list of `str`s, representing the tool's inputs.
        """

        # Our strategy here is as follows:
        # * Filter out any arguments that begin with "-" or "@" and
        #   aren't *just" "-" (since that indicates stdin).
        # * Then, look for arguments that are files in the tool's current
        #   directory.
        inputs = []
        for idx, arg in enumerate(self.args):
            if arg.startswith("-") or arg.startswith("@"):
                if arg == "-":
                    inputs.append(arg)
                continue

            candidate = Path(arg)
            if not candidate.is_file() and not (self.cwd / candidate).is_file():
                # NOTE(ww): pathlib's is_file returns False for device files, e.g. /dev/stdin.
                # It would be perverse for a build system to use these, but maybe worth
                # handling.
                continue

            # Annoying edge cases: most other flags that take filenames do so in
            # -flag=filename form, but -aux-info does it without the "=".
            # Similarly, we need to make sure not to catch an output flag's
            # argument here.
            if idx == 0 or self.args[idx - 1] not in ["-aux-info", "-o"]:
                inputs.append(arg)

        return inputs

    @property
    def outputs(self) -> List[str]:
        """
        Returns all "outputs" produced by the tool. "Outputs" is subjectively
        defined to be the "main" products of a tool, i.e. results of a particular
        stage or invocation and **not** any incidental or metadata files that
        might otherwise be created in the process.

        Tools may further refine the behavior of this mixin-supplied property
        by overriding it with their own, more specific behavior.

        Returns:
            A list of `str`, each of which is an output
        """

        o_flag_index = rindex_prefix(self.args, "-o")
        if o_flag_index is None:
            return []

        if self.args[o_flag_index] == "-o":
            return [self.args[o_flag_index + 1]]

        # NOTE(ww): Outputs like -ofoo. Gross, but valid according to GCC.
        return [self.args[o_flag_index][2:]]


class LangMixin:
    """
    A mixin for tools that have a "language" component, i.e.
    those that change their behavior based on the language that they're used with.
    """

    # NOTE(ww): Makes mypy happy when referencing self.args below.
    args: List[str]

    @property
    def lang(self) -> Lang:
        """
        Returns:
            A `canker.enums.Lang` value representing the tool's language
        """
        x_lang_map = {
            "c": Lang.C,
            "c-header": Lang.C,
            "c++": Lang.Cxx,
            "c++-header": Lang.Cxx,
        }

        # First, check for `-x lang`. This overrides the language determined by
        # the frontend's binary name (e.g. `g++`).
        x_flag_index = rindex_prefix(self.args, "-x")
        if x_flag_index is not None:
            if self.args[x_flag_index] == "-x":
                # TODO(ww): Maybe bounds check.
                x_lang = self.args[x_flag_index + 1]
            else:
                # NOTE(ww): -xc and -xc++ both work, at least on GCC.
                x_lang = self.args[x_flag_index][2:]
            return x_lang_map.get(x_lang, Lang.Unknown)

        # No `-x lang` means that we're operating in the frontend's default mode.
        if self.__class__ == CC:
            return Lang.C
        elif self.__class__ == CXX:
            return Lang.Cxx
        else:
            logger.debug(f"unknown default language mode for {self.__class__.__name__}")
            return Lang.Unknown


class StdMixin(LangMixin):
    """
    A mixin for tools that have a "standard" component, i.e.
    those that change their behavior based on a particular language standard.
    """

    @property
    def std(self) -> Std:
        """
        Returns:
            A `canker.enums.Std` value representing the tool's standard
        """

        # First, a special case: if -ansi is present, we're in
        # C89 mode for C code and C++03 mode for C++ code.
        if "-ansi" in self.args:
            if self.lang == Lang.C:
                return Std.C89
            elif self.lang == Lang.Cxx:
                return Std.Cxx03
            else:
                logger.debug(f"-ansi passed but unknown language: {self.lang}")
                return Std.Unknown

        # Experimentally, both GCC and clang respect the last -std=XXX flag passed.
        # See: https://stackoverflow.com/questions/40563269/passing-multiple-std-switches-to-g
        std_flag_index = rindex_prefix(self.args, "-std=")

        # No -std=XXX flags? The tool is operating in its default standard mode,
        # which is determined by its language.
        if std_flag_index is None:
            if self.lang == Lang.C:
                return Std.GnuUnknown
            elif self.lang == Lang.Cxx:
                return Std.GnuxxUnknown
            else:
                logger.debug(f"no -std= flag and unknown language: {self.lang}")
                return Std.Unknown

        last_std_flag = self.args[std_flag_index]
        std_flag_map = {
            # C89 flags.
            "-std=c89": Std.C89,
            "-std=c90": Std.C89,
            "-std=iso9899:1990": Std.C89,
            # C94 flags.
            "-std=iso9899:199409": Std.C94,
            # C99 flags.
            "-std=c99": Std.C99,
            "-std=c9x": Std.C99,
            "-std=iso9899:1999": Std.C99,
            "-std=iso9899:199x": Std.C99,
            # C11 flags.
            "-std=c11": Std.C11,
            "-std=c1x": Std.C11,
            "-std=iso9899:2011": Std.C11,
            # C17 flags.
            "-std=c17": Std.C17,
            "-std=c18": Std.C17,
            "-std=iso9899:2017": Std.C17,
            "-std=iso9899:2018": Std.C17,
            # C20 (presumptive) flags.
            "-std=c2x": Std.C2x,
            # GNU89 flags.
            "-std=gnu89": Std.Gnu89,
            "-std=gnu90": Std.Gnu89,
            # GNU99 flags.
            "-std=gnu99": Std.Gnu99,
            "-std=gnu9x": Std.Gnu99,
            # GNU11 flags.
            "-std=gnu11": Std.Gnu11,
            "-std=gnu1x": Std.Gnu11,
            # GNU17 flags.
            "-std=gnu17": Std.Gnu17,
            "-std=gnu18": Std.Gnu17,
            # GNU20 (presumptive) flags.
            "-std=gnu2x": Std.Gnu2x,
            # C++03 flags.
            # NOTE(ww): Both gcc and clang treat C++98 mode as C++03 mode.
            "-std=c++98": Std.Cxx03,
            "-std=c++03": Std.Cxx03,
            # C++11 flags.
            "-std=c++11": Std.Cxx11,
            "-std=c++0x": Std.Cxx11,
            # C++14 flags.
            "-std=c++14": Std.Cxx14,
            "-std=c++1y": Std.Cxx14,
            # C++17 flags.
            "-std=c++17": Std.Cxx17,
            "-std=c++1z": Std.Cxx17,
            # C++20 (presumptive) flags.
            "-std=c++2a": Std.Cxx2a,
            # GNU++03 flags.
            "-std=gnu++98": Std.Gnuxx03,
            "-std=gnu++03": Std.Gnuxx03,
            # GNU++11 flags.
            "-std=gnu++11": Std.Gnuxx11,
            "-std=gnu++0x": Std.Gnuxx11,
            # GNU++14 flags.
            "-std=gnu++14": Std.Gnuxx14,
            "-std=gnu++1y": Std.Gnuxx14,
            # GNU++17 flags.
            "-std=gnu++17": Std.Gnuxx17,
            "-std=gnu++1z": Std.Gnuxx17,
            # GNU++20 (presumptive) flags.
            "-std=gnu++2a": Std.Gnuxx2a,
        }

        std = std_flag_map.get(last_std_flag)
        if std is not None:
            return std

        # If we've made it here, then we've reached a -std=XXX flag that we
        # don't know yet. Make an effort to guess at it.
        std_name = last_std_flag.split("=")[1]
        if std_name.startswith("c++"):
            logger.debug(f"partially unrecognized c++ std: {last_std_flag}")
            return Std.CxxUnknown
        elif std_name.startswith("gnu++"):
            logger.debug(f"partially unrecognized gnu++ std: {last_std_flag}")
            return Std.GnuxxUnknown
        elif std_name.startswith("gnu"):
            logger.debug(f"partially unrecognized gnu c std: {last_std_flag}")
            return Std.GnuUnknown
        elif std_name.startswith("c") or std_name.startswith("iso9899"):
            logger.debug(f"partially unrecognized c std: {last_std_flag}")
            return Std.CUnknown

        logger.debug(f"completely unrecognized -std= flag: {last_std_flag}")
        return Std.Unknown


class OptMixin:
    """
    A mixin for tools that have an optimization level.
    """

    # NOTE(ww): Makes mypy happy when referencing self.args below.
    args: List[str]

    @property
    def opt(self) -> OptLevel:
        """
        Returns:
            A `canker.enums.OptLevel` value representing the optimization level
        """

        opt_flag_map = {
            "-O0": OptLevel.O0,
            "-O": OptLevel.O1,
            "-O1": OptLevel.O1,
            "-O2": OptLevel.O2,
            "-O3": OptLevel.O3,
            "-Ofast": OptLevel.OFast,
            "-Os": OptLevel.OSize,
            "-Oz": OptLevel.OSizeZ,
            "-Og": OptLevel.ODebug,
        }

        # The last optimization flag takes precedence, so iterate over the arguments
        # in reverse order.
        for arg in reversed(self.args):
            opt = opt_flag_map.get(arg)
            if opt is not None:
                return opt

            if not arg.startswith("-O"):
                continue

            # Special case: -O4 and above are currently equivalent to -O3 in
            # GCC and Clang. Identify these and map them to -O3.
            if re.fullmatch(r"^-O[1-9]\d*$", arg):
                return OptLevel.O3

            # Otherwise: We've found an argument that looks like -Osomething,
            # but we don't know what it is. Treat it as an unknown.
            logger.debug(f"unknown optimization level: {arg}")
            return OptLevel.Unknown

        # If we've made it here, then the arguments don't mention an explicit
        # optimization level. Both GCC and Clang use -O0 by default, so return that here.
        return OptLevel.O0


class CompilerTool(Tool, StdMixin, OptMixin):
    """
    Represents a generic (C or C++) compiler frontend.

    Like `Tool`, `CompilerTool` cannot be instantiated directly.
    """

    def __init__(self, args):
        if self.__class__ == CompilerTool:
            raise NotImplementedError(f"can't instantiate {self.__class__.__name__} directly")
        super().__init__(args)

    @property
    def stage(self) -> CompilerStage:
        """
        Returns:
            A `canker.enums.CompilerStage` value representing the stage that this tool is on
        """
        if len(self.args) == 0:
            return CompilerStage.Unknown

        stage_flag_map = {
            # NOTE(ww): See the TODO in CompilerStage.
            "-v": CompilerStage.Unknown,
            "-###": CompilerStage.Unknown,
            "-E": CompilerStage.Preprocess,
            "-fsyntax-only": CompilerStage.SyntaxOnly,
            "-S": CompilerStage.Assemble,
            "-c": CompilerStage.CompileObject,
        }

        for flag, stage in stage_flag_map.items():
            if flag in self.args:
                return stage

        # TODO(ww): Handle header precompilation here. GCC doesn't seem to
        # consider this a real "stage", but it's different enough from every
        # other stage to warrant special treatment.

        # No explicit stage flag? Both gcc and clang treat this as
        # "run all stages", so we do too.
        return CompilerStage.AllStages

    @property
    def outputs(self) -> List[str]:
        """
        Specializes `Tool.outputs` for compiler tools.
        """
        outputs = super().outputs
        if outputs != []:
            return outputs

        # Without an explicit `-o outfile`, the default output name(s)
        # depends on the compiler's stage.
        if self.stage == CompilerStage.Preprocess:
            # NOTE(ww): The preprocessor stage emits to stdout, but returning "-" as
            # a sentinel for that is very meh. If only Python had Rust-style enums.
            return ["-"]
        elif self.stage == CompilerStage.Assemble:
            # NOTE(ww): Outputs are created relative to the current working directory,
            # not relative to their input. We return them as relative paths to
            # indicate this (maybe we should just fully resolve them?)
            return [Path(input_).with_suffix(".s").name for input_ in self.inputs]
        elif self.stage == CompilerStage.CompileObject:
            return [Path(input_).with_suffix(".o").name for input_ in self.inputs]
        elif self.stage == CompilerStage.AllStages:
            # NOTE(ww): This will be wrong when we're doing header precompilation;
            # see the TODO in `stage`.
            return ["a.out"]
        else:
            return []

    def asdict(self) -> Dict[str, Any]:
        return {
            **super().asdict(),
            "lang": self.lang.name,
            "std": self.std.name,
            "stage": self.stage.name,
            "opt": self.opt.name,
        }


class CC(CompilerTool):
    """
    A specialization of `CompilerTool` for the C compiler frontend.
    """

    def __repr__(self) -> str:
        return f"<CC {self.wrapped_tool()} {self.lang} {self.std} {self.stage}>"


class CXX(CompilerTool):
    """
    A specialization of `CompilerTool` for the C++ compiler frontend.
    """

    def __repr__(self) -> str:
        return f"<CXX {self.wrapped_tool()} {self.lang} {self.std} {self.stage}>"


class CPP(Tool, StdMixin):
    """
    Represents the C preprocessor tool.
    """

    def __repr__(self) -> str:
        return f"<CPP {self.wrapped_tool()} {self.lang} {self.std}>"

    def asdict(self) -> Dict[str, Any]:
        return {
            **super().asdict(),
            "lang": self.lang.name,
            "std": self.std.name,
        }


class LD(Tool):
    """
    Represents the linker.
    """

    @property
    def outputs(self) -> List[str]:
        """
        Specializes `Tool.outputs` for the linker.
        """

        outputs = super().outputs
        if outputs != []:
            return outputs

        # The GNU linker additionally supports --output=OUTFILE and
        # --output OUTFILE. Handle them here.
        output_flag_index = rindex_prefix(self.args, "--output")
        if output_flag_index is None:
            return ["a.out"]

        # Split option form.
        if self.args[output_flag_index] == "--output":
            return [self.args[output_flag_index + 1]]

        # Assignment form.
        return [self.args[output_flag_index].split("=")[1]]

    def __repr__(self) -> str:
        return f"<LD {self.wrapped_tool()}>"


class AS(Tool):
    """
    Represents the assembler.
    """

    def __repr__(self) -> str:
        return f"<AS {self.wrapped_tool()}>"
