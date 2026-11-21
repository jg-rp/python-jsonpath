"""Replace UTF-16 escape sequences with Unicode characters."""

import re

from .exceptions import JSONPathSyntaxError
from .token import Token

_RE_ESCAPE_U = re.compile(r"(\\u[0-9a-fA-F]{4}|\\.)")
_RE_INVALID_CHARACTER = re.compile("[\u0000-\u001f]")


def unescape_string(value: str, token: Token, quote: str) -> str:
    """Return `value` with escape sequences replaced with Unicode code points."""
    if _RE_INVALID_CHARACTER.search(value):
        raise JSONPathSyntaxError("invalid character", token=token)

    if "\\" not in value:
        return value

    return _unescape(value, token, quote)


def _unescape(escaped: str, token: Token, quote: str) -> str:  # noqa: PLR0912
    unescaped: list[str] = []
    parts = [p for p in _RE_ESCAPE_U.split(escaped) if p]
    length = len(parts)
    pos = 0

    while pos < length:
        part = parts[pos]
        pos += 1

        if not part.startswith("\\"):
            unescaped.append(part)
        elif part == '\\"' and quote == '"':
            unescaped.append('"')
        elif part == "\\'" and quote == "'":
            unescaped.append("'")
        elif part == "\\\\":
            unescaped.append("\\")
        elif part == "\\/":
            unescaped.append("/")
        elif part == "\\b":
            unescaped.append("\b")
        elif part == "\\f":
            unescaped.append("\f")
        elif part == "\\n":
            unescaped.append("\n")
        elif part == "\\r":
            unescaped.append("\r")
        elif part == "\\t":
            unescaped.append("\t")
        elif part == "\\u":
            # Subsequent \u is guaranteed to be followed by four hex digits.
            raise JSONPathSyntaxError("invalid escape sequence", token=token)
        elif part.startswith("\\u"):
            code_point = int(part[2:], 16)  # noqa: FURB166

            if _is_low_surrogate(code_point):
                raise JSONPathSyntaxError("invalid escape sequence", token=token)

            if _is_high_surrogate(code_point):
                if pos >= length:
                    raise JSONPathSyntaxError("invalid escape sequence", token=token)

                next_part = parts[pos]
                pos += 1

                if not (len(next_part) == 6 and next_part.startswith("\\u")):
                    raise JSONPathSyntaxError("invalid escape sequence", token=token)

                low_surrogate = int(next_part[2:], 16)  # noqa: FURB166

                if not _is_low_surrogate(low_surrogate):
                    raise JSONPathSyntaxError("invalid escape sequence", token=token)

                code_point = 0x10000 + (
                    ((code_point & 0x03FF) << 10) | (low_surrogate & 0x03FF)
                )

            unescaped.append(chr(code_point))
        else:
            raise JSONPathSyntaxError("invalid escape sequence", token=token)

    return "".join(unescaped)


def _is_high_surrogate(codepoint: int) -> bool:
    return 0xD800 <= codepoint <= 0xDBFF


def _is_low_surrogate(codepoint: int) -> bool:
    return 0xDC00 <= codepoint <= 0xDFFF
