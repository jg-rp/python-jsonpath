import pytest

from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.exceptions import JSONPathTypeError


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def test_unclosed_selection_list(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError, match=r"unexpected end of selector list"):
        env.compile("$[1,2")


def test_function_missing_param(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathTypeError):
        env.compile("$[?(length()==1)]")


def test_function_too_many_params(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathTypeError):
        env.compile("$[?(length(@.a, @.b)==1)]")
