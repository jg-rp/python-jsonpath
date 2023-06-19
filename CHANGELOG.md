# Python JSONPath Change Log

## Version 0.8.0 (unreleased)

**Breaking changes**

- Changed the `JSONPathMatch.parts` representation of the non-standard _keys_ selector (default `~`) to be `~` followed by the key name. It used to be two "parts", `~` and key index.

**Fixes**

- Changed `findall()` and `finditer()` to accept `data` arguments of any `io.IOBase` subclass, not just `TextIO`.

**Features**

- Added the `JSONPointer` class and methods for converting a `JSONPathMatch` to a `JSONPointer`.
- Added `jsonpath.resolve()`, a convenience function for resolving a [JSON Pointer](https://datatracker.ietf.org/doc/html/rfc6901).
- Added `jsonpath.match()`, which returns a `JSONPathMatch` instance for the first match of a path, or `None` if there were no matches.
- All selectors now use `env.match_class` to instantiate new `JSONPathMatch` objects. This allows for subclassing of `JSONPathMatch`.

## Version 0.7.1

**Fixes**

- Fixed a bug with the filter context selector (default `_`) when it's used as a filter function argument.

## Version 0.7.0

**Breaking changes**

- `JSONPathIndexError` now requires a `token` parameter. It used to be optional.
- Filter expressions that resolve JSON paths (like `SelfPath` and `RootPath`) now return a `NodeList`. The node list must then be explicitly unpacked by `JSONPathEnvironment.compare()` and any filter function that has a `with_node_lists` attribute set to `True`. This is done for the benefit of the `count()` filter function and standards compliance.

**Features**

- `missing` is now an allowed alias of `undefined` when using the `isinstance()` filter function.

**IETF JSONPath Draft compliance**

- The built-in `count()` filter function is now compliant with the standard, operating on a "nodelist" instead of node values.

## Version 0.6.0

**Breaking changes**

- The "extra filter context" identifier now defaults to `_`. Previously it defaulted to `#`, but it has been decided that `#` is better suited as a current key/property or index identifier.

**Features**

- Added a non-standard keys/properties selector ([docs](https://jg-rp.github.io/python-jsonpath/syntax/#keys-or), [source](https://github.com/jg-rp/python-jsonpath/blob/main/jsonpath/selectors.py#L193)).
- Added a non-standard `typeof()` filter function. `type()` is an alias for `typeof()` ([docs](https://jg-rp.github.io/python-jsonpath/functions/#typeof), [source](https://github.com/jg-rp/python-jsonpath/blob/main/jsonpath/function_extensions/typeof.py)).
- Added a non-standard `isinstance()` filter function. `is()` is an alias for `isinstance()` ([docs](https://jg-rp.github.io/python-jsonpath/functions/#isinstance), [source](https://github.com/jg-rp/python-jsonpath/blob/main/jsonpath/function_extensions/is_instance.py)).
- Added a current key/property or index identifier. When filtering a mapping, `#` will hold key associated with the current node (`@`). When filtering a sequence, `#` will hold the current index. See [docs](https://jg-rp.github.io/python-jsonpath/syntax/#filters-expression).

**IETF JSONPath Draft compliance**

- Don't allow leading zeros in index selectors. We now raise a `JSONPathSyntaxError`.
- Validate the built-in `count()` function's argument is array-like.

## Version 0.5.0

**Features**

- Added the built-in `match` filter function.
- Added the built-in `search` filter function.
- Added the built-in `value` filter function.
- Pass the current environment to filter function validation.
- Added support for the wildcard selector in selector segment lists.

**Fixes**

- Fixed a bug where the current object identifier (`@`) would evaluate to `undefined` when a filter is applied to an array of strings.
- Compound paths that have a trailing `|` or `&` now raise a `JSONPathSyntaxError`.

**IETF JSONPath Draft compliance**

- Removed support for dotted index selectors.
- Raise a `JSONPathSyntaxError` for unescaped whitespace and control characters.
- Raise a `JSONPathSyntaxError` for empty selector segments.
- Raise a `JSONPathIndexError` if an index selector is out of range.
- Raise a `JSONPathSyntaxError` for too many colons in a slice selector.
- Raise a `JSONPathIndexError` if a slice selector argument is out of range.
- Allow nested filters.

## Version 0.4.0

**IETF JSONPath Draft compliance**

- **Behavioral change.** When applied to a JSON object, filters now have an implicit preceding wildcard selector and the "current" (`@`) object is set to each of the object's values. This is now consistent with applying filters to arrays and adheres to the IETF JSONPath Internet Draft.

## Version 0.3.0

**IETF JSONPath Draft compliance**

- Added support for function extensions.
- Added the built-in `length()` function.
- Added the built-in `count()` function. `count()` is an alias for `length()`.
- Support filters without parentheses.
- Adhere to IETF JSONPath draft escaping in quoted property selectors.
- Handle UTF-16 surrogate pairs in quoted property selectors.

**Features**

- Added the built-in `keys()` function.
- Added `parent` and `children` properties to `JSONPathMatch`. Now we can traverse the "document tree" after finding matches.
- Added a `parts` property to `JSONPathMatch`. `parts` is a tuple of `int`s, `slice`s and `str`s that can be used with `JSONPathEnvironment.getitem()` to get the matched object from the original data structure, or equivalent data structures. It is the keys, indices and slices that make up a concrete path.

## Version 0.2.0

**Fixes**

- Fixed a bug with `CompoundJSONPath.finditer()` and the intersection operator (`&`). The intersection operation was returning just the left hand results.

## Version 0.1.0

First release
