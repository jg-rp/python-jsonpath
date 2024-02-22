"""JSONPathEnvironment API test cases."""
import asyncio
from typing import List

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath import JSONPathSyntaxError
from jsonpath import JSONPathTypeError


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def test_find_all_from_object(env: JSONPathEnvironment) -> None:
    """Test that we can pass a Python object to findall."""
    rv = env.findall("$.some", {"some": 1, "thing": 2})
    assert rv == [1]


def test_find_all_from_json_string(env: JSONPathEnvironment) -> None:
    """Test that we can pass a JSON string to findall."""
    rv = env.findall("$.some", '{"some": 1, "thing": 2}')
    assert rv == [1]


def test_find_all_with_extra_filter_context(env: JSONPathEnvironment) -> None:
    """Test that we can pass extra filter context to findall."""
    rv = env.findall(
        "$[?(@.some == _.other)]",
        {"foo": {"some": 1, "thing": 2}},
        filter_context={"other": 1},
    )
    assert rv == [{"some": 1, "thing": 2}]


def test_find_iter_from_object(env: JSONPathEnvironment) -> None:
    """Test that we can pass a Python object to finditer."""
    matches = env.finditer("$.some", {"some": 1, "thing": 2})
    assert [match.obj for match in matches] == [1]


def test_find_iter_from_json_string(env: JSONPathEnvironment) -> None:
    """Test that we can pass a JSON string to finditer."""
    matches = env.finditer("$.some", '{"some": 1, "thing": 2}')
    assert [match.obj for match in matches] == [1]


def test_find_iter_with_extra_filter_context(env: JSONPathEnvironment) -> None:
    """Test that we can pass extra filter context to finditer."""
    matches = env.finditer(
        "$[?(@.some == _.other)]",
        {"foo": {"some": 1, "thing": 2}},
        filter_context={"other": 1},
    )
    assert [match.obj for match in matches] == [{"some": 1, "thing": 2}]


def test_find_all_async_from_object(env: JSONPathEnvironment) -> None:
    """Test that we can pass a Python object to findall_async."""

    async def coro() -> List[object]:
        return await env.findall_async("$.some", {"some": 1, "thing": 2})

    assert asyncio.run(coro()) == [1]


def test_find_all_async_from_json_string(env: JSONPathEnvironment) -> None:
    """Test that we can pass a JSON string to findall."""

    async def coro() -> List[object]:
        return await env.findall_async("$.some", '{"some": 1, "thing": 2}')

    assert asyncio.run(coro()) == [1]


def test_find_all_async_with_extra_filter_context(env: JSONPathEnvironment) -> None:
    """Test that we can pass extra filter context to findall_async."""

    async def coro() -> List[object]:
        return await env.findall_async(
            "$[?(@.some == _.other)]",
            {"foo": {"some": 1, "thing": 2}},
            filter_context={"other": 1},
        )

    assert asyncio.run(coro()) == [{"some": 1, "thing": 2}]


def test_find_iter_async_from_object(env: JSONPathEnvironment) -> None:
    """Test that we can pass a Python object to finditer."""

    async def coro() -> List[object]:
        matches = await env.finditer_async("$.some", {"some": 1, "thing": 2})
        return [match.obj async for match in matches]

    assert asyncio.run(coro()) == [1]


def test_find_iter_async_from_json_string(env: JSONPathEnvironment) -> None:
    """Test that we can pass a JSON string to finditer."""

    async def coro() -> List[object]:
        matches = await env.finditer_async("$.some", '{"some": 1, "thing": 2}')
        return [match.obj async for match in matches]

    assert asyncio.run(coro()) == [1]


def test_find_iter_async_with_extra_filter_context(env: JSONPathEnvironment) -> None:
    """Test that we can pass extra filter context to finditer."""

    async def coro() -> List[object]:
        matches = await env.finditer_async(
            "$[?(@.some == _.other)]",
            {"foo": {"some": 1, "thing": 2}},
            filter_context={"other": 1},
        )
        return [match.obj async for match in matches]

    assert asyncio.run(coro()) == [{"some": 1, "thing": 2}]


def test_match(env: JSONPathEnvironment) -> None:
    """Test that we can get the first match of a path."""
    match = env.match("$.some", {"some": 1, "thing": 2})
    assert match is not None
    assert match.obj == 1


def test_no_match(env: JSONPathEnvironment) -> None:
    """Test that we get `None` if there are no matches."""
    match = env.match("$.other", {"some": 1, "thing": 2})
    assert match is None


def test_match_compound_path(env: JSONPathEnvironment) -> None:
    """Test that we can get the first match of a compound path."""
    match = env.match("$.some | $.thing", {"some": 1, "thing": 2})
    assert match is not None
    assert match.obj == 1


def test_no_match_compound_path(env: JSONPathEnvironment) -> None:
    """Test that we get `None` if there are no matches in a compound path."""
    match = env.match("$.other | $.foo", {"some": 1, "thing": 2})
    assert match is None


def test_no_unicode_escape() -> None:
    """Test that we can disable decoding of UTF-16 escape sequences."""
    document = {"𝄞": "A"}
    selector = '$["\\uD834\\uDD1E"]'

    env = JSONPathEnvironment(unicode_escape=True)
    assert env.findall(selector, document) == ["A"]

    env = JSONPathEnvironment(unicode_escape=False)
    assert env.findall(selector, document) == []
    assert env.findall(selector, {"\\uD834\\uDD1E": "B"}) == ["B"]


def test_custom_keys_selector_token() -> None:
    """Test that we can change the non-standard keys selector."""

    class MyJSONPathEnvironment(JSONPathEnvironment):
        keys_selector_token = "*~"

    env = MyJSONPathEnvironment()
    data = {"foo": {"a": 1, "b": 2, "c": 3}}
    assert env.findall("$.foo.*~", data) == ["a", "b", "c"]
    assert env.findall("$.foo.*", data) == [1, 2, 3]


def test_custom_fake_root_identifier_token() -> None:
    """Test that we can change the non-standard fake root identifier."""

    class MyJSONPathEnvironment(JSONPathEnvironment):
        fake_root_token = "$$"

    env = MyJSONPathEnvironment()
    data = {"foo": {"a": 1, "b": 2, "c": 3}}
    assert env.findall("$$[?@.foo.a == 1]", data) == [data]
    assert env.findall("$$[?@.foo.a == 7]", data) == []
    assert env.findall("$.*", data) == [{"a": 1, "b": 2, "c": 3}]


def test_disable_fake_root_identifier() -> None:
    """Test that we can disable the non-standard fake root identifier."""

    class MyJSONPathEnvironment(JSONPathEnvironment):
        fake_root_token = ""

    env = MyJSONPathEnvironment()
    with pytest.raises(JSONPathSyntaxError):
        env.compile("^[?@.a == 42]")


def test_disable_keys_selector() -> None:
    """Test that we can disable the non-standard keys selector."""

    class MyJSONPathEnvironment(JSONPathEnvironment):
        keys_selector_token = ""

    env = MyJSONPathEnvironment()
    with pytest.raises(JSONPathSyntaxError):
        env.compile("*..~")


def test_disable_well_typed_checks() -> None:
    """Test that we can disable checks for well-typedness."""
    env = JSONPathEnvironment(well_typed=True)
    with pytest.raises(JSONPathTypeError):
        env.compile("$[?@.* > 2]")

    env = JSONPathEnvironment(well_typed=False)
    env.compile("$[?@.* > 2]")
