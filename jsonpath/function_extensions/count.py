"""The standard `count` function extension."""
from collections.abc import Sized
from typing import TYPE_CHECKING
from typing import List
from typing import Optional

from ..exceptions import JSONPathTypeError
from ..filter import Literal

if TYPE_CHECKING:
    from ..env import JSONPathEnvironment
    from ..token import Token


class Count:
    """The built-in `count` function."""

    def __call__(self, obj: Sized) -> Optional[int]:
        """Return an object's length, or `None` if the object does not have a length."""
        try:
            return len(obj)
        except TypeError:
            return None

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

        if isinstance(args[0], Literal):
            raise JSONPathTypeError(
                f"{token.value!r} requires a node list, "
                f"found {args[0].__class__.__name__}",
                token=token,
            )

        return args
