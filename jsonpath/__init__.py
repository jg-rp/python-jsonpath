# SPDX-FileCopyrightText: 2023-present James Prior <jamesgr.prior@gmail.com>
#
# SPDX-License-Identifier: MIT

from .path import CompoundJSONPath
from .path import JSONPath
from .env import JSONPathEnvironment
from .match import JSONPathMatch
from .lex import Lexer
from .parse import Parser

__all__ = (
    "compile",
    "CompoundJSONPath",
    "findall_async",
    "findall",
    "finditer_async",
    "finditer",
    "JSONPath",
    "JSONPathEnvironment",
    "JSONPathMatch",
    "Lexer",
    "Parser",
)


# For convenience
DEFAULT_ENV = JSONPathEnvironment()
findall = DEFAULT_ENV.findall
finditer = DEFAULT_ENV.finditer
findall_async = DEFAULT_ENV.findall_async
finditer_async = DEFAULT_ENV.finditer_async
compile = DEFAULT_ENV.compile  # pylint: disable=redefined-builtin
