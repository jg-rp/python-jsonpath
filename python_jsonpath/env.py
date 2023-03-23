"""Core JSONPath objects."""
from __future__ import annotations

import json
import re

from operator import getitem

from typing import Any
from typing import Iterable
from typing import Mapping
from typing import List
from typing import Sequence
from typing import Union

from .exceptions import JSONPathSyntaxError
from .exceptions import JSONPathTypeError

from .filter import UNDEFINED

from .lex import Lexer
from .parse import Parser

from .path import JSONPath
from .path import CompoundJSONPath

from .stream import TokenStream

from .token import TOKEN_EOF
from .token import TOKEN_UNION
from .token import TOKEN_INTERSECTION


class JSONPathEnvironment:
    """JSONPath configuration."""

    # TODO: Make these chars/tokens/operator not patterns
    root_pattern = r"\$"
    self_pattern = r"@"
    union_pattern = r"\|"
    intersection_pattern = r"&"

    # TODO: Interfaces and move to the constructor?
    lexer_class = Lexer
    parser_class = Parser

    def __init__(self) -> None:
        self.lexer = self.lexer_class(env=self)
        self.parser = self.parser_class(env=self)
        # TODO: don't reference lexer for this
        self.re_key = re.compile(self.lexer.key_pattern)

    def compile(self, path: str) -> Union[JSONPath, CompoundJSONPath]:
        """Prepare an internal representation of a JSONPath string."""
        tokens = self.lexer.tokenize(path)
        stream = TokenStream(tokens)
        _path: Union[JSONPath, CompoundJSONPath] = JSONPath(
            selectors=self.parser.parse(stream)
        )

        if stream.current.kind != TOKEN_EOF:
            _path = CompoundJSONPath(_path)
            while stream.current.kind != TOKEN_EOF:
                if stream.current.kind == TOKEN_UNION:
                    stream.next_token()
                    _path.union(JSONPath(selectors=self.parser.parse(stream)))
                elif stream.current.kind == TOKEN_INTERSECTION:
                    stream.next_token()
                    _path.intersection(JSONPath(selectors=self.parser.parse(stream)))
                else:
                    raise JSONPathSyntaxError(f"unexpected {stream.current}")

        return _path

    def findall(
        self,
        path: str,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
    ) -> List[object]:
        """Find all objects in `data` matching the given JSONPath. Return a
        list of matches, or an empty list if no matches.

        If `data` is a string, it will be loaded using :meth:`json.loads`.

        Raises a :class:`JSONPathSyntaxError` if the path is invalid.
        """
        # TODO: cache in convenience methods, not on .compile()
        _path = self.compile(path)
        if isinstance(data, str):
            data = json.loads(data)
        return _path.findall(data)

    def finditer(
        self,
        path: str,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
    ) -> Iterable[object]:
        """Return an iterator yielding :class:`JSONPathMatch` objects for each
        match of the path in the given `data`.

        If `data` is a string, it will be loaded using :meth:`json.loads`.

        Raises a :class:`JSONPathSyntaxError` if the path is invalid.
        """
        _path = self.compile(path)
        if isinstance(data, str):
            data = json.loads(data)
        return _path.finditer(data)

    def getitem(self, obj: Any, key: Any) -> Any:
        """Sequence and mapping item getter used throughout JSONPath resolution."""
        return getitem(obj, key)

    async def getitem_async(self, obj: Any, key: object) -> Any:
        """An async sequence and mapping item getter."""
        if hasattr(obj, "__getitem_async__"):
            return await obj.__getitem_async__(key)
        return getitem(obj, key)

    def is_truthy(self, obj: object) -> bool:
        """Test for truthiness when evaluating JSONPath filters."""
        # TODO: undefined
        return bool(obj)

    # pylint: disable=too-many-return-statements
    def compare(self, left: object, operator: str, right: object) -> bool:
        """Object comparison within JSONPath filters."""
        # TODO: better - this is temporary
        if operator == "and":
            return self.is_truthy(left) and self.is_truthy(right)
        if operator == "or":
            return self.is_truthy(left) or self.is_truthy(right)

        if operator == "==":
            return bool(left == right)
        if operator in ("!=", "<>"):
            return bool(left != right)

        if isinstance(right, Sequence):
            if operator == "in":
                return left in right

        # TODO: =~

        # This will catch booleans too.
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if operator == "<=":
                return left <= right
            if operator == ">=":
                return left >= right
            if operator == "<":
                return left < right
            if operator == ">":
                return left > right

        raise JSONPathTypeError(
            f"unknown operator: {type(left)} {operator} {type(right)}"
        )
