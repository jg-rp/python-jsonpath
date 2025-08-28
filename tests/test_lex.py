import json
import operator
from typing import Any
from typing import Dict

import pytest

from jsonpath import DEFAULT_ENV
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.token import Token

with open("tests/test_lex.json", encoding="UTF-8") as fd:
    """Loads the test case data. Each test case is:
    description: str
    path: str
    want: List[Token]
    """
    CASES = json.load(fd)["tests"]


@pytest.mark.parametrize("case", CASES, ids=operator.itemgetter("description"))
def test_default_lexer(case: Dict[str, Any]) -> None:
    tokens = list(DEFAULT_ENV.lexer.tokenize(case["path"]))
    want = [Token(**token) for token in case["want"]]
    assert tokens == want


def test_illegal_token() -> None:
    with pytest.raises(JSONPathSyntaxError):
        list(DEFAULT_ENV.lexer.tokenize("%"))
