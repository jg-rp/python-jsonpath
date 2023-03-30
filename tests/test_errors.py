import pytest

from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathSyntaxError


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def test_unclosed_selection_list(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError, match=r"unexpected end of selector list"):
        env.compile("$[1,2")
