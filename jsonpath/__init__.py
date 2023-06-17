# SPDX-FileCopyrightText: 2023-present James Prior <jamesgr.prior@gmail.com>
#
# SPDX-License-Identifier: MIT

from .env import JSONPathEnvironment
from .exceptions import JSONPathError
from .exceptions import JSONPathIndexError
from .exceptions import JSONPathNameError
from .exceptions import JSONPathSyntaxError
from .exceptions import JSONPathTypeError
from .exceptions import JSONPointerError
from .exceptions import JSONPointerIndexError
from .exceptions import JSONPointerKeyError
from .exceptions import JSONPointerResolutionError
from .exceptions import JSONPointerTypeError
from .filter import UNDEFINED
from .lex import Lexer
from .match import JSONPathMatch
from .parse import Parser
from .path import CompoundJSONPath
from .path import JSONPath
from .pointer import JSONPointer
from .pointer import resolve

__all__ = (
    "compile",
    "CompoundJSONPath",
    "findall_async",
    "findall",
    "finditer_async",
    "finditer",
    "JSONPath",
    "JSONPathEnvironment",
    "JSONPathError",
    "JSONPathIndexError",
    "JSONPathMatch",
    "JSONPathNameError",
    "JSONPathSyntaxError",
    "JSONPathTypeError",
    "JSONPointer",
    "JSONPointerError",
    "JSONPointerIndexError",
    "JSONPointerKeyError",
    "JSONPointerResolutionError",
    "JSONPointerTypeError",
    "Lexer",
    "Parser",
    "resolve",
    "UNDEFINED",
)


# For convenience
DEFAULT_ENV = JSONPathEnvironment()
findall = DEFAULT_ENV.findall
finditer = DEFAULT_ENV.finditer
findall_async = DEFAULT_ENV.findall_async
finditer_async = DEFAULT_ENV.finditer_async
compile = DEFAULT_ENV.compile  # noqa: A001
