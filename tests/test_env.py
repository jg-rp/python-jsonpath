"""JSONPathEnvironment API test cases."""
import asyncio
from typing import List

import pytest

from jsonpath import JSONPathEnvironment


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
        "$[?(@.some == #.other)]",
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
        "$[?(@.some == #.other)]",
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
            "$[?(@.some == #.other)]",
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
            "$[?(@.some == #.other)]",
            {"foo": {"some": 1, "thing": 2}},
            filter_context={"other": 1},
        )
        return [match.obj async for match in matches]

    assert asyncio.run(coro()) == [{"some": 1, "thing": 2}]
