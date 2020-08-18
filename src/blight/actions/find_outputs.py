"""
The `FindOutputs` action.
"""

import enum
import json
from collections import defaultdict
from pathlib import Path

from blight.action import Action
from blight.tool import CC, CXX, LD
from blight.util import flock_append


@enum.unique
class OutputKind(enum.Enum):
    """
    A collection of common output kinds for build tools.

    This enumeration is not exhaustive.
    """

    Object: str = "object"
    SharedLibrary: str = "shared"
    StaticLibrary: str = "static"
    Executable: str = "executable"
    KernelModule: str = "kernel"
    Unknown: str = "unknown"


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


class FindOutputs(Action):
    def before_run(self, tool):
        output_map = defaultdict(list)
        for output in tool.outputs:
            output = Path(output)
            if not output.is_absolute():
                output = tool.cwd / output

            # Special case: a.out is produced by both the linker
            # and compiler tools by default.
            if output.name == "a.out" and tool.__class__ in [CC, CXX, LD]:
                output_map[OutputKind.Executable.value].append(str(output))
            else:
                kind = OUTPUT_SUFFIX_KIND_MAP.get(output.suffix, OutputKind.Unknown)
                output_map[kind.value].append(str(output))

        output = Path(self._config["output"])
        with flock_append(output) as io:
            outputs_record = {"tool": tool.asdict(), "outputs": output_map}
            print(json.dumps(outputs_record), file=io)

    # TODO(ww): Could do after_run here and check whether each output
    # in output_map was actually created.
