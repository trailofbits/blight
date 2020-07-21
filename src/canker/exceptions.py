"""
Exceptions for canker.
"""


class CankerError(ValueError):
    """
    Raised whenever an internal condition isn't met.
    """

    pass


class BuildError(CankerError):
    """
    Raised whenever a wrapped tool fails.
    """

    pass
