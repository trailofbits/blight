import enum


class CompilerStage(enum.Enum):
    # TODO(ww): Maybe handle -v, -###, --help, --help=..., etc.

    # The preprocessor stage (i.e., `cc -E`)
    Preprocess = enum.auto()

    # Preprocessor, parsing, and type checking only (i.e., `cc -fsyntax-only`)
    SyntaxOnly = enum.auto()

    # Compile to assembly but don't run the assembler (i.e., `cc -S`)
    Assemble = enum.auto()

    # Compile and assemble to an individual object file (i.e., `cc -c`)
    CompileObject = enum.auto()

    # Run all stages, including the linker (i.e., `cc`)
    AllStages = enum.auto()

    # An unknown or unqualified stage.
    Unknown = enum.auto()


class Lang(enum.Enum):
    C = enum.auto()
    Cxx = enum.auto()
    Unknown = enum.auto()


class Std(enum.Enum):
    def is_unknown(self):
        return self in [Std.CUnknown, Std.CxxUnknown, Std.GnuUnknown, Std.GnuxxUnknown, Std.Unknown]

    # C standards.
    C89 = enum.auto()
    C94 = enum.auto()
    C99 = enum.auto()
    C11 = enum.auto()
    C17 = enum.auto()
    C2x = enum.auto()

    # GNU C standards.
    Gnu89 = enum.auto()
    Gnu99 = enum.auto()
    Gnu11 = enum.auto()
    Gnu17 = enum.auto()
    Gnu2x = enum.auto()

    # C++ standards.
    Cxx03 = enum.auto()
    Cxx11 = enum.auto()
    Cxx14 = enum.auto()
    Cxx17 = enum.auto()
    Cxx2a = enum.auto()

    # GNU C++ standards.
    Gnuxx03 = enum.auto()
    Gnuxx11 = enum.auto()
    Gnuxx14 = enum.auto()
    Gnuxx17 = enum.auto()
    Gnuxx2a = enum.auto()

    # C, but unknown standard.
    CUnknown = enum.auto()

    # C++, but unknown standard.
    CxxUnknown = enum.auto()

    # GNU C, but unknown standard.
    GnuUnknown = enum.auto()

    # GNU C++, but unknown standard.
    GnuxxUnknown = enum.auto()

    # Completely unknown.
    Unknown = enum.auto()
