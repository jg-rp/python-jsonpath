from __future__ import annotations

import itertools
import json
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncIterable
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar
from typing import Union

from .match import FilterContextVars
from .match import JSONPathMatch

if TYPE_CHECKING:
    from .env import JSONPathEnvironment
    from .selectors import JSONPathSelector


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
        self._selectors = tuple(selectors)

    def __str__(self) -> str:
        return self.env.root_token + "".join(
            str(selector) for selector in self._selectors
        )

    def findall(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """Return a list of objects matching this path in the given data."""
        if isinstance(data, str):
            data = json.loads(data)
        return [
            match.obj for match in self.finditer(data, filter_context=filter_context)
        ]

    def finditer(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> Iterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        if isinstance(data, str):
            data = json.loads(data)

        matches: Iterable[JSONPathMatch] = [
            JSONPathMatch(
                path=self.env.root_token,
                obj=data,
                root=data,
                filter_context=filter_context or {},
            )
        ]

        for selector in self._selectors:
            matches = selector.resolve(matches)

        return matches

    async def findall_async(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """An async version of :meth:`findall`."""
        if isinstance(data, str):
            data = json.loads(data)
        return [
            match.obj
            async for match in await self.finditer_async(
                data, filter_context=filter_context
            )
        ]

    async def finditer_async(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> AsyncIterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        if isinstance(data, str):
            data = json.loads(data)

        async def root_iter() -> AsyncIterable[JSONPathMatch]:
            yield JSONPathMatch(
                path=self.env.root_token,
                obj=data,
                root=data,
                filter_context=filter_context or {},
            )

        matches: AsyncIterable[JSONPathMatch] = root_iter()

        for selector in self._selectors:
            matches = selector.resolve_async(matches)

        return matches

    def empty(self) -> bool:
        """Return `True` if this path has no selectors."""
        return bool(self._selectors)


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
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """Return a list of objects matching this path in the given data."""
        objs = self.path.findall(data, filter_context=filter_context)

        for op, path in self.paths:
            _objs = path.findall(data, filter_context=filter_context)
            if op == self.union_token:
                objs.extend(_objs)
            else:
                assert op == self.intersection_token, op
                objs = [obj for obj in objs if obj in _objs]

        return objs

    def finditer(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        filter_context: Optional[FilterContextVars] = None,
    ) -> Iterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        matches = self.path.finditer(data, filter_context=filter_context)

        for op, path in self.paths:
            _matches = path.finditer(data, filter_context=filter_context)
            if op == self.union_token:
                matches = itertools.chain(matches, _matches)
            else:
                assert op == self.intersection_token
                _objs = [match.obj for match in _matches]
                matches = (match for match in matches if match.obj in _objs)

        return matches

    async def findall_async(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """An async version of :meth:`findall`."""
        objs = await self.path.findall_async(data, filter_context=filter_context)

        for op, path in self.paths:
            _objs = await path.findall_async(data, filter_context=filter_context)
            if op == self.union_token:
                objs.extend(_objs)
            else:
                assert op == self.intersection_token
                objs = [obj for obj in objs if obj in _objs]

        return objs

    async def finditer_async(
        self,
        data: Union[str, Sequence[Any], Mapping[str, Any]],
        filter_context: Optional[FilterContextVars] = None,
    ) -> AsyncIterable[JSONPathMatch]:
        """Generate :class:`JSONPathMatch` objects for each match of
        this path in the given data."""
        matches = await self.path.finditer_async(data, filter_context=filter_context)

        for op, path in self.paths:
            _matches = await path.finditer_async(data, filter_context=filter_context)
            if op == self.union_token:
                matches = _achain(matches, _matches)
            else:
                assert op == self.intersection_token
                _objs = [match.obj async for match in _matches]
                matches = (match async for match in matches if match.obj in _objs)

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
