# TODO: Base exception with token/index/lineno handling
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .token import Token


class JSONPathError(Exception):
    """Base exception for all JSONPath syntax and type errors."""


class JSONPathSyntaxError(JSONPathError):
    """An exception raised when parsing a JSONPath string."""

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token

    def __str__(self) -> str:
        msg = super().__str__()
        line, column = self.token.position()
        # TODO: give context from source path string
        return f"{msg}, line {line}, column {column}"


class JSONPathTypeError(Exception):
    """"""


def _truncate_message(value: str, num: int, end: str = "...") -> str:
    if len(value) < num:
        return value
    return f"{value[:num-len(end)]}{end}"
