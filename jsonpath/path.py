# noqa: D100
from __future__ import annotations

import itertools
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

from jsonpath._data import load_data
from jsonpath.match import FilterContextVars
from jsonpath.match import JSONPathMatch
from jsonpath.selectors import IndexSelector
from jsonpath.selectors import ListSelector
from jsonpath.selectors import PropertySelector

if TYPE_CHECKING:
    from io import IOBase

    from .env import JSONPathEnvironment
    from .selectors import JSONPathSelector


class JSONPath:
    """A compiled JSONPath ready to be applied to a JSON string or Python object.

    Arguments:
        env: The `JSONPathEnvironment` this path is bound to.
        selectors: An iterable of `JSONPathSelector` objects, as generated by
            a `Parser`.

    Attributes:
        env: The `JSONPathEnvironment` this path is bound to.
        selectors: The `JSONPathSelector` instances that make up this path.
    """

    __slots__ = ("env", "selectors")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        selectors: Iterable[JSONPathSelector],
    ) -> None:
        self.env = env
        self.selectors = tuple(selectors)

    def __str__(self) -> str:
        return self.env.root_token + "".join(
            str(selector) for selector in self.selectors
        )

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, JSONPath) and self.selectors == __value.selectors

    def __hash__(self) -> int:
        return hash(self.selectors)

    def findall(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """Find all objects in `data` matching the given JSONPath `path`.

        If `data` is a string or a file-like objects, it will be loaded
        using `json.loads()` and the default `JSONDecoder`.

        Arguments:
            data: A JSON document or Python object implementing the `Sequence`
                or `Mapping` interfaces.
            filter_context: Arbitrary data made available to filters using
                the _filter context_ selector.

        Returns:
            A list of matched objects. If there are no matches, the list will
            be empty.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        return [
            match.obj for match in self.finditer(data, filter_context=filter_context)
        ]

    def finditer(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> Iterable[JSONPathMatch]:
        """Generate `JSONPathMatch` objects for each match.

        If `data` is a string or a file-like objects, it will be loaded
        using `json.loads()` and the default `JSONDecoder`.

        Arguments:
            data: A JSON document or Python object implementing the `Sequence`
                or `Mapping` interfaces.
            filter_context: Arbitrary data made available to filters using
                the _filter context_ selector.

        Returns:
            An iterator yielding `JSONPathMatch` objects for each match.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        _data = load_data(data)
        matches: Iterable[JSONPathMatch] = [
            JSONPathMatch(
                filter_context=filter_context or {},
                obj=_data,
                parent=None,
                parts=(),
                root=_data,
            )
        ]

        for selector in self.selectors:
            matches = selector.resolve(matches)

        return matches

    async def findall_async(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """An async version of `findall()`."""
        return [
            match.obj
            async for match in await self.finditer_async(
                data, filter_context=filter_context
            )
        ]

    async def finditer_async(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> AsyncIterable[JSONPathMatch]:
        """An async version of `finditer()`."""
        _data = load_data(data)

        async def root_iter() -> AsyncIterable[JSONPathMatch]:
            yield self.env.match_class(
                filter_context=filter_context or {},
                obj=_data,
                parent=None,
                parts=(),
                root=_data,
            )

        matches: AsyncIterable[JSONPathMatch] = root_iter()

        for selector in self.selectors:
            matches = selector.resolve_async(matches)

        return matches

    def match(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> Union[JSONPathMatch, None]:
        """Return a `JSONPathMatch` instance for the first object found in _data_.

        `None` is returned if there are no matches.

        Arguments:
            data: A JSON document or Python object implementing the `Sequence`
                or `Mapping` interfaces.
            filter_context: Arbitrary data made available to filters using
                the _filter context_ selector.

        Returns:
            A `JSONPathMatch` object for the first match, or `None` if there were
                no matches.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        try:
            return next(iter(self.finditer(data, filter_context=filter_context)))
        except StopIteration:
            return None

    def empty(self) -> bool:
        """Return `True` if this path has no selectors."""
        return not bool(self.selectors)

    def singular_query(self) -> bool:
        """Return `True` if this JSONPath query is a singular query."""
        for selector in self.selectors:
            if isinstance(selector, (PropertySelector, IndexSelector)):
                continue
            if (
                isinstance(selector, ListSelector)
                and len(selector.items) == 1
                and isinstance(selector.items[0], (PropertySelector, IndexSelector))
            ):
                continue
            return False
        return True


class CompoundJSONPath:
    """Multiple `JSONPath`s combined."""

    __slots__ = ("env", "path", "paths")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        path: Union[JSONPath, CompoundJSONPath],
        paths: Iterable[Tuple[str, JSONPath]] = (),
    ) -> None:
        self.env = env
        self.path = path
        self.paths = tuple(paths)

    def __str__(self) -> str:
        buf: List[str] = [str(self.path)]
        for op, path in self.paths:
            buf.append(f" {op} ")
            buf.append(str(path))
        return "".join(buf)

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, CompoundJSONPath)
            and self.path == __value.path
            and self.paths == __value.paths
        )

    def __hash__(self) -> int:
        return hash((self.path, self.paths))

    def findall(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """Find all objects in `data` matching the given JSONPath `path`.

        If `data` is a string or a file-like objects, it will be loaded
        using `json.loads()` and the default `JSONDecoder`.

        Arguments:
            data: A JSON document or Python object implementing the `Sequence`
                or `Mapping` interfaces.
            filter_context: Arbitrary data made available to filters using
                the _filter context_ selector.

        Returns:
            A list of matched objects. If there are no matches, the list will
                be empty.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        objs = self.path.findall(data, filter_context=filter_context)

        for op, path in self.paths:
            _objs = path.findall(data, filter_context=filter_context)
            if op == self.env.union_token:
                objs.extend(_objs)
            else:
                assert op == self.env.intersection_token, op
                objs = [obj for obj in objs if obj in _objs]

        return objs

    def finditer(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> Iterable[JSONPathMatch]:
        """Generate `JSONPathMatch` objects for each match.

        If `data` is a string or a file-like objects, it will be loaded
        using `json.loads()` and the default `JSONDecoder`.

        Arguments:
            data: A JSON document or Python object implementing the `Sequence`
                or `Mapping` interfaces.
            filter_context: Arbitrary data made available to filters using
                the _filter context_ selector.

        Returns:
            An iterator yielding `JSONPathMatch` objects for each match.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        matches = self.path.finditer(data, filter_context=filter_context)

        for op, path in self.paths:
            _matches = path.finditer(data, filter_context=filter_context)
            if op == self.env.union_token:
                matches = itertools.chain(matches, _matches)
            else:
                assert op == self.env.intersection_token
                _objs = [match.obj for match in _matches]
                matches = (match for match in matches if match.obj in _objs)

        return matches

    def match(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> Union[JSONPathMatch, None]:
        """Return a `JSONPathMatch` instance for the first object found in _data_.

        `None` is returned if there are no matches.

        Arguments:
            data: A JSON document or Python object implementing the `Sequence`
                or `Mapping` interfaces.
            filter_context: Arbitrary data made available to filters using
                the _filter context_ selector.

        Returns:
            A `JSONPathMatch` object for the first match, or `None` if there were
                no matches.

        Raises:
            JSONPathSyntaxError: If the path is invalid.
            JSONPathTypeError: If a filter expression attempts to use types in
                an incompatible way.
        """
        try:
            return next(iter(self.finditer(data, filter_context=filter_context)))
        except StopIteration:
            return None

    async def findall_async(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> List[object]:
        """An async version of `findall()`."""
        objs = await self.path.findall_async(data, filter_context=filter_context)

        for op, path in self.paths:
            _objs = await path.findall_async(data, filter_context=filter_context)
            if op == self.env.union_token:
                objs.extend(_objs)
            else:
                assert op == self.env.intersection_token
                objs = [obj for obj in objs if obj in _objs]

        return objs

    async def finditer_async(
        self,
        data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
        *,
        filter_context: Optional[FilterContextVars] = None,
    ) -> AsyncIterable[JSONPathMatch]:
        """An async version of `finditer()`."""
        matches = await self.path.finditer_async(data, filter_context=filter_context)

        for op, path in self.paths:
            _matches = await path.finditer_async(data, filter_context=filter_context)
            if op == self.env.union_token:
                matches = _achain(matches, _matches)
            else:
                assert op == self.env.intersection_token
                _objs = [match.obj async for match in _matches]
                matches = (match async for match in matches if match.obj in _objs)

        return matches

    def union(self, path: JSONPath) -> CompoundJSONPath:
        """Union of this path and another path."""
        return self.__class__(
            env=self.env,
            path=self.path,
            paths=self.paths + ((self.env.union_token, path),),
        )

    def intersection(self, path: JSONPath) -> CompoundJSONPath:
        """Intersection of this path and another path."""
        return self.__class__(
            env=self.env,
            path=self.path,
            paths=self.paths + ((self.env.intersection_token, path),),
        )


T = TypeVar("T")


async def _achain(*iterables: AsyncIterable[T]) -> AsyncIterable[T]:
    for it in iterables:
        async for element in it:
            yield element
