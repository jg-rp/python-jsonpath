import asyncio
from typing import List

import pytest

import jsonpath


def test_convenience_compile() -> None:
    # Implicit root identifier works by default, but not when strict=True.
    path = jsonpath.compile("a.*")
    assert isinstance(path, jsonpath.JSONPath)
    assert path.findall({"a": [1, 2, 3]}) == [1, 2, 3]


def test_convenience_compile_strict() -> None:
    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.compile("a.*", strict=True)

    path = jsonpath.compile("$.a.*", strict=True)
    assert isinstance(path, jsonpath.JSONPath)
    assert path.findall({"a": [1, 2, 3]}) == [1, 2, 3]


def test_convenience_findall() -> None:
    assert jsonpath.findall("a.*", {"a": [1, 2, 3]}) == [1, 2, 3]


def test_convenience_findall_strict() -> None:
    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.findall("a.*", {"a": [1, 2, 3]}, strict=True)

    assert jsonpath.findall("$.a.*", {"a": [1, 2, 3]}, strict=True) == [1, 2, 3]


def test_convenience_findall_async() -> None:
    async def coro() -> List[object]:
        return await jsonpath.findall_async("a.*", {"a": [1, 2, 3]})

    assert asyncio.run(coro()) == [1, 2, 3]


def test_convenience_findall_async_strict() -> None:
    async def coro() -> List[object]:
        with pytest.raises(jsonpath.JSONPathSyntaxError):
            await jsonpath.findall_async("a.*", {"a": [1, 2, 3]}, strict=True)

        return await jsonpath.findall_async("$.a.*", {"a": [1, 2, 3]}, strict=True)

    assert asyncio.run(coro()) == [1, 2, 3]


def test_convenience_finditer() -> None:
    matches = list(jsonpath.finditer("a.*", {"a": [1, 2, 3]}))
    assert [m.obj for m in matches] == [1, 2, 3]


def test_convenience_finditer_strict() -> None:
    with pytest.raises(jsonpath.JSONPathSyntaxError):
        list(jsonpath.finditer("a.*", {"a": [1, 2, 3]}, strict=True))

    matches = list(jsonpath.finditer("$.a.*", {"a": [1, 2, 3]}, strict=True))
    assert [m.obj for m in matches] == [1, 2, 3]


def test_convenience_finditer_async_strict() -> None:
    async def coro() -> List[object]:
        with pytest.raises(jsonpath.JSONPathSyntaxError):
            await jsonpath.finditer_async("a.*", {"a": [1, 2, 3]}, strict=True)

        it = await jsonpath.finditer_async("$.a.*", {"a": [1, 2, 3]}, strict=True)
        return [m.obj async for m in it]

    assert asyncio.run(coro()) == [1, 2, 3]


def test_convenience_match() -> None:
    match = jsonpath.match("a.*", {"a": [1, 2, 3]})
    assert isinstance(match, jsonpath.JSONPathMatch)
    assert match.obj == 1


def test_convenience_match_strict() -> None:
    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.match("a.*", {"a": [1, 2, 3]}, strict=True)

    match = jsonpath.match("$.a.*", {"a": [1, 2, 3]})
    assert isinstance(match, jsonpath.JSONPathMatch)
    assert match.obj == 1


def test_convenience_query() -> None:
    query = jsonpath.query("a.*", {"a": [1, 2, 3]})
    assert isinstance(query, jsonpath.Query)
    assert list(query.values()) == [1, 2, 3]


def test_convenience_query_strict() -> None:
    with pytest.raises(jsonpath.JSONPathSyntaxError):
        jsonpath.query("a.*", {"a": [1, 2, 3]}, strict=True)

    query = jsonpath.query("$.a.*", {"a": [1, 2, 3]})
    assert isinstance(query, jsonpath.Query)
    assert list(query.values()) == [1, 2, 3]
