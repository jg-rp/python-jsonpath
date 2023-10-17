import cProfile
import json
import sys
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import NamedTuple
from typing import Sequence
from typing import Union

from jsonpath import compile
from jsonpath import findall

# ruff: noqa: D100 D101 D103 T201


class CTSCase(NamedTuple):
    query: str
    data: Union[Sequence[Any], Mapping[str, Any]]


def valid_queries() -> Sequence[CTSCase]:
    with open("tests/cts/cts.json") as fd:
        data = json.load(fd)

    return [
        (CTSCase(t["selector"], t["document"]))
        for t in data["tests"]
        if not t.get("invalid_selector", False)
    ]


QUERIES = valid_queries()

COMPILE_AND_FIND_STMT = """\
for _ in range(100):
    for query, data in QUERIES:
        findall(query, data)"""


JUST_COMPILE_STMT = """\
for _ in range(100):
    for query, _ in QUERIES:
        compile(query)"""

JUST_FIND_STMT = """\
for _ in range(100):
    for path, data in compiled_queries:
        path.findall(data)"""


def profile_compile_and_find() -> None:
    cProfile.runctx(
        COMPILE_AND_FIND_STMT,
        globals={"findall": findall, "QUERIES": QUERIES},
        locals={},
        sort="cumtime",
    )


def profile_just_compile() -> None:
    cProfile.runctx(
        JUST_COMPILE_STMT,
        globals={"compile": compile, "QUERIES": QUERIES},
        locals={},
        sort="cumtime",
    )


def profile_just_find() -> None:
    compiled_queries = [(compile(q), d) for q, d in QUERIES]

    cProfile.runctx(
        JUST_FIND_STMT,
        globals={"compiled_queries": compiled_queries},
        locals={},
        sort="cumtime",
    )


if __name__ == "__main__":
    file_path = Path(__file__)
    usage = (
        f"usage: {file_path.name} (--compile-and-find | --just-find | --just-compile)\n"
    )

    if len(sys.argv) < 2:  # noqa: PLR2004
        sys.stderr.write(usage)
        sys.exit(1)

    arg = sys.argv[1]
    if arg == "--compile-and-find":
        profile_compile_and_find()
    elif arg == "--just-find":
        profile_just_find()
    elif arg == "--just-compile":
        profile_just_compile()
    else:
        sys.stderr.write(usage)
        sys.exit(1)
