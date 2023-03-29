"""JSONPath tokenization."""
from __future__ import annotations

import re
from functools import partial
from typing import TYPE_CHECKING, Iterator, Pattern

from .exceptions import JSONPathSyntaxError
from .token import (
    TOKEN_AND,
    TOKEN_BARE_PROPERTY,
    TOKEN_BRACKET_PROPERTY,
    TOKEN_COMMA,
    TOKEN_CONTAINS,
    TOKEN_DDOT,
    TOKEN_DOT_INDEX,
    TOKEN_DOT_PROPERTY,
    TOKEN_DOUBLE_QUOTE_STRING,
    TOKEN_EQ,
    TOKEN_FALSE,
    TOKEN_FILTER_CONTEXT,
    TOKEN_FILTER_END,
    TOKEN_FILTER_START,
    TOKEN_FLOAT,
    TOKEN_GE,
    TOKEN_GT,
    TOKEN_ILLEGAL,
    TOKEN_IN,
    TOKEN_INDEX,
    TOKEN_INT,
    TOKEN_INTERSECTION,
    TOKEN_LE,
    TOKEN_LG,
    TOKEN_LIST_END,
    TOKEN_LIST_SLICE,
    TOKEN_LIST_START,
    TOKEN_LPAREN,
    TOKEN_LT,
    TOKEN_MISSING,
    TOKEN_NE,
    TOKEN_NIL,
    TOKEN_NONE,
    TOKEN_NOT,
    TOKEN_NULL,
    TOKEN_OR,
    TOKEN_PROPERTY,
    TOKEN_RE,
    TOKEN_RE_FLAGS,
    TOKEN_RE_PATTERN,
    TOKEN_ROOT,
    TOKEN_RPAREN,
    TOKEN_SELF,
    TOKEN_SINGLE_QUOTE_STRING,
    TOKEN_SKIP,
    TOKEN_SLICE,
    TOKEN_SLICE_START,
    TOKEN_SLICE_STEP,
    TOKEN_SLICE_STOP,
    TOKEN_STRING,
    TOKEN_TRUE,
    TOKEN_UNDEFINED,
    TOKEN_UNION,
    TOKEN_WILD,
    Token,
)

if TYPE_CHECKING:
    from . import JSONPathEnvironment


class Lexer:
    """Tokenize a JSONPath string."""

    def __init__(self, *, env: JSONPathEnvironment) -> None:
        self.env = env

        self.key_pattern = r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*"

        self.double_quote_pattern = r'"(?P<G_DQUOTE>(?:(?!(?<!\\)").)*)"'
        self.single_quote_pattern = r"'(?P<G_SQUOTE>(?:(?!(?<!\\)').)*)'"

        # .thing
        self.dot_property_pattern = rf"\.(?P<G_PROP>{self.key_pattern})"

        # [thing]
        self.bracketed_property_pattern = rf"\[\s*(?P<G_BPROP>{self.key_pattern})\s*]"

        # .1
        # NOTE: `.1` can be a dot property where the key is "1".
        self.dot_index_pattern = r"\.\s*(?P<G_DINDEX>\d+)\b"

        # [1] or [-1]
        self.index_pattern = r"\[\s*(?P<G_INDEX>\-?\s*\d+)\s*]"

        # [:] or [1:-1] or [1:] or [:1] or [-1:] or [:-1] or [::] or [-1:0:-1]
        self.slice_pattern = (
            r"\[\s*(?P<G_SLICE_START>\-?\d*)\s*"
            r":\s*(?P<G_SLICE_STOP>\-?\d*)\s*"
            r"(?::\s*(?P<G_SLICE_STEP>\-?\d*))?\s*]"
        )

        self.slice_list_pattern = (
            r"(?P<G_LSLICE_START>\-?\d*)\s*"
            r":\s*(?P<G_LSLICE_STOP>\-?\d*)\s*"
            r"(?::\s*(?P<G_LSLICE_STEP>\-?\d*))?"
        )

        # .* or [*] or .[*]
        self.wild_pattern = r"\.?(?:\[\s*\*\s*]|\*)"

        # `not` or !
        self.logical_not_pattern = r"(?:not|!)"

        # && or `and`
        self.bool_and_pattern = r"(?:&&|and)"

        # || or `or`
        self.bool_or_pattern = r"(?:\|\||or)"

        # /pattern/ or /pattern/flags
        self.re_pattern = r"/(?P<G_RE>.+?)/(?P<G_RE_FLAGS>[aims]*)"

        self.rules = self.compile_rules()

    def compile_rules(self) -> Pattern[str]:
        """Prepare regular expression rules."""
        rules = [
            (TOKEN_DOUBLE_QUOTE_STRING, self.double_quote_pattern),
            (TOKEN_SINGLE_QUOTE_STRING, self.single_quote_pattern),
            (TOKEN_RE_PATTERN, self.re_pattern),
            (TOKEN_DOT_INDEX, self.dot_index_pattern),
            (TOKEN_INDEX, self.index_pattern),
            (TOKEN_SLICE, self.slice_pattern),
            (TOKEN_WILD, self.wild_pattern),
            (TOKEN_LIST_SLICE, self.slice_list_pattern),
            (TOKEN_FILTER_START, r"\[\s*\?\s*\("),
            (TOKEN_FILTER_END, r"\)\s*]"),
            (TOKEN_BRACKET_PROPERTY, self.bracketed_property_pattern),
            (TOKEN_DOT_PROPERTY, self.dot_property_pattern),
            (TOKEN_FLOAT, r"-?\d+\.\d*(?:e[+-]?\d+)?"),
            (TOKEN_INT, r"-?\d+(?:e[+\-]?\d+)?\b"),
            (TOKEN_DDOT, r"\.\."),
            (TOKEN_AND, self.bool_and_pattern),
            (TOKEN_OR, self.bool_or_pattern),
            (TOKEN_ROOT, re.escape(self.env.root_token)),
            (TOKEN_SELF, re.escape(self.env.self_token)),
            (TOKEN_UNION, re.escape(self.env.union_token)),
            (TOKEN_INTERSECTION, re.escape(self.env.intersection_token)),
            (TOKEN_FILTER_CONTEXT, re.escape(self.env.filter_context_token)),
            (TOKEN_IN, r"in"),
            (TOKEN_TRUE, r"[Tt]rue"),
            (TOKEN_FALSE, r"[Ff]alse"),
            (TOKEN_NIL, r"[Nn]il"),
            (TOKEN_NULL, r"[Nn]ull"),
            (TOKEN_NONE, r"[Nn]one"),
            (TOKEN_CONTAINS, r"contains"),
            (TOKEN_UNDEFINED, r"undefined"),
            (TOKEN_MISSING, r"missing"),
            (TOKEN_LIST_START, r"\["),
            (TOKEN_LIST_END, r"]"),
            (TOKEN_COMMA, r","),
            (TOKEN_EQ, r"=="),
            (TOKEN_NE, r"!="),
            (TOKEN_LG, r"<>"),
            (TOKEN_LE, r"<="),
            (TOKEN_GE, r">="),
            (TOKEN_RE, r"=~"),
            (TOKEN_LT, r"<"),
            (TOKEN_GT, r">"),
            (TOKEN_NOT, self.logical_not_pattern),
            (TOKEN_BARE_PROPERTY, self.key_pattern),
            (TOKEN_LPAREN, r"\("),
            (TOKEN_RPAREN, r"\)"),
            (TOKEN_SKIP, r"[ \n\t\r\.]+"),
            (TOKEN_ILLEGAL, r"."),
        ]

        return re.compile(
            "|".join(f"(?P<{token}>{pattern})" for token, pattern in rules),
            re.DOTALL,
        )

    def tokenize(self, path: str) -> Iterator[Token]:  # noqa PLR0912
        """Generate a sequence of tokens from a JSONPath string."""
        _token = partial(Token, path=path)

        for match in self.rules.finditer(path):
            kind = match.lastgroup
            assert kind is not None

            if kind == TOKEN_DOT_PROPERTY:
                yield _token(
                    kind=TOKEN_PROPERTY,
                    value=match.group("G_PROP"),
                    index=match.start("G_PROP"),
                )
            elif kind == TOKEN_BRACKET_PROPERTY:
                yield _token(
                    kind=TOKEN_PROPERTY,
                    value=match.group("G_BPROP"),
                    index=match.start("G_BPROP"),
                )
            elif kind == TOKEN_BARE_PROPERTY:
                yield _token(
                    kind=TOKEN_BARE_PROPERTY,
                    value=match.group(),
                    index=match.start(),
                )
            elif kind == TOKEN_LIST_SLICE:
                yield _token(
                    kind=TOKEN_SLICE_START,
                    value=match.group("G_LSLICE_START"),
                    index=match.start("G_LSLICE_START"),
                )
                yield _token(
                    kind=TOKEN_SLICE_STOP,
                    value=match.group("G_LSLICE_STOP"),
                    index=match.start("G_LSLICE_STOP"),
                )
                yield _token(
                    kind=TOKEN_SLICE_STEP,
                    value=match.group("G_LSLICE_STEP") or "",
                    index=match.start("G_LSLICE_STEP"),
                )
            elif kind == TOKEN_DOT_INDEX:
                yield _token(
                    kind=TOKEN_INDEX,
                    value=match.group("G_DINDEX"),
                    index=match.start("G_DINDEX"),
                )
            elif kind == TOKEN_INDEX:
                yield _token(
                    kind=TOKEN_INDEX,
                    value=match.group("G_INDEX"),
                    index=match.start("G_INDEX"),
                )
            elif kind == TOKEN_SLICE:
                yield _token(
                    kind=TOKEN_SLICE_START,
                    value=match.group("G_SLICE_START"),
                    index=match.start("G_SLICE_START"),
                )
                yield _token(
                    kind=TOKEN_SLICE_STOP,
                    value=match.group("G_SLICE_STOP"),
                    index=match.start("G_SLICE_STOP"),
                )
                yield _token(
                    kind=TOKEN_SLICE_STEP,
                    value=match.group("G_SLICE_STEP") or "",
                    index=match.start("G_SLICE_STEP"),
                )
            elif kind == TOKEN_DOUBLE_QUOTE_STRING:
                yield _token(
                    kind=TOKEN_STRING,
                    value=match.group("G_DQUOTE"),
                    index=match.start("G_DQUOTE"),
                )
            elif kind == TOKEN_SINGLE_QUOTE_STRING:
                yield _token(
                    kind=TOKEN_STRING,
                    value=match.group("G_SQUOTE"),
                    index=match.start("G_SQUOTE"),
                )
            elif kind == TOKEN_RE_PATTERN:
                yield _token(
                    kind=TOKEN_RE_PATTERN,
                    value=match.group("G_RE"),
                    index=match.start("G_RE"),
                )
                yield _token(
                    TOKEN_RE_FLAGS,
                    value=match.group("G_RE_FLAGS"),
                    index=match.start("G_RE_FLAGS"),
                )
            elif kind in (TOKEN_NONE, TOKEN_NULL):
                yield _token(
                    kind=TOKEN_NIL,
                    value=match.group(),
                    index=match.start(),
                )
            elif kind == TOKEN_SKIP:
                continue
            elif kind == TOKEN_ILLEGAL:
                raise JSONPathSyntaxError(
                    f"unexpected token {match.group()!r}",
                    token=_token(
                        TOKEN_ILLEGAL,
                        value=match.group(),
                        index=match.start(),
                    ),
                )
            else:
                yield _token(
                    kind=kind,
                    value=match.group(),
                    index=match.start(),
                )
