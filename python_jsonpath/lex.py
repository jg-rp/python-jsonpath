"""JSONPath tokenization."""
from __future__ import annotations
import re

from functools import partial

from typing import Iterator
from typing import Pattern
from typing import TYPE_CHECKING

from .exceptions import JSONPathSyntaxError

from .token import Token
from .token import TOKEN_AND
from .token import TOKEN_BRACKET_PROPERTY
from .token import TOKEN_COMMA
from .token import TOKEN_DDOT
from .token import TOKEN_DOT_INDEX
from .token import TOKEN_DOT_PROPERTY
from .token import TOKEN_EQ
from .token import TOKEN_FALSE
from .token import TOKEN_FILTER_END
from .token import TOKEN_FILTER_START
from .token import TOKEN_FLOAT
from .token import TOKEN_GE
from .token import TOKEN_GT
from .token import TOKEN_ILLEGAL
from .token import TOKEN_IN
from .token import TOKEN_INDEX
from .token import TOKEN_INT
from .token import TOKEN_INTERSECTION
from .token import TOKEN_LE
from .token import TOKEN_LG
from .token import TOKEN_LIST_END
from .token import TOKEN_LIST_PROPERTY
from .token import TOKEN_LIST_SLICE
from .token import TOKEN_LIST_START
from .token import TOKEN_LPAREN
from .token import TOKEN_LT
from .token import TOKEN_NE
from .token import TOKEN_NIL
from .token import TOKEN_NONE
from .token import TOKEN_NOT
from .token import TOKEN_NULL
from .token import TOKEN_OR
from .token import TOKEN_PROPERTY
from .token import TOKEN_QUOTE_PROPERTY
from .token import TOKEN_RE
from .token import TOKEN_RE_FLAGS
from .token import TOKEN_RE_PATTERN
from .token import TOKEN_ROOT
from .token import TOKEN_RPAREN
from .token import TOKEN_SELF
from .token import TOKEN_SKIP
from .token import TOKEN_SLICE
from .token import TOKEN_SLICE_START
from .token import TOKEN_SLICE_STEP
from .token import TOKEN_SLICE_STOP
from .token import TOKEN_STRING
from .token import TOKEN_TRUE
from .token import TOKEN_UNION
from .token import TOKEN_WILD

if TYPE_CHECKING:
    from . import JSONPathEnvironment

# TODO: A "scope" operator (like `$` and `@`, but for arbitrary scope lookup)


class Lexer:
    """Tokenize a JSONPath string."""

    key_pattern = r"[a-zA-Z_][a-zA-Z0-9_-]*"

    # 'thing' or "thing" in the right hand side of a filter expression or in a list
    string_pattern = r"(?P<G_QUOTE>[\"'])(?P<G_QUOTED>.*?)(?P=G_QUOTE)"

    # .thing
    dot_property_pattern = rf"\.(?P<G_PROP>{key_pattern})"

    # [thing]
    bracketed_property_pattern = rf"\[\s*(?P<G_BPROP>{key_pattern})\s*]"

    # ["thing"] or ['thing']
    quoted_property_pattern = (
        r"\[\s*(?P<G_PQUOTE>[\"'])(?P<G_PQUOTED>.*?)(?P=G_PQUOTE)\s*]"
    )

    # .1
    # NOTE: `.1` can be a dot property where the key is "1".
    dot_index_pattern = r"\.\s*(?P<G_DINDEX>\d+)\b"

    # [1] or [-1]
    index_pattern = r"\[\s*(?P<G_INDEX>\-?\s*\d+)\s*]"

    # [:] or [1:-1] or [1:] or [:1] or [-1:] or [:-1] or [::] or [-1:0:-1]
    slice_pattern = (
        r"\[\s*(?P<G_SLICE_START>\-?\d*)\s*"
        r":\s*(?P<G_SLICE_STOP>\-?\d*)\s*"
        r"(?::\s*(?P<G_SLICE_STEP>\-?\d*))?\s*]"
    )

    slice_list_pattern = (
        r"(?P<G_LSLICE_START>\-?\d*)\s*"
        r":\s*(?P<G_LSLICE_STOP>\-?\d*)\s*"
        r"(?::\s*(?P<G_LSLICE_STEP>\-?\d*))?"
    )

    # .* or [*] or .[*]
    wild_pattern = r"\.?(?:\[\s*\*\s*]|\*)"

    # && or and
    bool_and_pattern = r"(?:&&|and)"

    # || or `or`
    bool_or_pattern = r"(?:\|\||or)"

    # /pattern/ or /pattern/flags
    re_pattern = r"/(?P<G_RE>.+?)/(?P<G_RE_FLAGS>[aims]*)"

    def __init__(self, *, env: JSONPathEnvironment) -> None:
        self.env = env
        self.rules = self.compile_rules()

    def compile_rules(self) -> Pattern[str]:
        """Prepare regular expression rules."""
        rules = [
            (TOKEN_QUOTE_PROPERTY, self.quoted_property_pattern),
            (TOKEN_STRING, self.string_pattern),
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
            (TOKEN_FLOAT, r"-?\d+\.\d*"),
            (TOKEN_INT, r"-?\d+\b"),
            (TOKEN_DDOT, r"\.\."),
            # (TOKEN_DOT, r"\."),
            (TOKEN_ROOT, self.env.root_pattern),
            (TOKEN_SELF, self.env.self_pattern),
            (TOKEN_UNION, self.env.union_pattern),
            (TOKEN_INTERSECTION, self.env.intersection_pattern),
            (TOKEN_AND, self.bool_and_pattern),
            (TOKEN_OR, self.bool_or_pattern),
            (TOKEN_IN, r"in"),
            (TOKEN_NOT, r"not"),
            (TOKEN_TRUE, r"[Tt]rue"),
            (TOKEN_FALSE, r"[Ff]alse"),
            (TOKEN_NIL, r"[Nn]il"),
            (TOKEN_NULL, r"[Nn]ull"),
            (TOKEN_NONE, r"[Nn]one"),
            (TOKEN_LIST_PROPERTY, self.key_pattern),
            (TOKEN_LIST_START, r"\["),
            (TOKEN_LIST_END, r"]"),
            (TOKEN_COMMA, r","),
            (TOKEN_EQ, r"=="),
            (TOKEN_NE, r"!="),
            (TOKEN_LG, r"<>"),
            (TOKEN_LT, r"<"),
            (TOKEN_GT, r">"),
            (TOKEN_LE, r"<="),
            (TOKEN_GE, r">="),
            (TOKEN_RE, r"=~"),
            (TOKEN_LPAREN, r"\("),
            (TOKEN_RPAREN, r"\)"),
            (TOKEN_SKIP, r"[ \n\t\r\.]+"),
            (TOKEN_ILLEGAL, r"."),
        ]

        return re.compile(
            "|".join(f"(?P<{token}>{pattern})" for token, pattern in rules),
            re.DOTALL,
        )

    def tokenize(self, path: str) -> Iterator[Token]:
        """Generate a sequence of tokens from a JSONPath string."""
        _token = partial(Token, path=path)

        for match in self.rules.finditer(path):
            kind = match.lastgroup
            assert kind is not None

            if kind == TOKEN_QUOTE_PROPERTY:
                yield _token(
                    kind=TOKEN_PROPERTY,
                    value=match.group("G_PQUOTED"),
                    index=match.start("G_PQUOTED"),
                )
            elif kind == TOKEN_DOT_PROPERTY:
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
            elif kind == TOKEN_LIST_PROPERTY:
                yield _token(
                    kind=TOKEN_LIST_PROPERTY,
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
            elif kind == TOKEN_STRING:
                yield _token(
                    kind=TOKEN_STRING,
                    value=match.group("G_QUOTED"),
                    index=match.start("G_QUOTED"),
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
            elif kind == TOKEN_SKIP:
                continue
            elif kind == TOKEN_ILLEGAL:
                # TODO: line and column number
                raise JSONPathSyntaxError(
                    f"unexpected token {kind!r}: {match.group()!r}"
                )
            else:
                yield _token(
                    kind=kind,
                    value=match.group(),
                    index=match.start(),
                )
