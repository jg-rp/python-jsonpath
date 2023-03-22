from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from typing import Generic
from typing import List
from typing import Mapping
from typing import Pattern
from typing import Sequence
from typing import TypeVar
from typing import TYPE_CHECKING

from .exceptions import JSONPathTypeError

if TYPE_CHECKING:
    from .path import JSONPath
    from .selectors import FilterContext

# TODO: __str__ methods


class FilterExpression(ABC):
    """"""

    @abstractmethod
    def evaluate(self, context: FilterContext) -> object:
        """"""

    @abstractmethod
    async def evaluate_async(self, context: FilterContext) -> object:
        """"""


class Nil(FilterExpression):
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return other is None or isinstance(other, Nil)

    def __repr__(self) -> str:  # pragma: no cover
        return "NIL()"

    def __str__(self) -> str:  # pragma: no cover
        return ""

    def evaluate(self, context: FilterContext) -> None:
        return None

    async def evaluate_async(self, context: FilterContext) -> None:
        return None


NIL = Nil()

LITERAL_EXPRESSION_T = TypeVar("LITERAL_EXPRESSION_T")


class Literal(FilterExpression, Generic[LITERAL_EXPRESSION_T]):
    """"""

    __slots__ = ("value",)

    def __init__(self, *, value: LITERAL_EXPRESSION_T) -> None:
        self.value = value

    def __str__(self) -> str:
        return repr(self.value)

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    def evaluate(self, context: FilterContext) -> LITERAL_EXPRESSION_T:
        """"""
        return self.value

    async def evaluate_async(self, context: FilterContext) -> LITERAL_EXPRESSION_T:
        """"""
        return self.value


class BooleanLiteral(Literal[bool]):
    __slots__ = ()


TRUE = BooleanLiteral(value=True)


FALSE = BooleanLiteral(value=False)


class StringLiteral(Literal[str]):
    __slots__ = ()


class IntegerLiteral(Literal[int]):
    __slots__ = ()


class FloatLiteral(Literal[float]):
    __slots__ = ()


class RegexLiteral(Literal[Pattern[str]]):
    __slots__ = ()


class ListLiteral(FilterExpression):
    __slots__ = ("items",)

    def __init__(self, items: List[FilterExpression]) -> None:
        self.items = items

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ListLiteral) and self.items == other.items

    def evaluate(self, context: FilterContext) -> object:
        return [item.evaluate(context) for item in self.items]

    async def evaluate_async(self, context: FilterContext) -> object:
        return [await item.evaluate_async(context) for item in self.items]


class PrefixExpression(FilterExpression):
    __slots__ = ("operator", "right")

    def __init__(self, operator: str, right: FilterExpression):
        self.operator = operator
        self.right = right

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PrefixExpression)
            and self.operator == other.operator
            and self.right == other.right
        )

    def _evaluate(self, context: FilterContext, right: object) -> object:
        if self.operator == "not":
            return not context.env.is_truthy(right)
        raise JSONPathTypeError(f"unknown operator {self.operator} {self.right}")

    def evaluate(self, context: FilterContext) -> object:
        return self._evaluate(context, self.right.evaluate(context))

    async def evaluate_async(self, context: FilterContext) -> object:
        return self._evaluate(context, await self.right.evaluate_async(context))


class InfixExpression(FilterExpression):
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

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, InfixExpression)
            and self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )

    def evaluate(self, context: FilterContext) -> bool:
        return context.env.compare(
            self.left.evaluate(context), self.operator, self.right.evaluate(context)
        )

    async def evaluate_async(self, context: FilterContext) -> bool:
        return context.env.compare(
            await self.left.evaluate_async(context),
            self.operator,
            await self.right.evaluate_async(context),
        )


class BooleanExpression(FilterExpression):
    """"""

    __slots__ = ("expression",)

    def __init__(self, expression: FilterExpression):
        self.expression = expression

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, BooleanExpression) and self.expression == other.expression
        )

    def evaluate(self, context: FilterContext) -> bool:
        return context.env.is_truthy(self.expression.evaluate(context))

    async def evaluate_async(self, context: FilterContext) -> bool:
        return context.env.is_truthy(await self.expression.evaluate_async(context))


class Path(FilterExpression, ABC):
    __slots__ = ("path",)

    def __init__(self, path: JSONPath) -> None:
        self.path = path


class SelfPath(Path):
    def evaluate(self, context: FilterContext) -> object:
        if not isinstance(context.current, (Sequence, Mapping)):
            return None

        matches = self.path.findall(context.current)
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        return matches

    async def evaluate_async(self, context: FilterContext) -> object:
        if not isinstance(context.current, (Sequence, Mapping)):
            return None

        matches = await self.path.findall_async(context.current)
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        return matches


class RootPath(Path):
    def evaluate(self, context: FilterContext) -> object:
        return self.path.findall(context.root)

    async def evaluate_async(self, context: FilterContext) -> object:
        return await self.path.findall_async(context.root)
