from typing import Tuple

_VALID_UNICODE_CATEGORIES = frozenset(
    [
        "L",
        "M",
        "N",
        "P",
        "S",
        "Z",
        "C",
        "Lu",
        "Ll",
        "Lt",
        "Lm",
        "Lo",
        "Mn",
        "Mc",
        "Me",
        "Nd",
        "Nl",
        "No",
        "Pc",
        "Pd",
        "Ps",
        "Pe",
        "Pi",
        "Pf",
        "Po",
        "Sm",
        "Sc",
        "Sk",
        "So",
        "Zs",
        "Zl",
        "Zp",
        "Cc",
        "Cf",
        "Cn",
        "Co",
        "Cs",
    ]
)

_ALLOWED_SINGLE_CHAR_ESCAPES = frozenset("()*+-.?[\\]^nrt{|}")


def check_iregexp(pattern: str) -> bool:  # noqa: PLR0911, PLR0912
    """Return True if `pattern` conforms to RFC 9485, or False otherwise."""
    pos = 0
    length = len(pattern)
    group_depth = 0
    expect_atom = True

    while pos < length:
        ch = pattern[pos]

        if ch == "(":
            group_depth += 1
            pos += 1
            expect_atom = True

        elif ch == ")":
            if group_depth == 0:
                return False
            group_depth -= 1
            pos += 1
            expect_atom = False

        # Branch
        elif ch == "|":
            pos += 1
            expect_atom = True

        # Single-character quantifiers
        elif ch in "*+?":
            if expect_atom:
                return False
            pos += 1
            expect_atom = True  # Disallow stacked quantifiers like '++' or '*+'

        # Range quantifiers {n}, {n,}, {n,m}
        elif ch == "{":
            if expect_atom:
                return False
            pos = _check_range_quantifier(pattern, pos + 1, length)
            if pos == -1:
                return False
            expect_atom = True

        # Character classes [...]
        elif ch == "[":
            pos = _check_char_class(pattern, pos + 1, length)
            if pos == -1:
                return False
            expect_atom = False

        # Escape sequences (\)
        elif ch == "\\":
            pos = _check_escape(pattern, pos + 1, length)
            if pos == -1:
                return False
            expect_atom = False

        # Disallowed unescaped closing symbols
        elif ch in "]}":
            return False

        # Literal character
        else:
            pos += 1
            expect_atom = False

    return group_depth == 0


def _check_char_class(pattern: str, pos: int, length: int) -> int:  # noqa: PLR0911
    if pos >= length:
        return -1

    if pattern[pos] == "^":
        pos += 1

    has_item = False

    # Optional leading '-'
    if pos < length and pattern[pos] == "-":
        has_item = True
        pos += 1

    while pos < length:
        ch = pattern[pos]

        if ch == "]":
            return (pos + 1) if has_item else -1

        # Optional trailing '-' right before ']'
        if ch == "-" and pos + 1 < length and pattern[pos + 1] == "]":
            return pos + 2

        # Parse CCE1 atom
        pos, is_cc = _parse_cc_atom(pattern, pos, length)
        if pos == -1:
            return -1

        has_item = True

        # Check for range: CCchar "-" CCchar
        if is_cc and pos < length and pattern[pos] == "-":
            if pos + 1 < length and pattern[pos + 1] == "]":
                # Trailing '-'
                return pos + 2

            pos += 1  # Skip range '-'
            pos, is_cc = _parse_cc_atom(pattern, pos, length)
            if pos == -1 or not is_cc:
                return -1

    return -1


def _parse_cc_atom(pattern: str, pos: int, length: int) -> Tuple[int, bool]:  # noqa: PLR0911
    """Return (next_pos, is_ccchar)."""
    if pos >= length:
        return -1, False

    ch = pattern[pos]
    if ch == "\\":
        if pos + 1 >= length:
            return -1, False

        esc = pattern[pos + 1]

        if esc in _ALLOWED_SINGLE_CHAR_ESCAPES:
            return pos + 2, True  # SingleCharEsc is a valid CCchar

        if esc in "pP":
            if pos + 2 >= length or pattern[pos + 2] != "{":
                return -1, False

            close_b = pattern.find("}", pos + 3)
            if close_b == -1:
                return -1, False

            if pattern[pos + 3 : close_b] not in _VALID_UNICODE_CATEGORIES:
                return -1, False

            return (close_b + 1, False)

        return -1, False

    if ch in "-[]":
        # Unescaped '-', '[', and ']' are excluded from CCchar
        return -1, False

    return pos + 1, True


def _check_escape(pattern: str, pos: int, length: int) -> int:  # noqa: PLR0911
    if pos >= length:
        return -1

    esc = pattern[pos]

    if esc in _ALLOWED_SINGLE_CHAR_ESCAPES:
        return pos + 1

    if esc in "pP":
        pos += 1
        if pos >= length or pattern[pos] != "{":
            return -1
        pos += 1
        close_bracket = pattern.find("}", pos)
        if close_bracket == -1:
            return -1

        prop_name = pattern[pos:close_bracket]
        if prop_name not in _VALID_UNICODE_CATEGORIES:
            return -1

        return close_bracket + 1

    return -1


def _check_range_quantifier(pattern: str, pos: int, length: int) -> int:
    has_initial_digits = False
    comma_found = False

    while pos < length:
        ch = pattern[pos]

        if ch.isdigit():
            if not comma_found:
                has_initial_digits = True
            pos += 1

        elif ch == ",":
            if comma_found or not has_initial_digits:
                return -1
            comma_found = True
            pos += 1

        elif ch == "}":
            if not has_initial_digits:
                return -1
            return pos + 1

        else:
            return -1

    return -1


def map_iregexp(pattern: str, *, escape_anchors: bool = True, wrap: bool = True) -> str:
    r"""Map I-Regexp `pattern` to a "regex" pattern.

    Assumes `pattern` has already passed RFC 9485 validation.

    Arguments:
        pattern: A regular expression pattern following RFC 9485 syntax.
        escape_anchors: When True, treat `^` and `$` as normal characters.
        wrap: When True, wrap the result in `^(?:` and `)$`.

    Returns:
        A regular expression pattern suitable for the "regex" package. The result
            is not guaranteed to be compatible with Python's "re" module due to the
            lack of support for `\p{..}` and `\P{..}` escape sequences.
    """
    out = ["^(?:"] if wrap else []
    pos = 0
    length = len(pattern)

    while pos < length:
        ch = pattern[pos]

        # Dot outside character classes maps to [^\n\r]
        if ch == ".":
            out.append(r"[^\n\r]")
            pos += 1

        # Literal ^ and $ outside char classes must be escaped
        elif escape_anchors and ch in "^$":
            out.append("\\")
            out.append(ch)
            pos += 1

        elif ch == "[":
            out.append("[")
            pos += 1
            while pos < length:
                c = pattern[pos]
                out.append(c)
                pos += 1
                if c == "\\":
                    if pos < length:
                        out.append(pattern[pos])
                        pos += 1
                elif c == "]":
                    break

        elif ch == "\\":
            out.append("\\")
            pos += 1
            if pos < length:
                out.append(pattern[pos])
                pos += 1

        # 5. All other literal characters
        else:
            out.append(ch)
            pos += 1

    if wrap:
        out.append(")$")

    return "".join(out)
