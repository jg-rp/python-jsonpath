"""JSON Pointer. See https://datatracker.ietf.org/doc/html/rfc6901."""
from __future__ import annotations

import codecs
import json
from functools import reduce
from io import IOBase
from operator import getitem
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
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

UNDEFINED = object()


class JSONPointer:
    """Identify a single, specific value in JSON-like data, as per RFC 6901.

    Args:
        pointer: A string representation of a JSON Pointer.
        parts: The keys, indices and/or slices that make up a JSON Pointer. If
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

    keys_selector = "~"
    max_int_index = (2**53) - 1
    min_int_index = -(2**53) + 1

    def __init__(
        self,
        pointer: str,
        *,
        parts: Tuple[Union[int, str], ...] = (),
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> None:
        self.parts = parts or self._parse(
            pointer,
            unicode_escape=unicode_escape,
            uri_decode=uri_decode,
        )
        self._s = pointer

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

        # TODO: lstrip pointer
        # TODO: handle pointer without leading slash and not empty string
        return tuple(
            self._index(p.replace("~1", "/").replace("~0", "~")) for p in s.split("/")
        )[1:]

    def _index(self, s: str) -> Union[str, int]:
        # Reject non-zero ints that start with a zero.
        if len(s) > 1 and s.startswith("0"):
            return s

        try:
            index = int(s)
            if index < self.min_int_index or index > self.max_int_index:
                raise JSONPointerIndexError("index out of range")
            return index
        except ValueError:
            return s

    def _getitem(self, obj: Any, key: Any) -> Any:  # noqa: PLR0912
        try:
            return getitem(obj, key)
        except KeyError as err:
            # Try a string repr of the index-like item as a mapping key.
            if isinstance(key, int):
                try:
                    return getitem(obj, str(key))
                except KeyError:
                    raise JSONPointerKeyError(key) from err
            # Handle non-standard keys selector
            if (
                isinstance(key, str)
                and isinstance(obj, Mapping)
                and key.startswith(self.keys_selector)
                and key[1:] in obj
            ):
                return key[1:]
            raise JSONPointerKeyError(key) from err
        except TypeError as err:
            if isinstance(obj, Sequence):
                if key == "-":
                    # "-" is a valid index when appending to a JSON array
                    # with JSON Patch, but not when resolving a JSON Pointer.
                    raise JSONPointerIndexError("index out of range") from None

                # Try int index. Reject non-zero ints that start with a zero.
                if isinstance(key, str):
                    index = self._index(key)
                    if isinstance(index, int):
                        try:
                            return getitem(obj, int(key))
                        except IndexError as index_err:
                            raise JSONPointerIndexError(
                                f"index out of range: {key}"
                            ) from index_err
            raise JSONPointerTypeError(f"pointer type error: {key}: {err}") from err
        except IndexError as err:
            raise JSONPointerIndexError(f"index out of range: {key}") from err

    def resolve(
        self,
        data: Union[str, IOBase, Sequence[object], Mapping[str, object]],
        *,
        default: object = UNDEFINED,
    ) -> object:
        """Resolve this pointer against _data_.

        Args:
            data: The target JSON "document" or equivalent Python objects.
            default: A default value to return if the pointer can't be resolved
                against the given data.

        Returns:
            The object in _data_ pointed to by this pointer.

        Raises:
            JSONPointerIndexError: When attempting to access a sequence by
                an out of range index, unless a default is given.
            JSONPointerKeyError: If any mapping object along the path does not
                contain a specified key, unless a default is given.
            JSONPointerTypeError: When attempting to resolve a non-index string
                path part against a sequence, unless a default is given.
        """
        if isinstance(data, str):
            data = json.loads(data)
        elif isinstance(data, IOBase):
            data = json.loads(data.read())
        try:
            return reduce(self._getitem, self.parts, data)
        except JSONPointerResolutionError:
            if default is not UNDEFINED:
                return default
            raise

    def resolve_parent(
        self, data: Union[str, IOBase, Sequence[object], Mapping[str, object]]
    ) -> Tuple[Union[Sequence[object], Mapping[str, object], None], object]:
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
                an out of range index, unless using the special `-` index.
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
            return (parent, UNDEFINED)

    @classmethod
    def from_match(
        cls,
        match: JSONPathMatch,
    ) -> JSONPointer:
        """Return a JSON Pointer for the path from a JSONPathMatch instance."""
        # A rfc6901 string representation of match.parts.
        if not match.parts:
            # This should not happen, unless the JSONPathMatch has been tampered with.
            pointer = ""
        else:
            pointer = "/" + "/".join(
                str(p).replace("~", "~0").replace("/", "~1") for p in match.parts
            )

        return cls(
            pointer,
            parts=match.parts,
            unicode_escape=False,
            uri_decode=False,
        )

    @classmethod
    def from_parts(
        cls,
        parts: Iterable[Union[int, str]],
        *,
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> JSONPointer:
        """Build a JSON Pointer from _parts_.

        Args:
            parts: The keys, indices and/or slices that make up a JSONPointer.
            unicode_escape: If `True`, UTF-16 escape sequences will be decoded
                before parsing the pointer.
            uri_decode: If `True`, the pointer will be unescaped using _urllib_
                before being parsed.
        """
        _parts = (str(p) for p in parts)
        if uri_decode:
            _parts = (unquote(p) for p in _parts)
        if unicode_escape:
            _parts = (
                codecs.decode(p.replace("\\/", "/"), "unicode-escape")
                .encode("utf-16", "surrogatepass")
                .decode("utf-16")
                for p in _parts
            )

        __parts = tuple(_parts)

        if __parts:
            pointer = "/" + "/".join(
                p.replace("~", "~0").replace("/", "~1") for p in __parts
            )
        else:
            pointer = ""

        return cls(
            pointer,
            parts=__parts,
            unicode_escape=False,
            uri_decode=False,
        )

    def is_relative_to(self, other: JSONPointer) -> bool:
        """Return _True_ if this pointer points to a child of _other_."""
        return (
            len(other.parts) < len(self.parts)
            and self.parts[: len(other.parts)] == other.parts
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, JSONPointer) and self.parts == other.parts


def resolve(
    pointer: Union[str, Iterable[Union[str, int]]],
    data: Union[str, IOBase, Sequence[object], Mapping[str, object]],
    *,
    default: object = UNDEFINED,
    unicode_escape: bool = True,
    uri_decode: bool = False,
) -> object:
    """Resolve JSON Pointer _pointer_ against _data_.

    Args:
        pointer: A string representation of a JSON Pointer or an iterable of
            JSON Pointer parts.
        data: The target JSON "document" or equivalent Python objects.
        default: A default value to return if the pointer can't be resolved.
            against the given data.
        unicode_escape: If `True`, UTF-16 escape sequences will be decoded
            before parsing the pointer.
        uri_decode: If `True`, the pointer will be unescaped using _urllib_
            before being parsed.

    Returns:
        The object in _data_ pointed to by this pointer.

    Raises:
        JSONPointerIndexError: When attempting to access a sequence by
            an out of range index, unless a default is given.
        JSONPointerKeyError: If any mapping object along the path does not contain
            a specified key, unless a default is given.
        JSONPointerTypeError: When attempting to resolve a non-index string path
            part against a sequence, unless a default is given.
    """
    if isinstance(pointer, str):
        try:
            return JSONPointer(
                pointer, unicode_escape=unicode_escape, uri_decode=uri_decode
            ).resolve(data)
        except JSONPointerResolutionError:
            if default is not UNDEFINED:
                return default
            raise

    try:
        return JSONPointer.from_parts(
            pointer, unicode_escape=unicode_escape, uri_decode=uri_decode
        ).resolve(data)
    except JSONPointerResolutionError:
        if default is not UNDEFINED:
            return default
        raise
