"""The default JSONPath parser."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional

from jsonpath.function_extensions.filter_function import ExpressionType
from jsonpath.function_extensions.filter_function import FilterFunction

from .exceptions import JSONPathSyntaxError
from .exceptions import JSONPathTypeError
from .filter import CURRENT_KEY
from .filter import FALSE
from .filter import NIL
from .filter import TRUE
from .filter import UNDEFINED_LITERAL
from .filter import BooleanExpression
from .filter import FilterContextPath
from .filter import FilterExpression
from .filter import FilterQuery
from .filter import FloatLiteral
from .filter import FunctionExtension
from .filter import InfixExpression
from .filter import IntegerLiteral
from .filter import ListLiteral
from .filter import Literal
from .filter import Nil
from .filter import PrefixExpression
from .filter import RegexLiteral
from .filter import RelativeFilterQuery
from .filter import RootFilterQuery
from .filter import StringLiteral
from .path import JSONPath
from .segments import JSONPathChildSegment
from .segments import JSONPathRecursiveDescentSegment
from .segments import JSONPathSegment
from .selectors import Filter
from .selectors import IndexSelector
from .selectors import JSONPathSelector
from .selectors import KeysSelector
from .selectors import PropertySelector
from .selectors import SliceSelector
from .selectors import WildSelector
from .token import TOKEN_AND
from .token import TOKEN_COLON
from .token import TOKEN_COMMA
from .token import TOKEN_CONTAINS
from .token import TOKEN_DDOT
from .token import TOKEN_DOT
from .token import TOKEN_DOUBLE_QUOTE_STRING
from .token import TOKEN_EOF
from .token import TOKEN_EQ
from .token import TOKEN_FALSE
from .token import TOKEN_FILTER
from .token import TOKEN_FILTER_CONTEXT
from .token import TOKEN_FLOAT
from .token import TOKEN_FUNCTION
from .token import TOKEN_GE
from .token import TOKEN_GT
from .token import TOKEN_IN
from .token import TOKEN_INT
from .token import TOKEN_INTERSECTION
from .token import TOKEN_KEY
from .token import TOKEN_KEYS
from .token import TOKEN_LBRACKET
from .token import TOKEN_LE
from .token import TOKEN_LG
from .token import TOKEN_LPAREN
from .token import TOKEN_LT
from .token import TOKEN_MISSING
from .token import TOKEN_NAME
from .token import TOKEN_NE
from .token import TOKEN_NIL
from .token import TOKEN_NONE
from .token import TOKEN_NOT
from .token import TOKEN_NULL
from .token import TOKEN_OR
from .token import TOKEN_PSEUDO_ROOT
from .token import TOKEN_RBRACKET
from .token import TOKEN_RE
from .token import TOKEN_RE_FLAGS
from .token import TOKEN_RE_PATTERN
from .token import TOKEN_ROOT
from .token import TOKEN_RPAREN
from .token import TOKEN_SELF
from .token import TOKEN_SINGLE_QUOTE_STRING
from .token import TOKEN_TRUE
from .token import TOKEN_UNDEFINED
from .token import TOKEN_UNION
from .token import TOKEN_WILD
from .token import Token

if TYPE_CHECKING:
    from .env import JSONPathEnvironment
    from .stream import TokenStream

# ruff: noqa: D102

INVALID_NAME_SELECTOR_CHARS = [
    "\x00",
    "\x01",
    "\x02",
    "\x03",
    "\x04",
    "\x05",
    "\x06",
    "\x07",
    "\x08",
    "\t",
    "\n",
    "\x0b",
    "\x0c",
    "\r",
    "\x0e",
    "\x0f",
    "\x10",
    "\x11",
    "\x12",
    "\x13",
    "\x14",
    "\x15",
    "\x16",
    "\x17",
    "\x18",
    "\x19",
    "\x1a",
    "\x1b",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x1f",
]


class Parser:
    """A JSONPath parser bound to a JSONPathEnvironment."""

    PRECEDENCE_LOWEST = 1
    PRECEDENCE_LOGICAL_OR = 3
    PRECEDENCE_LOGICAL_AND = 4
    PRECEDENCE_RELATIONAL = 5
    PRECEDENCE_MEMBERSHIP = 6
    PRECEDENCE_PREFIX = 7

    PRECEDENCES = {
        TOKEN_AND: PRECEDENCE_LOGICAL_AND,
        TOKEN_CONTAINS: PRECEDENCE_MEMBERSHIP,
        TOKEN_EQ: PRECEDENCE_RELATIONAL,
        TOKEN_GE: PRECEDENCE_RELATIONAL,
        TOKEN_GT: PRECEDENCE_RELATIONAL,
        TOKEN_IN: PRECEDENCE_MEMBERSHIP,
        TOKEN_LE: PRECEDENCE_RELATIONAL,
        TOKEN_LG: PRECEDENCE_RELATIONAL,
        TOKEN_LT: PRECEDENCE_RELATIONAL,
        TOKEN_NE: PRECEDENCE_RELATIONAL,
        TOKEN_NOT: PRECEDENCE_PREFIX,
        TOKEN_OR: PRECEDENCE_LOGICAL_OR,
        TOKEN_RE: PRECEDENCE_RELATIONAL,
        TOKEN_RPAREN: PRECEDENCE_LOWEST,
    }

    # Mapping of operator token to canonical string.
    BINARY_OPERATORS = {
        TOKEN_AND: "&&",
        TOKEN_CONTAINS: "contains",
        TOKEN_EQ: "==",
        TOKEN_GE: ">=",
        TOKEN_GT: ">",
        TOKEN_IN: "in",
        TOKEN_LE: "<=",
        TOKEN_LG: "<>",
        TOKEN_LT: "<",
        TOKEN_NE: "!=",
        TOKEN_OR: "||",
        TOKEN_RE: "=~",
    }

    COMPARISON_OPERATORS = frozenset(
        [
            "==",
            ">=",
            ">",
            "<=",
            "<",
            "!=",
            "=~",
        ]
    )

    # Infix operators that accept filter expression literals.
    INFIX_LITERAL_OPERATORS = frozenset(
        [
            "==",
            ">=",
            ">",
            "<=",
            "<",
            "!=",
            "<>",
            "=~",
            "in",
            "contains",
        ]
    )

    PREFIX_OPERATORS = frozenset(
        [
            TOKEN_NOT,
        ]
    )

    RE_FLAG_MAP = {
        "a": re.A,
        "i": re.I,
        "m": re.M,
        "s": re.S,
    }

    _INVALID_NAME_SELECTOR_CHARS = f"[{''.join(INVALID_NAME_SELECTOR_CHARS)}]"
    RE_INVALID_NAME_SELECTOR = re.compile(
        rf'(?:(?!(?<!\\)"){_INVALID_NAME_SELECTOR_CHARS})'
    )

    def __init__(self, *, env: JSONPathEnvironment) -> None:
        self.env = env

        self.token_map: Dict[str, Callable[[TokenStream], FilterExpression]] = {
            TOKEN_DOUBLE_QUOTE_STRING: self.parse_string_literal,
            TOKEN_PSEUDO_ROOT: self.parse_root_path,
            TOKEN_FALSE: self.parse_boolean,
            TOKEN_FILTER_CONTEXT: self.parse_filter_context_path,
            TOKEN_FLOAT: self.parse_float_literal,
            TOKEN_FUNCTION: self.parse_function_extension,
            TOKEN_INT: self.parse_integer_literal,
            TOKEN_KEY: self.parse_current_key,
            TOKEN_LBRACKET: self.parse_list_literal,
            TOKEN_LPAREN: self.parse_grouped_expression,
            TOKEN_MISSING: self.parse_undefined,
            TOKEN_NIL: self.parse_nil,
            TOKEN_NONE: self.parse_nil,
            TOKEN_NOT: self.parse_prefix_expression,
            TOKEN_NULL: self.parse_nil,
            TOKEN_RE_PATTERN: self.parse_regex,
            TOKEN_ROOT: self.parse_root_path,
            TOKEN_SELF: self.parse_self_path,
            TOKEN_SINGLE_QUOTE_STRING: self.parse_string_literal,
            TOKEN_TRUE: self.parse_boolean,
            TOKEN_UNDEFINED: self.parse_undefined,
        }

        self.list_item_map: Dict[str, Callable[[TokenStream], FilterExpression]] = {
            TOKEN_FALSE: self.parse_boolean,
            TOKEN_FLOAT: self.parse_float_literal,
            TOKEN_INT: self.parse_integer_literal,
            TOKEN_NIL: self.parse_nil,
            TOKEN_NONE: self.parse_nil,
            TOKEN_NULL: self.parse_nil,
            TOKEN_DOUBLE_QUOTE_STRING: self.parse_string_literal,
            TOKEN_SINGLE_QUOTE_STRING: self.parse_string_literal,
            TOKEN_TRUE: self.parse_boolean,
        }

        self.function_argument_map: Dict[
            str, Callable[[TokenStream], FilterExpression]
        ] = {
            TOKEN_DOUBLE_QUOTE_STRING: self.parse_string_literal,
            TOKEN_PSEUDO_ROOT: self.parse_root_path,
            TOKEN_FALSE: self.parse_boolean,
            TOKEN_FILTER_CONTEXT: self.parse_filter_context_path,
            TOKEN_FLOAT: self.parse_float_literal,
            TOKEN_FUNCTION: self.parse_function_extension,
            TOKEN_INT: self.parse_integer_literal,
            TOKEN_KEY: self.parse_current_key,
            TOKEN_NIL: self.parse_nil,
            TOKEN_NONE: self.parse_nil,
            TOKEN_NULL: self.parse_nil,
            TOKEN_ROOT: self.parse_root_path,
            TOKEN_SELF: self.parse_self_path,
            TOKEN_SINGLE_QUOTE_STRING: self.parse_string_literal,
            TOKEN_TRUE: self.parse_boolean,
        }

    def parse(self, stream: TokenStream) -> Iterator[JSONPathSegment]:
        """Parse a JSONPath from a stream of tokens."""
        # TODO: Optionally require TOKEN_ROOT
        if stream.current().kind in {TOKEN_ROOT, TOKEN_PSEUDO_ROOT}:
            stream.next()

        yield from self.parse_path(stream)

        if stream.current().kind not in (TOKEN_EOF, TOKEN_INTERSECTION, TOKEN_UNION):
            raise JSONPathSyntaxError(
                f"unexpected token {stream.current().value!r}",
                token=stream.current(),
            )

    def parse_path(self, stream: TokenStream) -> Iterable[JSONPathSegment]:
        """Parse a JSONPath query string.

        This method assumes the root, current or pseudo root identifier has
        already been consumed.
        """
        while True:
            stream.skip_whitespace()
            _token = stream.current()
            if _token.kind == TOKEN_DOT:
                stream.eat(TOKEN_DOT)
                # Assert that dot is followed by shorthand selector without whitespace.
                stream.expect(TOKEN_NAME, TOKEN_WILD, TOKEN_KEYS)
                token = stream.current()
                selectors = self.parse_selectors(stream)
                yield JSONPathChildSegment(
                    env=self.env, token=token, selectors=selectors
                )
            elif _token.kind == TOKEN_DDOT:
                token = stream.eat(TOKEN_DDOT)
                selectors = self.parse_selectors(stream)
                if not selectors:
                    raise JSONPathSyntaxError(
                        "missing selector for recursive descent segment",
                        token=stream.current(),
                    )
                yield JSONPathRecursiveDescentSegment(
                    env=self.env, token=token, selectors=selectors
                )
            elif _token.kind == TOKEN_LBRACKET:
                selectors = self.parse_selectors(stream)
                yield JSONPathChildSegment(
                    env=self.env, token=_token, selectors=selectors
                )
            elif _token.kind in {TOKEN_NAME, TOKEN_WILD, TOKEN_KEYS}:
                # A non-standard "bare" path. One without a leading identifier (`$`,
                # `@`, `^` or `_`).
                token = stream.current()
                selectors = self.parse_selectors(stream)
                yield JSONPathChildSegment(
                    env=self.env, token=token, selectors=selectors
                )
            else:
                break

    def parse_selectors(self, stream: TokenStream) -> tuple[JSONPathSelector, ...]:
        token = stream.next()

        if token.kind == TOKEN_NAME:
            return (
                PropertySelector(
                    env=self.env,
                    token=token,
                    name=token.value,
                    shorthand=True,
                ),
            )

        if token.kind == TOKEN_WILD:
            return (
                WildSelector(
                    env=self.env,
                    token=token,
                    shorthand=True,
                ),
            )

        if token.kind == TOKEN_KEYS:
            return (
                KeysSelector(
                    env=self.env,
                    token=token,
                    shorthand=True,
                ),
            )

        if token.kind == TOKEN_LBRACKET:
            stream.pos -= 1
            return tuple(self.parse_bracketed_selection(stream))

        stream.pos -= 1
        return ()

    def parse_bracketed_selection(self, stream: TokenStream) -> List[JSONPathSelector]:  # noqa: PLR0912
        """Parse a comma separated list of JSONPath selectors."""
        segment_token = stream.eat(TOKEN_LBRACKET)
        selectors: List[JSONPathSelector] = []

        while True:
            stream.skip_whitespace()
            token = stream.current()

            if token.kind == TOKEN_RBRACKET:
                break

            if token.kind == TOKEN_INT:
                if (
                    stream.peek().kind == TOKEN_COLON
                    or stream.peek(2).kind == TOKEN_COLON
                ):
                    selectors.append(self.parse_slice(stream))
                else:
                    self._raise_for_leading_zero(token)
                    selectors.append(
                        IndexSelector(
                            env=self.env,
                            token=token,
                            index=int(token.value),
                        )
                    )
                    stream.next()
            elif token.kind in (
                TOKEN_DOUBLE_QUOTE_STRING,
                TOKEN_SINGLE_QUOTE_STRING,
            ):
                selectors.append(
                    PropertySelector(
                        env=self.env,
                        token=token,
                        name=self._decode_string_literal(token),
                        shorthand=False,
                    ),
                )
                stream.next()
            elif token.kind == TOKEN_COLON:
                selectors.append(self.parse_slice(stream))
            elif token.kind == TOKEN_WILD:
                selectors.append(
                    WildSelector(
                        env=self.env,
                        token=token,
                        shorthand=False,
                    )
                )
                stream.next()
            elif token.kind == TOKEN_KEYS:
                selectors.append(
                    KeysSelector(env=self.env, token=token, shorthand=False)
                )
                stream.next()
            elif token.kind == TOKEN_FILTER:
                selectors.append(self.parse_filter_selector(stream))
            elif token.kind == TOKEN_EOF:
                raise JSONPathSyntaxError("unexpected end of query", token=token)
            else:
                raise JSONPathSyntaxError(
                    f"unexpected token in bracketed selection {token.kind!r}",
                    token=token,
                )

            stream.skip_whitespace()

            if stream.current().kind == TOKEN_EOF:
                raise JSONPathSyntaxError(
                    "unexpected end of segment",
                    token=stream.current(),
                )

            if stream.current().kind != TOKEN_RBRACKET:
                stream.eat(TOKEN_COMMA)
                stream.skip_whitespace()
                if stream.current().kind == TOKEN_RBRACKET:
                    raise JSONPathSyntaxError(
                        "unexpected trailing comma", token=stream.current()
                    )

        stream.eat(TOKEN_RBRACKET)

        if not selectors:
            raise JSONPathSyntaxError("empty bracketed segment", token=segment_token)

        return selectors

    def parse_slice(self, stream: TokenStream) -> SliceSelector:
        """Parse a slice JSONPath expression from a stream of tokens."""
        token = stream.current()
        start: Optional[int] = None
        stop: Optional[int] = None
        step: Optional[int] = None

        def _maybe_index(token: Token) -> bool:
            if token.kind == TOKEN_INT:
                if len(token.value) > 1 and token.value.startswith(("0", "-0")):
                    raise JSONPathSyntaxError(
                        f"invalid index {token.value!r}", token=token
                    )
                return True
            return False

        # 1: or :
        if _maybe_index(stream.current()):
            start = int(stream.current().value)
            stream.next()

        stream.skip_whitespace()
        stream.expect(TOKEN_COLON)
        stream.next()
        stream.skip_whitespace()

        # 1 or 1: or : or ?
        if _maybe_index(stream.current()):
            stop = int(stream.current().value)
            stream.next()
            stream.skip_whitespace()
            if stream.current().kind == TOKEN_COLON:
                stream.next()
        elif stream.current().kind == TOKEN_COLON:
            stream.expect(TOKEN_COLON)
            stream.next()

        # 1 or ?
        stream.skip_whitespace()
        if _maybe_index(stream.current()):
            step = int(stream.current().value)
            stream.next()

        return SliceSelector(
            env=self.env,
            token=token,
            start=start,
            stop=stop,
            step=step,
        )

    def parse_filter_selector(self, stream: TokenStream) -> Filter:
        token = stream.eat(TOKEN_FILTER)
        expr = self.parse_filter_expression(stream)

        if self.env.well_typed and isinstance(expr, FunctionExtension):
            func = self.env.function_extensions.get(expr.name)
            if (
                func
                and isinstance(func, FilterFunction)
                and func.return_type == ExpressionType.VALUE
            ):
                raise JSONPathTypeError(
                    f"result of {expr.name}() must be compared", token=token
                )

        if isinstance(expr, (Literal, Nil)):
            raise JSONPathSyntaxError(
                "filter expression literals outside of "
                "function expressions must be compared",
                token=token,
            )

        return Filter(env=self.env, token=token, expression=BooleanExpression(expr))

    def parse_boolean(self, stream: TokenStream) -> FilterExpression:
        if stream.next().kind == TOKEN_TRUE:
            return TRUE
        return FALSE

    def parse_nil(self, stream: TokenStream) -> FilterExpression:
        stream.next()
        return NIL

    def parse_undefined(self, stream: TokenStream) -> FilterExpression:
        stream.next()
        return UNDEFINED_LITERAL

    def parse_string_literal(self, stream: TokenStream) -> FilterExpression:
        return StringLiteral(value=self._decode_string_literal(stream.next()))

    def parse_integer_literal(self, stream: TokenStream) -> FilterExpression:
        # Convert to float first to handle scientific notation.
        return IntegerLiteral(value=int(float(stream.next().value)))

    def parse_float_literal(self, stream: TokenStream) -> FilterExpression:
        return FloatLiteral(value=float(stream.next().value))

    def parse_prefix_expression(self, stream: TokenStream) -> FilterExpression:
        token = stream.next()
        assert token.kind == TOKEN_NOT
        return PrefixExpression(
            operator="!",
            right=self.parse_filter_expression(
                stream, precedence=self.PRECEDENCE_PREFIX
            ),
        )

    def parse_infix_expression(
        self, stream: TokenStream, left: FilterExpression
    ) -> FilterExpression:
        token = stream.next()
        precedence = self.PRECEDENCES.get(token.kind, self.PRECEDENCE_LOWEST)
        right = self.parse_filter_expression(stream, precedence)
        operator = self.BINARY_OPERATORS[token.kind]

        if self.env.well_typed and operator in self.COMPARISON_OPERATORS:
            self._raise_for_non_comparable_function(left, token)
            self._raise_for_non_comparable_function(right, token)

        if operator not in self.INFIX_LITERAL_OPERATORS:
            if isinstance(left, (Literal, Nil)):
                raise JSONPathSyntaxError(
                    "filter expression literals outside of "
                    "function expressions must be compared",
                    token=token,
                )
            if isinstance(right, (Literal, Nil)):
                raise JSONPathSyntaxError(
                    "filter expression literals outside of "
                    "function expressions must be compared",
                    token=token,
                )

        return InfixExpression(left, operator, right)

    def parse_grouped_expression(self, stream: TokenStream) -> FilterExpression:
        stream.eat(TOKEN_LPAREN)
        expr = self.parse_filter_expression(stream)

        while stream.current().kind != TOKEN_RPAREN:
            token = stream.current()
            if token.kind == TOKEN_EOF:
                raise JSONPathSyntaxError("unbalanced parentheses", token=token)

            if token.kind not in self.BINARY_OPERATORS:
                raise JSONPathSyntaxError(
                    f"expected an expression, found '{token.value}'",
                    token=token,
                )

            expr = self.parse_infix_expression(stream, expr)

        stream.eat(TOKEN_RPAREN)
        return expr

    def parse_root_path(self, stream: TokenStream) -> FilterExpression:
        root = stream.next()
        return RootFilterQuery(
            JSONPath(
                env=self.env,
                segments=self.parse_path(stream),
                pseudo_root=root.kind == TOKEN_PSEUDO_ROOT,
            )
        )

    def parse_self_path(self, stream: TokenStream) -> FilterExpression:
        stream.next()
        return RelativeFilterQuery(
            JSONPath(env=self.env, segments=self.parse_path(stream))
        )

    def parse_current_key(self, stream: TokenStream) -> FilterExpression:
        stream.next()
        return CURRENT_KEY

    def parse_filter_context_path(self, stream: TokenStream) -> FilterExpression:
        stream.next()
        return FilterContextPath(
            JSONPath(env=self.env, segments=self.parse_path(stream))
        )

    def parse_regex(self, stream: TokenStream) -> FilterExpression:
        pattern = stream.current().value
        flags = 0
        if stream.peek().kind == TOKEN_RE_FLAGS:
            stream.next()
            for flag in set(stream.next().value):
                flags |= self.RE_FLAG_MAP[flag]
        return RegexLiteral(value=re.compile(pattern, flags))

    def parse_list_literal(self, stream: TokenStream) -> FilterExpression:
        stream.eat(TOKEN_LBRACKET)
        list_items: List[FilterExpression] = []

        while True:
            stream.skip_whitespace()

            if stream.current().kind == TOKEN_RBRACKET:
                break

            try:
                list_items.append(self.list_item_map[stream.current().kind](stream))
            except KeyError as err:
                raise JSONPathSyntaxError(
                    f"unexpected {stream.current().value!r}",
                    token=stream.current(),
                ) from err

            stream.skip_whitespace()
            if stream.current().kind != TOKEN_RBRACKET:
                stream.eat(TOKEN_COMMA)
                stream.skip_whitespace()

        stream.eat(TOKEN_RBRACKET)
        return ListLiteral(list_items)

    def parse_function_extension(self, stream: TokenStream) -> FilterExpression:
        function_arguments: List[FilterExpression] = []
        function_token = stream.next()
        stream.eat(TOKEN_LPAREN)

        while True:
            stream.skip_whitespace()
            token = stream.current()

            if token.kind == TOKEN_RPAREN:
                break

            try:
                func = self.function_argument_map[token.kind]
            except KeyError as err:
                raise JSONPathSyntaxError(
                    f"unexpected {token.value!r}", token=token
                ) from err

            expr = func(stream)
            stream.skip_whitespace()

            while stream.current().kind in self.BINARY_OPERATORS:
                expr = self.parse_infix_expression(stream, expr)

            function_arguments.append(expr)
            stream.skip_whitespace()

            if stream.current().kind != TOKEN_RPAREN:
                stream.eat(TOKEN_COMMA)

        stream.eat(TOKEN_RPAREN)

        return FunctionExtension(
            function_token.value,
            self.env.validate_function_extension_signature(
                function_token, function_arguments
            ),
        )

    def parse_filter_expression(
        self, stream: TokenStream, precedence: int = PRECEDENCE_LOWEST
    ) -> FilterExpression:
        stream.skip_whitespace()
        token = stream.current()

        try:
            left = self.token_map[token.kind](stream)
        except KeyError as err:
            if token.kind in (TOKEN_EOF, TOKEN_RBRACKET):
                msg = "end of expression"
            else:
                msg = repr(token.value)
            raise JSONPathSyntaxError(f"unexpected {msg}", token=token) from err

        while True:
            stream.skip_whitespace()
            kind = stream.current().kind

            if (
                kind not in self.BINARY_OPERATORS
                or self.PRECEDENCES.get(kind, self.PRECEDENCE_LOWEST) < precedence
            ):
                break

            left = self.parse_infix_expression(stream, left)

        return left

    def _decode_string_literal(self, token: Token) -> str:
        if self.env.unicode_escape:
            if token.kind == TOKEN_SINGLE_QUOTE_STRING:
                value = token.value.replace('"', '\\"').replace("\\'", "'")
            else:
                value = token.value
            try:
                rv = json.loads(f'"{value}"')
                assert isinstance(rv, str)
                return rv
            except json.JSONDecodeError as err:
                raise JSONPathSyntaxError(str(err).split(":")[1], token=token) from None

        return token.value

    def _raise_for_non_comparable_function(
        self, expr: FilterExpression, token: Token
    ) -> None:
        if isinstance(expr, FilterQuery) and not expr.path.singular_query():
            raise JSONPathTypeError("non-singular query is not comparable", token=token)

        if isinstance(expr, FunctionExtension):
            func = self.env.function_extensions.get(expr.name)
            if (
                isinstance(func, FilterFunction)
                and func.return_type != ExpressionType.VALUE
            ):
                raise JSONPathTypeError(
                    f"result of {expr.name}() is not comparable", token
                )

    def _raise_for_leading_zero(self, token: Token) -> None:
        if (
            len(token.value) > 1 and token.value.startswith("0")
        ) or token.value.startswith("-0"):
            raise JSONPathSyntaxError("leading zero in index selector", token=token)
