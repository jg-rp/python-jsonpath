"""A non-standard "typeof" filter function."""

from typing import Mapping
from typing import Sequence

from jsonpath.filter import UNDEFINED
from jsonpath.filter import UNDEFINED_LITERAL


class TypeOf:
    """A non-standard "typeof" filter function.

    Arguments:
        single_number_type: If True, will return "number" for ints and floats,
            otherwise we'll use "int" and "float" respectively. Defaults to `True`.
    """

    def __init__(self, *, single_number_type: bool = True) -> None:
        self.single_number_type = single_number_type

    def __call__(self, obj: object) -> str:  # noqa: PLR0911
        """Return the type of _obj_ as a string.

        The strings returned from this function use JSON terminology, much
        like the result of JavaScript's `typeof` operator.
        """
        if obj is UNDEFINED or obj is UNDEFINED_LITERAL:
            return "undefined"
        if obj is None:
            return "null"
        if isinstance(obj, str):
            return "string"
        if isinstance(obj, Sequence):
            return "array"
        if isinstance(obj, Mapping):
            return "object"
        if isinstance(obj, bool):
            return "boolean"
        if isinstance(obj, int):
            return "number" if self.single_number_type else "int"
        if isinstance(obj, float):
            return "number" if self.single_number_type else "float"
        return "object"
