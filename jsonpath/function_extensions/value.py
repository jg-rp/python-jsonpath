"""The standard `value` function extension."""
from typing import Sequence

from jsonpath.filter import UNDEFINED


def value(obj: object) -> object:
    """Return the first object in the sequence if the sequence has only one item."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Sequence):
        if len(obj) == 1:
            return obj[0]
        return UNDEFINED
    return obj
