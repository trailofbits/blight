"""
The `FindInputs` action.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from blight.action import Action
from blight.constants import INPUT_SUFFIX_KIND_MAP
from blight.enums import InputKind
from blight.tool import Tool
from blight.util import flock_append


class Input(BaseModel):
    """
    Represents a single input to a tool.
    """

    kind: InputKind
    """
    The kind of input.
    """

    prenormalized_path: str
    """
    The path to the input, as passed directly to the tool itself.

    This copy of the path may be relative; consumers should prefer
    `path` for an absolute copy.
    """

    path: Path
    """
    The path to the input, as created by the tool.

    **NOTE**: This path may not actually exist, as a build system may arbitrarily
    choose to rename or relocate any inputs consumed by individual tools.
    """

    store_path: Optional[Path]
    """
    An optional stable path to the input, as preserved by the `FindInputs` action.

    `store_path` is only present if the `store=/some/dir/` setting is passed in the
    `FindInputs` configuration **and** the tool actually consumes the expected input.
    """

    content_hash: Optional[str]
    """
    A SHA256 hash of the input's content.

    `content_hash` is only present if the `store=/some/dir/` setting is passed in the
    `FindInputs` configuration **and** the tool actually consumes the expected input.
    """


class InputsRecord(BaseModel):
    """
    Represents a single `FindInputs` record. Each record contains a representation
    of the tool invocation that consumes the inputs, as well as the list of `Input`s
    associated with the invocation.
    """

    tool: Tool
    """
    The `Tool` invocation.
    """

    inputs: List[Input]
    """
    A list of `Input`s.
    """

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {Tool: lambda t: t.asdict()}


class FindInputs(Action):
    def before_run(self, tool: Tool) -> None:
        inputs = []
        for input in tool.inputs:
            input_path = Path(input)
            if not input_path.is_absolute():
                input_path = tool.cwd / input_path

            kind = INPUT_SUFFIX_KIND_MAP.get(input_path.suffix, InputKind.Unknown)

            inputs.append(Input(prenormalized_path=input, kind=kind, path=input_path))

        self._inputs = inputs

    def after_run(self, tool: Tool, *, run_skipped: bool = False) -> None:
        inputs = InputsRecord(tool=tool, inputs=self._inputs)

        if tool.is_journaling():
            # NOTE(ms): The `tool` member is excluded to avoid journal bloat.
            self._result = inputs.dict(exclude={"tool"})
        else:
            output_path = Path(self._config["output"])
            with flock_append(output_path) as io:
                print(inputs.json(), file=io)
