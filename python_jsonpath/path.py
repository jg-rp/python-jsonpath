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
from typing import Union
from typing import TYPE_CHECKING

from .match import JSONPathMatch

if TYPE_CHECKING:
    from .selectors import JSONPathSelector


class JSONPath:
    """A compiled JSONPath ready to be applied to a JSON string or Python object."""

    __slots__ = ("_selectors",)

    def __init__(self, *, selectors: Iterable[JSONPathSelector]) -> None:
        self._selectors = list(selectors)

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
            JSONPathMatch(path="$", obj=data, root=data)
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
            yield JSONPathMatch(path="$", obj=data, root=data)

        matches: AsyncIterable[JSONPathMatch] = root_iter()

        for selector in self._selectors:
            matches = selector.resolve_async(matches)

        return matches


class CompoundJSONPath:
    """Multiple :class:`JSONPath`s combined."""

    __slots__ = ("path", "paths")

    def __init__(self, path: Union[JSONPath, CompoundJSONPath]) -> None:
        self.path = path
        self.paths: List[Tuple[(str, JSONPath)]] = []

    def findall(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> List[object]:
        """Return a list of objects matching this path in the given data."""
        objs = self.path.findall(data)

        for op, path in self.paths:
            assert op in ("|", "&")
            _objs = path.findall(data)
            if op == "|":
                objs.extend(_objs)
            elif op == "&":
                objs = [obj for obj in objs if obj in _objs]

        return objs

    def finditer(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> Iterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        matches = self.path.finditer(data)

        for op, path in self.paths:
            assert op in ("|", "&")
            _matches = path.finditer(data)
            if op == "|":
                matches = itertools.chain(matches, _matches)
            elif op == "&":
                _objs = [match.obj for match in _matches]
                _matches = (match for match in matches if match.obj in _objs)

        return matches

    async def findall_async(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> List[object]:
        """An async version of :meth:`findall`."""
        objs = await self.path.findall_async(data)

        for op, path in self.paths:
            assert op in ("|", "&")
            _objs = await path.findall_async(data)
            if op == "|":
                objs.extend(_objs)
            elif op == "&":
                objs = [obj for obj in objs if obj in _objs]

        return objs

    async def finditer_async(
        self, data: Union[str, Sequence[Any], Mapping[str, Any]]
    ) -> AsyncIterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        matches = await self.path.finditer_async(data)

        for op, path in self.paths:
            assert op in ("|", "&")
            _matches = await path.finditer_async(data)
            if op == "|":
                matches = _achain(matches, _matches)
            elif op == "&":
                _objs = [match.obj async for match in _matches]
                _matches = (match async for match in matches if match.obj in _objs)

        return matches

    def union(self, path: JSONPath) -> CompoundJSONPath:
        """In-place union of this path and another path."""
        self.paths.append(("|", path))
        return self

    def intersection(self, path: JSONPath) -> CompoundJSONPath:
        """In-place intersection of this path and another path."""
        self.paths.append(("&", path))
        return self


T = TypeVar("T")


async def _achain(*iterables: AsyncIterable[T]) -> AsyncIterable[T]:
    for it in iterables:
        async for element in it:
            yield element
