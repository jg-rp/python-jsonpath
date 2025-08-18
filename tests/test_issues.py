from jsonpath import findall


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
