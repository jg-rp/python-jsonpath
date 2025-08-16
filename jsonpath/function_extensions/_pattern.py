from typing import List


def map_re(pattern: str) -> str:
    escaped = False
    char_class = False
    parts: List[str] = []
    for ch in pattern:
        if escaped:
            parts.append(ch)
            escaped = False
            continue

        if ch == ".":
            if not char_class:
                parts.append(r"(?:(?![\r\n])\P{Cs}|\p{Cs}\p{Cs})")
            else:
                parts.append(ch)
        elif ch == "\\":
            escaped = True
            parts.append(ch)
        elif ch == "[":
            char_class = True
            parts.append(ch)
        elif ch == "]":
            char_class = False
            parts.append(ch)
        else:
            parts.append(ch)

    return "".join(parts)
