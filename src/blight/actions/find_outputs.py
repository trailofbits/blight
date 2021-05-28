"""
The `FindOutputs` action.
"""

import hashlib
import logging
import re
import shutil
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from blight.action import Action
from blight.constants import OUTPUT_SUFFIX_KIND_MAP, OUTPUT_SUFFIX_PATTERN_MAP
from blight.enums import OutputKind
from blight.tool import CC, CXX, LD, Tool
from blight.util import flock_append

logger = logging.getLogger(__name__)


class Output(BaseModel):
    """
    Represents a single output from a tool.
    """

    kind: OutputKind
    """
    The kind of output.
    """

    prenormalized_path: str
    """
    The path to the output, as passed directly to the tool itself.

    This copy of the path may be relative; consumers should prefer
    `path` for an absolute copy.
    """

    path: Path
    """
    The path to the output, as created by the tool.

    **NOTE**: This path may not actually exist, as a build system may arbitrarily
    choose to rename or relocate any outputs produced by individual tools.
    """

    store_path: Optional[Path]
    """
    An optional stable path to the output, as preserved by the `FindOutputs` action.

    `store_path` is only present if the `store=/some/dir/` setting is passed in the
    `FindActions` configuration **and** the tool actually produces the expected output.
    """


class OutputsRecord(BaseModel):
    """
    Represents a single `FindOuputs` record. Each record contains a representation
    of the tool invocation that produced the outputs, as well as the list of `Output`s
    associated with the invocation.
    """

    tool: Tool
    """
    The `Tool` invocation.
    """

    outputs: List[Output]
    """
    A list of `Output`s.
    """

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {Tool: lambda t: t.asdict()}


class FindOutputs(Action):
    def before_run(self, tool: Tool) -> None:
        outputs = []
        for output in tool.outputs:
            output_path = Path(output)
            if not output_path.is_absolute():
                output_path = tool.cwd / output_path

            # Special case: a.out is produced by both the linker and compiler tools by default.
            if output_path.name == "a.out" and tool.__class__ in [CC, CXX, LD]:
                kind = OutputKind.Executable
            else:
                kind = OUTPUT_SUFFIX_KIND_MAP.get(output_path.suffix, OutputKind.Unknown)

                # Last attempt: try some common patterns for output kinds if we can't
                # match the suffix precisely.
                if kind == OutputKind.Unknown:
                    kind = next(
                        (
                            k
                            for (p, k) in OUTPUT_SUFFIX_PATTERN_MAP.items()
                            if re.match(p, str(output_path))
                        ),
                        OutputKind.Unknown,
                    )

            outputs.append(Output(prenormalized_path=output, kind=kind, path=output_path))

        self._outputs = outputs

    def after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:
        store = self._config.get("store")
        if store is not None:
            store_path = Path(store)
            store_path.mkdir(parents=True, exist_ok=True)

            for output in self._outputs:
                if not output.path.exists():
                    logger.warning(f"tool={tool}'s output ({output.path}) does not exist")
                    continue

                # Outputs aren't guaranteed to have unique basenames and subsequent
                # steps in the build system could even modify a particular output
                # in-place, so we give each output a `store_path` based on a hash
                # of its content.
                content_hash = hashlib.sha256(output.path.read_bytes()).hexdigest()
                output_store_path = store_path / f"{output.path.name}-{content_hash}"
                if not output_store_path.exists():
                    shutil.copy(output.path, output_store_path)
                output.store_path = output_store_path

        outputs_record = OutputsRecord(tool=tool, outputs=self._outputs)
        output_path = Path(self._config["output"])
        with flock_append(output_path) as io:
            print(outputs_record.json(), file=io)
