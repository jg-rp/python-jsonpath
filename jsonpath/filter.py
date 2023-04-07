"""Filter expression nodes."""
from __future__ import annotations

import json
import re
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Generic
from typing import List
from typing import Mapping
from typing import Pattern
from typing import Sequence
from typing import TypeVar

from .exceptions import JSONPathTypeError

if TYPE_CHECKING:
    from .path import JSONPath
    from .selectors import FilterContext

# ruff: noqa: D102


class FilterExpression(ABC):
    """Base class for all filter expression nodes."""

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


NIL = Nil()


class _Undefined:
    def __str__(self) -> str:
        return "<UNDEFINED>"

    def __repr__(self) -> str:
        return "<UNDEFINED>"


UNDEFINED = _Undefined()


class Undefined(FilterExpression):
    """The constant `undefined`."""

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Undefined) or other is UNDEFINED

    def __str__(self) -> str:
        return "undefined"

    def evaluate(self, _: FilterContext) -> object:
        return UNDEFINED

    async def evaluate_async(self, _: FilterContext) -> object:
        return UNDEFINED


UNDEFINED_LITERAL = Undefined()

LITERAL_EXPRESSION_T = TypeVar("LITERAL_EXPRESSION_T")


class Literal(FilterExpression, Generic[LITERAL_EXPRESSION_T]):
    """Base class for filter expression literals."""

    __slots__ = ("value",)

    def __init__(self, *, value: LITERAL_EXPRESSION_T) -> None:
        self.value = value

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


class BooleanLiteral(Literal[bool]):
    """A Boolean `True` or `False`."""

    __slots__ = ()


TRUE = BooleanLiteral(value=True)


FALSE = BooleanLiteral(value=False)


class StringLiteral(Literal[str]):
    """A string literal."""

    __slots__ = ()


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

        pattern = re.sub(r"\\(.)", r"\1", self.value.pattern)
        return f"/{pattern}/{''.join(flags)}"


class RegexArgument(FilterExpression):
    """A compiled regex."""

    __slots__ = ("pattern",)

    def __init__(self, pattern: Pattern[str]) -> None:
        self.pattern = pattern

    def __str__(self) -> str:
        return repr(self.pattern.pattern)

    def evaluate(self, _: FilterContext) -> object:
        return self.pattern

    async def evaluate_async(self, _: FilterContext) -> object:
        return self.pattern


class ListLiteral(FilterExpression):
    """A list literal."""

    __slots__ = ("items",)

    def __init__(self, items: List[FilterExpression]) -> None:
        self.items = items

    def __str__(self) -> str:
        items = ", ".join(str(item) for item in self.items)
        return f"[{items}]"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ListLiteral) and self.items == other.items

    def evaluate(self, context: FilterContext) -> object:
        return [item.evaluate(context) for item in self.items]

    async def evaluate_async(self, context: FilterContext) -> object:
        return [await item.evaluate_async(context) for item in self.items]


class PrefixExpression(FilterExpression):
    """An expression composed of a prefix operator and another expression."""

    __slots__ = ("operator", "right")

    def __init__(self, operator: str, right: FilterExpression):
        self.operator = operator
        self.right = right

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


class InfixExpression(FilterExpression):
    """A pair of expressions and a comparison or logical operator."""

    __slots__ = ("left", "operator", "right")

    def __init__(
        self,
        left: FilterExpression,
        operator: str,
        right: FilterExpression,
    ):
        self.left = left
        self.operator = operator
        self.right = right

    def __str__(self) -> str:
        return f"{self.left} {self.operator} {self.right}"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InfixExpression)
            and self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )

    def evaluate(self, context: FilterContext) -> bool:
        if isinstance(self.left, Undefined) and isinstance(self.right, Undefined):
            return True
        left = self.left.evaluate(context)
        right = self.right.evaluate(context)
        return context.env.compare(left, self.operator, right)

    async def evaluate_async(self, context: FilterContext) -> bool:
        if isinstance(self.left, Undefined) and isinstance(self.right, Undefined):
            return True
        left = await self.left.evaluate_async(context)
        right = await self.right.evaluate_async(context)
        return context.env.compare(left, self.operator, right)


class BooleanExpression(FilterExpression):
    """An expression that always evaluates to `True` or `False`."""

    __slots__ = ("expression",)

    def __init__(self, expression: FilterExpression):
        self.expression = expression

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


class Path(FilterExpression, ABC):
    """Base expression for all _sub paths_ found in filter expressions."""

    __slots__ = ("path",)

    def __init__(self, path: JSONPath) -> None:
        self.path = path


class SelfPath(Path):
    """A JSONPath starting at the current node."""

    def __str__(self) -> str:
        return "@" + str(self.path)[1:]

    def evaluate(self, context: FilterContext) -> object:  # noqa: PLR0911
        if isinstance(context.current, str):
            if self.path.empty():
                return context.current
            return UNDEFINED
        if not isinstance(context.current, (Sequence, Mapping)):
            if self.path.empty():
                return context.current
            return UNDEFINED

        try:
            matches = self.path.findall(context.current)
        except json.JSONDecodeError:  # this should never happen
            return UNDEFINED

        if not matches:
            return UNDEFINED
        if len(matches) == 1:
            return matches[0]
        return matches

    async def evaluate_async(self, context: FilterContext) -> object:  # noqa: PLR0911
        if isinstance(context.current, str):
            if self.path.empty():
                return context.current
            return UNDEFINED
        if not isinstance(context.current, (Sequence, Mapping)):
            if self.path.empty():
                return context.current
            return UNDEFINED

        try:
            matches = await self.path.findall_async(context.current)
        except json.JSONDecodeError:
            return UNDEFINED

        if not matches:
            return UNDEFINED
        if len(matches) == 1:
            return matches[0]
        return matches


class RootPath(Path):
    """A JSONPath starting at the root node."""

    def __str__(self) -> str:
        return str(self.path)

    def evaluate(self, context: FilterContext) -> object:
        matches = self.path.findall(context.root)
        if not matches:
            return UNDEFINED
        if len(matches) == 1:
            return matches[0]
        return matches

    async def evaluate_async(self, context: FilterContext) -> object:
        matches = await self.path.findall_async(context.root)
        if not matches:
            return UNDEFINED
        if len(matches) == 1:
            return matches[0]
        return matches


class FilterContextPath(Path):
    """A JSONPath starting at the root of any extra context data."""

    def __str__(self) -> str:
        path_repr = str(self.path)
        return "#" + path_repr[1:]

    def evaluate(self, context: FilterContext) -> object:
        matches = self.path.findall(context.extra_context)
        if not matches:
            return UNDEFINED
        if len(matches) == 1:
            return matches[0]
        return matches

    async def evaluate_async(self, context: FilterContext) -> object:
        matches = await self.path.findall_async(context.extra_context)
        if not matches:
            return UNDEFINED
        if len(matches) == 1:
            return matches[0]
        return matches


class FunctionExtension(FilterExpression):
    """A filter function."""

    __slots__ = ("name", "args")

    def __init__(self, name: str, args: Sequence[FilterExpression]) -> None:
        self.name = name
        self.args = args

    def __str__(self) -> str:
        args = [str(arg) for arg in self.args]
        return f"{self.name}({', '.join(args)})"

    def evaluate(self, context: FilterContext) -> object:
        try:
            func = context.env.function_extensions[self.name]
        except KeyError:
            return UNDEFINED
        args = [arg.evaluate(context) for arg in self.args]
        return func(*args)

    async def evaluate_async(self, context: FilterContext) -> object:
        try:
            func = context.env.function_extensions[self.name]
        except KeyError:
            return UNDEFINED
        args = [await arg.evaluate_async(context) for arg in self.args]
        return func(*args)
