from collections.abc import Mapping
from typing import Optional
from typing import Tuple


def keys(obj: Mapping[str, object]) -> Optional[Tuple[str, ...]]:
    try:
        return tuple(obj.keys())
    except AttributeError:
        return None
