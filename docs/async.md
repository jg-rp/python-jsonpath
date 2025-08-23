# Async API

Largely motivated by its integration with [Python Liquid](https://jg-rp.github.io/liquid/jsonpath/introduction), Python JSONPath offers an asynchronous API that allows for items in a target data structure to be "fetched" lazily.

[`findall_async()`](api.md#jsonpath.JSONPathEnvironment.findall_async) and [`finditer_async()`](api.md#jsonpath.JSONPathEnvironment.finditer_async) are [asyncio](https://docs.python.org/3/library/asyncio.html) equivalents to [`findall()`](api.md#jsonpath.JSONPathEnvironment.findall) and [`finditer()`](api.md#jsonpath.JSONPathEnvironment.finditer). By default, any class implementing the [mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) or [sequence](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence) interfaces, and a `__getitem_async__()` method, will have `__getitem_async__()` awaited instead of calling `__getitem__()` when resolving mapping keys or sequence indices.

## Example

In this example, showing a lazy-loading collections of `Player` objects, only the "A" team's players are fetched from the database, and only when they are first accessed.

```python
from collections import abc
from dataclasses import dataclass
from typing import Dict
from typing import Iterator
from typing import List

import jsonpath


@dataclass
class Player:
    name: str
    pid: int
    rank: int


class LazyPlayers(abc.Mapping[str, Player]):
    def __init__(self, names: List[str]):
        self.names = names
        self.cached_players: Dict[str, Player] = {}

    def __len__(self) -> int:
        return len(self.names)

    def __iter__(self) -> Iterator[str]:
        return iter(self.names)

    def __getitem__(self, k: str) -> Player:
        if self.cached_players is None:
            # Blocking IO here
            self.cached_players = get_stuff_from_database()
        return self.cached_players[k]

    async def __getitem_async__(self, k: str) -> Player:
        if self.cached_players is None:
            # Do async IO here.
            self.cached_players = await get_stuff_from_database_async()
        return self.cached_players[k]


data = {
    "teams": {
        "A Team": LazyPlayers(["Sue", "Bob"]),
        "B Team": LazyPlayers(["Sally", "Frank"]),
    }
}

best_a_team_players = jsonpath.findall_async("$.teams['A Team'][?rank >= 8]", data)

```
