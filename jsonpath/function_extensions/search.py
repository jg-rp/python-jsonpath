"""The standard `search` function extension."""

try:
    import regex as re

    REGEX_AVAILABLE = True
except ImportError:
    import re  # type: ignore

    REGEX_AVAILABLE = False

from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction

from ._pattern import map_re


class Search(FilterFunction):
    """A type-aware implementation of the standard `search` function."""

    arg_types = [ExpressionType.VALUE, ExpressionType.VALUE]
    return_type = ExpressionType.LOGICAL

    def __call__(self, string: str, pattern: str) -> bool:
        """Return `True` if _string_ contains _pattern_, or `False` otherwise."""
        # XXX: re.search caches compiled patterns internally, but `map_re` is not
        # cached.
        if REGEX_AVAILABLE:
            try:
                pattern = map_re(pattern)
            except TypeError:
                return False

        try:
            return bool(re.search(pattern, string))
        except (TypeError, re.error):
            return False
