"""Extra filter context test cases."""
import pytest

from jsonpath import JSONPathEnvironment


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def test_filter_context_selector_in_filter_function(env: JSONPathEnvironment) -> None:
    """Test that we can pass extra filter context to findall."""
    rv = env.findall(
        "$[?(@.some == length(_.other))]",
        {"foo": {"some": 1, "thing": 2}},
        filter_context={"other": ["a"]},
    )
    assert rv == [{"some": 1, "thing": 2}]
