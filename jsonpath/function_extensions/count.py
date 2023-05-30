"""The standard `count` function extension."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import List

from ..exceptions import JSONPathTypeError
from ..filter import Literal
from ..filter import Nil

if TYPE_CHECKING:
    from ..env import JSONPathEnvironment
    from ..match import NodeList
    from ..token import Token


class Count:
    """The built-in `count` function."""

    with_node_lists = True

    def __call__(self, node_list: NodeList) -> int:
        """Return the number of nodes in the node list."""
        return len(node_list)

    def validate(
        self,
        _: "JSONPathEnvironment",
        args: List[object],
        token: "Token",
    ) -> List[object]:
        """Function argument validation."""
        if len(args) != 1:  # noqa: PLR2004
            raise JSONPathTypeError(
                f"{token.value!r} requires 1 arguments, found {len(args)}",
                token=token,
            )

        if isinstance(args[0], (Literal, Nil)):
            raise JSONPathTypeError(
                f"{token.value!r} requires a node list, "
                f"found {args[0].__class__.__name__}",
                token=token,
            )

        return args
