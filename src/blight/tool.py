"""
Encapsulations of the tools supported by blight.
"""

import itertools
import json
import logging
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from blight import util
from blight.constants import COMPILER_FLAG_INJECTION_VARIABLES
from blight.enums import (
    BlightTool,
    BuildTool,
    CodeModel,
    CompilerFamily,
    CompilerStage,
    Lang,
    OptLevel,
    Std,
)
from blight.exceptions import BlightError, BuildError, SkipRun
from blight.protocols import (
    CanonicalizedArgsProtocol,
    IndexedUndefinesProtocol,
    LangProtocol,
)
from blight.util import json_helper

logger = logging.getLogger(__name__)


RESPONSE_FILE_RECURSION_LIMIT = 64
"""
Response files can contain further `@file` arguments, because of course they can.

Neither clang nor GCC is explicit in their documentation about their recursion limits,
if they have any. We choose an arbitrary limit here.
"""


class Tool:
    """
    Represents a generic tool wrapped by blight.

    Every `Tool` has two views of its supplied arguments:

    * An "effective" view, provided by `Tool.args`
    * A "canonicalized" view, provided by `Tool.canonicalized_args`

    The "effective" view is used to invoke the underlying wrapped tool. It should
    never differ from the original arguments supplied to the invocation, **except**
    for when a user configures an action that **intentionally** modifies the
    arguments.

    The "canonicalized" view is used to model the behavior of the underlying wrapped
    tool. Specific `Tool` subclasses may specialize the canonicalized view to improve
    modeling fidelity. For example, tools that support the `@file` syntax (see
    `ResponseFileMixin`) for expanding arguments may augment `canonicalized_args`
    to reflect a fully expanded and normalized version of the original arguments.

    The "canonicalized" view always derives directly from the "effective" view:
    any modifications made to the "effective" arguments by an action will be
    propagated to the "canonicalized" arguments.

    `Tool` instances cannot be created directory; a specific subclass must be used.
    """

    @classmethod
    def build_tool(cls) -> BuildTool:
        """
        Returns the `BuildTool` enum associated with this `Tool`.
        """
        return BuildTool(cls.__name__)

    @classmethod
    def blight_tool(cls) -> BlightTool:
        """
        Returns the `BlightTool` enum associated with this `Tool`.
        """
        return cls.build_tool().blight_tool

    @classmethod
    def wrapped_tool(cls) -> str:
        """
        Returns the executable name or path of the tool that this blight tool wraps.
        """
        wrapped_tool = os.getenv(cls.blight_tool().env)
        if wrapped_tool is None:
            raise BlightError(f"No wrapped tool found for {cls.build_tool()}")
        return wrapped_tool

    def __init__(self, args: List[str]) -> None:
        if self.__class__ == Tool:
            raise NotImplementedError(f"can't instantiate {self.__class__.__name__} directly")
        self._args = args
        self._canonicalized_args = args.copy()
        self._env = self._fixup_env()
        self._cwd = Path(os.getcwd()).resolve()
        self._actions = util.load_actions()
        self._skip_run = False
        self._action_results: Dict[str, Optional[Dict[str, Any]]] = {}
        self._journal_path = os.getenv("BLIGHT_JOURNAL_PATH")

    def _fixup_env(self) -> Dict[str, str]:
        """
        Fixes up `os.environ` to remove any references to blight's swizzled paths,
        if any are present.
        """
        env = dict(os.environ)
        env["PATH"] = util.unswizzled_path()
        return env

    def _before_run(self) -> None:
        for action in self._actions:
            try:
                action._before_run(self)
            except SkipRun:
                self._skip_run = True

    def _after_run(self) -> None:
        for action in self._actions:
            action._after_run(self, run_skipped=self._skip_run)

            if self.is_journaling():
                self._action_results[action.__class__.__name__] = action.result

    def _commit_journal(self) -> None:
        if self.is_journaling():
            with util.flock_append(self._journal_path) as io:  # type: ignore
                json.dump(self._action_results, io, default=json_helper)
                # NOTE(ww): `json.dump` doesn't do this for us.
                io.write("\n")

    def run(self) -> None:
        """
        Runs the wrapped tool with the original arguments.
        """
        self._before_run()

        if not self._skip_run:
            status = subprocess.run([self.wrapped_tool(), *self.args], env=self._env)
            if status.returncode != 0:
                raise BuildError(
                    f"{self.wrapped_tool()} exited with status code {status.returncode}"
                )

        self._after_run()

        self._commit_journal()

    def is_journaling(self) -> bool:
        """
        Returns:
            `True` if this `Tool` is in "journaling" mode.
        """
        return self._journal_path is not None

    def asdict(self) -> Dict[str, Any]:
        """
        Returns:
            A dictionary representation of this tool
        """

        return {
            "name": self.__class__.__name__,
            "wrapped_tool": self.wrapped_tool(),
            "args": self.args,
            "canonicalized_args": self.canonicalized_args,
            "cwd": str(self._cwd),
            "env": self._env,
        }

    @property
    def args(self) -> List[str]:
        return self._args

    @args.setter
    def args(self, args_: List[str]) -> None:
        self._args = args_

        # NOTE(ww): Modifying the effective arguments also propagates
        # those changes to the canonicalized arguments. This shouldn't be a problem,
        # since mixins that specialize `canonicalized_args` call
        # `super.canonicalized_args` to get the most recent copy.
        self._canonicalized_args = args_.copy()

    @property
    def canonicalized_args(self) -> List[str]:
        # NOTE(ww): `canonicalized_args` doesn't need an explicit setter property,
        # since all specializations of it are expected to modify the underlying
        # list.
        return self._canonicalized_args

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
        for idx, arg in enumerate(self.canonicalized_args):
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
            if idx == 0 or self.canonicalized_args[idx - 1] not in ["-aux-info", "-o"]:
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

        o_flag_index = util.rindex_prefix(self.canonicalized_args, "-o")
        if o_flag_index is None:
            return []

        if self.canonicalized_args[o_flag_index] == "-o":
            return [self.canonicalized_args[o_flag_index + 1]]

        # NOTE(ww): Outputs like -ofoo. Gross, but valid according to GCC.
        return [self.canonicalized_args[o_flag_index][2:]]


class LangMixin:
    """
    A mixin for tools that have a "language" component, i.e.
    those that change their behavior based on the language that they're used with.
    """

    @property
    def lang(self: CanonicalizedArgsProtocol) -> Lang:
        """
        Returns:
            A `blight.enums.Lang` value representing the tool's language
        """
        x_lang_map = {"c": Lang.C, "c-header": Lang.C, "c++": Lang.Cxx, "c++-header": Lang.Cxx}

        # First, check for `-x lang`. This overrides the language determined by
        # the frontend's binary name (e.g. `g++`).
        x_flag_index = util.rindex_prefix(self.canonicalized_args, "-x")
        if x_flag_index is not None:
            if self.canonicalized_args[x_flag_index] == "-x":
                # TODO(ww): Maybe bounds check.
                x_lang = self.canonicalized_args[x_flag_index + 1]
            else:
                # NOTE(ww): -xc and -xc++ both work, at least on GCC.
                x_lang = self.canonicalized_args[x_flag_index][2:]
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
    def std(self: LangProtocol) -> Std:
        """
        Returns:
            A `blight.enums.Std` value representing the tool's standard
        """

        # First, a special case: if -ansi is present, we're in
        # C89 mode for C code and C++03 mode for C++ code.
        if "-ansi" in self.canonicalized_args:
            if self.lang == Lang.C:
                return Std.C89
            elif self.lang == Lang.Cxx:
                return Std.Cxx03
            else:
                logger.debug(f"-ansi passed but unknown language: {self.lang}")
                return Std.Unknown

        # Experimentally, both GCC and clang respect the last -std=XXX flag passed.
        # See: https://stackoverflow.com/questions/40563269/passing-multiple-std-switches-to-g
        std_flag_index = util.rindex_prefix(self.canonicalized_args, "-std=")

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

        last_std_flag = self.canonicalized_args[std_flag_index]
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
            "-std=c++20": Std.Cxx2a,
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
            "-std=gnu++20": Std.Gnuxx2a,
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

    @property
    def opt(self: CanonicalizedArgsProtocol) -> OptLevel:
        """
        Returns:
            A `blight.enums.OptLevel` value representing the optimization level
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
        for arg in reversed(self.canonicalized_args):
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


class ResponseFileMixin:
    """
    A mixin for tools that support the `@file` syntax for adding command-line arguments
    via an input file.

    These appear to originate from Windows and are called "response files" there, hence
    the name of this mixin.
    """

    def _expand_response_file(
        self, response_file: Path, working_dir: Path, level: int
    ) -> List[str]:
        if level >= RESPONSE_FILE_RECURSION_LIMIT:
            logger.debug(f"recursion limit exceeded: {response_file} in {working_dir}")
            return []

        # Non-absolute response files are resolved relative to `working_dir`, which
        # begins at the CWD initially and changes to the parent directory of the
        # including file for nested response files.
        if not response_file.is_absolute():
            response_file = working_dir / response_file

        if not response_file.is_file():
            logger.debug(f"response file {response_file} does not exist")
            # TODO(ww): Instead of returning empty here, maybe return `@response_file`?
            return []

        args = shlex.split(response_file.read_text())
        response_files = [(idx, arg) for (idx, arg) in enumerate(args) if arg.startswith("@")]
        for idx, nested_rf in response_files:
            args = util.insert_items_at_idx(
                args,
                idx,
                self._expand_response_file(
                    Path(nested_rf[1:]), response_file.parent.resolve(), level + 1
                ),
            )

        return args

    @property
    def canonicalized_args(self) -> List[str]:
        """
        Overrides the behavior of `Tool.canonicalized_args`, expanding any response file arguments
        in a depth-first manner.
        """

        # NOTE(ww): This method badly needs some typechecking TLC.
        # The `super()` call to `canonicalized_args` probably needs to be handled
        # with a `self: CanonicalizedArgsProtocol` hint, but that causes other problems
        # related to mypy's ability to see `_expand_response_file`.

        response_files = [
            (idx, arg)
            for (idx, arg) in enumerate(super().canonicalized_args)  # type: ignore
            if arg.startswith("@")
        ]
        expanded_args = super().canonicalized_args  # type: ignore
        for idx, response_file in response_files:
            expanded_args = util.insert_items_at_idx(
                expanded_args,
                idx,
                self._expand_response_file(Path(response_file[1:]), self.cwd, 0),  # type: ignore
            )

        self._canonicalized_args = expanded_args
        return self._canonicalized_args  # type: ignore[no-any-return]


class DefinesMixin:
    """
    A mixin for tools that support the `-Dname[=value]` and `-Uname` syntaxes for defining
    and undefining C preprocessor macros.
    """

    @property
    def indexed_undefines(self: IndexedUndefinesProtocol) -> Dict[str, int]:
        """
        Returns a dictionary of indices for undefined macros. This is used in
        `defines` to ensure that we don't incorrectly report a subsequently undefined
        macro as defined. Only the rightmost index of each undefined macro is saved.

        Returns:
            A dict of `name: index` for each undefined macro.
        """
        indexed_undefines = {}
        for idx, arg in enumerate(self.canonicalized_args):
            if not arg.startswith("-U"):
                continue

            # Both `-Uname` and `-U name` work in GCC and Clang.
            undefine = self.canonicalized_args[idx + 1] if arg == "-U" else arg[2:]

            indexed_undefines[undefine] = idx

        return indexed_undefines

    @property
    def defines(self: IndexedUndefinesProtocol) -> List[Tuple[str, str]]:
        """
        The list of **effective** defines for this tool invocation. An "effective"
        define is one that is not canceled out by a subsequent undefine.

        Returns:
            A list of tuples of (name, value) for each effectively defined macro.
        """
        defines = []
        for idx, arg in enumerate(self.canonicalized_args):
            if not arg.startswith("-D"):
                continue

            # Both `-Dname[=value]` and `-D name[=value]` work in GCC and Clang.
            define = self.canonicalized_args[idx + 1] if arg == "-D" else arg[2:]

            components = define.split("=", 1)
            name = components[0]

            # NOTE(ww): 1 is the default macro value.
            # It's actually an integer at the preprocessor level, but we model everything
            # as strings here to avoid complicating things.
            value = "1" if len(components) == 1 else components[1]

            # Is this macro subsequently undefined? If so, don't include it in
            # the defines list.
            if self.indexed_undefines.get(name, -1) > idx:
                continue

            defines.append((name, value))

        return defines


class CodeModelMixin:
    """
    A mixin for tools that support the `-mcmodel=MODEL` syntax for declaring their
    code model.
    """

    @property
    def code_model(self: CanonicalizedArgsProtocol) -> CodeModel:
        """
        Returns:
            A `blight.enums.CodeModel` value representing the tool's code model
        """
        code_model_map = {
            "-mcmodel=small": CodeModel.Small,
            "-mcmodel=medlow": CodeModel.Small,
            "-mcmodel=medium": CodeModel.Medium,
            "-mcmodel=medany": CodeModel.Medium,
            "-mcmodel=large": CodeModel.Large,
            "-mcmodel=kernel": CodeModel.Kernel,
        }

        # NOTE(ww): Both Clang and GCC seem to default to the "small" code model
        # when none is specified, at least on x86-64. But this might not be consistent
        # across architectures, so maybe we should return `CodeModel.Unknown` here
        # instead.
        code_model = util.ritem_prefix(self.canonicalized_args, "-mcmodel=")
        if code_model is None:
            return CodeModel.Small

        return code_model_map.get(code_model, CodeModel.Unknown)


class LinkSearchMixin:
    """
    A mixin for tools that support the `-Lpath` and `-llib` syntaxes for specifying
    library paths and libraries, respectively.
    """

    @property
    def explicit_library_search_paths(self: CanonicalizedArgsProtocol) -> List[Path]:
        """
        Returns a list of library search paths that are explicitly specified in
        the tool's invocation. Semantically, these paths are (normally) given
        priority over all other search paths.

        NOTE: This is **not** the same as the complete list of library search paths,
        which is tool-specific and host-dependent.
        """

        shorts = util.collect_option_values(self.canonicalized_args, "-L")
        longs = util.collect_option_values(
            self.canonicalized_args, "--library-path", style=util.OptionValueStyle.EqualOrSpace
        )

        sorted_values = sorted(itertools.chain(shorts, longs), key=lambda v: v[0])

        return [(self.cwd / value[1]).resolve() for value in sorted_values]

    @property
    def library_names(self: CanonicalizedArgsProtocol) -> List[str]:
        """
        Returns a list of library names (without suffixes) for libraries that
        are explicitly specified in the tool's invocation.

        NOTE: This list does not include any libraries that are
        listed as "inputs" to the tool rather than as linkage specifications.
        """

        shorts = util.collect_option_values(self.canonicalized_args, "-l")
        longs = util.collect_option_values(
            self.canonicalized_args, "--library", style=util.OptionValueStyle.EqualOrSpace
        )

        sorted_values = sorted(itertools.chain(shorts, longs), key=lambda v: v[0])

        return [f"lib{value[1]}" for value in sorted_values]


# NOTE(ww): The funny mixin order here (`ResponseFileMixin` before `Tool`) and elsewhere
# is because Python defines its class hierarchy from right to left. `ResponseFileMixin`
# therefore needs to come first in order to properly override `canonicalized_args`.
class CompilerTool(
    LinkSearchMixin, ResponseFileMixin, Tool, StdMixin, OptMixin, DefinesMixin, CodeModelMixin
):
    """
    Represents a generic (C or C++) compiler frontend.

    Like `Tool`, `CompilerTool` cannot be instantiated directly.
    """

    def __init__(self, args: List[str]) -> None:
        if self.__class__ == CompilerTool:
            raise NotImplementedError(f"can't instantiate {self.__class__.__name__} directly")

        super().__init__(args)

        # #40 and #41: These should be handled in an overridden implementation
        # of `canonicalized_args`.
        injection_vars = COMPILER_FLAG_INJECTION_VARIABLES & self._env.keys()
        if injection_vars:
            logger.warning(f"not tracking compiler's own instrumentation: {injection_vars}")

    @property
    def family(self) -> CompilerFamily:
        """
        Returns:
            A `blight.enums.CompilerFamily` value representing the "family" of compilers
            that this tool belongs to.
        """

        # NOTE(ww): Both GCC and Clang support -### as an alias for -v, but
        # with additional guarantees around argument quoting. Do other families support it?

        result = subprocess.run([self.wrapped_tool(), "-###"], capture_output=True)

        # If the command exited with an error, we're likely dealing with a frontend
        # that doesn't understand `-###`.
        if result.returncode != 0:
            logger.warning("compiler fingerprint failed: frontend didn't recognize -###?")
            # ...but even still, we can infer a bit from the error message.
            if b"tcc: error" in result.stderr:
                return CompilerFamily.Tcc
            else:
                return CompilerFamily.Unknown

        # We expect the relevant parts of `-###` on stderr. The lack of any output
        # again suggests that the frontend doesn't understand the flag.
        if not result.stderr:
            logger.warning("compiler fingerprint failed: frontend didn't produce output for -###?")
            return CompilerFamily.Unknown

        # Finally, we do some silly substring checks.
        # TODO(ww): Better heuristics here?
        if b"Apple clang version" in result.stderr:
            return CompilerFamily.AppleLlvm
        elif b"clang version" in result.stderr:
            return CompilerFamily.MainlineLlvm
        elif b"gcc version" in result.stderr:
            return CompilerFamily.Gcc
        else:
            return CompilerFamily.Unknown

    @property
    def stage(self) -> CompilerStage:
        """
        Returns:
            A `blight.enums.CompilerStage` value representing the stage that this tool is on
        """

        # TODO(ww): Refactor this entire method. Both GCC and Clang can actually
        # run multiple stages per invocation, e.g. `-x c foo.c -x c++ bar.cpp`,
        # so we should model this as "stages" instead. This, in turn, will require
        # us to reevaluate our output guesswork below.

        if len(self.canonicalized_args) == 0:
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
            if flag in self.canonicalized_args:
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


class CPP(Tool, StdMixin, DefinesMixin):
    """
    Represents the C preprocessor tool.
    """

    def __repr__(self) -> str:
        return f"<CPP {self.wrapped_tool()} {self.lang} {self.std}>"

    def asdict(self) -> Dict[str, Any]:
        return {**super().asdict(), "lang": self.lang.name, "std": self.std.name}


class LD(LinkSearchMixin, ResponseFileMixin, Tool):
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
        output_flag_index = util.rindex_prefix(self.canonicalized_args, "--output")
        if output_flag_index is None:
            return ["a.out"]

        # Split option form.
        if self.canonicalized_args[output_flag_index] == "--output":
            return [self.canonicalized_args[output_flag_index + 1]]

        # Assignment form.
        return [self.canonicalized_args[output_flag_index].split("=")[1]]

    def __repr__(self) -> str:
        return f"<LD {self.wrapped_tool()}>"


class AS(ResponseFileMixin, Tool):
    """
    Represents the assembler.
    """

    def __repr__(self) -> str:
        return f"<AS {self.wrapped_tool()}>"


class AR(ResponseFileMixin, Tool):
    """
    Represents the archiver.
    """

    @property
    def outputs(self) -> List[str]:
        """
        Specializes `Tool.outputs` for the archiver.
        """

        # TODO(ww): This doesn't support `ar x`, which explodes the archive
        # (i.e., treats it as input) instead of treats it as output.
        # It would be pretty strange for a build system to do this, but it's
        # probably something we should detect at the very least.

        # TODO(ww): We also don't support `ar t`, which queries the given
        # archive to provide a table listing of its contents.

        # NOTE(ww): `ar`'s POSIX and GNU CLIs are annoyingly complicated.
        # We save ourselves some pain by scanning from left-to-right, looking
        # for the first argument that looks like an archive output
        # (since the archiver only ever produces one output at a time).
        for arg in self.canonicalized_args:
            if arg.startswith("-"):
                continue

            maybe_archive_suffixes = Path(arg).suffixes
            if len(maybe_archive_suffixes) > 0 and maybe_archive_suffixes[0] == ".a":
                return [arg]

        logger.debug("couldn't infer output for archiver")
        return []

    def __repr__(self) -> str:
        return f"<AR {self.wrapped_tool()}>"


class STRIP(ResponseFileMixin, Tool):
    """
    Represents the stripping tool.
    """

    def __repr__(self) -> str:
        return f"<STRIP {self.wrapped_tool()}>"


class INSTALL(Tool):
    """
    Represents the install tool.
    """

    def _install_parser(self) -> util.ArgumentParser:
        parser = util.ArgumentParser(
            prog=self.build_tool().value, add_help=False, allow_abbrev=False
        )

        def add_flag(short: str, dest: str, **kwargs: Any) -> None:
            parser.add_argument(short, action="store_true", dest=dest, **kwargs)

        add_flag("-b", "overwrite")
        add_flag("-C", "copy_no_mtime")
        add_flag("-c", "copy", default=True)
        add_flag("-d", "directory_mode")
        add_flag("-M", "disable_mmap")
        add_flag("-p", "preserve_mtime")
        add_flag("-S", "safe_copy")
        add_flag("-s", "exec_strip")
        add_flag("-v", "verbose")
        parser.add_argument("-f", dest="flags")
        parser.add_argument("-g", dest="group")
        parser.add_argument("-m", dest="mode")
        parser.add_argument("-o", dest="owner")
        parser.add_argument("trailing", nargs="+", default=[])

        return parser

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)
        self._parser = self._install_parser()

        try:
            (self._matches, self._unknown) = self._parser.parse_known_args(args)
        except ValueError as e:
            logger.error(f"argparse error: {e}")
            self._matches = self._parser.default_namespace()
            self._unknown = args

    @property
    def directory_mode(self) -> bool:
        """
        Returns whether this `install` invocation is in "directory mode," i.e.
        is creating directories instead of installing files.
        """
        return self._matches.directory_mode  # type: ignore[no-any-return]

    @property
    def inputs(self) -> List[str]:
        """
        Specializes `Tool.inputs` for the install tool.
        """

        # Directory mode: all positionals are new directories, i.e. outputs.
        if self.directory_mode:
            return []

        # `install` requires at least two positionals outside of directory mode,
        # so this probably indicates an unknown GNUism like `--help`.
        if len(self._matches.trailing) < 2:
            logger.debug(f"install called with no positionals (hint: unknown args: {self._unknown}")
            return []

        # Otherwise, we're either installing one file to another or we're
        # installing multiple files to a directory. Test the last positional
        # to determine which mode we're in.
        maybe_dir = self._cwd / self._matches.trailing[-1]
        if maybe_dir.is_dir():
            return self._matches.trailing[0:-1]  # type: ignore[no-any-return]
        else:
            return [self._matches.trailing[0]]

    @property
    def outputs(self) -> List[str]:
        """
        Specializes `Tool.outputs` for the install tool.
        """

        # Directory mode: treat created directories as outputs.
        if self.directory_mode:
            return self._matches.trailing  # type: ignore[no-any-return]

        # `install` requires at least two positionals outside of directory mode,
        # so this probably indicates an unknown GNUism like `--help`.
        if len(self._matches.trailing) < 2:
            logger.debug(f"install called with no positionals (hint: unknown args: {self._unknown}")
            return []

        # If we're installing multiple files to a destination directory,
        # then our outputs are every input, under the destination.
        # Otherwise, our output is a single file.
        maybe_dir = self._cwd / self._matches.trailing[-1]
        if maybe_dir.is_dir():
            inputs = [Path(input_) for input_ in self._matches.trailing[0:-1]]
            return [str(maybe_dir / input_.name) for input_ in inputs]
        else:
            return [self._matches.trailing[-1]]

    def __repr__(self) -> str:
        return f"<INSTALL {self.wrapped_tool()}>"
