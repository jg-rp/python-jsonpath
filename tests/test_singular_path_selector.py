import json
import operator

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath import NodeList

from ._cts_case import Case


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment(strict=False)


with open("tests/singular_path_selector.json", encoding="utf8") as fd:
    data = [Case(**case) for case in json.load(fd)["tests"]]


@pytest.mark.parametrize("case", data, ids=operator.attrgetter("name"))
def test_singular_path_selector(env: JSONPathEnvironment, case: Case) -> None:
    assert case.document is not None
    nodes = NodeList(env.finditer(case.selector, case.document))

    if case.results is not None:
        assert case.results_paths is not None
        assert nodes.values() in case.results
        assert nodes.paths() in case.results_paths
    else:
        assert case.result_paths is not None
        assert nodes.values() == case.result
        assert nodes.paths() == case.result_paths
