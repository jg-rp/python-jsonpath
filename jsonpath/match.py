""""""

from typing import Any
from typing import Mapping
from typing import Sequence
from typing import Union


# pylint: disable=too-few-public-methods
class JSONPathMatch:
    """Bind a matched object to its path."""

    __slots__ = ("path", "obj", "root")

    def __init__(
        self,
        *,
        path: str,
        obj: object,
        root: Union[Sequence[Any], Mapping[str, Any]],
    ) -> None:
        self.path = path
        self.obj = obj
        self.root = root

    def __str__(self) -> str:
        return f"{_truncate(str(self.obj), 5)} @ {_truncate(self.path, 5)}"


def _truncate(val: str, num: int, end: str = "...") -> str:
    # Replaces consecutive whitespace with a single newline.
    # Treats quoted whitespace the same as unquoted whitespace.
    words = val.split()
    if len(words) < num:
        return " ".join(words)
    return " ".join(words[:num]) + end
