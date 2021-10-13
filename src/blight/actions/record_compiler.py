import os
import re
import hashlib
import logging
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict

from blight.action import CompilerAction, LDAction
from blight.tool import Tool
from blight.util import flock_append


def is_blight_env(key):
    """Return True if the key is associated
    with blight
    """
    return key.startswith("BLIGHT")


def SHA256(value):
    """Get sha256 hash from the value"""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_compiler_with_sysroot(wrapped_tool) -> str:
    """Get the compiler profile with the dummy sysroot
    as options
    """
    envs = os.environ.copy()
    cwd_path = os.getcwd()
    proc = subprocess.Popen(
        [
            wrapped_tool,
            "-E",
            "-v",
            "-x",
            "c++",
            "-isysroot",
            cwd_path + "/xyz",
            "-",
            "-fsyntax-only",
            "-Wno-missing-sysroot",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=envs,
    )
    value, error = proc.communicate("")
    return value.decode("utf-8")


def get_compiler_without_sysroot(wrapped_tool) -> str:
    """Get the compiler profile without sysroot"""
    envs = os.environ.copy()
    proc = subprocess.Popen(
        [
            wrapped_tool,
            "-E",
            "-v",
            "-x",
            "c++",
            "-",
            "-fsyntax-only",
            "-Wno-missing-sysroot",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=envs,
    )
    value, error = proc.communicate("")
    return value.decode("utf-8")


def get_compiler_info(wrapped_tool) -> str:
    """Get the compiler info in json format"""
    compiler = dict()
    sysroot = get_compiler_with_sysroot(wrapped_tool).splitlines()
    no_sysroot = get_compiler_without_sysroot(wrapped_tool).splitlines()
    
    # replace the special character from list to avoid getting issues
    # while generating string from json
    compiler["sysroot"] = [path.replace('"', "'") for path in sysroot]
    compiler["no_sysroot"] = [path.replace('"', "'") for path in no_sysroot]
    sha256 = SHA256(json.dumps(compiler))

    # Embed compiler info hash with the json to map it with compile command
    compiler["hash"] = sha256
    return json.dumps(compiler).replace('"', '\\"').replace("\\\\", "\\"), sha256


def cc_as_string(tool_record: Dict, hash_str=None):
    tool_record["hash"] = hash_str
    return json.dumps(tool_record).replace('"', '\\"').replace("\\\\", "\\")


_ALIGN = 4
def align_string(string: str) -> str:
    length = len(string)
    length_aligned = length if length % _ALIGN == 0 else (int(length / _ALIGN) + 1) * _ALIGN
    return string.ljust(length_aligned, '\0')


class CompileCommand(CompilerAction):
    def __init__(self, config):
        super(CompileCommand, self).__init__(config)
        self._tool = None

    def _is_input_assembly(self):
        has_assembly = False
        if self._tool is not None:
            for inpt in self._tool.inputs:
                has_assembly = has_assembly or \
                               str(inpt).endswith(".S") or \
                               str(inpt).endswith(".s")
        return has_assembly

    def _get_header_file(self):
        output = Path(self._config["output"])
        tool_record = self._tool.asdict()

        cmd_hash = SHA256(json.dumps(tool_record))
        header_file = "{}/{}.h".format(output, cmd_hash)
        if os.path.exists(header_file):
            os.remove(header_file)
        return header_file

    def _get_tool_asdict(self):
        if self._tool is None:
            return dict()

        tool_record = self._tool.asdict()
        envs = tool_record["env"]
        updated_envs = dict()
        for key, value in envs.items():
            if key == "PS1" or key == "LS_COLORS" or is_blight_env(key):
                continue
            if isinstance(value, str):
                updated_envs[key] = value.replace('"', "'")
            elif isinstance(value, list):
                updated_envs[key] = [v.replace('"', "'") for v in value]
            else:
                updated_envs[key] = value

        args = tool_record["args"]
        canonicalized_args = tool_record["canonicalized_args"]
        tool_record["args"] = [v.replace('"', "'") for v in args]
        tool_record["canonicalized_args"] = [v.replace('"', "'") for v in canonicalized_args]
        tool_record["env"] = updated_envs
        tool_record["wrapped_tool"] = shutil.which(self._tool.wrapped_tool())
        return tool_record

    def before_run(self, tool: Tool) -> None:
        self._tool = tool
        if self._is_input_assembly():
            return

        comp_info, sha256 = get_compiler_info(self._tool.wrapped_tool())
        cc_string = cc_as_string(self._get_tool_asdict(), sha256)        
        
        file = self._get_header_file()
        with flock_append(file) as io:
            variable = """
#ifndef __linux__
    __attribute__((used,section(\"__DATA,.trailofbits_cc\"))) static const char var_{}[] = \"{}\";
    __attribute__((used,selectany,section(\"__DATA,.trailofbits_ci\"))) extern const char compinfo_{}[] = \"{}\";
#else
    __attribute__((used,section(\".trailofbits_cc, \\"S\\", @note;\\n#\"))) static const char var_{}[] = \"''{}\";
   /* __attribute__((used,section(\".trailofbits_ci, \\"S\\", @note;\\n#\"))) extern const char compinfo_{}[] __attribute__((weak)) = \"{}\";
   */
#endif""".format(
                SHA256(cc_string),
                cc_string.strip(),
                sha256,
                comp_info.strip(),
                SHA256(cc_string),
                cc_string.strip(),
                sha256,
                comp_info.strip(),
            )
            print(variable, file=io)

        tool.args += ["-include", file, 
                      "-Wno-overlength-strings",
                      "-Wno-error",
                      "-Wno-extern-initializer",
                      "-Wno-unknown-escape-sequence"]
