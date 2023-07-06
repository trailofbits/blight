"""
Actions supported by blight.
"""

from .benchmark import Benchmark
from .cc_for_cxx import CCForCXX
from .demo import Demo
from .embed_bitcode import EmbedBitcode
from .embed_commands import EmbedCommands  # noqa: F401
from .find_inputs import FindInputs
from .find_outputs import FindOutputs
from .ignore_flags import IgnoreFlags
from .ignore_flto import IgnoreFlto
from .ignore_werror import IgnoreWerror
from .inject_flags import InjectFlags
from .lint import Lint
from .record import Record
from .skip_strip import SkipStrip

__all__ = [
    "Benchmark",
    "CCForCXX",
    "Demo",
    "EmbedBitcode",
    "FindInputs",
    "FindOutputs",
    "IgnoreFlags",
    "IgnoreFlto",
    "IgnoreWerror",
    "InjectFlags",
    "Lint",
    "Record",
    "SkipStrip",
    "EmbedCommands",
]
