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
        if stream.current.kind in {TOKEN_ROOT, TOKEN_PSEUDO_ROOT}:
            stream.next_token()

        yield from self.parse_path(stream, in_filter=False)

        if stream.current.kind not in (TOKEN_EOF, TOKEN_INTERSECTION, TOKEN_UNION):
            raise JSONPathSyntaxError(
                f"unexpected token {stream.current.value!r}",
                token=stream.current,
            )

    def parse_path(
        self,
        stream: TokenStream,
        *,
        in_filter: bool = False,
    ) -> Iterable[JSONPathSegment]:
        """Parse a top-level JSONPath, or one that is nested in a filter."""
        while True:
            if stream.current.kind == TOKEN_DDOT:
                token = stream.next_token()
                selectors = self.parse_selectors(stream)
                if not selectors:
                    raise JSONPathSyntaxError(
                        "missing selector for recursive descent segment",
                        token=stream.current,
                    )
                yield JSONPathRecursiveDescentSegment(
                    env=self.env, token=token, selectors=selectors
                )
            elif (
                stream.skip(TOKEN_DOT)
                and stream.current.kind
                in {
                    TOKEN_NAME,
                    TOKEN_WILD,
                    TOKEN_KEYS,
                }
            ) or stream.current.kind == TOKEN_LBRACKET:
                token = stream.current
                selectors = self.parse_selectors(stream)
                yield JSONPathChildSegment(
                    env=self.env, token=token, selectors=selectors
                )
            else:
                if in_filter:
                    stream.push(stream.current)
                break

            stream.next_token()

    def parse_selectors(self, stream: TokenStream) -> tuple[JSONPathSelector, ...]:
        if stream.current.kind == TOKEN_NAME:
            return (
                PropertySelector(
                    env=self.env,
                    token=stream.current,
                    name=stream.current.value,
                    shorthand=True,
                ),
            )

        if stream.current.kind == TOKEN_WILD:
            return (WildSelector(env=self.env, token=stream.current, shorthand=True),)

        if stream.current.kind == TOKEN_KEYS:
            return (
                KeysSelector(
                    env=self.env,
                    token=stream.current,
                    shorthand=True,
                ),
            )

        if stream.current.kind == TOKEN_LBRACKET:
            return tuple(self.parse_bracketed_selection(stream))

        return ()

    def parse_slice(self, stream: TokenStream) -> SliceSelector:
        """Parse a slice JSONPath expression from a stream of tokens."""
        tok = stream.current
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
        if _maybe_index(stream.current):
            start = int(stream.current.value)
            stream.next_token()

        stream.expect(TOKEN_COLON)
        stream.next_token()

        # 1 or 1: or : or ?
        if _maybe_index(stream.current):
            stop = int(stream.current.value)
            stream.next_token()
            if stream.current.kind == TOKEN_COLON:
                stream.next_token()
        elif stream.current.kind == TOKEN_COLON:
            stream.expect(TOKEN_COLON)
            stream.next_token()

        # 1 or ?
        if _maybe_index(stream.current):
            step = int(stream.current.value)
            stream.next_token()

        stream.push(stream.current)

        return SliceSelector(
            env=self.env,
            token=tok,
            start=start,
            stop=stop,
            step=step,
        )

    def parse_bracketed_selection(self, stream: TokenStream) -> List[JSONPathSelector]:  # noqa: PLR0912
        """Parse a comma separated list of JSONPath selectors."""
        tok = stream.next_token()  # Skip LBRACKET
        selectors: List[JSONPathSelector] = []

        while stream.current.kind != TOKEN_RBRACKET:
            if stream.current.kind == TOKEN_INT:
                if stream.peek.kind == TOKEN_COLON:
                    selectors.append(self.parse_slice(stream))
                else:
                    if (
                        len(stream.current.value) > 1
                        and stream.current.value.startswith("0")
                    ) or stream.current.value.startswith("-0"):
                        raise JSONPathSyntaxError(
                            "leading zero in index selector", token=stream.current
                        )
                    selectors.append(
                        IndexSelector(
                            env=self.env,
                            token=stream.current,
                            index=int(stream.current.value),
                        )
                    )
            elif stream.current.kind in (
                TOKEN_DOUBLE_QUOTE_STRING,
                TOKEN_SINGLE_QUOTE_STRING,
            ):
                selectors.append(
                    PropertySelector(
                        env=self.env,
                        token=stream.current,
                        name=self._decode_string_literal(stream.current),
                        shorthand=False,
                    ),
                )
            elif stream.current.kind == TOKEN_COLON:
                selectors.append(self.parse_slice(stream))
            elif stream.current.kind == TOKEN_WILD:
                selectors.append(
                    WildSelector(
                        env=self.env,
                        token=stream.current,
                        shorthand=False,
                    )
                )
            elif stream.current.kind == TOKEN_FILTER:
                selectors.append(self.parse_filter_selector(stream))
            elif stream.current.kind == TOKEN_EOF:
                raise JSONPathSyntaxError(
                    "unexpected end of query", token=stream.current
                )
            else:
                raise JSONPathSyntaxError(
                    f"unexpected token in bracketed selection {stream.current.kind!r}",
                    token=stream.current,
                )

            if stream.peek.kind == TOKEN_EOF:
                raise JSONPathSyntaxError(
                    "unexpected end of selector list",
                    token=stream.current,
                )

            if stream.peek.kind != TOKEN_RBRACKET:
                stream.expect_peek(TOKEN_COMMA)
                stream.next_token()
                stream.expect_peek_not(TOKEN_RBRACKET, "unexpected trailing comma")

            stream.next_token()

        if not selectors:
            raise JSONPathSyntaxError("empty bracketed segment", token=tok)

        return selectors

    def parse_filter_selector(self, stream: TokenStream) -> Filter:
        tok = stream.next_token()
        expr = self.parse_filter_expression(stream)

        if self.env.well_typed and isinstance(expr, FunctionExtension):
            func = self.env.function_extensions.get(expr.name)
            if (
                func
                and isinstance(func, FilterFunction)
                and func.return_type == ExpressionType.VALUE
            ):
                raise JSONPathTypeError(
                    f"result of {expr.name}() must be compared", token=tok
                )

        if isinstance(expr, (Literal, Nil)):
            raise JSONPathSyntaxError(
                "filter expression literals outside of "
                "function expressions must be compared",
                token=tok,
            )

        return Filter(env=self.env, token=tok, expression=BooleanExpression(expr))

    def parse_boolean(self, stream: TokenStream) -> FilterExpression:
        if stream.current.kind == TOKEN_TRUE:
            return TRUE
        return FALSE

    def parse_nil(self, _: TokenStream) -> FilterExpression:
        return NIL

    def parse_undefined(self, _: TokenStream) -> FilterExpression:
        return UNDEFINED_LITERAL

    def parse_string_literal(self, stream: TokenStream) -> FilterExpression:
        return StringLiteral(value=self._decode_string_literal(stream.current))

    def parse_integer_literal(self, stream: TokenStream) -> FilterExpression:
        # Convert to float first to handle scientific notation.
        return IntegerLiteral(value=int(float(stream.current.value)))

    def parse_float_literal(self, stream: TokenStream) -> FilterExpression:
        return FloatLiteral(value=float(stream.current.value))

    def parse_prefix_expression(self, stream: TokenStream) -> FilterExpression:
        tok = stream.next_token()
        assert tok.kind == TOKEN_NOT
        return PrefixExpression(
            operator="!",
            right=self.parse_filter_expression(
                stream, precedence=self.PRECEDENCE_PREFIX
            ),
        )

    def parse_infix_expression(
        self, stream: TokenStream, left: FilterExpression
    ) -> FilterExpression:
        tok = stream.next_token()
        precedence = self.PRECEDENCES.get(tok.kind, self.PRECEDENCE_LOWEST)
        right = self.parse_filter_expression(stream, precedence)
        operator = self.BINARY_OPERATORS[tok.kind]

        if self.env.well_typed and operator in self.COMPARISON_OPERATORS:
            self._raise_for_non_comparable_function(left, tok)
            self._raise_for_non_comparable_function(right, tok)

        if operator not in self.INFIX_LITERAL_OPERATORS:
            if isinstance(left, (Literal, Nil)):
                raise JSONPathSyntaxError(
                    "filter expression literals outside of "
                    "function expressions must be compared",
                    token=tok,
                )
            if isinstance(right, (Literal, Nil)):
                raise JSONPathSyntaxError(
                    "filter expression literals outside of "
                    "function expressions must be compared",
                    token=tok,
                )

        return InfixExpression(left, operator, right)

    def parse_grouped_expression(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        expr = self.parse_filter_expression(stream)
        stream.next_token()

        while stream.current.kind != TOKEN_RPAREN:
            if stream.current.kind == TOKEN_EOF:
                raise JSONPathSyntaxError(
                    "unbalanced parentheses", token=stream.current
                )

            if stream.current.kind not in self.BINARY_OPERATORS:
                raise JSONPathSyntaxError(
                    f"expected an expression, found '{stream.current.value}'",
                    token=stream.current,
                )

            expr = self.parse_infix_expression(stream, expr)

        stream.expect(TOKEN_RPAREN)
        return expr

    def parse_root_path(self, stream: TokenStream) -> FilterExpression:
        root = stream.next_token()
        return RootFilterQuery(
            JSONPath(
                env=self.env,
                segments=self.parse_path(stream, in_filter=True),
                pseudo_root=root.kind == TOKEN_PSEUDO_ROOT,
            )
        )

    def parse_self_path(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        return RelativeFilterQuery(
            JSONPath(env=self.env, segments=self.parse_path(stream, in_filter=True))
        )

    def parse_current_key(self, _: TokenStream) -> FilterExpression:
        return CURRENT_KEY

    def parse_filter_context_path(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        return FilterContextPath(
            JSONPath(env=self.env, segments=self.parse_path(stream, in_filter=True))
        )

    def parse_regex(self, stream: TokenStream) -> FilterExpression:
        pattern = stream.current.value
        flags = 0
        if stream.peek.kind == TOKEN_RE_FLAGS:
            stream.next_token()
            for flag in set(stream.current.value):
                flags |= self.RE_FLAG_MAP[flag]
        return RegexLiteral(value=re.compile(pattern, flags))

    def parse_list_literal(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        list_items: List[FilterExpression] = []

        while stream.current.kind != TOKEN_RBRACKET:
            try:
                list_items.append(self.list_item_map[stream.current.kind](stream))
            except KeyError as err:
                raise JSONPathSyntaxError(
                    f"unexpected {stream.current.value!r}",
                    token=stream.current,
                ) from err

            if stream.peek.kind != TOKEN_RBRACKET:
                stream.expect_peek(TOKEN_COMMA)
                stream.next_token()

            stream.next_token()

        return ListLiteral(list_items)

    def parse_function_extension(self, stream: TokenStream) -> FilterExpression:
        function_arguments: List[FilterExpression] = []
        tok = stream.next_token()

        while stream.current.kind != TOKEN_RPAREN:
            try:
                func = self.function_argument_map[stream.current.kind]
            except KeyError as err:
                raise JSONPathSyntaxError(
                    f"unexpected {stream.current.value!r}",
                    token=stream.current,
                ) from err

            expr = func(stream)

            # The argument could be a comparison or logical expression
            peek_kind = stream.peek.kind
            while peek_kind in self.BINARY_OPERATORS:
                stream.next_token()
                expr = self.parse_infix_expression(stream, expr)
                peek_kind = stream.peek.kind

            function_arguments.append(expr)

            if stream.peek.kind != TOKEN_RPAREN:
                stream.expect_peek(TOKEN_COMMA)
                stream.next_token()

            stream.next_token()

        return FunctionExtension(
            tok.value,
            self.env.validate_function_extension_signature(tok, function_arguments),
        )

    def parse_filter_expression(
        self, stream: TokenStream, precedence: int = PRECEDENCE_LOWEST
    ) -> FilterExpression:
        try:
            left = self.token_map[stream.current.kind](stream)
        except KeyError as err:
            if stream.current.kind in (TOKEN_EOF, TOKEN_RBRACKET):
                msg = "end of expression"
            else:
                msg = repr(stream.current.value)
            raise JSONPathSyntaxError(
                f"unexpected {msg}", token=stream.current
            ) from err

        while True:
            peek_kind = stream.peek.kind
            if (
                peek_kind in (TOKEN_EOF, TOKEN_RBRACKET)
                or self.PRECEDENCES.get(peek_kind, self.PRECEDENCE_LOWEST) < precedence
            ):
                break

            if peek_kind not in self.BINARY_OPERATORS:
                return left

            stream.next_token()
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
