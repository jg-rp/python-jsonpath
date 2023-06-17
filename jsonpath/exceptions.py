"""JSONPath exceptions."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

if TYPE_CHECKING:
    from .token import Token


class JSONPathError(Exception):
    """Base exception for all errors.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Optional[Token] = None) -> None:
        super().__init__(*args)
        self.token: Optional[Token] = token

    def __str__(self) -> str:
        msg = super().__str__()

        if not self.token:
            return msg

        line, column = self.token.position()
        return f"{msg}, line {line}, column {column}"


class JSONPathSyntaxError(JSONPathError):
    """An exception raised when parsing a JSONPath string.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathTypeError(JSONPathError):
    """An exception raised due to a type error.

    This should only occur at when evaluating filter expressions.
    """


class JSONPathIndexError(JSONPathError):
    """An exception raised when an array index is out of range.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathNameError(JSONPathError):
    """An exception raised when an unknown function extension is called.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


class JSONPointerError(Exception):
    """Base class for all JSON Pointer errors."""


class JSONPointerEncodeError(JSONPointerError):
    """An exception raised when a JSONPathMatch can't be encoded to a JSON Pointer."""


class JSONPointerResolutionError(JSONPointerError):
    """Base exception for those that can be raised during pointer resolution."""


class JSONPointerIndexError(JSONPointerResolutionError, IndexError):
    """An exception raised when an array index is out of range."""


class JSONPointerKeyError(JSONPointerResolutionError, KeyError):
    """An exception raised when a pointer references a mapping with a missing key."""


class JSONPointerTypeError(JSONPointerResolutionError, TypeError):
    """An exception raised when a pointer resolves a string against a sequence."""


def _truncate_message(value: str, num: int, end: str = "...") -> str:
    if len(value) < num:
        return value
    return f"{value[:num-len(end)]}{end}"


def _truncate_words(val: str, num: int, end: str = "...") -> str:
    # Replaces consecutive whitespace with a single newline.
    words = val.split()
    if len(words) < num:
        return " ".join(words)
    return " ".join(words[:num]) + end
