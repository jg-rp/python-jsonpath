import pytest

from jsonpath import JSONPatch
from jsonpath import JSONPatchError
from jsonpath import JSONPointerIndexError
from jsonpath import findall
from jsonpath import pointer


def test_issue_72_andy() -> None:
    query = "andy"
    data = {"andy": [1, 2, 3]}
    assert findall(query, data) == [[1, 2, 3]]


def test_issue_72_orders() -> None:
    query = "orders"
    data = {"orders": [1, 2, 3]}
    assert findall(query, data) == [[1, 2, 3]]


def test_issue_103() -> None:
    query = "$..book[?(@.borrowers[?(@.name == _.name)])]"
    data = {
        "store": {
            "book": [
                {
                    "category": "reference",
                    "author": "Nigel Rees",
                    "title": "Sayings of the Century",
                    "price": 8.95,
                },
                {
                    "category": "fiction",
                    "author": "Evelyn Waugh",
                    "title": "Sword of Honour",
                    "price": 12.99,
                    "borrowers": [
                        {"name": "John", "id": 101},
                        {"name": "Jane", "id": 102},
                    ],
                },
                {
                    "category": "fiction",
                    "author": "Herman Melville",
                    "title": "Moby Dick",
                    "isbn": "0-553-21311-3",
                    "price": 8.99,
                },
                {
                    "category": "fiction",
                    "author": "J. R. R. Tolkien",
                    "title": "The Lord of the Rings",
                    "isbn": "0-395-19395-8",
                    "price": 22.99,
                    "borrowers": [{"name": "Peter", "id": 103}],
                },
            ],
            "bicycle": {"color": "red", "price": 19.95},
        }
    }

    filter_context = {"name": "John"}

    want = [
        {
            "category": "fiction",
            "author": "Evelyn Waugh",
            "title": "Sword of Honour",
            "price": 12.99,
            "borrowers": [{"name": "John", "id": 101}, {"name": "Jane", "id": 102}],
        }
    ]

    assert findall(query, data, filter_context=filter_context) == want


def test_quoted_reserved_word_and() -> None:
    query = "$['and']"
    data = {"and": [1, 2, 3]}
    assert findall(query, data) == [[1, 2, 3]]


def test_quoted_reserved_word_or() -> None:
    query = "$['or']"
    data = {"or": [1, 2, 3]}
    assert findall(query, data) == [[1, 2, 3]]


def test_issue_115() -> None:
    data = {
        "users": [
            {"name": "Sue", "score": 100},
            {"name": "John", "score": 86},
            {"name": "Sally", "score": 84},
            {"name": "Jane", "score": 55},
        ]
    }

    assert pointer.resolve("/users/0/score", data) == 100  # noqa: PLR2004

    # Negative index
    with pytest.raises(JSONPointerIndexError):
        pointer.resolve("/users/-1/score", data)


def test_issue_117() -> None:
    # When the target value is an array of length 2, /foo/2 is the same as /foo/-
    patch = JSONPatch().add(path="/foo/2", value=99)
    data = {"foo": ["bar", "baz"]}
    assert patch.apply(data) == {"foo": ["bar", "baz", 99]}

    # Array length + 1 raises
    patch = JSONPatch().add(path="/foo/3", value=99)
    data = {"foo": ["bar", "baz"]}
    with pytest.raises(JSONPatchError):
        patch.apply(data)


def test_issue_124() -> None:
    query_raw = r"$[?@type =~ /studio\/material\/.*/]"
    query = "$[?@type =~ /studio\\/material\\/.*/]"

    data = [
        {"type": "studio/material/a"},
        {"type": "studio/material/b"},
        {"type": "studio foo"},
    ]

    want = [{"type": "studio/material/a"}, {"type": "studio/material/b"}]

    assert findall(query, data) == want
    assert findall(query_raw, data) == want
