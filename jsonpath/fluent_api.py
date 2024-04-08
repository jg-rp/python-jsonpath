"""A fluent API for managing JSONPathMatch iterators."""

from __future__ import annotations

import collections
import itertools
from typing import TYPE_CHECKING
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Tuple

if TYPE_CHECKING:
    from jsonpath import JSONPathMatch
    from jsonpath import JSONPointer


class Query:
    """A fluent API for managing `JSONPathMatch` iterators.

    Usually you'll want to use `jsonpath.query()` or `JSONPathEnvironment.query()`
    to create instances of `Query` rather than instantiating `Query` directly.

    Arguments:
        it: A `JSONPathMatch` iterable, as you'd get from `jsonpath.finditer()` or
            `JSONPathEnvironment.finditer()`.

    **New in version 1.1.0**
    """

    def __init__(self, it: Iterable[JSONPathMatch]) -> None:
        self._it = iter(it)

    def __iter__(self) -> Iterator[JSONPathMatch]:
        return self._it

    def limit(self, n: int) -> Query:
        """Limit the query iterator to at most _n_ matches.

        Raises:
            ValueError: If _n_ < 0.
        """
        if n < 0:
            raise ValueError("can't limit by a negative number of matches")

        self._it = itertools.islice(self._it, n)
        return self

    def head(self, n: int) -> Query:
        """Limit the query iterator to at most the first _n_ matches.

        `head()` is an alias for `limit()`.

        Raises:
            ValueError: If _n_ < 0.
        """
        return self.limit(n)

    def first(self, n: int) -> Query:
        """Limit the query iterator to at most the first _n_ matches.

        `first()` is an alias for `limit()`.

        Raises:
            ValueError: If _n_ < 0.
        """
        return self.limit(n)

    def drop(self, n: int) -> Query:
        """Skip up to _n_ matches from the query iterator.

        Raises:
            ValueError: If _n_ < 0.
        """
        if n < 0:
            raise ValueError("can't drop a negative number of matches")

        if n > 0:
            next(itertools.islice(self._it, n, n), None)

        return self

    def skip(self, n: int) -> Query:
        """Skip up to _n_ matches from the query iterator.

        Raises:
            ValueError: If _n_ < 0.
        """
        return self.drop(n)

    def tail(self, n: int) -> Query:
        """Drop matches up to the last _n_ matches from the iterator.

        Raises:
            ValueError: If _n_ < 0.
        """
        if n < 0:
            raise ValueError("can't select a negative number of matches")

        self._it = iter(collections.deque(self._it, maxlen=n))
        return self

    def last(self, n: int) -> Query:
        """Drop up to the last _n_ matches from the iterator.

        `last()` is an alias for `tail()`.

        Raises:
            ValueError: If _n_ < 0.
        """
        return self.tail(n)

    def values(self) -> Iterable[object]:
        """Return an iterable of objects associated with each match."""
        return (m.obj for m in self._it)

    def locations(self) -> Iterable[str]:
        """Return an iterable of normalized paths, one for each match."""
        return (m.path for m in self._it)

    def items(self) -> Iterable[Tuple[str, object]]:
        """Return an iterable of (path, object) tuples, one for each match."""
        return ((m.path, m.obj) for m in self._it)

    def pointers(self) -> Iterable[JSONPointer]:
        """Return an iterable of JSONPointers, one for each match."""
        return (m.pointer() for m in self._it)

    def first_one(self) -> Optional[JSONPathMatch]:
        """Return the first `JSONPathMatch` or `None` if there were no matches."""
        try:
            return next(self._it)
        except StopIteration:
            return None

    def one(self) -> Optional[JSONPathMatch]:
        """Return the first `JSONPathMatch` or `None` if there were no matches.

        `one()` is an alias for `first_one()`.
        """
        return self.first_one()

    def last_one(self) -> Optional[JSONPathMatch]:
        """Return the last `JSONPathMatch` or `None` if there were no matches."""
        try:
            return next(iter(self.tail(1)))
        except StopIteration:
            return None

    def tee(self, n: int = 2) -> Tuple[Query, ...]:
        """Return _n_ independent queries by teeing this query's iterator.

        It is not safe to use a `Query` instance after calling `tee()`.
        """
        return tuple(Query(it) for it in itertools.tee(self._it, n))

    def take(self, n: int) -> Query:
        """Return a new query iterating over the next _n_ matches.

        It is safe to continue using this query after calling take.
        """
        return Query(list(itertools.islice(self._it, n)))
