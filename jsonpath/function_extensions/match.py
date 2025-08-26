"""The standard `match` function extension."""

from typing import Optional

try:
    import regex as re

    REGEX_AVAILABLE = True
except ImportError:
    import re  # type: ignore

    REGEX_AVAILABLE = False

try:
    from iregexp_check import check

    IREGEXP_AVAILABLE = True
except ImportError:
    IREGEXP_AVAILABLE = False

from jsonpath.exceptions import JSONPathError
from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction
from jsonpath.lru_cache import LRUCache
from jsonpath.lru_cache import ThreadSafeLRUCache

from ._pattern import map_re


class Match(FilterFunction):
    """The standard `match` function.

    Arguments:
        cache_capacity: The size of the regular expression cache.
        debug: When `True`, raise an exception when regex pattern compilation
            fails. The default - as required by RFC 9535 - is `False`, which
            silently ignores bad patterns.
        thread_safe: When `True`, use a `ThreadSafeLRUCache` instead of an
            instance of `LRUCache`.
    """

    arg_types = [ExpressionType.VALUE, ExpressionType.VALUE]
    return_type = ExpressionType.LOGICAL

    def __init__(
        self,
        *,
        cache_capacity: int = 300,
        debug: bool = False,
        thread_safe: bool = False,
    ):
        self._cache: LRUCache[str, Optional[re.Pattern[str]]] = (
            ThreadSafeLRUCache(capacity=cache_capacity)
            if thread_safe
            else LRUCache(capacity=cache_capacity)
        )

        self.debug = debug

    def __call__(self, value: object, pattern: object) -> bool:
        """Return `True` if _value_ matches _pattern_, or `False` otherwise."""
        if not isinstance(value, str) or not isinstance(pattern, str):
            return False

        try:
            _pattern = self._cache[pattern]
        except KeyError:
            if IREGEXP_AVAILABLE and not check(pattern):
                if self.debug:
                    raise JSONPathError(
                        "search pattern is not a valid I-Regexp", token=None
                    ) from None
                _pattern = None
            else:
                if REGEX_AVAILABLE:
                    pattern = map_re(pattern)

                try:
                    _pattern = re.compile(pattern)
                except re.error:
                    if self.debug:
                        raise
                    _pattern = None

            self._cache[pattern] = _pattern

        if _pattern is None:
            return False

        return bool(_pattern.fullmatch(value))
