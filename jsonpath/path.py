from __future__ import annotations

import itertools
import json

from typing import Any
from typing import AsyncIterable
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import TypeVar
from typing import TYPE_CHECKING
from typing import Union

from .match import JSONPathMatch
from .selectors import JSONPathSelector

if TYPE_CHECKING:
    from .env import JSONPathEnvironment


class JSONPath:
    """A compiled JSONPath ready to be applied to a JSON string or Python object."""

    __slots__ = ("env", "_selectors")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        selectors: Iterable[JSONPathSelector],
    ) -> None:
        self.env = env
        self._selectors = list(selectors)

    def __str__(self) -> str:
        return self.env.root_token + "".join(
            str(selector) for selector in self._selectors
        )

    def findall(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> List[object]:
        """Return a list of objects matching this path in the given data."""
        if isinstance(data, str):
            data = json.loads(data)
        # pylint bug?
        # pylint: disable=not-an-iterable
        return [match.obj for match in self.finditer(data)]

    def finditer(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> Iterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        if isinstance(data, str):
            data = json.loads(data)

        matches: Iterable[JSONPathMatch] = [
            JSONPathMatch(path=self.env.root_token, obj=data, root=data)
        ]

        for selector in self._selectors:
            matches = selector.resolve(matches)

        return matches

    async def findall_async(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> List[object]:
        """An async version of :meth:`findall`."""
        if isinstance(data, str):
            data = json.loads(data)
        # pylint: disable=not-an-iterable
        return [match.obj async for match in await self.finditer_async(data)]

    async def finditer_async(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> AsyncIterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        if isinstance(data, str):
            data = json.loads(data)

        async def root_iter() -> AsyncIterable[JSONPathMatch]:
            yield JSONPathMatch(path=self.env.root_token, obj=data, root=data)

        matches: AsyncIterable[JSONPathMatch] = root_iter()

        for selector in self._selectors:
            matches = selector.resolve_async(matches)

        return matches


class CompoundJSONPath:
    """Multiple :class:`JSONPath`s combined."""

    __slots__ = ("path", "paths")

    root_token = "$"
    union_token = "|"
    intersection_token = "&"

    def __init__(self, path: Union[JSONPath, CompoundJSONPath]) -> None:
        self.path = path
        self.paths: List[Tuple[(str, JSONPath)]] = []

    def __str__(self) -> str:
        buf: List[str] = [str(self.path)]
        for op, path in self.paths:
            buf.append(f" {op} ")
            buf.append(str(path))
        return "".join(buf)

    def findall(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> List[object]:
        """Return a list of objects matching this path in the given data."""
        objs = self.path.findall(data)

        for op, path in self.paths:
            _objs = path.findall(data)
            if op == self.union_token:
                objs.extend(_objs)
            elif op == self.intersection_token:
                objs = [obj for obj in objs if obj in _objs]

        return objs

    def finditer(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> Iterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        matches = self.path.finditer(data)

        for op, path in self.paths:
            _matches = path.finditer(data)
            if op == self.union_token:
                matches = itertools.chain(matches, _matches)
            elif op == self.intersection_token:
                _objs = [match.obj for match in _matches]
                _matches = (match for match in matches if match.obj in _objs)

        return matches

    async def findall_async(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> List[object]:
        """An async version of :meth:`findall`."""
        objs = await self.path.findall_async(data)

        for op, path in self.paths:
            _objs = await path.findall_async(data)
            if op == self.union_token:
                objs.extend(_objs)
            elif op == self.intersection_token:
                objs = [obj for obj in objs if obj in _objs]

        return objs

    async def finditer_async(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> AsyncIterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        matches = await self.path.finditer_async(data)

        for op, path in self.paths:
            _matches = await path.finditer_async(data)
            if op == self.union_token:
                matches = _achain(matches, _matches)
            elif op == self.intersection_token:
                _objs = [match.obj async for match in _matches]
                _matches = (match async for match in matches if match.obj in _objs)

        return matches

    def union(self, path: JSONPath) -> CompoundJSONPath:
        """In-place union of this path and another path."""
        self.paths.append((self.union_token, path))
        return self

    def intersection(self, path: JSONPath) -> CompoundJSONPath:
        """In-place intersection of this path and another path."""
        self.paths.append((self.intersection_token, path))
        return self


T = TypeVar("T")


async def _achain(*iterables: AsyncIterable[T]) -> AsyncIterable[T]:
    for it in iterables:
        async for element in it:
            yield element
