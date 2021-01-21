"""
Enumerations for blight.
"""

import enum


@enum.unique
class CompilerStage(enum.Enum):
    """
    Models the known stages that a compiler tool can be in.
    """

    # TODO(ww): Maybe handle -v, -###, --help, --help=..., etc.

    Preprocess = enum.auto()
    """
    Preprocess only (e.g., `cc -E`)
    """

    SyntaxOnly = enum.auto()
    """
    Preprocess, parse, and typecheck only (e.g., `cc -fsyntax-only`)
    """

    Assemble = enum.auto()
    """
    Compile to assembly but don't run the assembler (e.g., `cc -S`)
    """

    CompileObject = enum.auto()
    """
    Compile and assemble to an individual object (e.g. `cc -c`)
    """

    AllStages = enum.auto()
    """
    All stages, including the linker (e.g. `cc`)
    """

    Unknown = enum.auto()
    """
    An unknown or unqualified stage.
    """


@enum.unique
class Lang(enum.Enum):
    """
    Models the known languages for a tool.
    """

    # TODO(ww): Maybe add each of the following:
    # * Asm (assembly)
    # * PreprocessedC (C that's already gone through the preprocessor)
    # * PreprocessedCxx (C++ that's already gone through the preprocessor)

    C = enum.auto()
    """
    The C programming language.
    """

    Cxx = enum.auto()
    """
    The C++ programming language.
    """

    Unknown = enum.auto()
    """
    An unknown language.
    """


@enum.unique
class Std(enum.Enum):
    """
    Models the various language standards for a tool.
    """

    def is_unknown(self) -> bool:
        """
        Returns:
            `True` if the standard is unknown
        """
        return self in [Std.CUnknown, Std.CxxUnknown, Std.GnuUnknown, Std.GnuxxUnknown, Std.Unknown]

    def is_cstd(self) -> bool:
        """
        Returns:
            `True` if the standard is a C standard
        """
        return self in [
            Std.C89,
            Std.C94,
            Std.C99,
            Std.C11,
            Std.C17,
            Std.C2x,
            Std.Gnu89,
            Std.Gnu99,
            Std.Gnu11,
            Std.Gnu17,
            Std.Gnu2x,
            Std.CUnknown,
            Std.GnuUnknown,
        ]

    def is_cxxstd(self) -> bool:
        """
        Returns:
            `True` if the standard is a C++ standard
        """
        return self in [
            Std.Cxx03,
            Std.Cxx11,
            Std.Cxx14,
            Std.Cxx17,
            Std.Cxx2a,
            Std.Gnuxx03,
            Std.Gnuxx11,
            Std.Gnuxx14,
            Std.Gnuxx17,
            Std.Gnuxx2a,
            Std.CxxUnknown,
            Std.GnuxxUnknown,
        ]

    def lang(self) -> Lang:
        """
        Returns: a `Lang` corresponding to this `Std`.
        """
        if self.is_cstd():
            return Lang.C
        elif self.is_cxxstd():
            return Lang.Cxx
        else:
            return Lang.Unknown

    C89 = enum.auto()
    """
    C89 (a.k.a. C90, iso9899:1990)
    """

    C94 = enum.auto()
    """
    C94 (a.k.a. iso9899:199409)
    """

    C99 = enum.auto()
    """
    C99 (a.k.a. C9x, iso9899:1999, iso9899:199x)
    """

    C11 = enum.auto()
    """
    C11 (a.k.a. C1x, iso9899:2011)
    """

    C17 = enum.auto()
    """
    C17 (a.k.a. C18, iso9899:2017, iso9899:2018)
    """

    C2x = enum.auto()
    """
    C2x
    """

    Gnu89 = enum.auto()
    """
    GNU C89 (a.k.a. GNU C 90)
    """

    Gnu99 = enum.auto()
    """
    GNU C99 (a.k.a. GNU C 9x)
    """

    Gnu11 = enum.auto()
    """
    GNU C11 (a.k.a. GNU C11x)
    """

    Gnu17 = enum.auto()
    """
    GNU C17 (a.k.a. GNU C18)
    """

    Gnu2x = enum.auto()
    """
    GNU C2x
    """

    Cxx03 = enum.auto()
    """
    C++03 (a.k.a. C++98)
    """

    Cxx11 = enum.auto()
    """
    C++11 (a.k.a. C++0x)
    """

    Cxx14 = enum.auto()
    """
    C++14 (a.k.a. C++1y)
    """

    Cxx17 = enum.auto()
    """
    C++17 (a.k.a. C++1z)
    """

    Cxx2a = enum.auto()
    """
    C++2a (a.k.a. C++20)
    """

    Gnuxx03 = enum.auto()
    """
    GNU C++03 (a.k.a. GNU C++98)
    """

    Gnuxx11 = enum.auto()
    """
    GNU C++11 (a.k.a. GNU C++0x)
    """

    Gnuxx14 = enum.auto()
    """
    GNU C++14 (a.k.a. GNU C++1y)
    """

    Gnuxx17 = enum.auto()
    """
    GNU C++17 (a.k.a. GNU C++1z)
    """

    Gnuxx2a = enum.auto()
    """
    GNU C++2a (a.k.a. GNU C++20)
    """

    CUnknown = enum.auto()
    """
    Standard C, but an unknown version.
    """

    CxxUnknown = enum.auto()
    """
    Standard C++, but an unknown version.
    """

    GnuUnknown = enum.auto()
    """
    GNU C, but an unknown version.
    """

    GnuxxUnknown = enum.auto()
    """
    GNU C++, but an unknown version.
    """

    Unknown = enum.auto()
    """
    A completely unknown language standard.
    """


@enum.unique
class OptLevel(enum.Enum):
    """
    Models the known optimization levels.
    """

    def for_size(self) -> bool:
        """
        Returns:
            `True` if the optimization is for compiled size
        """
        return self == OptLevel.OSize or self == OptLevel.OSizeZ

    def for_performance(self) -> bool:
        """
        Returns:
            `True` if the optimization is for performance
        """
        return self in [OptLevel.O1, OptLevel.O2, OptLevel.O3, OptLevel.OFast]

    def for_debug(self) -> bool:
        """
        Returns:
            `True` if the optimization is for debugging experience
        """
        return self == OptLevel.ODebug

    O0 = enum.auto()
    """
    No optimizations.
    """

    O1 = enum.auto()
    """
    Minimal performance optimizations.
    """

    O2 = enum.auto()
    """
    Some performance optimizations.
    """

    O3 = enum.auto()
    """
    Aggressive performance optimizations.
    """

    OFast = enum.auto()
    """
    Aggressive, possibly standards-breaking performance optimizations.
    """

    OSize = enum.auto()
    """
    Size optimizations.
    """

    OSizeZ = enum.auto()
    """
    More aggressive size optimizations (Clang only).
    """

    ODebug = enum.auto()
    """
    Debugging experience optimizations.
    """

    Unknown = enum.auto()
    """
    An unknown optimization level.
    """


@enum.unique
class CodeModel(enum.Enum):
    """
    Models the known machine code models.
    """

    Small = enum.auto()
    """
    The `small` machine code model (also `medlow` in Clang).
    """

    Medium = enum.auto()
    """
    The `medium` machine code model (also `medany` in Clang).
    """

    Large = enum.auto()
    """
    The `large` machine code model.
    """

    Kernel = enum.auto()
    """
    The `kernel` machine code model.
    """

    Unknown = enum.auto()
    """
    An unknown machine code model.
    """
