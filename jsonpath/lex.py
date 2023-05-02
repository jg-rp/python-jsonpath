"""JSONPath tokenization."""
from __future__ import annotations

import re
from functools import partial
from typing import TYPE_CHECKING
from typing import Iterator
from typing import Pattern

from .exceptions import JSONPathSyntaxError
from .token import TOKEN_AND
from .token import TOKEN_BARE_PROPERTY
from .token import TOKEN_BRACKET_PROPERTY
from .token import TOKEN_COMMA
from .token import TOKEN_CONTAINS
from .token import TOKEN_DDOT
from .token import TOKEN_DOT_INDEX
from .token import TOKEN_DOT_PROPERTY
from .token import TOKEN_DOUBLE_QUOTE_STRING
from .token import TOKEN_EQ
from .token import TOKEN_FALSE
from .token import TOKEN_FILTER_CONTEXT
from .token import TOKEN_FILTER_END
from .token import TOKEN_FILTER_START
from .token import TOKEN_FLOAT
from .token import TOKEN_FUNCTION
from .token import TOKEN_GE
from .token import TOKEN_GT
from .token import TOKEN_ILLEGAL
from .token import TOKEN_IN
from .token import TOKEN_INDEX
from .token import TOKEN_INT
from .token import TOKEN_INTERSECTION
from .token import TOKEN_KEY
from .token import TOKEN_KEYS
from .token import TOKEN_LE
from .token import TOKEN_LG
from .token import TOKEN_LIST_SLICE
from .token import TOKEN_LIST_START
from .token import TOKEN_LPAREN
from .token import TOKEN_LT
from .token import TOKEN_MISSING
from .token import TOKEN_NE
from .token import TOKEN_NIL
from .token import TOKEN_NONE
from .token import TOKEN_NOT
from .token import TOKEN_NULL
from .token import TOKEN_OR
from .token import TOKEN_PROPERTY
from .token import TOKEN_RBRACKET
from .token import TOKEN_RE
from .token import TOKEN_RE_FLAGS
from .token import TOKEN_RE_PATTERN
from .token import TOKEN_ROOT
from .token import TOKEN_RPAREN
from .token import TOKEN_SELF
from .token import TOKEN_SINGLE_QUOTE_STRING
from .token import TOKEN_SKIP
from .token import TOKEN_SLICE
from .token import TOKEN_SLICE_START
from .token import TOKEN_SLICE_STEP
from .token import TOKEN_SLICE_STOP
from .token import TOKEN_STRING
from .token import TOKEN_TRUE
from .token import TOKEN_UNDEFINED
from .token import TOKEN_UNION
from .token import TOKEN_WILD
from .token import Token

if TYPE_CHECKING:
    from . import JSONPathEnvironment


class Lexer:
    """Tokenize a JSONPath string."""

    key_pattern = r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*"

    def __init__(self, *, env: JSONPathEnvironment) -> None:
        self.env = env

        self.double_quote_pattern = r'"(?P<G_DQUOTE>(?:(?!(?<!\\)").)*)"'
        self.single_quote_pattern = r"'(?P<G_SQUOTE>(?:(?!(?<!\\)').)*)'"

        # .thing
        self.dot_property_pattern = rf"\.(?P<G_PROP>{self.key_pattern})"

        # [thing]
        self.bracketed_property_pattern = rf"\[\s*(?P<G_BPROP>{self.key_pattern})\s*]"

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

        # func(
        self.function_pattern = r"(?P<G_FUNC>[a-z][a-z_0-9]+)\(\s*"

        self.rules = self.compile_rules()

    def compile_rules(self) -> Pattern[str]:
        """Prepare regular expression rules."""
        rules = [
            (TOKEN_DOUBLE_QUOTE_STRING, self.double_quote_pattern),
            (TOKEN_SINGLE_QUOTE_STRING, self.single_quote_pattern),
            (TOKEN_RE_PATTERN, self.re_pattern),
            (TOKEN_INDEX, self.index_pattern),
            (TOKEN_SLICE, self.slice_pattern),
            (TOKEN_WILD, self.wild_pattern),
            (TOKEN_LIST_SLICE, self.slice_list_pattern),
            (TOKEN_FILTER_START, r"\[\s*\?\s*\(?"),
            (TOKEN_FILTER_END, r"\)\s*]"),
            (TOKEN_FUNCTION, self.function_pattern),
            (TOKEN_BRACKET_PROPERTY, self.bracketed_property_pattern),
            (TOKEN_DOT_PROPERTY, self.dot_property_pattern),
            (TOKEN_FLOAT, r"-?\d+\.\d*(?:e[+-]?\d+)?"),
            (TOKEN_INT, r"-?\d+(?:e[+\-]?\d+)?\b"),
            (TOKEN_DDOT, r"\.\."),
            (TOKEN_AND, self.bool_and_pattern),
            (TOKEN_OR, self.bool_or_pattern),
            (TOKEN_ROOT, re.escape(self.env.root_token)),
            (TOKEN_SELF, re.escape(self.env.self_token)),
            (TOKEN_KEY, re.escape(self.env.key_token)),
            (TOKEN_UNION, re.escape(self.env.union_token)),
            (TOKEN_INTERSECTION, re.escape(self.env.intersection_token)),
            (TOKEN_FILTER_CONTEXT, re.escape(self.env.filter_context_token)),
            (TOKEN_KEYS, re.escape(self.env.keys_selector_token)),
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
            (TOKEN_RBRACKET, r"]"),
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
            elif kind == TOKEN_FUNCTION:
                yield _token(
                    kind=TOKEN_FUNCTION,
                    value=match.group("G_FUNC"),
                    index=match.start("G_FUNC"),
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
