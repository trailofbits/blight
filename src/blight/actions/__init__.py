"""
Actions supported by blight.
"""

from .benchmark import Benchmark  # noqa: F401
from .cc_for_cxx import CCForCXX  # noqa: F401
from .demo import Demo  # noqa: F401
from .embed_bitcode import EmbedBitcode  # noqa: F401
from .find_inputs import FindInputs  # noqa: F401
from .find_outputs import FindOutputs  # noqa: F401
from .ignore_flags import IgnoreFlags  # noqa: F401
from .ignore_flto import IgnoreFlto  # noqa: F401
from .ignore_werror import IgnoreWerror  # noqa: F401
from .inject_flags import InjectFlags  # noqa: F401
from .record import Record  # noqa: F401
from .skip_strip import SkipStrip  # noqa: F401
