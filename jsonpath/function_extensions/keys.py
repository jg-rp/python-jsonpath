"""The built-in `keys` function extension."""
from typing import Mapping
from typing import Optional
from typing import Tuple


def keys(obj: Mapping[str, object]) -> Optional[Tuple[str, ...]]:
    """Return an object's keys, or `None` if the object has no _keys_ method."""
    try:
        return tuple(obj.keys())
    except AttributeError:
        return None
