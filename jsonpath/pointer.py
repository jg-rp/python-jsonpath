"""JSON Pointer. See https://datatracker.ietf.org/doc/html/rfc6901."""
from __future__ import annotations

import codecs
import re
from functools import reduce
from operator import getitem
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import Union
from urllib.parse import unquote

from jsonpath._data import load_data
from jsonpath.exceptions import JSONPointerError
from jsonpath.exceptions import JSONPointerIndexError
from jsonpath.exceptions import JSONPointerKeyError
from jsonpath.exceptions import JSONPointerResolutionError
from jsonpath.exceptions import JSONPointerTypeError
from jsonpath.exceptions import RelativeJSONPointerIndexError
from jsonpath.exceptions import RelativeJSONPointerSyntaxError

if TYPE_CHECKING:
    from io import IOBase

    from .match import JSONPathMatch


class _Undefined:
    def __str__(self) -> str:
        return "<jsonpath.pointer.UNDEFINED>"


UNDEFINED = _Undefined()


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
        self._s = self._encode(self.parts)

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
            s = self._unicode_escape(s)

        s = s.lstrip()
        if s and not s.startswith("/"):
            raise JSONPointerError(
                "pointer must start with a slash or be the empty string"
            )

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
            # Handle non-standard keys/property selector/pointer.
            if (
                isinstance(key, str)
                and isinstance(obj, Mapping)
                and key.startswith((self.keys_selector, "#"))
                and key[1:] in obj
            ):
                return key[1:]
            # Handle non-standard index/property pointer (`#`)
            raise JSONPointerKeyError(key) from err
        except TypeError as err:
            if isinstance(obj, Sequence) and not isinstance(obj, str):
                if key == "-":
                    # "-" is a valid index when appending to a JSON array
                    # with JSON Patch, but not when resolving a JSON Pointer.
                    raise JSONPointerIndexError("index out of range") from None
                # Handle non-standard index pointer.
                if isinstance(key, str) and key.startswith("#"):
                    _index = int(key[1:])
                    if _index >= len(obj):
                        raise JSONPointerIndexError(
                            f"index out of range: {_index}"
                        ) from err
                    return _index
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
            raise JSONPointerTypeError(f"{key}: {err}") from err
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
        data = load_data(data)
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
                exists but the last object does not, `(parent, UNDEFINED)` will
                be returned.

        Raises:
            JSONPointerIndexError: When attempting to access a sequence by
                an out of range index, unless using the special `-` index.
            JSONPointerKeyError: If any mapping object along the path does not
                contain a specified key, unless it is the last part of the
                pointer.
            JSONPointerTypeError: When attempting to resolve a non-index string
                path part against a sequence.
        """
        if not self.parts:
            return (None, self.resolve(data))

        _data = load_data(data)
        parent = reduce(self._getitem, self.parts[:-1], _data)

        try:
            return (parent, self._getitem(parent, self.parts[-1]))
        except (JSONPointerIndexError, JSONPointerKeyError):
            return (parent, UNDEFINED)

    @staticmethod
    def _encode(parts: Iterable[Union[int, str]]) -> str:
        if parts:
            return "/" + "/".join(
                str(p).replace("~", "~0").replace("/", "~1") for p in parts
            )
        return ""

    def _unicode_escape(self, s: str) -> str:
        # UTF-16 escape sequences - possibly surrogate pairs - inside UTF-8
        # encoded strings. As per https://datatracker.ietf.org/doc/html/rfc4627
        # section 2.5.
        return (
            codecs.decode(s.replace("\\/", "/"), "unicode-escape")
            .encode("utf-16", "surrogatepass")
            .decode("utf-16")
        )

    @classmethod
    def from_match(
        cls,
        match: JSONPathMatch,
    ) -> JSONPointer:
        """Return a JSON Pointer for the path from a JSONPathMatch instance."""
        # A rfc6901 string representation of match.parts.
        if match.parts:
            pointer = cls._encode(match.parts)
        else:
            # This should not happen, unless the JSONPathMatch has been tampered with.
            pointer = ""

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

        Returns:
            A new `JSONPointer` built from _parts_.
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
            pointer = cls._encode(__parts)
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

    def __repr__(self) -> str:
        return f"JSONPointer({self._s!r})"

    def exists(
        self, data: Union[str, IOBase, Sequence[object], Mapping[str, object]]
    ) -> bool:
        """Return _True_ if this pointer can be resolved against _data_.

        Note that `JSONPointer.resolve()` can return legitimate falsy values
        that form part of the target JSON document. This method will return
        `True` if a falsy value is found.

        Args:
            data: The target JSON "document" or equivalent Python objects.

        Returns:
            _True_ if this pointer can be resolved against _data_, or _False_
                otherwise.

        **_New in version 0.9.0_**
        """
        try:
            self.resolve(data)
        except JSONPointerResolutionError:
            return False
        return True

    def parent(self) -> JSONPointer:
        """Return this pointer's parent, as a new `JSONPointer`.

        If this pointer points to the document root, _self_ is returned.

        **_New in version 0.9.0_**
        """
        if not self.parts:
            return self
        parent_parts = self.parts[:-1]
        return JSONPointer(
            self._encode(parent_parts),
            parts=parent_parts,
            unicode_escape=False,
            uri_decode=False,
        )

    def __truediv__(self, other: object) -> JSONPointer:
        """Join this pointer with _other_.

        _other_ is expected to be a JSON Pointer string, possibly without a
        leading slash. If _other_ does have a leading slash, the previous
        pointer is ignored and a new JSONPath is returned from _other_.

        _other_ should not be a "Relative JSON Pointer".
        """
        if not isinstance(other, str):
            raise TypeError(
                "unsupported operand type for /: "
                f"{self.__class__.__name__!r} and {other.__class__.__name__!r}"
            )

        other = self._unicode_escape(other.lstrip())
        if other.startswith("/"):
            return JSONPointer(other, unicode_escape=False, uri_decode=False)

        parts = self.parts + tuple(
            self._index(p.replace("~1", "/").replace("~0", "~"))
            for p in other.split("/")
        )

        return JSONPointer(
            self._encode(parts), parts=parts, unicode_escape=False, uri_decode=False
        )

    def join(self, *parts: str) -> JSONPointer:
        """Join this pointer with _parts_.

        Each part is expected to be a JSON Pointer string, possibly without a
        leading slash. If a part does have a leading slash, the previous
        pointer is ignored and a new `JSONPath` is created, and processing of
        remaining parts continues.
        """
        pointer = self
        for part in parts:
            pointer = pointer / part
        return pointer

    def to(
        self,
        rel: Union[RelativeJSONPointer, str],
        *,
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> JSONPointer:
        """Return a new pointer relative to this pointer.

        Args:
            rel: A `RelativeJSONPointer` or a string following "Relative JSON
                Pointer" syntax.
            unicode_escape: If `True`, UTF-16 escape sequences will be decoded
                before parsing the pointer.
            uri_decode: If `True`, the pointer will be unescaped using _urllib_
                before being parsed.

        See https://www.ietf.org/id/draft-hha-relative-json-pointer-00.html
        """
        relative_pointer = (
            RelativeJSONPointer(
                rel, unicode_escape=unicode_escape, uri_decode=uri_decode
            )
            if isinstance(rel, str)
            else rel
        )

        return relative_pointer.to(self)


RE_RELATIVE_POINTER = re.compile(
    r"(?P<ORIGIN>\d+)(?P<INDEX_G>(?P<SIGN>[+\-])(?P<INDEX>\d))?(?P<POINTER>.*)",
    re.DOTALL,
)


class RelativeJSONPointer:
    """A Relative JSON Pointer.

    See https://www.ietf.org/id/draft-hha-relative-json-pointer-00.html

    Args:
        rel: A string following Relative JSON Pointer syntax.
        unicode_escape: If `True`, UTF-16 escape sequences will be decoded
            before parsing the pointer.
        uri_decode: If `True`, the pointer will be unescaped using _urllib_
            before being parsed.
    """

    __slots__ = ("origin", "index", "pointer")

    def __init__(
        self,
        rel: str,
        *,
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> None:
        self.origin, self.index, self.pointer = self._parse(
            rel, unicode_escape=unicode_escape, uri_decode=uri_decode
        )

    def __str__(self) -> str:
        sign = "+" if self.index > 0 else ""
        index = "" if self.index == 0 else f"{sign}{self.index}"
        return f"{self.origin}{index}{self.pointer}"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, RelativeJSONPointer) and str(self) == str(__value)

    def _parse(
        self,
        rel: str,
        *,
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> Tuple[int, int, Union[JSONPointer, str]]:
        rel = rel.lstrip()
        match = RE_RELATIVE_POINTER.match(rel)
        if not match:
            raise RelativeJSONPointerSyntaxError("", rel)

        # Steps to move
        origin = self._zero_or_positive(match.group("ORIGIN"), rel)

        # Optional index manipulation
        if match.group("INDEX_G"):
            index = self._zero_or_positive(match.group("INDEX"), rel)
            if index == 0:
                raise RelativeJSONPointerSyntaxError("index offset can't be zero", rel)
            if match.group("SIGN") == "-":
                index = -index
        else:
            index = 0

        # Pointer or '#'. Empty string is OK.
        _pointer = match.group("POINTER").strip()
        pointer = (
            JSONPointer(
                _pointer,
                unicode_escape=unicode_escape,
                uri_decode=uri_decode,
            )
            if _pointer != "#"
            else _pointer
        )

        return (origin, index, pointer)

    def _zero_or_positive(self, s: str, rel: str) -> int:
        # TODO: accept start and stop index for better error messages
        if s.startswith("0") and len(s) > 1:
            raise RelativeJSONPointerSyntaxError("unexpected leading zero", rel)
        try:
            return int(s)
        except ValueError as err:
            raise RelativeJSONPointerSyntaxError(
                "expected positive int or zero", rel
            ) from err

    def _int_like(self, obj: Any) -> bool:
        if isinstance(obj, int):
            return True
        try:
            int(obj)
        except ValueError:
            return False
        return True

    def to(
        self,
        pointer: Union[JSONPointer, str],
        *,
        unicode_escape: bool = True,
        uri_decode: bool = False,
    ) -> JSONPointer:
        """Return a new JSONPointer relative to _pointer_.

        Args:
            pointer: A `JSONPointer` instance or a string following JSON
                Pointer syntax.
            unicode_escape: If `True`, UTF-16 escape sequences will be decoded
                before parsing the pointer.
            uri_decode: If `True`, the pointer will be unescaped using _urllib_
                before being parsed.
        """
        _pointer = (
            JSONPointer(pointer, unicode_escape=unicode_escape, uri_decode=uri_decode)
            if isinstance(pointer, str)
            else pointer
        )

        # Move to origin
        if self.origin > len(_pointer.parts):
            raise RelativeJSONPointerIndexError(
                f"origin ({self.origin}) exceeds root ({len(_pointer.parts)})"
            )

        if self.origin < 1:
            parts = list(_pointer.parts)
        else:
            parts = list(_pointer.parts[: -self.origin])

        # Array index offset
        if self.index and parts and self._int_like(parts[-1]):
            new_index = int(parts[-1]) + self.index
            if new_index < 0:
                raise RelativeJSONPointerIndexError(
                    f"index offset out of range {new_index}"
                )
            parts[-1] = int(parts[-1]) + self.index

        # Pointer or index/property
        if isinstance(self.pointer, JSONPointer):
            parts.extend(self.pointer.parts)
        else:
            assert self.pointer == "#"
            parts[-1] = f"#{parts[-1]}"

        return JSONPointer.from_parts(
            parts, unicode_escape=unicode_escape, uri_decode=uri_decode
        )


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
