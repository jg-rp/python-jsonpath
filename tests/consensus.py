"""Test Python JSONPath against the json-path-comparison project's regression suite.

Assumes a version of the regression suite is available in the current working
directory as "comparison_regression_suite.yaml".

See https://github.com/cburgmer/json-path-comparison.

We've deliberately named this file so as to exclude it when running `pytest` or
`hatch run test`. Target it specifically using `pytest tests/consensus.py`.
"""
import operator
import unittest
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union

import pytest
from yaml import safe_load

import jsonpath


@dataclass
class Query:
    id: str  # noqa: A003
    selector: str
    document: Union[Mapping[str, Any], Sequence[Any]]
    consensus: Any = None
    not_found_consensus: Any = None
    scalar_not_found_consensus: Any = None
    scalar_consensus: Any = None
    ordered: Optional[bool] = None


RENAME_MAP = {
    "not-found-consensus": "not_found_consensus",
    "scalar-not-found-consensus": "scalar_not_found_consensus",
    "scalar-consensus": "scalar_consensus",
}

SKIP = {
    "bracket_notation_with_number_on_object": "Bad consensus",
    "bracket_notation_with_number_on_string": "Invalid document",
    "dot_notation_with_number_-1": "Unexpected token",
    "dot_notation_with_number_on_object": "conflict with compliance",
}


def clean_query(query: Dict[str, Any]) -> Dict[str, Any]:
    # Replace hyphens with underscores in dict names.
    for old, new in RENAME_MAP.items():
        if old in query:
            query[new] = query[old]
            del query[old]
    return query


def queries() -> List[Query]:
    with open("comparison_regression_suite.yaml", encoding="utf8") as fd:
        data = safe_load(fd)
    return [Query(**clean_query(q)) for q in data["queries"]]


QUERIES_WITH_CONSENSUS = [
    q for q in queries() if q.consensus is not None and q.consensus != "NOT_SUPPORTED"
]


@pytest.mark.parametrize("query", QUERIES_WITH_CONSENSUS, ids=operator.attrgetter("id"))
def test_consensus(query: Query) -> None:
    if query.id in SKIP:
        pytest.skip(reason=SKIP[query.id])
    case = unittest.TestCase()
    rv = jsonpath.findall(query.selector, query.document)
    case.assertCountEqual(rv, query.consensus)  # noqa: PT009
