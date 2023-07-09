"""A non-standard "isinstance" filter function."""

from typing import Mapping
from typing import Sequence

from jsonpath.filter import UNDEFINED
from jsonpath.filter import UNDEFINED_LITERAL


class IsInstance:
    """A non-standard "isinstance" filter function."""

    def __call__(self, obj: object, t: str) -> bool:  # noqa: PLR0911
        """Return `True` if the type of _obj_ matches _t_.

        This function allows _t_ to be one of several aliases for the real
        Python "type". Some of these aliases follow JavaScript/JSON semantics.
        """
        if obj is UNDEFINED or obj is UNDEFINED_LITERAL:
            return t in ("undefined", "missing")
        if obj is None:
            return t in ("null", "nil", "None", "none")
        if isinstance(obj, str):
            return t in ("str", "string")
        if isinstance(obj, Sequence):
            return t in ("array", "list", "sequence", "tuple")
        if isinstance(obj, Mapping):
            return t in ("object", "dict", "mapping")
        if isinstance(obj, bool):
            return t in ("bool", "boolean")
        if isinstance(obj, int):
            return t in ("number", "int")
        if isinstance(obj, float):
            return t in ("number", "float")
        return t == "object"
