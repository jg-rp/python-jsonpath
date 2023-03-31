"""JSONPath exceptions."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

if TYPE_CHECKING:
    from .token import Token


class JSONPathError(Exception):
    """Base exception for all JSONPath syntax and type errors."""

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
    """An exception raised when parsing a JSONPath string."""

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathTypeError(JSONPathError):
    """An exception raised at filter evaluation time when a filter
    expression can not be evaluated due to type errors."""


class JSONPathNameError(JSONPathError):
    """An exception raised when an unknown function extension is called."""

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


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
