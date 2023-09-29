"""The standard `match` function extension."""

import re

from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction


class Match(FilterFunction):
    """A type-aware implementation of the standard `match` function."""

    arg_types = [ExpressionType.VALUE, ExpressionType.VALUE]
    return_type = ExpressionType.LOGICAL

    def __call__(self, string: str, pattern: str) -> bool:
        """Return `True` if _string_ matches _pattern_, or `False` otherwise."""
        try:
            # re.fullmatch caches compiled patterns internally
            return bool(re.fullmatch(pattern, string))
        except (TypeError, re.error):
            return False
