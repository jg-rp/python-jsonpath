# Singular Query Selector

The singular query selector consist of an embedded absolute singular query, the result of which is used as an object member name or array element index.

If the embedded query resolves to a string or int value, at most one object member value or array element value is selected. Otherwise the singular query selector selects nothing.

## Syntax

```
selector                = name-selector /
                          wildcard-selector /
                          slice-selector /
                          index-selector /
                          filter-selector /
                          singular-query-selector

singular-query-selector = abs-singular-query
```

## Examples

```json
{
  "a": {
    "j": [1, 2, 3],
    "p": {
      "q": [4, 5, 6]
    }
  },
  "b": ["j", "p", "q"],
  "c d": {
    "x": {
      "y": 1
    }
  }
}
```

| Query                 | Result             | Result Path      | Comment                                                           |
| --------------------- | ------------------ | ---------------- | ----------------------------------------------------------------- |
| `$.a[$.b[1]]`         | `{"q": [4, 5, 6]}` | `$['a']['p']`    | Object name from embedded singular query                          |
| `$.a.j[$['c d'].x.y]` | `2`                | `$['a']['j'][1]` | Array index from embedded singular query                          |
| `$.a[$.b]`            |                    |                  | Embedded singular query does not resolve to a string or int value |
