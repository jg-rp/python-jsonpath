# Python JSONPath Change Log

## Version 0.3.0 (unreleased)

- Added support for function extensions.
- Added the built-in `length()` function.
- Added the built-in `count()` function. `count()` is an alias for `length()`
- Added the built-in `keys()` function.
- Support filters without parentheses.
- Adhere to IETF JSONPath draft escaping in quoted property selectors.

## Version 0.2.0

**Fixes**

- Fixed a bug with `CompoundJSONPath.finditer()` and the intersection operator (`&`). The intersection operation was returning just the left hand results.

## Version 0.1.0

First release
