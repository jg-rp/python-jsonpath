# Python JSONPath Change Log

## Version 0.5.0 (unreleased)

**Features**

- Added the built-in `match` filter function.
- Added the built-in `search` filter function.
- Added the built-in `value` filter function.

**Fixes**

- Fixed a bug where the current object selector (`@`) would evaluate to `undefined` when a filter is applied to an array of strings.

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
