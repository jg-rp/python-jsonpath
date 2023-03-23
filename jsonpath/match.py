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
        # TODO: truncate str(obj)
        return f"{self.obj} @ {self.path}"
