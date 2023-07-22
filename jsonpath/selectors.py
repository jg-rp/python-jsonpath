"""JSONPath selector objects, as returned from `Parser.parse`."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Mapping
from collections.abc import Sequence
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncIterable
from typing import Iterable
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

from .exceptions import JSONPathIndexError
from .exceptions import JSONPathTypeError

if TYPE_CHECKING:
    from .env import JSONPathEnvironment
    from .filter import BooleanExpression
    from .match import JSONPathMatch
    from .token import Token

# ruff: noqa: D102


class JSONPathSelector(ABC):
    """Base class for all JSONPath selectors."""

    __slots__ = ("env", "token")

    def __init__(self, *, env: JSONPathEnvironment, token: Token) -> None:
        self.env = env
        self.token = token

    @abstractmethod
    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        """Expand matches from previous JSONPath selectors in to new matches."""

    @abstractmethod
    def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        """An async version of `resolve`."""


class PropertySelector(JSONPathSelector):
    """A JSONPath property."""

    __slots__ = ("name",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        name: str,
    ) -> None:
        super().__init__(env=env, token=token)
        self.name = name

    def __str__(self) -> str:
        return f"['{self.name}']"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, PropertySelector)
            and self.name == __value.name
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.name, self.token))

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if not isinstance(match.obj, Mapping):
                continue

            with suppress(KeyError):
                _match = self.env.match_class(
                    filter_context=match.filter_context(),
                    obj=self.env.getitem(match.obj, self.name),
                    parent=match,
                    parts=match.parts + (self.name,),
                    path=match.path + f"['{self.name}']",
                    root=match.root,
                )
                match.add_child(_match)
                yield _match

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if not isinstance(match.obj, Mapping):
                continue

            with suppress(KeyError):
                _match = self.env.match_class(
                    filter_context=match.filter_context(),
                    obj=await self.env.getitem_async(match.obj, self.name),
                    parent=match,
                    parts=match.parts + (self.name,),
                    path=match.path + f"['{self.name}']",
                    root=match.root,
                )
                match.add_child(_match)
                yield _match


class IndexSelector(JSONPathSelector):
    """Dotted and bracketed sequence access by index."""

    __slots__ = ("index", "_as_key")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        index: int,
    ) -> None:
        if index < env.min_int_index or index > env.max_int_index:
            raise JSONPathIndexError("index out of range", token=token)

        super().__init__(env=env, token=token)
        self.index = index
        self._as_key = str(self.index)

    def __str__(self) -> str:
        return f"[{self.index}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, IndexSelector)
            and self.index == __value.index
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.index, self.token))

    def _normalized_index(self, obj: Sequence[object]) -> int:
        if self.index < 0 and len(obj) >= abs(self.index):
            return len(obj) + self.index
        return self.index

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if isinstance(match.obj, Mapping):
                # Try the string representation of the index as a key.
                with suppress(KeyError):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=self.env.getitem(match.obj, self._as_key),
                        parent=match,
                        parts=match.parts + (self._as_key,),
                        path=f"{match.path}['{self.index}']",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match
            elif isinstance(match.obj, Sequence) and not isinstance(match.obj, str):
                norm_index = self._normalized_index(match.obj)
                with suppress(IndexError):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=self.env.getitem(match.obj, self.index),
                        parent=match,
                        parts=match.parts + (norm_index,),
                        path=match.path + f"[{norm_index}]",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if isinstance(match.obj, Mapping):
                # Try the string representation of the index as a key.
                with suppress(KeyError):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=await self.env.getitem_async(match.obj, self._as_key),
                        parent=match,
                        parts=match.parts + (self._as_key,),
                        path=f"{match.path}['{self.index}']",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match
            elif isinstance(match.obj, Sequence) and not isinstance(match.obj, str):
                norm_index = self._normalized_index(match.obj)
                with suppress(IndexError):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=await self.env.getitem_async(match.obj, self.index),
                        parent=match,
                        parts=match.parts + (norm_index,),
                        path=match.path + f"[{norm_index}]",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match


class KeysSelector(JSONPathSelector):
    """Select an mapping's keys/properties."""

    __slots__ = ()

    def __str__(self) -> str:
        return f"[{self.env.keys_selector_token}]"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, KeysSelector) and self.token == __value.token

    def __hash__(self) -> int:
        return hash(self.token)

    def _keys(self, match: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(match.obj, Mapping):
            for i, key in enumerate(match.obj.keys()):
                _match = self.env.match_class(
                    filter_context=match.filter_context(),
                    obj=key,
                    parent=match,
                    parts=match.parts + (f"{self.env.keys_selector_token}{key}",),
                    path=f"{match.path}[{self.env.keys_selector_token}][{i}]",
                    root=match.root,
                )
                match.add_child(_match)
                yield _match

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            yield from self._keys(match)

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            for _match in self._keys(match):
                yield _match


class SliceSelector(JSONPathSelector):
    """Sequence slicing selector."""

    __slots__ = ("slice",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        step: Optional[int] = None,
    ) -> None:
        super().__init__(env=env, token=token)
        self._check_range(start, stop, step)
        self.slice = slice(start, stop, step)

    def __str__(self) -> str:
        stop = self.slice.stop if self.slice.stop is not None else ""
        start = self.slice.start if self.slice.start is not None else ""
        step = self.slice.step if self.slice.step is not None else "1"
        return f"[{start}:{stop}:{step}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, SliceSelector)
            and self.slice == __value.slice
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((str(self), self.token))

    def _check_range(self, *indices: Optional[int]) -> None:
        for i in indices:
            if i is not None and (
                i < self.env.min_int_index or i > self.env.max_int_index
            ):
                raise JSONPathIndexError("index out of range", token=self.token)

    def _normalized_index(self, obj: Sequence[object], index: int) -> int:
        if index < 0 and len(obj) >= abs(index):
            return len(obj) + index
        return index

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if not isinstance(match.obj, Sequence) or self.slice.step == 0:
                continue

            idx = self.slice.start or 0
            step = self.slice.step or 1
            for obj in self.env.getitem(match.obj, self.slice):
                norm_index = self._normalized_index(match.obj, idx)
                _match = self.env.match_class(
                    filter_context=match.filter_context(),
                    obj=obj,
                    parent=match,
                    parts=match.parts + (norm_index,),
                    path=f"{match.path}[{norm_index}]",
                    root=match.root,
                )
                match.add_child(_match)
                yield _match
                idx += step

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if not isinstance(match.obj, Sequence) or self.slice.step == 0:
                continue

            idx = self.slice.start or 0
            step = self.slice.step or 1
            for obj in await self.env.getitem_async(match.obj, self.slice):
                norm_index = self._normalized_index(match.obj, idx)
                _match = self.env.match_class(
                    filter_context=match.filter_context(),
                    obj=obj,
                    parent=match,
                    parts=match.parts + (norm_index,),
                    path=f"{match.path}[{norm_index}]",
                    root=match.root,
                )
                match.add_child(_match)
                yield _match
                idx += step


class WildSelector(JSONPathSelector):
    """Wildcard expansion selector."""

    def __str__(self) -> str:
        return "[*]"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, WildSelector) and self.token == __value.token

    def __hash__(self) -> int:
        return hash(self.token)

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if isinstance(match.obj, str):
                continue
            if isinstance(match.obj, Mapping):
                for key, val in match.obj.items():
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=val,
                        parent=match,
                        parts=match.parts + (key,),
                        path=match.path + f"['{key}']",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match
            elif isinstance(match.obj, Sequence):
                for i, val in enumerate(match.obj):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=val,
                        parent=match,
                        parts=match.parts + (i,),
                        path=f"{match.path}[{i}]",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if isinstance(match.obj, Mapping):
                for key, val in match.obj.items():
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=val,
                        parent=match,
                        parts=match.parts + (key,),
                        path=match.path + f"['{key}']",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match
            elif isinstance(match.obj, Sequence):
                for i, val in enumerate(match.obj):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=val,
                        parent=match,
                        parts=match.parts + (i,),
                        path=f"{match.path}[{i}]",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match


class RecursiveDescentSelector(JSONPathSelector):
    """A JSONPath selector that visits all objects recursively."""

    def __str__(self) -> str:
        return ".."

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, RecursiveDescentSelector)
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash(self.token)

    def _expand(self, match: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(match.obj, Mapping):
            for key, val in match.obj.items():
                if isinstance(val, str):
                    pass
                elif isinstance(val, (Mapping, Sequence)):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=val,
                        parent=match,
                        parts=match.parts + (key,),
                        path=match.path + f"['{key}']",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match
                    yield from self._expand(_match)
        elif isinstance(match.obj, Sequence) and not isinstance(match.obj, str):
            for i, val in enumerate(match.obj):
                if isinstance(val, str):
                    pass
                elif isinstance(val, (Mapping, Sequence)):
                    _match = self.env.match_class(
                        filter_context=match.filter_context(),
                        obj=val,
                        parent=match,
                        parts=match.parts + (i,),
                        path=f"{match.path}[{i}]",
                        root=match.root,
                    )
                    match.add_child(_match)
                    yield _match
                    yield from self._expand(_match)

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            yield match
            yield from self._expand(match)

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            yield match
            for _match in self._expand(match):
                yield _match


T = TypeVar("T")


async def _alist(it: List[T]) -> AsyncIterable[T]:
    for item in it:
        yield item


class ListSelector(JSONPathSelector):
    """A JSONPath selector representing a list of properties, slices or indices."""

    __slots__ = ("items",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        items: List[
            Union[
                SliceSelector,
                KeysSelector,
                IndexSelector,
                PropertySelector,
                WildSelector,
            ]
        ],
    ) -> None:
        super().__init__(env=env, token=token)
        self.items = tuple(items)

    def __str__(self) -> str:
        buf: List[str] = []
        for item in self.items:
            if isinstance(item, SliceSelector):
                stop = item.slice.stop if item.slice.stop is not None else ""
                start = item.slice.start if item.slice.start is not None else ""
                step = item.slice.step if item.slice.step is not None else "1"
                buf.append(f"{start}:{stop}:{step}")
            elif isinstance(item, PropertySelector):
                buf.append(f"'{item.name}'")
            elif isinstance(item, WildSelector):
                buf.append("*")
            elif isinstance(item, KeysSelector):
                buf.append(self.env.keys_selector_token)
            else:
                buf.append(str(item.index))
        return f"[{', '.join(buf)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, ListSelector)
            and self.items == __value.items
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.items, self.token))

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        _matches = list(matches)
        for item in self.items:
            yield from item.resolve(_matches)

    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        _matches = [m async for m in matches]
        for item in self.items:
            async for match in item.resolve_async(_alist(_matches)):
                yield match


class Filter(JSONPathSelector):
    """A filter selector."""

    __slots__ = ("expression", "cacheable_nodes")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        expression: BooleanExpression,
    ) -> None:
        super().__init__(env=env, token=token)
        self.expression = expression
        # Compile-time check for cacheable nodes.
        self.cacheable_nodes = self.expression.cacheable_nodes()

    def __str__(self) -> str:
        return f"[?({self.expression})]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, Filter)
            and self.expression == __value.expression
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((str(self.expression), self.token))

    def resolve(  # noqa: PLR0912
        self, matches: Iterable[JSONPathMatch]
    ) -> Iterable[JSONPathMatch]:
        if self.cacheable_nodes and self.env.filter_caching:
            expr = self.expression.cache_tree()
        else:
            expr = self.expression

        for match in matches:
            if isinstance(match.obj, Mapping):
                for key, val in match.obj.items():
                    context = FilterContext(
                        env=self.env,
                        current=val,
                        root=match.root,
                        extra_context=match.filter_context(),
                        current_key=key,
                    )
                    try:
                        if expr.evaluate(context):
                            _match = self.env.match_class(
                                filter_context=match.filter_context(),
                                obj=val,
                                parent=match,
                                parts=match.parts + (key,),
                                path=match.path + f"['{key}']",
                                root=match.root,
                            )
                            match.add_child(_match)
                            yield _match
                    except JSONPathTypeError as err:
                        if not err.token:
                            err.token = self.token
                        raise

            elif isinstance(match.obj, Sequence) and not isinstance(match.obj, str):
                for i, obj in enumerate(match.obj):
                    context = FilterContext(
                        env=self.env,
                        current=obj,
                        root=match.root,
                        extra_context=match.filter_context(),
                        current_key=i,
                    )
                    try:
                        if expr.evaluate(context):
                            _match = self.env.match_class(
                                filter_context=match.filter_context(),
                                obj=obj,
                                parent=match,
                                parts=match.parts + (i,),
                                path=f"{match.path}[{i}]",
                                root=match.root,
                            )
                            match.add_child(_match)
                            yield _match
                    except JSONPathTypeError as err:
                        if not err.token:
                            err.token = self.token
                        raise

    async def resolve_async(  # noqa: PLR0912
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        if self.cacheable_nodes and self.env.filter_caching:
            expr = self.expression.cache_tree()
        else:
            expr = self.expression

        async for match in matches:
            if isinstance(match.obj, Mapping):
                for key, val in match.obj.items():
                    context = FilterContext(
                        env=self.env,
                        current=val,
                        root=match.root,
                        extra_context=match.filter_context(),
                        current_key=key,
                    )

                    try:
                        result = await expr.evaluate_async(context)
                    except JSONPathTypeError as err:
                        if not err.token:
                            err.token = self.token
                        raise

                    if result:
                        _match = self.env.match_class(
                            filter_context=match.filter_context(),
                            obj=val,
                            parent=match,
                            parts=match.parts + (key,),
                            path=match.path + f"['{key}']",
                            root=match.root,
                        )
                        match.add_child(_match)
                        yield _match

            elif isinstance(match.obj, Sequence) and not isinstance(match.obj, str):
                for i, obj in enumerate(match.obj):
                    context = FilterContext(
                        env=self.env,
                        current=obj,
                        root=match.root,
                        extra_context=match.filter_context(),
                        current_key=i,
                    )

                    try:
                        result = await expr.evaluate_async(context)
                    except JSONPathTypeError as err:
                        if not err.token:
                            err.token = self.token
                        raise
                    if result:
                        _match = self.env.match_class(
                            filter_context=match.filter_context(),
                            obj=obj,
                            parent=match,
                            parts=match.parts + (i,),
                            path=f"{match.path}[{i}]",
                            root=match.root,
                        )
                        match.add_child(_match)
                        yield _match


class FilterContext:
    """A filter expression context."""

    __slots__ = (
        "current_key",
        "current",
        "env",
        "extra_context",
        "root",
    )

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        current: object,
        root: Union[Sequence[Any], Mapping[str, Any]],
        extra_context: Optional[Mapping[str, Any]] = None,
        current_key: Union[str, int, None] = None,
    ) -> None:
        self.env = env
        self.current = current
        self.root = root
        self.extra_context = extra_context or {}
        self.current_key = current_key

    def __str__(self) -> str:
        return (
            f"FilterContext(current={self.current}, "
            f"extra_context={self.extra_context!r})"
        )
