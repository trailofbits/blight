"""
Constant tables and maps for various blight APIs and actions.
"""

from blight.enums import OutputKind

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
