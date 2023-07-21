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

    def __str__(self) -> str:
        return f"pointer index error {super().__str__()}"


class JSONPointerKeyError(JSONPointerResolutionError, KeyError):
    """An exception raised when a pointer references a mapping with a missing key."""

    def __str__(self) -> str:
        return f"pointer key error {super().__str__()}"


class JSONPointerTypeError(JSONPointerResolutionError, TypeError):
    """An exception raised when a pointer resolves a string against a sequence."""

    def __str__(self) -> str:
        return f"pointer type error {super().__str__()}"


class RelativeJSONPointerError(Exception):
    """Base class for all Relative JSON Pointer errors."""


class RelativeJSONPointerIndexError(RelativeJSONPointerError):
    """An exception raised when modifying a pointer index out of range."""


class RelativeJSONPointerSyntaxError(RelativeJSONPointerError):
    """An exception raised when we fail to parse a relative JSON Pointer."""

    def __init__(self, msg: str, rel: str) -> None:
        super().__init__(msg)
        self.rel = rel

    def __str__(self) -> str:
        if not self.rel:
            return super().__str__()

        msg = self.rel[:7]
        if len(msg) == 6:  # noqa: PLR2004
            msg += ".."
        return f"{super().__str__()} {msg!r}"


class JSONPatchError(Exception):
    """Base class for all JSON Patch errors."""


class JSONPatchTestFailure(JSONPatchError):  # noqa: N818
    """An exception raised when a JSON Patch _test_ op fails."""


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
