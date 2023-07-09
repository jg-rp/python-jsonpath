"""The standard `search` function extension."""

import re
from typing import TYPE_CHECKING
from typing import List
from typing import Pattern
from typing import Union

from jsonpath.exceptions import JSONPathTypeError
from jsonpath.filter import RegexArgument
from jsonpath.filter import StringLiteral

if TYPE_CHECKING:
    from jsonpath.env import JSONPathEnvironment
    from jsonpath.token import Token


class Search:
    """The built-in `search` function.

    This implementation uses the standard _re_ module, without attempting to map
    I-Regexps to Python regex.
    """

    def __call__(self, string: str, pattern: Union[str, Pattern[str], None]) -> bool:
        """Return `True` if the given string contains _pattern_, `False` otherwise."""
        # The IETF JSONPath draft requires us to return `False` if the pattern was
        # invalid. We use `None` to indicate the pattern could not be compiled.
        if string is None or pattern is None:
            return False

        try:
            return bool(re.search(pattern, string))
        except (TypeError, re.error):
            return False

    def validate(
        self,
        _: "JSONPathEnvironment",
        args: List[object],
        token: "Token",
    ) -> List[object]:
        """Function argument validation."""
        if len(args) != 2:  # noqa: PLR2004
            raise JSONPathTypeError(
                f"{token.value!r} requires 2 arguments, found {len(args)}",
                token=token,
            )

        if isinstance(args[1], StringLiteral):
            try:
                return [args[0], RegexArgument(re.compile(args[1].value))]
            except re.error:
                return [None, None]

        return args
