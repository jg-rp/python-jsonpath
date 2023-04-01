"""The JSONPath match object, as returned from :meth:`JSONPath.finditer`."""
from __future__ import annotations

from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

FilterContextVars = Mapping[str, Any]
PathPart = Union[int, slice, str]


class JSONPathMatch:
    """Bind a matched object to its path."""

    __slots__ = (
        "_filter_context",
        "children",
        "obj",
        "parent",
        "parts",
        "path",
        "root",
    )

    def __init__(
        self,
        *,
        filter_context: FilterContextVars,
        obj: object,
        parent: Optional[JSONPathMatch],
        path: str,
        parts: Tuple[PathPart, ...],
        root: Union[Sequence[Any], Mapping[str, Any]],
    ) -> None:
        self._filter_context = filter_context
        self.children: List[JSONPathMatch] = []
        self.obj = obj
        self.parent = parent
        self.parts = parts
        self.path = path
        self.root = root

    def __str__(self) -> str:
        return f"{_truncate(str(self.obj), 5)!r} @ {_truncate(self.path, 5)}"

    def add_child(self, *children: JSONPathMatch) -> None:
        self.children.extend(children)

    def filter_context(self) -> FilterContextVars:
        """"""
        return self._filter_context


def _truncate(val: str, num: int, end: str = "...") -> str:
    # Replaces consecutive whitespace with a single newline.
    # Treats quoted whitespace the same as unquoted whitespace.
    words = val.split()
    if len(words) < num:
        return " ".join(words)
    return " ".join(words[:num]) + end
