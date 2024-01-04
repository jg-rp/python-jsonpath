import json
import timeit
from typing import Any
from typing import Mapping
from typing import NamedTuple
from typing import Sequence
from typing import Union

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

COMPILE_AND_FIND_SETUP = "from jsonpath import findall"

COMPILE_AND_FIND_STMT = """\
for query, data in QUERIES:
    findall(query, data)"""

JUST_COMPILE_SETUP = "from jsonpath import compile"

JUST_COMPILE_STMT = """\
for query, _ in QUERIES:
    compile(query)"""

JUST_FIND_SETUP = """\
from jsonpath import compile
compiled_queries = [(compile(q), d) for q, d in QUERIES]
"""

JUST_FIND_STMT = """\
for path, data in compiled_queries:
    path.findall(data)"""


def benchmark(number: int = 100, best_of: int = 3) -> None:
    print(
        f"repeating {len(QUERIES)} queries on small data {number} times, "
        f"best of {best_of} rounds"
    )

    results = timeit.repeat(
        COMPILE_AND_FIND_STMT,
        setup=COMPILE_AND_FIND_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("compile and find", results)

    results = timeit.repeat(
        JUST_COMPILE_STMT,
        setup=JUST_COMPILE_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("just compile", results)

    results = timeit.repeat(
        JUST_FIND_STMT,
        setup=JUST_FIND_SETUP,
        globals={"QUERIES": QUERIES},
        number=number,
        repeat=best_of,
    )

    print("just find", results)


if __name__ == "__main__":
    benchmark()
