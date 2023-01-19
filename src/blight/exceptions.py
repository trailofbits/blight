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


class SkipRun(BlightError):  # noqa: N818
    """
    A special error that `before_run` actions can raise to tell the underlying
    tool not to actually run.
    """

    pass
