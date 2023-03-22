"""The default JSONPath parser."""
# pylint: disable=missing-function-docstring
from __future__ import annotations

import re

from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from .exceptions import JSONPathSyntaxError

from .filter import BooleanExpression
from .filter import FALSE
from .filter import FilterExpression
from .filter import FloatLiteral
from .filter import InfixExpression
from .filter import IntegerLiteral
from .filter import ListLiteral
from .filter import NIL
from .filter import PrefixExpression
from .filter import RegexLiteral
from .filter import RootPath
from .filter import SelfPath
from .filter import StringLiteral
from .filter import TRUE

from .path import JSONPath
from .stream import TokenStream

from .selectors import Filter
from .selectors import IndexSelector
from .selectors import JSONPathSelector
from .selectors import ListSelector
from .selectors import PropertySelector
from .selectors import RecursiveDescentSelector
from .selectors import SliceSelector
from .selectors import WildSelector

from .token import TOKEN_AND
from .token import TOKEN_COMMA
from .token import TOKEN_CONTAINS
from .token import TOKEN_DDOT
from .token import TOKEN_EOF
from .token import TOKEN_EQ
from .token import TOKEN_FALSE
from .token import TOKEN_FILTER_END
from .token import TOKEN_FILTER_START
from .token import TOKEN_FLOAT
from .token import TOKEN_GE
from .token import TOKEN_GT
from .token import TOKEN_IN
from .token import TOKEN_INDEX
from .token import TOKEN_INT
from .token import TOKEN_INTERSECTION
from .token import TOKEN_LE
from .token import TOKEN_LG
from .token import TOKEN_LIST_END
from .token import TOKEN_LIST_PROPERTY
from .token import TOKEN_LIST_START
from .token import TOKEN_LPAREN
from .token import TOKEN_LT
from .token import TOKEN_NE
from .token import TOKEN_NIL
from .token import TOKEN_NOT
from .token import TOKEN_NULL
from .token import TOKEN_OR
from .token import TOKEN_PROPERTY
from .token import TOKEN_RE
from .token import TOKEN_RE_FLAGS
from .token import TOKEN_RE_PATTERN
from .token import TOKEN_ROOT
from .token import TOKEN_RPAREN
from .token import TOKEN_SELF
from .token import TOKEN_SLICE_START
from .token import TOKEN_SLICE_STEP
from .token import TOKEN_SLICE_STOP
from .token import TOKEN_STRING
from .token import TOKEN_TRUE
from .token import TOKEN_UNION
from .token import TOKEN_WILD

if TYPE_CHECKING:
    from .env import JSONPathEnvironment


class Parser:
    """A JSONPath expression parser bound to a JSONPathEnvironment."""

    PRECEDENCE_LOWEST = 1
    PRECEDENCE_LOGICALRIGHT = 3
    PRECEDENCE_LOGICAL = 4
    PRECEDENCE_RELATIONAL = 5
    PRECEDENCE_MEMBERSHIP = 6
    PRECEDENCE_PREFIX = 7

    PRECEDENCES = {
        TOKEN_AND: PRECEDENCE_LOGICALRIGHT,
        TOKEN_CONTAINS: PRECEDENCE_MEMBERSHIP,
        TOKEN_EQ: PRECEDENCE_RELATIONAL,
        TOKEN_GE: PRECEDENCE_RELATIONAL,
        TOKEN_GT: PRECEDENCE_RELATIONAL,
        TOKEN_IN: PRECEDENCE_MEMBERSHIP,
        TOKEN_LE: PRECEDENCE_RELATIONAL,
        TOKEN_LG: PRECEDENCE_RELATIONAL,
        TOKEN_LT: PRECEDENCE_RELATIONAL,
        TOKEN_NE: PRECEDENCE_RELATIONAL,
        TOKEN_NOT: PRECEDENCE_LOGICALRIGHT,
        TOKEN_OR: PRECEDENCE_LOGICALRIGHT,
        TOKEN_RE: PRECEDENCE_RELATIONAL,
        TOKEN_RPAREN: PRECEDENCE_LOWEST,
    }

    BINARY_OPERATORS = frozenset(
        (
            TOKEN_AND,
            TOKEN_CONTAINS,
            TOKEN_EQ,
            TOKEN_GE,
            TOKEN_GT,
            TOKEN_IN,
            TOKEN_LE,
            TOKEN_LG,
            TOKEN_LT,
            TOKEN_NE,
            TOKEN_OR,
            TOKEN_RE,
        )
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

    def __init__(self, *, env: JSONPathEnvironment) -> None:
        self.env = env

        self.token_map: Dict[str, Callable[[TokenStream], FilterExpression]] = {
            TOKEN_FALSE: self.parse_boolean,
            TOKEN_FLOAT: self.parse_float_literal,
            TOKEN_INT: self.parse_integer_literal,
            TOKEN_LPAREN: self.parse_grouped_expression,
            TOKEN_NIL: self.parse_nil,
            TOKEN_NOT: self.parse_prefix_expression,
            TOKEN_NULL: self.parse_nil,
            TOKEN_RE_PATTERN: self.parse_regex,
            TOKEN_ROOT: self.parse_root_path,
            TOKEN_SELF: self.parse_self_path,
            TOKEN_STRING: self.parse_string_literal,
            TOKEN_TRUE: self.parse_boolean,
        }

        self.list_item_map: Dict[str, Callable[[TokenStream], FilterExpression]] = {
            TOKEN_FALSE: self.parse_boolean,
            TOKEN_FLOAT: self.parse_float_literal,
            TOKEN_INT: self.parse_integer_literal,
            TOKEN_NIL: self.parse_nil,
            TOKEN_NULL: self.parse_nil,
            TOKEN_STRING: self.parse_string_literal,
            TOKEN_TRUE: self.parse_boolean,
        }

    def parse(self, stream: TokenStream) -> Iterable[JSONPathSelector]:
        """Parse a JSONPath from a stream of tokens."""
        if stream.current.kind == TOKEN_ROOT:
            stream.next_token()
        yield from self.parse_path(stream, in_filter=False)

        if stream.current.kind not in (TOKEN_EOF, TOKEN_INTERSECTION, TOKEN_UNION):
            raise JSONPathSyntaxError(
                f"unexpected token {stream.current!r}",
            )

    def parse_path(
        self,
        stream: TokenStream,
        in_filter: bool = False,
    ) -> Iterable[JSONPathSelector]:
        """Parse a top-level JSONPath, or one that is nested in a filter."""
        while True:
            if stream.current.kind == TOKEN_PROPERTY:
                yield PropertySelector(
                    env=self.env,
                    token=stream.current,
                    name=stream.current.value,
                )
            elif stream.current.kind == TOKEN_INDEX:
                yield IndexSelector(
                    env=self.env,
                    token=stream.current,
                    index=int(stream.current.value),
                )
            elif stream.current.kind == TOKEN_SLICE_START:
                yield self.parse_slice(stream)
            elif stream.current.kind == TOKEN_WILD:
                yield WildSelector(
                    env=self.env,
                    token=stream.current,
                )
            elif stream.current.kind == TOKEN_DDOT:
                yield RecursiveDescentSelector(
                    env=self.env,
                    token=stream.current,
                )
            elif stream.current.kind == TOKEN_LIST_START:
                yield self.parse_selector_list(stream)
            elif stream.current.kind == TOKEN_FILTER_START and not in_filter:
                yield self.parse_filter(stream)
            else:
                stream.push(stream.current)
                break

            stream.next_token()

    def parse_slice(self, stream: TokenStream) -> SliceSelector:
        """Parse a slice JSONPath expression from a stream of tokens."""
        start_token = stream.next_token()
        stream.expect(TOKEN_SLICE_STOP)
        stop_token = stream.next_token()
        stream.expect(TOKEN_SLICE_STEP)
        step_token = stream.current

        if not start_token.value:
            start: Optional[int] = None
        else:
            start = int(start_token.value)

        if not stop_token.value:
            stop: Optional[int] = None
        else:
            stop = int(stop_token.value)

        if not step_token.value:
            step: Optional[int] = None
        else:
            step = int(step_token.value)

        return SliceSelector(
            env=self.env,
            token=start_token,
            start=start,
            stop=stop,
            step=step,
        )

    def parse_selector_list(self, stream: TokenStream) -> ListSelector:
        """Parse a comma separated list JSONPath selectors from a stream
        of tokens."""
        tok = stream.next_token()
        list_items: List[Union[IndexSelector, PropertySelector, SliceSelector]] = []

        while stream.current.kind != TOKEN_LIST_END:
            if stream.current.kind == TOKEN_INT:
                list_items.append(
                    IndexSelector(
                        env=self.env,
                        token=stream.current,
                        index=int(stream.current.value),
                    )
                )
            elif stream.current.kind in (TOKEN_LIST_PROPERTY, TOKEN_STRING):
                list_items.append(
                    PropertySelector(
                        env=self.env,
                        token=stream.current,
                        name=stream.current.value,
                    )
                )
            elif stream.current.kind == TOKEN_SLICE_START:
                list_items.append(self.parse_slice(stream))
            elif stream.current.kind == TOKEN_EOF:
                raise JSONPathSyntaxError("unexpected end of list")
            stream.next_token()
            if stream.peek.kind != TOKEN_LIST_END:
                stream.expect_peek(TOKEN_COMMA)
                stream.next_token()

        return ListSelector(env=self.env, token=tok, items=list_items)

    def parse_filter(self, stream: TokenStream) -> Filter:
        tok = stream.next_token()
        expr = BooleanExpression(self.parse_filter_selector(stream))

        if stream.peek.kind == TOKEN_RPAREN:
            raise JSONPathSyntaxError("unmatched ')'")

        stream.next_token()
        assert stream.current.kind == TOKEN_FILTER_END
        return Filter(env=self.env, token=tok, expression=expr)

    def parse_boolean(self, stream: TokenStream) -> FilterExpression:
        if stream.current.kind == TOKEN_TRUE:
            return TRUE
        return FALSE

    def parse_nil(self, _: TokenStream) -> FilterExpression:
        return NIL

    def parse_string_literal(self, stream: TokenStream) -> FilterExpression:
        return StringLiteral(value=stream.current.value)

    def parse_integer_literal(self, stream: TokenStream) -> FilterExpression:
        return IntegerLiteral(value=int(stream.current.value))

    def parse_float_literal(self, stream: TokenStream) -> FilterExpression:
        return FloatLiteral(value=float(stream.current.value))

    def parse_prefix_expression(self, stream: TokenStream) -> FilterExpression:
        tok = stream.next_token()
        assert tok.kind == TOKEN_NOT
        return PrefixExpression(
            operator="not",
            right=self.parse_filter_selector(
                stream, precedence=self.PRECEDENCE_LOGICALRIGHT
            ),
        )

    def parse_infix_expression(
        self, stream: TokenStream, left: FilterExpression
    ) -> FilterExpression:
        tok = stream.next_token()
        precedence = self.PRECEDENCES.get(tok.kind, self.PRECEDENCE_LOWEST)
        return InfixExpression(
            left, tok.value, self.parse_filter_selector(stream, precedence)
        )

    def parse_grouped_expression(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        expr = self.parse_filter_selector(stream)
        stream.next_token()

        while stream.current.kind != TOKEN_RPAREN:
            if stream.current.kind in (TOKEN_EOF, TOKEN_FILTER_END):
                raise JSONPathSyntaxError("unbalanced parentheses")
            expr = self.parse_infix_expression(stream, expr)

        stream.expect(TOKEN_RPAREN)
        return expr

    def parse_root_path(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        return RootPath(JSONPath(selectors=self.parse_path(stream, in_filter=True)))

    def parse_self_path(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        return SelfPath(JSONPath(selectors=self.parse_path(stream, in_filter=True)))

    def parse_regex(self, stream: TokenStream) -> FilterExpression:
        pattern = re.escape(stream.current.value)
        if stream.peek.kind == TOKEN_RE_FLAGS:
            stream.next_token()
            flags = 0
            for flag in set(stream.current.value):
                flags |= self.RE_FLAG_MAP[flag]
        return RegexLiteral(value=re.compile(pattern, flags))

    def parse_list_literal(self, stream: TokenStream) -> FilterExpression:
        stream.next_token()
        list_items: List[FilterExpression] = []

        while stream.current.kind != TOKEN_LIST_END:
            try:
                list_items.append(self.list_item_map[stream.current.kind](stream))
            except KeyError as err:
                # TODO: line number etc.
                raise JSONPathSyntaxError(f"unexpected {stream.current}") from err

            stream.next_token()
            if stream.peek.kind != TOKEN_LIST_END:
                stream.expect_peek(TOKEN_COMMA)
                stream.next_token()

        return ListLiteral(list_items)

    def parse_filter_selector(
        self, stream: TokenStream, precedence: int = PRECEDENCE_LOWEST
    ) -> FilterExpression:
        try:
            left = self.token_map[stream.current.kind](stream)
        except KeyError as err:
            if stream.current.kind in (TOKEN_EOF, TOKEN_FILTER_END):
                msg = "end of expression"
            else:
                msg = repr(stream.current.value)
            raise JSONPathSyntaxError(f"unexpected {msg}") from err

        while True:
            peek_kind = stream.peek.kind
            if (
                peek_kind in (TOKEN_EOF, TOKEN_FILTER_END)
                or self.PRECEDENCES.get(peek_kind, self.PRECEDENCE_LOWEST) < precedence
            ):
                break

            if peek_kind not in self.BINARY_OPERATORS:
                return left

            stream.next_token()
            left = self.parse_infix_expression(stream, left)

        return left
