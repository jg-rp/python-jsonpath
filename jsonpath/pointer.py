"""JSON Pointer. See https://datatracker.ietf.org/doc/html/rfc6901."""
from __future__ import annotations

import codecs
import json
from functools import reduce
from io import IOBase
from operator import getitem
from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import Union
from urllib.parse import unquote

from .exceptions import JSONPointerIndexError
from .exceptions import JSONPointerKeyError
from .exceptions import JSONPointerResolutionError
from .exceptions import JSONPointerTypeError

if TYPE_CHECKING:
    from .match import JSONPathMatch


class JSONPointer:
    """A JSON Pointer, as per rfc6901.

    Args:
        s: A string representation of a JSON Pointer.
        parts: The keys, indices and/or slices that make up a JSONPathMatch. If
            given, it is assumed that the parts have already been parsed by the
            JSONPath parser. `unicode_escape` and `uri_decode` are ignored if
            _parts_ is given.
        unicode_escape: If `True`, UTF-16 escape sequences will be decoded
            before parsing the pointer.
        uri_decode: If `True`, the pointer will be unescaped using _urllib_
            before being parsed.

    Attributes:
        keys_selector (str): The non-standard token used to target a mapping
            key or name.
        max_int_index (int): The maximum integer allowed when resolving array
            items by index. Defaults to `(2**53) - 1`.
        min_int_index (int): The minimum integer allowed when resolving array
            items by index. Defaults to `-(2**53) + 1`.
    """

    __slots__ = ("_s", "parts")

    keys_selector = ("~",)
    max_int_index = (2**53) - 1
    min_int_index = -(2**53) + 1

    def __init__(
        self,
        s: str,
        *,
        parts: Tuple[Union[int, str], ...] = (),
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> None:
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
    ) -> Tuple[Union[int, str], ...]:
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

        return tuple(
            self._index(p.replace("~1", "/").replace("~0", "~")) for p in s.split("/")
        )[1:]

    def _index(self, s: str) -> Union[str, int]:
        try:
            index = int(s)
            if index < self.min_int_index or index > self.max_int_index:
                raise JSONPointerIndexError("index out of range")
            return index
        except ValueError:
            return s

    def _getitem(self, obj: Any, key: Any) -> Any:
        try:
            return getitem(obj, key)
        except KeyError as err:
            # Try a string repr of the index-like item as a mapping key.
            if isinstance(key, int):
                try:
                    return getitem(obj, str(key))
                except KeyError:
                    raise JSONPointerKeyError(str(err)) from err
            # Handle non-standard keys selector
            if (
                isinstance(key, str)
                and isinstance(obj, Mapping)
                and key.startswith(self.keys_selector)
                and key[1:] in obj
            ):
                return key[1:]
            raise JSONPointerKeyError(str(err)) from err
        except TypeError as err:
            if isinstance(obj, Sequence):
                if key == "-":
                    # "-" is a valid index when appending to a JSON array
                    # with JSON Patch, but not when resolving a JSON Pointer.
                    raise JSONPointerIndexError("index out of range") from None
                try:
                    return getitem(obj, int(key))
                except ValueError:
                    pass
            raise JSONPointerTypeError(str(err)) from err
        except IndexError as err:
            raise JSONPointerIndexError(str(err)) from err

    def resolve(
        self, data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]]
    ) -> object:
        """Resolve this pointer against _data_.

        Args:
            data: The target JSON "document" or equivalent Python objects.

        Returns:
            The object in _data_ pointed to by this pointer.

        Raises:
            JSONPointerIndexError: When attempting to access a sequence by
                and out of range index.
            JSONPointerKeyError: If any mapping object along the path does not
                contain a specified key.
            JSONPointerTypeError: When attempting to resolve a non-index string
                path part against a sequence.
        """
        if isinstance(data, str):
            data = json.loads(data)
        elif isinstance(data, IOBase):
            data = json.loads(data.read())
        return reduce(self._getitem, self.parts, data)

    def resolve_parent(
        self, data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]]
    ) -> Tuple[Union[Sequence[Any], Mapping[str, Any], None], object]:
        """Resolve this pointer against _data_, return the object and its parent.

        Args:
            data: The target JSON "document" or equivalent Python objects.

        Returns:
            A `(parent, object)` tuple, where parent will be `None` if this
                pointer points to the root node in the document. If the parent
                exists but the last object does not, `(parent, None)` will be
                returned.

        Raises:
            JSONPointerIndexError: When attempting to access a sequence by
                and out of range index, unless using the special `-` index.
            JSONPointerKeyError: If any mapping object along the path does not
                contain a specified key, unless it is the last part of the
                pointer.
            JSONPointerTypeError: When attempting to resolve a non-index string
                path part against a sequence.
        """
        if not len(self.parts):
            return (None, self.resolve(data))

        if isinstance(data, str):
            _data = json.loads(data)
        elif isinstance(data, IOBase):
            _data = json.loads(data.read())
        else:
            _data = data

        parent = reduce(self._getitem, self.parts[:-1], _data)

        try:
            return (parent, self._getitem(parent, self.parts[-1]))
        except (JSONPointerIndexError, JSONPointerKeyError):
            return (parent, None)

    @classmethod
    def from_match(
        cls,
        match: JSONPathMatch,
    ) -> JSONPointer:
        """Return a JSON Pointer for the path from a JSONPathMatch instance."""
        # A rfc6901 string representation of match.parts.
        return cls(
            "/"
            + "/".join(
                str(p).replace("~", "~0").replace("/", "~1") for p in match.parts
            ),
            parts=match.parts,
            unicode_escape=False,
            uri_decode=False,
        )


_missing = object()


def resolve(
    pointer: str,
    data: Union[str, IOBase, Sequence[Any], Mapping[str, Any]],
    *,
    default: object = _missing,
    unicode_escape: bool = True,
    uri_decode: bool = False,
) -> object:
    """Resolve JSON Pointer _pointer_ against _data_.

    Args:
        pointer: A string representation of a JSON Pointer.
        data: The target JSON "document" or equivalent Python objects.
        default: A default value to return if the pointer can't be resolved.
        unicode_escape: If `True`, UTF-16 escape sequences will be decoded
            before parsing the pointer.
        uri_decode: If `True`, the pointer will be unescaped using _urllib_
            before being parsed.

    Returns:
        The object in _data_ pointed to by this pointer.

    Raises:
        JSONPointerIndexError: When attempting to access a sequence by
            and out of range index.
        JSONPointerKeyError: If any mapping object along the path does not contain
            a specified key.
        JSONPointerTypeError: When attempting to resolve a non-index string path
            part against a sequence.
    """
    try:
        return JSONPointer(
            pointer, unicode_escape=unicode_escape, uri_decode=uri_decode
        ).resolve(data)
    except JSONPointerResolutionError:
        if default is not _missing:
            return default
        raise
