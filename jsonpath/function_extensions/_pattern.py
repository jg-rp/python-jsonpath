from typing import Optional
from typing import Sequence

try:
    import regex as re

    REGEX_AVAILABLE = True
except ImportError:
    import re  # type: ignore

    REGEX_AVAILABLE = False

from jsonpath.exceptions import JSONPathError
from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction
from jsonpath.lru_cache import LRUCache
from jsonpath.lru_cache import ThreadSafeLRUCache

from .._iregexp import check_iregexp
from .._iregexp import map_iregexp


class AbstractRegexFilterFunction(FilterFunction):
    """Base class for filter function that accept regular expression arguments.

    Arguments:
        cache_capacity: The size of the regular expression cache.
        debug: When `True`, raise an exception when regex pattern compilation
            fails. The default - as required by RFC 9535 - is `False`, which
            silently ignores bad patterns.
        thread_safe: When `True`, use a `ThreadSafeLRUCache` instead of an
            instance of `LRUCache`.
        check_iregexp: When `True`, check regular expression patterns for
            I-Regexp compliance.
    """

    arg_types: Sequence[ExpressionType] = [ExpressionType.VALUE, ExpressionType.VALUE]
    return_type: ExpressionType = ExpressionType.LOGICAL

    def __init__(
        self,
        *,
        cache_capacity: int = 300,
        debug: bool = False,
        thread_safe: bool = False,
        check_iregexp: bool = REGEX_AVAILABLE,
    ):
        self.cache: LRUCache[str, Optional[re.Pattern]] = (  # type: ignore
            ThreadSafeLRUCache(capacity=cache_capacity)
            if thread_safe
            else LRUCache(capacity=cache_capacity)
        )

        self.check_iregexp = check_iregexp
        self.debug = debug

    def check_cache(self, pattern: str) -> Optional[re.Pattern]:  # type: ignore
        """Return a compiled re pattern if `pattern` is valid, or `None` otherwise."""
        try:
            _pattern = self.cache[pattern]
        except KeyError:
            if self.check_iregexp and not check_iregexp(pattern):
                if self.debug:
                    raise JSONPathError(
                        "search pattern is not a valid I-Regexp", token=None
                    ) from None
                _pattern = None
            else:
                if REGEX_AVAILABLE:
                    pattern = map_iregexp(pattern, escape_anchors=False, wrap=False)

                try:
                    _pattern = re.compile(pattern)
                except re.error:
                    if self.debug:
                        raise
                    _pattern = None

            self.cache[pattern] = _pattern

        return _pattern
