"""
The `FindOutputs` action.
"""

import enum
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from blight.action import Action
from blight.tool import CC, CXX, LD, Tool
from blight.util import flock_append

logger = logging.getLogger(__name__)


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


class Output(BaseModel):
    kind: OutputKind
    path: Path
    store_path: Optional[Path]


class OutputRecord(BaseModel):
    tool: Tool
    outputs: List[Output]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {Tool: lambda t: t.asdict()}


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
        outputs = []
        for output_path in tool.outputs:
            output_path = Path(output_path)
            if not output_path.is_absolute():
                output_path = tool.cwd / output_path

            # Special case: a.out is produced by both the linker and compiler tools by default.
            if output_path.name == "a.out" and tool.__class__ in [CC, CXX, LD]:
                kind = OutputKind.Executable
            else:
                kind = OUTPUT_SUFFIX_KIND_MAP.get(output_path.suffix, OutputKind.Unknown)

            outputs.append(Output(kind=kind, path=output_path))

        self._outputs = outputs

    def after_run(self, tool):
        store = self._config.get("store")
        if store is not None:
            Path(store).mkdir(parents=True, exist_ok=True)

            for output in self.outputs["outputs"]:
                output = Path(output)
                if not output.exists():
                    logger.warning(f"{tool=}'s output ({output}) does not exist")
                    continue

        output_record = OutputRecord(tool=tool, outputs=self._outputs)

        record_output_path = Path(self._config["output"])
        with flock_append(record_output_path) as io:
            print(output_record.json(), file=io)
