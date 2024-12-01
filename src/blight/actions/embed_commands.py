"""
The `EmbedCommands` action.

`EmbedCommands` embeds JSON compile commands, including environment variables,
inside of a custom section of each built object file. These sections make it
into the final binary.
"""

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

from blight.action import CompilerAction
from blight.enums import Lang
from blight.tool import CompilerTool
from blight.util import flock_append


def cc_as_string(tool_record: Dict) -> str:
    return json.dumps(tool_record).replace('\\', '\\\\').replace('"', '\\"')


def add_to_envp(envp: Dict, key: str, value: Any) -> None:
    if isinstance(value, str):
        envp[key] = value
    elif isinstance(value, list):
        envp[key] = [v for v in value]
    else:
        envp[key] = value

VALID_EXTENSIONS = ("c", "cc", "cxx", "cpp", "c++")

def is_input_source_code(tool: CompilerTool) -> bool:
    for file_path in tool.inputs:
        extension = str(file_path).lower().split(".")[-1]
        if extension in VALID_EXTENSIONS:
            return True
    return False


def cc_as_dict(tool: CompilerTool) -> Dict:
    env: Dict[str, Any] = {}
    tool_dict = tool.asdict()
    old_env = tool_dict["env"]
    for key, value in old_env.items():
        if key == "PS1" or key == "LS_COLORS" or key.startswith("BLIGHT"):
            continue
        add_to_envp(env, key, value)

    for key, value in old_env.items():
        if key.startswith("BLIGHT_WRAPPED_"):
            add_to_envp(env, key[15:], value)

    return {
        "cwd": tool_dict["cwd"],
        "env": env,
        "args": [v for v in tool.args],
        "canonicalized_args": [v for v in tool.canonicalized_args],
        "wrapped_tool": shutil.which(tool.wrapped_tool()),
        "lang": tool.lang.name,
    }


_VARIABLE_TEMPLATE = """
#if !defined(__linux__)
__attribute__((section(\"__DATA,.trailofbits_cc\")))
#elif !defined(__clang__)
__attribute__((section(\".trailofbits_cc, \\"S\\", @note;\\n#\")))
#else
__attribute__((section(\".trailofbits_cc\")))
#endif
__attribute__((used))
static const char cc_{}[] = \"{}\";
"""


class EmbedCommands(CompilerAction):
    def __init__(self, config: dict[str, str]) -> None:
        super().__init__(config)

    def _get_header_file(self, cmd_hash: str) -> str:
        f = tempfile.NamedTemporaryFile(suffix=".h", delete=False)
        return f.name

    def before_run(self, tool: CompilerTool) -> None:
        if not is_input_source_code(tool):
            return

        cc_string = cc_as_string(cc_as_dict(tool)).strip()
        cmd_hash = hashlib.sha256(cc_string.encode()).hexdigest()
        header_file = self._get_header_file(cmd_hash)
        with flock_append(Path(header_file)) as io:
            variable = _VARIABLE_TEMPLATE.format(cmd_hash, cc_string)
            print(variable, file=io)

        tool.args += [
            "-include",
            header_file,
            "-Wno-overlength-strings",
            "-Wno-error",
            "-Wno-unknown-escape-sequence",
        ]
