"""
Exceptions for blight.
"""


class BlightError(ValueError):
    """
    Raised whenever an internal condition isn't met.
    """

    pass


class BuildError(BlightError):
    """
    Raised whenever a wrapped tool fails.
    """

    pass
