# Exceptions

Each of the following exceptions has a `token` property, referencing the [`Token`](custom_api.md#jsonpath.token.Token) that caused the error. You can use [`Token.position()`](custom_api.md#jsonpath.token.Token.position) to get the token's line and column number.

::: jsonpath.JSONPathError
    handler: python

::: jsonpath.JSONPathSyntaxError
    handler: python

::: jsonpath.JSONPathTypeError
    handler: python

::: jsonpath.JSONPathIndexError
    handler: python

::: jsonpath.JSONPathNameError
    handler: python

::: jsonpath.JSONPointerError
    handler: python

::: jsonpath.JSONPointerResolutionError
    handler: python

::: jsonpath.JSONPointerIndexError
    handler: python

::: jsonpath.JSONPointerKeyError
    handler: python

::: jsonpath.JSONPointerTypeError
    handler: python

::: jsonpath.RelativeJSONPointerError
    handler: python

::: jsonpath.RelativeJSONPointerIndexError
    handler: python

::: jsonpath.RelativeJSONPointerSyntaxError
    handler: python

::: jsonpath.JSONPatchError
    handler: python

::: jsonpath.JSONPatchTestFailure
    handler: python
