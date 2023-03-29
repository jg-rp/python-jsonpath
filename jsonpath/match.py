"""The JSONPath match object, as returned from :meth:`JSONPath.finditer`."""

from typing import Any, Mapping, Sequence, Union

FilterContextVars = Mapping[str, Any]


class JSONPathMatch:
    """Bind a matched object to its path."""

    __slots__ = ("_filter_context", "obj", "path", "root")

    def __init__(
        self,
        *,
        filter_context: FilterContextVars,
        obj: object,
        path: str,
        root: Union[Sequence[Any], Mapping[str, Any]],
    ) -> None:
        self.path = path
        self.obj = obj
        self.root = root
        self._filter_context = filter_context

    def __str__(self) -> str:
        return f"{_truncate(str(self.obj), 5)} @ {_truncate(self.path, 5)}"

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
