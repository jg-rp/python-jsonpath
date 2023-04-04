# noqa: D100
from __future__ import annotations

from collections import deque
from typing import Deque
from typing import Iterator

from .exceptions import JSONPathSyntaxError
from .token import TOKEN_EOF
from .token import Token

# ruff: noqa: D102


class TokenStream:
    """Step through or iterate a stream of tokens."""

    def __init__(self, token_iter: Iterator[Token]):
        self.iter = token_iter
        self._pushed: Deque[Token] = deque()
        self.current = Token("", "", -1, "")
        next(self)

    class TokenStreamIterator:
        """An iterable token stream."""

        def __init__(self, stream: TokenStream):
            self.stream = stream

        def __iter__(self) -> Iterator[Token]:
            return self

        def __next__(self) -> Token:
            tok = self.stream.current
            if tok.kind is TOKEN_EOF:
                self.stream.close()
                raise StopIteration
            next(self.stream)
            return tok

    def __iter__(self) -> Iterator[Token]:
        return self.TokenStreamIterator(self)

    def __next__(self) -> Token:
        tok = self.current
        if self._pushed:
            self.current = self._pushed.popleft()
        elif self.current.kind is not TOKEN_EOF:
            try:
                self.current = next(self.iter)
            except StopIteration:
                self.close()
        return tok

    def __str__(self) -> str:  # pragma: no cover
        return f"current: {self.current}\nnext: {self.peek}"

    def next_token(self) -> Token:
        """Return the next token from the stream."""
        return next(self)

    @property
    def peek(self) -> Token:
        """Look at the next token."""
        current = next(self)
        result = self.current
        self.push(current)
        return result

    def push(self, tok: Token) -> None:
        """Push a token back to the stream."""
        self._pushed.append(self.current)
        self.current = tok

    def close(self) -> None:
        """Close the stream."""
        self.current = Token(TOKEN_EOF, "", -1, "")

    def expect(self, *typ: str) -> None:
        if self.current.kind not in typ:
            raise JSONPathSyntaxError(
                f"expected {typ!r}, found {self.current.kind!r}",
                token=self.current,
            )

    def expect_peek(self, *typ: str) -> None:
        if self.peek.kind not in typ:
            raise JSONPathSyntaxError(
                f"expected {typ!r}, found {self.peek.kind!r}",
                token=self.peek,
            )
