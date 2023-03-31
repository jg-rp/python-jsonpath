from collections.abc import Sized
from typing import Union


def length(obj: Sized) -> Union[int, None]:
    try:
        return len(obj)
    except TypeError:
        return None
