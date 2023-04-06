"""Test Python JSONPath against the JSONPath Compliance Test Suite.

Assumes a version of the test suite is available in the current  working
directory as "cts.json".

See https://github.com/jsonpath-standard/jsonpath-compliance-test-suite.

We've deliberately named this file so as to exclude it when running `pytest`
or `hatch run test`. Target it specifically using `pytest tests/compliance.py`.
"""
import json
import operator
import unittest
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union

import pytest

import jsonpath


@dataclass
class Case:
    name: str
    selector: str
    document: Union[Mapping[str, Any], Sequence[Any], None] = None
    result: Any = None
    invalid_selector: Optional[bool] = None


SKIP = {
    "filter, nested": "not supported",
}


def cases() -> List[Case]:
    with open("cts.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    # TODO: skipping filter functions. Not supported.
    return [
        case
        for case in cases()
        if not case.invalid_selector and "function" not in case.name
    ]


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    assert case.document is not None

    test_case = unittest.TestCase()
    rv = jsonpath.findall(case.selector, case.document)
    test_case.assertCountEqual(rv, case.result)  # noqa: PT009
