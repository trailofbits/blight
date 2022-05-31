"""
Constant tables and maps for various blight APIs and actions.
"""

from blight.enums import InputKind, OutputKind

COMPILER_FLAG_INJECTION_VARIABLES = {"CL", "_CL_", "CCC_OVERRIDE_OPTIONS"}
"""
Environment variables that some compiler frontends use to do their own
flag injection.
"""

OUTPUT_SUFFIX_KIND_MAP = {
    ".o": OutputKind.Object,
    ".obj": OutputKind.Object,
    ".so": OutputKind.SharedLibrary,
    ".dylib": OutputKind.SharedLibrary,
    ".dll": OutputKind.SharedLibrary,
    ".a": OutputKind.StaticLibrary,
    ".lib": OutputKind.StaticLibrary,
    "": OutputKind.Executable,
    ".exe": OutputKind.Executable,
    ".bin": OutputKind.Executable,
    ".elf": OutputKind.Executable,
    ".com": OutputKind.Executable,
    ".ko": OutputKind.KernelModule,
    ".sys": OutputKind.KernelModule,
}
"""
A mapping of common output suffixes to their (expected) file kinds.

This mapping is not exhaustive.
"""


OUTPUT_SUFFIX_PATTERN_MAP = {
    r".*\.so\.\d+\.\d+\.\d+$": OutputKind.SharedLibrary,  # anything with libtool
    r".*\.so\.\d+\.\d+$": OutputKind.SharedLibrary,  # libssl.so.1.1
    r".*\.so\.\d+$": OutputKind.SharedLibrary,  # libc.so.6
}
"""
A mapping of common output suffix patterns to their (expected) file kinds.

This mapping is not exhaustive.
"""

INPUT_SUFFIX_KIND_MAP = {
    ".c": InputKind.Source,
    ".cc": InputKind.Source,
    ".cpp": InputKind.Source,
    ".cxx": InputKind.Source,
    ".o": InputKind.Object,
    ".obj": InputKind.Object,
    ".so": InputKind.SharedLibrary,
    ".dylib": InputKind.SharedLibrary,
    ".dll": InputKind.SharedLibrary,
    ".a": InputKind.StaticLibrary,
    ".lib": InputKind.StaticLibrary,
}
"""
A mapping of common input suffixes to their (expected) file kinds.

This mapping is not exhaustive.
"""
