"""Filter expression nodes."""

from __future__ import annotations

import copy
import json
import re
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Generic
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Pattern
from typing import Sequence
from typing import TypeVar

from jsonpath.function_extensions.filter_function import ExpressionType

from .exceptions import JSONPathTypeError
from .function_extensions import FilterFunction
from .match import NodeList
from .selectors import Filter as FilterSelector
from .selectors import ListSelector

if TYPE_CHECKING:
    from .path import JSONPath
    from .selectors import FilterContext

# ruff: noqa: D102


class FilterExpression(ABC):
    """Base class for all filter expression nodes."""

    __slots__ = ("volatile",)

    FORCE_CACHE = False

    def __init__(self) -> None:
        self.volatile: bool = any(child.volatile for child in self.children())

    @abstractmethod
    def evaluate(self, context: FilterContext) -> object:
        """Resolve the filter expression in the given _context_.

        Arguments:
            context: Contextual information the expression might choose
                use during evaluation.

        Returns:
            The result of evaluating the expression.
        """

    @abstractmethod
    async def evaluate_async(self, context: FilterContext) -> object:
        """An async version of `evaluate`."""

    @abstractmethod
    def children(self) -> List[FilterExpression]:
        """Return a list of direct child expressions."""

    @abstractmethod
    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        """Update this expression's child expressions.

        _children_ is assumed to have the same number of items as is returned
        by _self.children_, and in the same order.
        """


class Nil(FilterExpression):
    """The constant `nil`.

    Also aliased as `null` and `None`, sometimes.
    """

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return other is None or isinstance(other, Nil)

    def __repr__(self) -> str:  # pragma: no cover
        return "NIL()"

    def __str__(self) -> str:  # pragma: no cover
        return "nil"

    def evaluate(self, _: FilterContext) -> None:
        return None

    async def evaluate_async(self, _: FilterContext) -> None:
        return None

    def children(self) -> List[FilterExpression]:
        return []

    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        return


NIL = Nil()


class _Undefined:
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return (
            other is UNDEFINED_LITERAL
            or other is UNDEFINED
            or (isinstance(other, NodeList) and other.empty())
        )

    def __str__(self) -> str:
        return "<UNDEFINED>"

    def __repr__(self) -> str:
        return "<UNDEFINED>"


# This is equivalent to the spec's special `Nothing` value.
UNDEFINED = _Undefined()


class Undefined(FilterExpression):
    """The constant `undefined`."""

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Undefined)
            or other is UNDEFINED
            or (isinstance(other, NodeList) and len(other) == 0)
        )

    def __str__(self) -> str:
        return "undefined"

    def evaluate(self, _: FilterContext) -> object:
        return UNDEFINED

    async def evaluate_async(self, _: FilterContext) -> object:
        return UNDEFINED

    def children(self) -> List[FilterExpression]:
        return []

    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        return


UNDEFINED_LITERAL = Undefined()

LITERAL_EXPRESSION_T = TypeVar("LITERAL_EXPRESSION_T")


class Literal(FilterExpression, Generic[LITERAL_EXPRESSION_T]):
    """Base class for filter expression literals."""

    __slots__ = ("value",)

    def __init__(self, *, value: LITERAL_EXPRESSION_T) -> None:
        self.value = value
        super().__init__()

    def __str__(self) -> str:
        return repr(self.value).lower()

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    def evaluate(self, _: FilterContext) -> LITERAL_EXPRESSION_T:
        return self.value

    async def evaluate_async(self, _: FilterContext) -> LITERAL_EXPRESSION_T:
        return self.value

    def children(self) -> List[FilterExpression]:
        return []

    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        return


class BooleanLiteral(Literal[bool]):
    """A Boolean `True` or `False`."""

    __slots__ = ()


TRUE = BooleanLiteral(value=True)


FALSE = BooleanLiteral(value=False)


class StringLiteral(Literal[str]):
    """A string literal."""

    __slots__ = ()

    def __str__(self) -> str:
        return json.dumps(self.value)


class IntegerLiteral(Literal[int]):
    """An integer literal."""

    __slots__ = ()


class FloatLiteral(Literal[float]):
    """A float literal."""

    __slots__ = ()


class RegexLiteral(Literal[Pattern[str]]):
    """A regex literal."""

    __slots__ = ()

    RE_FLAG_MAP = {
        re.A: "a",
        re.I: "i",
        re.M: "m",
        re.S: "s",
    }

    RE_UNESCAPE = re.compile(r"\\(.)")

    def __str__(self) -> str:
        flags: List[str] = []
        for flag, ch in self.RE_FLAG_MAP.items():
            if self.value.flags & flag:
                flags.append(ch)

        return f"/{self.value.pattern}/{''.join(flags)}"


class ListLiteral(FilterExpression):
    """A list literal."""

    __slots__ = ("items",)

    def __init__(self, items: List[FilterExpression]) -> None:
        self.items = items
        super().__init__()

    def __str__(self) -> str:
        items = ", ".join(str(item) for item in self.items)
        return f"[{items}]"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ListLiteral) and self.items == other.items

    def evaluate(self, context: FilterContext) -> object:
        return [item.evaluate(context) for item in self.items]

    async def evaluate_async(self, context: FilterContext) -> object:
        return [await item.evaluate_async(context) for item in self.items]

    def children(self) -> List[FilterExpression]:
        return self.items

    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        self.items = children


class PrefixExpression(FilterExpression):
    """An expression composed of a prefix operator and another expression."""

    __slots__ = ("operator", "right")

    def __init__(self, operator: str, right: FilterExpression):
        self.operator = operator
        self.right = right
        super().__init__()

    def __str__(self) -> str:
        return f"{self.operator}{self.right}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PrefixExpression)
            and self.operator == other.operator
            and self.right == other.right
        )

    def _evaluate(self, context: FilterContext, right: object) -> object:
        if self.operator == "!":
            return not context.env.is_truthy(right)
        raise JSONPathTypeError(f"unknown operator {self.operator} {self.right}")

    def evaluate(self, context: FilterContext) -> object:
        return self._evaluate(context, self.right.evaluate(context))

    async def evaluate_async(self, context: FilterContext) -> object:
        return self._evaluate(context, await self.right.evaluate_async(context))

    def children(self) -> List[FilterExpression]:
        return [self.right]

    def set_children(self, children: List[FilterExpression]) -> None:
        assert len(children) == 1
        self.right = children[0]


class InfixExpression(FilterExpression):
    """A pair of expressions and a comparison or logical operator."""

    __slots__ = ("left", "operator", "right", "logical")

    def __init__(
        self,
        left: FilterExpression,
        operator: str,
        right: FilterExpression,
    ):
        self.left = left
        self.operator = operator
        self.right = right
        self.logical = operator in ("&&", "||")
        super().__init__()

    def __str__(self) -> str:
        if self.logical:
            return f"({self.left} {self.operator} {self.right})"
        return f"{self.left} {self.operator} {self.right}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InfixExpression)
            and self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )

    def evaluate(self, context: FilterContext) -> bool:
        left = self.left.evaluate(context)
        if not self.logical and isinstance(left, NodeList) and len(left) == 1:
            left = left[0].obj

        right = self.right.evaluate(context)
        if not self.logical and isinstance(right, NodeList) and len(right) == 1:
            right = right[0].obj

        return context.env.compare(left, self.operator, right)

    async def evaluate_async(self, context: FilterContext) -> bool:
        left = await self.left.evaluate_async(context)
        if not self.logical and isinstance(left, NodeList) and len(left) == 1:
            left = left[0].obj

        right = await self.right.evaluate_async(context)
        if not self.logical and isinstance(right, NodeList) and len(right) == 1:
            right = right[0].obj

        return context.env.compare(left, self.operator, right)

    def children(self) -> List[FilterExpression]:
        return [self.left, self.right]

    def set_children(self, children: List[FilterExpression]) -> None:
        assert len(children) == 2  # noqa: PLR2004
        self.left = children[0]
        self.right = children[1]


class BooleanExpression(FilterExpression):
    """An expression that always evaluates to `True` or `False`."""

    __slots__ = ("expression",)

    def __init__(self, expression: FilterExpression):
        self.expression = expression
        super().__init__()

    def cache_tree(self) -> BooleanExpression:
        """Return a copy of _self.expression_ augmented with caching nodes."""

        def _cache_tree(expr: FilterExpression) -> FilterExpression:
            children = expr.children()
            if expr.volatile:
                _expr = copy.copy(expr)
            elif not expr.FORCE_CACHE and len(children) == 0:
                _expr = expr
            else:
                _expr = CachingFilterExpression(copy.copy(expr))
            _expr.set_children([_cache_tree(child) for child in children])
            return _expr

        return BooleanExpression(_cache_tree(copy.copy(self.expression)))

    def cacheable_nodes(self) -> bool:
        """Return `True` if there are any cacheable nodes in this expression tree."""
        return any(
            isinstance(node, CachingFilterExpression)
            for node in walk(self.cache_tree())
        )

    def __str__(self) -> str:
        return str(self.expression)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, BooleanExpression) and self.expression == other.expression
        )

    def evaluate(self, context: FilterContext) -> bool:
        return context.env.is_truthy(self.expression.evaluate(context))

    async def evaluate_async(self, context: FilterContext) -> bool:
        return context.env.is_truthy(await self.expression.evaluate_async(context))

    def children(self) -> List[FilterExpression]:
        return [self.expression]

    def set_children(self, children: List[FilterExpression]) -> None:
        assert len(children) == 1
        self.expression = children[0]


class CachingFilterExpression(FilterExpression):
    """A FilterExpression wrapper that caches the result."""

    __slots__ = (
        "_cached",
        "_expr",
    )

    _UNSET = object()

    def __init__(self, expression: FilterExpression):
        self.volatile = False
        self._expr = expression
        self._cached: object = self._UNSET

    def evaluate(self, context: FilterContext) -> object:
        if self._cached is self._UNSET:
            self._cached = self._expr.evaluate(context)
        return self._cached

    async def evaluate_async(self, context: FilterContext) -> object:
        if self._cached is self._UNSET:
            self._cached = await self._expr.evaluate_async(context)
        return self._cached

    def children(self) -> List[FilterExpression]:
        return self._expr.children()

    def set_children(self, children: List[FilterExpression]) -> None:
        self._expr.set_children(children)


class Path(FilterExpression, ABC):
    """Base expression for all _sub paths_ found in filter expressions."""

    __slots__ = ("path",)

    def __init__(self, path: JSONPath) -> None:
        self.path = path
        super().__init__()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Path) and str(self) == str(other)

    def children(self) -> List[FilterExpression]:
        _children: List[FilterExpression] = []
        for segment in self.path.selectors:
            if isinstance(segment, ListSelector):
                _children.extend(
                    selector.expression
                    for selector in segment.items
                    if isinstance(selector, FilterSelector)
                )
        return _children

    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        # self.path has its own cache
        return


class SelfPath(Path):
    """A JSONPath starting at the current node."""

    __slots__ = ()

    def __init__(self, path: JSONPath) -> None:
        super().__init__(path)
        self.volatile = True

    def __str__(self) -> str:
        return "@" + str(self.path)[1:]

    def evaluate(self, context: FilterContext) -> object:
        if isinstance(context.current, str):  # TODO: refactor
            if self.path.empty():
                return context.current
            return NodeList()
        if not isinstance(context.current, (Sequence, Mapping)):
            if self.path.empty():
                return context.current
            return NodeList()

        return NodeList(self.path.finditer(context.current))

    async def evaluate_async(self, context: FilterContext) -> object:
        if isinstance(context.current, str):  # TODO: refactor
            if self.path.empty():
                return context.current
            return NodeList()
        if not isinstance(context.current, (Sequence, Mapping)):
            if self.path.empty():
                return context.current
            return NodeList()

        return NodeList(
            [match async for match in await self.path.finditer_async(context.current)]
        )


class RootPath(Path):
    """A JSONPath starting at the root node."""

    __slots__ = ()

    FORCE_CACHE = True

    def __init__(self, path: JSONPath) -> None:
        super().__init__(path)
        self.volatile = False

    def __str__(self) -> str:
        return str(self.path)

    def evaluate(self, context: FilterContext) -> object:
        return NodeList(self.path.finditer(context.root))

    async def evaluate_async(self, context: FilterContext) -> object:
        return NodeList(
            [match async for match in await self.path.finditer_async(context.root)]
        )


class FilterContextPath(Path):
    """A JSONPath starting at the root of any extra context data."""

    __slots__ = ()

    FORCE_CACHE = True

    def __init__(self, path: JSONPath) -> None:
        super().__init__(path)
        self.volatile = False

    def __str__(self) -> str:
        path_repr = str(self.path)
        return "_" + path_repr[1:]

    def evaluate(self, context: FilterContext) -> object:
        return NodeList(self.path.finditer(context.extra_context))

    async def evaluate_async(self, context: FilterContext) -> object:
        return NodeList(
            [
                match
                async for match in await self.path.finditer_async(context.extra_context)
            ]
        )


class FunctionExtension(FilterExpression):
    """A filter function."""

    __slots__ = ("name", "args")

    def __init__(self, name: str, args: Sequence[FilterExpression]) -> None:
        self.name = name
        self.args = args
        super().__init__()

    def __str__(self) -> str:
        args = [str(arg) for arg in self.args]
        return f"{self.name}({', '.join(args)})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FunctionExtension)
            and other.name == self.name
            and other.args == self.args
        )

    def evaluate(self, context: FilterContext) -> object:
        try:
            func = context.env.function_extensions[self.name]
        except KeyError:
            return UNDEFINED  # TODO: should probably raise an exception
        args = [arg.evaluate(context) for arg in self.args]
        return func(*self._unpack_node_lists(func, args))

    async def evaluate_async(self, context: FilterContext) -> object:
        try:
            func = context.env.function_extensions[self.name]
        except KeyError:
            return UNDEFINED  # TODO: should probably raise an exception
        args = [await arg.evaluate_async(context) for arg in self.args]
        return func(*self._unpack_node_lists(func, args))

    def _unpack_node_lists(
        self, func: Callable[..., Any], args: List[object]
    ) -> List[object]:
        if isinstance(func, FilterFunction):
            _args: List[object] = []
            for idx, arg in enumerate(args):
                if func.arg_types[idx] != ExpressionType.NODES and isinstance(
                    arg, NodeList
                ):
                    if len(arg) == 0:
                        # If the query results in an empty nodelist, the
                        # argument is the special result Nothing.
                        _args.append(UNDEFINED)
                    elif len(arg) == 1:
                        # If the query results in a nodelist consisting of a
                        # single node, the argument is the value of the node
                        _args.append(arg[0].obj)
                    else:
                        # This should not be possible as a non-singular query
                        # would have been rejected when checking function
                        # well-typedness.
                        _args.append(arg)
                else:
                    _args.append(arg)
            return _args

        # Legacy way to indicate that a filter function wants node lists as arguments.
        if getattr(func, "with_node_lists", False):
            return args

        return [
            obj.values_or_singular() if isinstance(obj, NodeList) else obj
            for obj in args
        ]

    def children(self) -> List[FilterExpression]:
        return list(self.args)

    def set_children(self, children: List[FilterExpression]) -> None:
        assert len(children) == len(self.args)
        self.args = children


class CurrentKey(FilterExpression):
    """The key/property or index associated with the current object."""

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()
        self.volatile = True

    def __str__(self) -> str:
        return "#"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CurrentKey)

    def evaluate(self, context: FilterContext) -> object:
        if context.current_key is None:
            return UNDEFINED
        return context.current_key

    async def evaluate_async(self, context: FilterContext) -> object:
        return self.evaluate(context)

    def children(self) -> List[FilterExpression]:
        return []

    def set_children(self, children: List[FilterExpression]) -> None:  # noqa: ARG002
        return


CURRENT_KEY = CurrentKey()


def walk(expr: FilterExpression) -> Iterable[FilterExpression]:
    """Walk the filter expression tree starting at _expr_."""
    yield expr
    for child in expr.children():
        yield from walk(child)


VALUE_TYPE_EXPRESSIONS = (
    Nil,
    Undefined,
    Literal,
    ListLiteral,
    CurrentKey,
)
