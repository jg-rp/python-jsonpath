"""JSONPath tokens."""
import sys
from typing import Iterable
from typing import Iterator
from typing import Tuple

from .exceptions import JSONPathSyntaxError

# Utility tokens
TOKEN_EOF = sys.intern("EOF")
TOKEN_ILLEGAL = sys.intern("ILLEGAL")
TOKEN_SKIP = sys.intern("SKIP")

# JSONPath expression tokens
TOKEN_COLON = sys.intern("COLON")
TOKEN_COMMA = sys.intern("COMMA")
TOKEN_DDOT = sys.intern("DDOT")
TOKEN_DOT = sys.intern("DOT")
TOKEN_DOT_INDEX = sys.intern("DINDEX")
TOKEN_DOT_PROPERTY = sys.intern("DOT_PROPERTY")
TOKEN_FILTER = sys.intern("FILTER")
TOKEN_KEY = sys.intern("KEY")
TOKEN_KEYS = sys.intern("KEYS")
TOKEN_RBRACKET = sys.intern("RBRACKET")
TOKEN_BARE_PROPERTY = sys.intern("BARE_PROPERTY")
TOKEN_LIST_SLICE = sys.intern("LSLICE")
TOKEN_LIST_START = sys.intern("LBRACKET")
TOKEN_PROPERTY = sys.intern("PROP")
TOKEN_ROOT = sys.intern("ROOT")
TOKEN_SLICE_START = sys.intern("SLICE_START")
TOKEN_SLICE_STEP = sys.intern("SLICE_STEP")
TOKEN_SLICE_STOP = sys.intern("SLICE_STOP")
TOKEN_WILD = sys.intern("WILD")

# Filter expression tokens
TOKEN_AND = sys.intern("AND")
TOKEN_BLANK = sys.intern("BLANK")
TOKEN_CONTAINS = sys.intern("CONTAINS")
TOKEN_FILTER_CONTEXT = sys.intern("FILTER_CONTEXT")
TOKEN_FUNCTION = sys.intern("FUNCTION")
TOKEN_EMPTY = sys.intern("EMPTY")
TOKEN_EQ = sys.intern("EQ")
TOKEN_FALSE = sys.intern("FALSE")
TOKEN_FLOAT = sys.intern("FLOAT")
TOKEN_GE = sys.intern("GE")
TOKEN_GT = sys.intern("GT")
TOKEN_IN = sys.intern("IN")
TOKEN_INT = sys.intern("INT")
TOKEN_LE = sys.intern("LE")
TOKEN_LG = sys.intern("LG")
TOKEN_LPAREN = sys.intern("LPAREN")
TOKEN_LT = sys.intern("LT")
TOKEN_NE = sys.intern("NE")
TOKEN_NIL = sys.intern("NIL")
TOKEN_NONE = sys.intern("NONE")
TOKEN_NOT = sys.intern("NOT")
TOKEN_NULL = sys.intern("NULL")
TOKEN_OP = sys.intern("OP")
TOKEN_OR = sys.intern("OR")
TOKEN_RE = sys.intern("RE")
TOKEN_RE_FLAGS = sys.intern("RE_FLAGS")
TOKEN_RE_PATTERN = sys.intern("RE_PATTERN")
TOKEN_RPAREN = sys.intern("RPAREN")
TOKEN_SELF = sys.intern("SELF")
TOKEN_STRING = sys.intern("STRING")
TOKEN_DOUBLE_QUOTE_STRING = sys.intern("DOUBLE_QUOTE_STRING")
TOKEN_SINGLE_QUOTE_STRING = sys.intern("SINGLE_QUOTE_STRING")
TOKEN_TRUE = sys.intern("TRUE")
TOKEN_UNDEFINED = sys.intern("UNDEFINED")
TOKEN_MISSING = sys.intern("MISSING")

# Extension tokens
TOKEN_UNION = sys.intern("UNION")
TOKEN_INTERSECTION = sys.intern("INTERSECT")


class Token:
    """A token, as returned from `lex.Lexer.tokenize()`.

    Attributes:
        kind (str): The token's type. It is always one of the constants defined
            in _jsonpath.token.py_.
        value (str): The _path_ substring containing text for the token.
        index (str): The index at which _value_ starts in _path_.
        path (str): A reference to the complete JSONPath string from which this
            token derives.
    """

    __slots__ = ("kind", "value", "index", "path")

    def __init__(
        self,
        kind: str,
        value: str,
        index: int,
        path: str,
    ) -> None:
        self.kind = kind
        self.value = value
        self.index = index
        self.path = path

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Token(kind={self.kind!r}, value={self.value!r}, "
            f"index={self.index}, path={self.path!r})"
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Token)
            and self.kind == other.kind
            and self.value == other.value
            and self.index == other.index
            and self.path == other.path
        )

    def __hash__(self) -> int:
        return hash((self.kind, self.value, self.index, self.path))

    def position(self) -> Tuple[int, int]:
        """Return the line and column number for the start of this token."""
        line_number = self.value.count("\n", 0, self.index) + 1
        column_number = self.index - self.value.rfind("\n", 0, self.index)
        return (line_number, column_number - 1)


class TokenStream:
    """Step through a stream of tokens."""

    eof = Token(TOKEN_EOF, "", -1, "")

    __slots__ = ("tokens", "pos")

    def __init__(self, token_iter: Iterable[Token]):
        self.tokens = tuple(token_iter)
        self.pos = 0

    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    @property
    def current(self) -> Token:
        """The current token in the stream.

        Returns EOF if we're at the end of the stream.
        """
        try:
            return self.tokens[self.pos]
        except IndexError:
            return self.eof

    @property
    def peek(self) -> Token:
        """The next token in the stream.

        Returns EOF if we're at or one away from the end of the stream.
        """
        try:
            return self.tokens[self.pos + 1]
        except IndexError:
            return self.eof

    def __next__(self) -> Token:
        self.pos += 1
        return self.tokens[self.pos - 1]

    def next_token(self) -> Token:
        """Return the current token ans advance the stream."""
        return next(self)

    def backup(self) -> None:
        """Go back one token in the stream."""
        if self.pos > 0:
            self.pos -= 1

    def expect(self, *typ: str) -> None:
        """Raise an exception if the current token's type is not in _typ_."""
        if self.current.kind not in typ:
            if len(typ) == 1:
                _typ = repr(typ[0])
            else:
                _typ = f"one of {typ!r}"
            raise JSONPathSyntaxError(
                f"expected {_typ}, found {self.current.kind!r}",
                token=self.current,
            )

    def expect_peek(self, *typ: str) -> None:
        """Raise an exception if the next token's type is not in _typ_."""
        if self.peek.kind not in typ:
            if len(typ) == 1:
                _typ = repr(typ[0])
            else:
                _typ = f"one of {typ!r}"
            raise JSONPathSyntaxError(
                f"expected {_typ}, found {self.peek.kind!r}",
                token=self.peek,
            )
