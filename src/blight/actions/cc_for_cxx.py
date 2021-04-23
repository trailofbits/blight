"""
The `CCForCXX` action.
"""

from blight.action import CCAction
from blight.tool import CC


class CCForCXX(CCAction):
    """
    An action for detecting whether the C compiler is being used as if it's
    a C++ compiler, and correcting the build when so.

    This action is used to fix a particular kind of misconfigured C++ build,
    where the C++ compiler is referred to as if it were a C compiler.

    For example, in Make:

    ```make
    CC := clang++
    CFLAGS := -std=c++17

    all:
        $(CC) $(CFLAGS) -o whatever foo.cpp bar.cpp
    ```

    Whereas the correct use would be:

    ```make
    CXX := clang++
    CXXFLAGS := -std=c++17

    all:
        $(CXX) $(CXXFLAGS) -o whatever foo.cpp bar.cpp
    ```

    This action fixes these builds by checking whether `CC` is being used
    as a C++ compiler. If it is, it explicitly injects additional flags
    to force the compiler into C++ mode.
    """

    # NOTE(ww): type ignore here because mypy thinks this is a Liskov
    # substitution principle violation -- it can't see that `CompilerAction`
    # is safely specialized for `CompilerTool`.
    def before_run(self, tool: CC) -> None:  # type: ignore
        # NOTE(ww): Currently, the only way we check whether CC is being used
        # as a C++ compiler is by checking whether one of the `-std=c++XX`
        # flags has been passed. This won't catch all cases; someone could use
        # CC as a C++ compiler with the default C++ standard.
        # Other options for detecting this:
        # * Check for common C++-only linkages, like -lstdc++fs
        # * Check whether tool.inputs contains files that look like C++
        if tool.std.is_cxxstd():
            tool.args[:0] = ["-x", "c++"]
