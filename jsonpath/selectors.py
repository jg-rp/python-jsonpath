"""JSONPath segments and selectors, as returned from `Parser.parse`."""

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
from typing import Optional
from typing import Union

from .exceptions import JSONPathIndexError
from .exceptions import JSONPathTypeError
from .serialize import canonical_string

if TYPE_CHECKING:
    from .env import JSONPathEnvironment
    from .filter import BooleanExpression
    from .match import JSONPathMatch
    from .token import Token

# ruff: noqa: D102


class JSONPathSelector(ABC):
    """Base class for all JSONPath segments and selectors."""

    __slots__ = ("env", "token")

    def __init__(self, *, env: JSONPathEnvironment, token: Token) -> None:
        self.env = env
        self.token = token

    @abstractmethod
    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        """Apply the segment/selector to each node in _matches_.

        Arguments:
            node: A node matched by preceding segments/selectors.

        Returns:
            The `JSONPathMatch` instances created by applying this selector to each
            preceding node.
        """

    @abstractmethod
    def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        """An async version of `resolve`."""


class PropertySelector(JSONPathSelector):
    """A shorthand or bracketed property selector."""

    __slots__ = ("name", "shorthand")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        name: str,
        shorthand: bool,
    ) -> None:
        super().__init__(env=env, token=token)
        self.name = name
        self.shorthand = shorthand

    def __str__(self) -> str:
        return (
            f"[{canonical_string(self.name)}]"
            if self.shorthand
            else f"{canonical_string(self.name)}"
        )

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, PropertySelector)
            and self.name == __value.name
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.name, self.token))

    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            with suppress(KeyError):
                match = node.new_child(self.env.getitem(node.obj, self.name), self.name)
                node.add_child(match)
                yield match

    async def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            with suppress(KeyError):
                match = node.new_child(
                    await self.env.getitem_async(node.obj, self.name), self.name
                )
                node.add_child(match)
                yield match


class IndexSelector(JSONPathSelector):
    """Select an element from an array by index.

    XXX: Change to make unquoted keys/properties a "singular path selector"
    https://github.com/ietf-wg-jsonpath/draft-ietf-jsonpath-base/issues/522

    Considering we don't require mapping (JSON object) keys/properties to
    be quoted, and that we support mappings with numeric keys, we also check
    to see if the "index" is a mapping key, which is non-standard.
    """

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
        return str(self.index)

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

    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            # Try the string representation of the index as a key.
            with suppress(KeyError):
                match = node.new_child(
                    self.env.getitem(node.obj, self._as_key), self.index
                )
                node.add_child(match)
                yield match
        elif isinstance(node.obj, Sequence) and not isinstance(node.obj, str):
            norm_index = self._normalized_index(node.obj)
            with suppress(IndexError):
                match = node.new_child(
                    self.env.getitem(node.obj, self.index), norm_index
                )
                node.add_child(match)
                yield match

    async def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            # Try the string representation of the index as a key.
            with suppress(KeyError):
                match = node.new_child(
                    await self.env.getitem_async(node.obj, self._as_key), self.index
                )
                node.add_child(match)
                yield match
        elif isinstance(node.obj, Sequence) and not isinstance(node.obj, str):
            norm_index = self._normalized_index(node.obj)
            with suppress(IndexError):
                match = node.new_child(
                    await self.env.getitem_async(node.obj, self.index), norm_index
                )
                node.add_child(match)
                yield match


class KeysSelector(JSONPathSelector):
    """Select mapping/object keys/properties.

    NOTE: This is a non-standard selector.
    """

    __slots__ = ("shorthand",)

    def __init__(
        self, *, env: JSONPathEnvironment, token: Token, shorthand: bool
    ) -> None:
        super().__init__(env=env, token=token)
        self.shorthand = shorthand

    def __str__(self) -> str:
        return (
            f"[{self.env.keys_selector_token}]"
            if self.shorthand
            else self.env.keys_selector_token
        )

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, KeysSelector) and self.token == __value.token

    def __hash__(self) -> int:
        return hash(self.token)

    def _keys(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            for i, key in enumerate(node.obj.keys()):
                match = node.__class__(
                    filter_context=node.filter_context(),
                    obj=key,
                    parent=node,
                    parts=node.parts + (f"{self.env.keys_selector_token}{key}",),
                    path=f"{node.path}[{self.env.keys_selector_token}][{i}]",
                    root=node.root,
                )
                node.add_child(match)
                yield match

    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        yield from self._keys(node)

    async def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        for match in self._keys(node):
            yield match


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
        return f"{start}:{stop}:{step}"

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

    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if not isinstance(node.obj, Sequence) or self.slice.step == 0:
            return

        for norm_index, obj in zip(  # noqa: B905
            range(*self.slice.indices(len(node.obj))),
            self.env.getitem(node.obj, self.slice),
        ):
            match = node.new_child(obj, norm_index)
            node.add_child(match)
            yield match

    async def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        if not isinstance(node.obj, Sequence) or self.slice.step == 0:
            return

        for norm_index, obj in zip(  # noqa: B905
            range(*self.slice.indices(len(node.obj))),
            await self.env.getitem_async(node.obj, self.slice),
        ):
            match = node.new_child(obj, norm_index)
            node.add_child(match)
            yield match


class WildSelector(JSONPathSelector):
    """Select all items from a sequence/array or values from a mapping/object."""

    __slots__ = ("shorthand",)

    def __init__(
        self, *, env: JSONPathEnvironment, token: Token, shorthand: bool
    ) -> None:
        super().__init__(env=env, token=token)
        self.shorthand = shorthand

    def __str__(self) -> str:
        return "[*]" if self.shorthand else "*"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, WildSelector) and self.token == __value.token

    def __hash__(self) -> int:
        return hash(self.token)

    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            for key, val in node.obj.items():
                match = node.new_child(val, key)
                node.add_child(match)
                yield match

        elif isinstance(node.obj, Sequence) and not isinstance(node.obj, str):
            for i, val in enumerate(node.obj):
                match = node.new_child(val, i)
                node.add_child(match)
                yield match

    async def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        if isinstance(node.obj, Mapping):
            for key, val in node.obj.items():
                match = node.new_child(val, key)
                node.add_child(match)
                yield match

        elif isinstance(node.obj, Sequence) and not isinstance(node.obj, str):
            for i, val in enumerate(node.obj):
                match = node.new_child(val, i)
                node.add_child(match)
                yield match


class Filter(JSONPathSelector):
    """Filter sequence/array items or mapping/object values with a filter expression."""

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
        return f"?{self.expression}"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, Filter)
            and self.expression == __value.expression
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((str(self.expression), self.token))

    def resolve(self, node: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if self.cacheable_nodes and self.env.filter_caching:
            expr = self.expression.cache_tree()
        else:
            expr = self.expression

        if isinstance(node.obj, Mapping):
            for key, val in node.obj.items():
                context = FilterContext(
                    env=self.env,
                    current=val,
                    root=node.root,
                    extra_context=node.filter_context(),
                    current_key=key,
                )
                try:
                    if expr.evaluate(context):
                        match = node.new_child(val, key)
                        node.add_child(match)
                        yield match
                except JSONPathTypeError as err:
                    if not err.token:
                        err.token = self.token
                    raise

        elif isinstance(node.obj, Sequence) and not isinstance(node.obj, str):
            for i, obj in enumerate(node.obj):
                context = FilterContext(
                    env=self.env,
                    current=obj,
                    root=node.root,
                    extra_context=node.filter_context(),
                    current_key=i,
                )
                try:
                    if expr.evaluate(context):
                        match = node.new_child(obj, i)
                        node.add_child(match)
                        yield match
                except JSONPathTypeError as err:
                    if not err.token:
                        err.token = self.token
                    raise

    async def resolve_async(self, node: JSONPathMatch) -> AsyncIterable[JSONPathMatch]:
        if self.cacheable_nodes and self.env.filter_caching:
            expr = self.expression.cache_tree()
        else:
            expr = self.expression

        if isinstance(node.obj, Mapping):
            for key, val in node.obj.items():
                context = FilterContext(
                    env=self.env,
                    current=val,
                    root=node.root,
                    extra_context=node.filter_context(),
                    current_key=key,
                )

                try:
                    result = await expr.evaluate_async(context)
                except JSONPathTypeError as err:
                    if not err.token:
                        err.token = self.token
                    raise

                if result:
                    match = node.new_child(val, key)
                    node.add_child(match)
                    yield match

        elif isinstance(node.obj, Sequence) and not isinstance(node.obj, str):
            for i, obj in enumerate(node.obj):
                context = FilterContext(
                    env=self.env,
                    current=obj,
                    root=node.root,
                    extra_context=node.filter_context(),
                    current_key=i,
                )

                try:
                    result = await expr.evaluate_async(context)
                except JSONPathTypeError as err:
                    if not err.token:
                        err.token = self.token
                    raise
                if result:
                    match = node.new_child(obj, i)
                    node.add_child(match)
                    yield match


class FilterContext:
    """Contextual information and data for evaluating a filter expression."""

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
