# SPDX-FileCopyrightText: 2023-present James Prior <jamesgr.prior@gmail.com>
#
# SPDX-License-Identifier: MIT

from .env import JSONPathEnvironment
from .lex import Lexer
from .match import JSONPathMatch
from .parse import Parser
from .path import CompoundJSONPath, JSONPath

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
compile = DEFAULT_ENV.compile  # noqa: A001
