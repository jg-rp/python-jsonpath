# Python JSONPath Change Log

## Version 1.2.2

**Fixes**

- Fixed parsing of bare name selectors that start with a reserved word. See [issue #72](https://github.com/jg-rp/python-jsonpath/issues/72).

**Changes**

- We've dropped support for Python 3.7, which was end of life in June 2023.

## Version 1.2.1

**Fixes**

- Fixed the string representation regex literals in filter expressions. See [issue #70](https://github.com/jg-rp/python-jsonpath/issues/70).

## Version 1.2.0

**Fixes**

- Fixed handling of JSONPath literals in filter expressions. We now raise a `JSONPathSyntaxError` if a filter expression literal is not part of a comparison, membership or function expression. See [jsonpath-compliance-test-suite#81](https://github.com/jsonpath-standard/jsonpath-compliance-test-suite/pull/81).
- Fixed parsing of number literals including an exponent. Upper case 'e's are now allowed.
- Fixed handling of trailing commas in bracketed selection lists. We now raise a `JSONPathSyntaxError` in such cases.

**Compliance**

- Skipped tests for invalid escape sequences. The JSONPath spec is more strict than Python's JSON decoder when it comes to parsing `\u` escape sequences in string literals. We are adopting a policy of least surprise. The assertion is that most people will expect the JSONPath parser to behave the same as Python's JSON parser. See [jsonpath-compliance-test-suite #87](https://github.com/jsonpath-standard/jsonpath-compliance-test-suite/pull/87).
- Skipped tests for invalid integer and float literals. Same as above. We are deliberately choosing to match Python's int and float parsing behavior. See [jsonpath-compliance-test-suite #89](https://github.com/jsonpath-standard/jsonpath-compliance-test-suite/pull/89).
- Skipped tests for incorrect casing `true`, `false` and `null` literals.

**Features**

- Allow JSONPath filter expression membership operators (`contains` and `in`) to operate on object/mapping data as well as arrays/sequences. See [#55](https://github.com/jg-rp/python-jsonpath/issues/55).
- Added a `select()` method to the JSONPath [query iterator interface](https://jg-rp.github.io/python-jsonpath/query/), generating a projection of each JSONPath match by selecting a subset of its values.
- Added the `query()` method to the `JSONPath` class. Get a query iterator from an already compiled path.
- Added the `addne` and `addap` operations to [JSONPatch](https://jg-rp.github.io/python-jsonpath/api/#jsonpath.JSONPatch). `addne` (add if not exists) is like the standard `add` operation, but only adds object keys/values if the key does not exist. `addap` (add or append) is like the standard `add` operation, but assumes an index of `-` if the target index can not be resolved.

## Version 1.1.1

**Fixes**

- Fixed evaluation of JSONPath singular queries when they appear in a logical expression and without a comparison operator. Previously we were evaluating logical expressions with the value held by the single element node list, now we treat such filter queries as existence tests. See [#57](https://github.com/jg-rp/python-jsonpath/issues/57).

## Version 1.1.0

**Fixes**

- Fixed logical operator precedence in JSONPath filter expressions. Previously, logical _or_ (`||`) and logical _and_ (`&&`) had equal precedence. Now `&&` binds more tightly than `||`, as per RFC 9535.
- Fixed JSONPath bracketed selector list evaluation order. Previously we were iterating nodes for every list item, now we exhaust all matches for the first item before moving on to the next item.

**Features**

- Added the "query API", a fluent, chainable interface for manipulating `JSONPathMatch` iterators ([docs](https://jg-rp.github.io/python-jsonpath/query/), [source](https://github.com/jg-rp/python-jsonpath/blob/7665105de1501a5b2172f63a88db6d08b2b1702d/jsonpath/fluent_api.py#L17)).

## Version 1.0.0

[RFC 9535](https://datatracker.ietf.org/doc/html/rfc9535) (JSONPath: Query Expressions for JSON) is now out, replacing the [draft IETF JSONPath base](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-21).

**Breaking Changes**

- The undocumented `keys` function extension is no longer enabled by default. A new, well-typed `keys` function is planned for the future.

**Fixes**

- The lexer now sorts environment-controlled tokens by their length in descending order. This allows one custom token to be a prefix of another.

**Features**

- Added the non-standard "fake root" identifier, which defaults to `^` and can be customized with the `fake_root_token` attribute on a `JSONPathEnvironment` subclass. Using the fake root identifier is equivalent to the standard root identifier (`$`), but wraps the target JSON value in an array, so the root value can be conditionally selected using a filter.
- Non-standard environment-controlled tokens can now be disabled by setting them to the empty string.

## Version 0.10.3

**Breaking Changes**

- Changed the exception raised when attempting to compare a non-singular filter query from `JSONPathSyntaxError` to `JSONPathTypeError`.

**Fixes**

- Fixed handling of relative and root queries when used as arguments to filter functions. Previously, when those queries resulted in an empty node list, we were converting them to an empty regular list before passing it to functions that accept _ValueType_ arguments. Now, in such cases, we convert empty node lists to the special result _Nothing_, which is required by the spec.
- Fixed well-typedness checks on JSONPath logical expressions (those that involve `&&` or `||`) and non-singular filter queries. Previously we were erroneously applying the checks for comparison expressions to logical expressions too. Now non-singular queries in logical expressions act as an existence test. See [#45] (https://github.com/jg-rp/python-jsonpath/issues/45).

## Version 0.10.2

**Fixes**

- Fixed precedence of the logical not operator in JSONPath filter expressions. Previously, logical _or_ and logical _and_ had priority over _not_. See [#41](https://github.com/jg-rp/python-jsonpath/issues/41).

## Version 0.10.1

**Hot fix**

- Fixed priority of JSONPath lexer rules. Previously, standard short tokens (like `*` and `?`) had a higher priority than environment-controlled tokens (like `JSONPathEnvironment.keys_selector_token`), making it impossible to incorporate short token characters into longer environment-controlled tokens.

## Version 0.10.0

**Breaking Changes**

- We now enforce JSONPath filter expression "well-typedness" by default. That is, filter expressions are checked at compile time according to the [IETF JSONPath Draft function extension type system](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-21#section-2.4.1) and rules regarding non-singular query usage. If an expression is deemed to not be well-typed, a `JSONPathTypeError` is raised. This can be disabled in Python JSONPath by setting the `well_typed` argument to `JSONPathEnvironment` to `False`, or using `--no-type-checks` on the command line. See [#33](https://github.com/jg-rp/python-jsonpath/issues/33).
- The JSONPath lexer and parser have been refactored to accommodate [#30](https://github.com/jg-rp/python-jsonpath/issues/30). As a result, the tokens generated by the lexer and the ATS built by the parser have changed significantly. In the unlikely event that anyone is customizing the lexer or parser through subclassing, please [open an issue](https://github.com/jg-rp/python-jsonpath/issues) and I'll provide more details.
- Changed the normalized representation of JSONPath string literals to use double quotes instead of single quotes.
- Changed the normalized representation of JSONPath filter expressions to not include parentheses unless the expression includes one or more logical operators.
- The built-in implementation of the standard `length()` filter function is now a class and is renamed to `jsonpath.function_extensions.Length`.
- The built-in implementation of the standard `value()` filter function is now a class and is renamed to `jsonpath.function_extensions.Value`.

**Fixes**

- We no longer silently ignore invalid escape sequences in JSONPath string literals. For example, `$['\"']` used to be OK, it now raises a `JSONPathSyntaxError`. See [#31](https://github.com/jg-rp/python-jsonpath/issues/31).
- Fixed parsing of JSONPath integer literals that use scientific notation. Previously we raised a `JSONPathSyntaxError` for literals such as `1e2`.
- Fixed parsing of JSONPath comparison and logical expressions as filter function arguments. Previously we raised a `JSONPathSyntaxError` if a comparison or logical expression appeared as a filter function argument. Note that none of the built-in, standard filter functions accept arguments of `LogicalType`.
- Fixed parsing of nested JSONPath filter functions, where a function is used as an argument to another.
- Fixed JSONPath bracketed segments. We now handle an arbitrary number of filter selectors alongside name, index, slice and wildcard selectors, separated by commas. See [#30](https://github.com/jg-rp/python-jsonpath/issues/30).

## Version 0.9.0

**Breaking Changes**

- `CompoundJSONPath` instances are no longer updated in-place when using `.union()` and `.intersection()`. Instead, a new `CompoundJSONPath` is returned. `CompoundJSONPath.paths` is now a tuple instead of a list.

**Fixes**

- Fixed a bug with the parsing of JSON Pointers. When given an arbitrary string without slashes, `JSONPointer` would resolve to the document root. The empty string is the only valid pointer that should resolve to the document root. We now raise a `JSONPointerError` in such cases. See [#27](https://github.com/jg-rp/python-jsonpath/issues/27).
- Fixed handling of JSON documents containing only a top-level string.

**Features**

- Added a command line interface, exposing JSONPath, JSON Pointer and JSON Patch features ([docs](https://jg-rp.github.io/python-jsonpath/cli/), [source](https://github.com/jg-rp/python-jsonpath/blob/main/jsonpath/cli.py)).
- Added `JSONPointer.parent()`, a method that returns the parent of the pointer, as a new `JSONPointer` ([docs](https://jg-rp.github.io/python-jsonpath/pointers/#parent)).
- Implemented `JSONPointer.__truediv__()` to allow creation of child pointers from an existing pointer using the slash (`/`) operator ([docs](https://jg-rp.github.io/python-jsonpath/pointers/#slash-operator)).
- Added `JSONPointer.join()`, a method for creating child pointers. This is equivalent to using the slash (`/`) operator for each argument given to `join()` ([docs](https://jg-rp.github.io/python-jsonpath/pointers/#joinparts)).
- Added `JSONPointer.exists()`, a method that returns `True` if a the pointer can be resolved against some data, or `False` otherwise ([docs](https://jg-rp.github.io/python-jsonpath/pointers/#existsdata)).
- Added the `RelativeJSONPointer` class for building new `JSONPointer` instances from Relative JSON Pointer syntax ([docs](https://jg-rp.github.io/python-jsonpath/pointers/#torel), [API](https://jg-rp.github.io/python-jsonpath/api/#jsonpath.RelativeJSONPointer)).
- Added support for a non-standard index/property pointer using `#<property or index>`. This is to support Relative JSON Pointer's use of hash (`#`) when building `JSONPointer` instances from relative JSON Pointers.
- Added the `unicode_escape` argument to `JSONPathEnvironment`. When `True` (the default), UTF-16 escaped sequences found in JSONPath string literals will be decoded.

## Version 0.8.1

**Fixes**

- Fixed the string representation of a `JSONPointer` when built using `JSONPointer.from_parts()` and pointing to the document root. See [#21](https://github.com/jg-rp/python-jsonpath/issues/21).

## Version 0.8.0

**Breaking changes**

- Changed the `JSONPathMatch.parts` representation of the non-standard _keys_ selector (default `~`) to be `~` followed by the key name. It used to be two "parts", `~` and key index.
- All `FilterExpression` subclasses must now implement `children()` and `set_children()`. These methods facilitate filter expression inspection and caching.

**Fixes**

- Changed `findall()` and `finditer()` to accept `data` arguments of any `io.IOBase` subclass, not just `TextIO`.

**Features**

- Added the `JSONPointer` class and methods for converting a `JSONPathMatch` to a `JSONPointer`. `JSONPointer` is compliant with [RFC 6901](https://datatracker.ietf.org/doc/html/rfc6901) ([docs](https://jg-rp.github.io/python-jsonpath/api/#jsonpath.JSONPointer)).
- Added the `JSONPatch` class. `JSONPatch` implements [RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902) ([docs](https://jg-rp.github.io/python-jsonpath/api/#jsonpath.JSONPatch)).
- Added `jsonpath.pointer.resolve()`, a convenience function for resolving a JSON Pointer ([docs](https://jg-rp.github.io/python-jsonpath/quickstart/#pointerresolvepointer-data)).
- Added `jsonpath.patch.apply()`, a convenience function for applying a JSON Patch ([docs](https://jg-rp.github.io/python-jsonpath/quickstart/#patchapplypatch-data)).
- Added `jsonpath.match()`, a convenience function returning a `JSONPathMatch` instance for the first match of a path, or `None` if there were no matches ([docs](https://jg-rp.github.io/python-jsonpath/quickstart/#matchpath-data)).
- Added filter expression caching. Controlled with the `filter_caching` argument to `JSONPathEnvironment`, filter expression caching is enabled by default. See [#14]
- All selectors now use `env.match_class` to instantiate new `JSONPathMatch` objects. This allows for subclassing of `JSONPathMatch`.
- Added `jsonpath.filter.walk()` for the benefit of filter expression static analysis.

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
