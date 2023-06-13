"""JSON Pointer. See https://datatracker.ietf.org/doc/html/rfc6901."""
from __future__ import annotations

import codecs
from functools import reduce
from operator import getitem
from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import Union
from urllib.parse import unquote

from .exceptions import JSONPointerEncodeError
from .exceptions import JSONPointerIndexError

if TYPE_CHECKING:
    from .match import JSONPathMatch

DEFAULT_MAX_INT_INDEX = (2**53) - 1
DEFAULT_MIN_INT_INDEX = -(2**53) + 1

PARTS = Tuple[Union[int, str], ...]


class JSONPointer:
    """A JSON Pointer, as per rfc6901.

    Arguments:
        s: A string representation of a JSON Pointer.
        max_int_index: The maximum integer allowed when resolving array items by
            index. Defaults to `(2**53) - 1`.
        min_int_index: The minimum integer allowed when resolving array items by
            index. Defaults to `-(2**53) + 1`.
        parts: The keys, indices and/or slices that make up a JSONPathMatch. If
            given, it is assumed that the parts have already been parsed by the
            JSONPath parser. `unicode_escape` and `uri_decode` are ignored if
            _parts_ is given.
        unicode_escape: If `True`, UTF-16 escape sequences will be decoded
            before parsing the pointer.
        uri_decode: If `True`, the pointer will be unescaped using _urllib_
            before being parsed.
    """

    __slots__ = ("max_int_index", "min_int_index", "parts", "_s")

    def __init__(
        self,
        s: str,
        *,
        max_int_index: int = DEFAULT_MAX_INT_INDEX,
        min_int_index: int = DEFAULT_MIN_INT_INDEX,
        parts: PARTS = (),
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> None:
        self.max_int_index = max_int_index
        self.min_int_index = min_int_index
        self.parts = parts or self._parse(
            s,
            unicode_escape=unicode_escape,
            uri_decode=uri_decode,
        )
        self._s = s

    def __str__(self) -> str:
        return self._s

    def _parse(
        self,
        s: str,
        *,
        unicode_escape: bool,
        uri_decode: bool,
    ) -> PARTS:
        if uri_decode:
            s = unquote(s)

        if unicode_escape:
            # UTF-16 escape sequences - possibly surrogate pairs - inside UTF-8
            # encoded strings. As per https://datatracker.ietf.org/doc/html/rfc4627
            # section 2.5.
            s = (
                codecs.decode(s.replace("\\/", "/"), "unicode-escape")
                .encode("utf-16", "surrogatepass")
                .decode("utf-16")
            )

        parts = tuple(
            self._index(p.replace("~1", "/").replace("~0", "~")) for p in s.split("/")
        )

        if parts == ("",):
            return ()
        if parts == ("", ""):
            return ("",)
        return parts[1:]

    def _index(self, s: str) -> Union[str, int]:
        try:
            index = int(s)
            if index < self.min_int_index or index > self.max_int_index:
                raise JSONPointerIndexError("index out of range")
            return index
        except ValueError:
            return s

    def resolve(self, obj: Union[Sequence[Any], Mapping[str, Any]]) -> object:
        """Resolve this pointer against _data_."""

        def _getitem(obj: Any, key: Any) -> Any:
            try:
                return getitem(obj, key)
            except KeyError as err:
                # Try a string repr of the index-like item as a mapping key.
                if isinstance(key, int):
                    try:
                        return getitem(obj, str(key))
                    except KeyError:
                        raise err
                # TODO: handle non-standard keys selector
                raise
            except TypeError as err:
                if isinstance(obj, Sequence):
                    try:
                        return getitem(obj, int(key))
                    except ValueError:
                        raise err
                raise

        return reduce(_getitem, self.parts, obj)

    @classmethod
    def from_match(cls, match: JSONPathMatch, *, strict: bool = True) -> JSONPointer:
        """Return a JSON Pointer for the path from a JSONPathMatch instance."""
        if strict and "~" in match.parts:
            # TODO: reference env for current key selector token
            raise JSONPointerEncodeError(
                "can't encode a JSON Pointer containing key or index selectors"
            )

        # TODO: use "relative JSON Pointer" style `#` for keys selectors?

        # A rfc6901 string representation of match.parts.
        s = "/".join(
            [str(p).replace("~", "~0").replace("/", "~1") for p in match.parts]
        )

        return cls(s, parts=match.parts, unicode_escape=False, uri_decode=False)
