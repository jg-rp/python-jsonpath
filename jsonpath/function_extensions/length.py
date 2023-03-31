from collections.abc import Sized
from typing import Optional


def length(obj: Sized) -> Optional[int]:
    try:
        return len(obj)
    except TypeError:
        return None
