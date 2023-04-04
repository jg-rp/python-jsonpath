"""The standard `length` function extension."""
from collections.abc import Sized
from typing import Optional


def length(obj: Sized) -> Optional[int]:
    """Return an object's length, or `None` if the object does not have a length."""
    try:
        return len(obj)
    except TypeError:
        return None
