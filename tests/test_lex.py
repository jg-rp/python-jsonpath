import dataclasses
import operator
from typing import List

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.token import TOKEN_AND
from jsonpath.token import TOKEN_BARE_PROPERTY
from jsonpath.token import TOKEN_COMMA
from jsonpath.token import TOKEN_DDOT
from jsonpath.token import TOKEN_EQ
from jsonpath.token import TOKEN_FALSE
from jsonpath.token import TOKEN_FILTER_END
from jsonpath.token import TOKEN_FILTER_START
from jsonpath.token import TOKEN_FLOAT
from jsonpath.token import TOKEN_FUNCTION
from jsonpath.token import TOKEN_GT
from jsonpath.token import TOKEN_IN
from jsonpath.token import TOKEN_INDEX
from jsonpath.token import TOKEN_INT
from jsonpath.token import TOKEN_INTERSECTION
from jsonpath.token import TOKEN_LIST_START
from jsonpath.token import TOKEN_LT
from jsonpath.token import TOKEN_NIL
from jsonpath.token import TOKEN_NOT
from jsonpath.token import TOKEN_OR
from jsonpath.token import TOKEN_PROPERTY
from jsonpath.token import TOKEN_RBRACKET
from jsonpath.token import TOKEN_RE
from jsonpath.token import TOKEN_RE_FLAGS
from jsonpath.token import TOKEN_RE_PATTERN
from jsonpath.token import TOKEN_ROOT
from jsonpath.token import TOKEN_RPAREN
from jsonpath.token import TOKEN_SELF
from jsonpath.token import TOKEN_SLICE_START
from jsonpath.token import TOKEN_SLICE_STEP
from jsonpath.token import TOKEN_SLICE_STOP
from jsonpath.token import TOKEN_STRING
from jsonpath.token import TOKEN_TRUE
from jsonpath.token import TOKEN_UNION
from jsonpath.token import TOKEN_WILD
from jsonpath.token import Token


@dataclasses.dataclass
class Case:
    description: str
    path: str
    want: List[Token]


TEST_CASES = [
    Case(
        description="just root",
        path="$",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$"),
        ],
    ),
    Case(
        description="root dot property",
        path="$.some.thing",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.some.thing"),
            Token(kind=TOKEN_PROPERTY, value="some", index=2, path="$.some.thing"),
            Token(kind=TOKEN_PROPERTY, value="thing", index=7, path="$.some.thing"),
        ],
    ),
    Case(
        description="root bracket property",
        path="$[some][thing]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$[some][thing]"),
            Token(kind=TOKEN_PROPERTY, value="some", index=2, path="$[some][thing]"),
            Token(kind=TOKEN_PROPERTY, value="thing", index=8, path="$[some][thing]"),
        ],
    ),
    Case(
        description="root double quoted property",
        path='$["some"]',
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path='$["some"]'),
            Token(kind=TOKEN_LIST_START, value="[", index=1, path='$["some"]'),
            Token(kind=TOKEN_STRING, value="some", index=3, path='$["some"]'),
            Token(kind=TOKEN_RBRACKET, value="]", index=8, path='$["some"]'),
        ],
    ),
    Case(
        description="root single quoted property",
        path="$['some']",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$['some']"),
            Token(kind=TOKEN_LIST_START, value="[", index=1, path="$['some']"),
            Token(kind=TOKEN_STRING, value="some", index=3, path="$['some']"),
            Token(kind=TOKEN_RBRACKET, value="]", index=8, path="$['some']"),
        ],
    ),
    Case(
        description="root dot bracket property",
        path="$.[some][thing]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.[some][thing]"),
            Token(kind=TOKEN_PROPERTY, value="some", index=3, path="$.[some][thing]"),
            Token(kind=TOKEN_PROPERTY, value="thing", index=9, path="$.[some][thing]"),
        ],
    ),
    Case(
        description="root bracket index",
        path="$[1]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$[1]"),
            Token(kind=TOKEN_INDEX, value="1", index=2, path="$[1]"),
        ],
    ),
    Case(
        description="root dot bracket index",
        path="$.[1]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.[1]"),
            Token(kind=TOKEN_INDEX, value="1", index=3, path="$.[1]"),
        ],
    ),
    Case(
        description="empty slice",
        path="[:]",
        want=[
            Token(kind=TOKEN_SLICE_START, value="", index=1, path="[:]"),
            Token(kind=TOKEN_SLICE_STOP, value="", index=2, path="[:]"),
            Token(kind=TOKEN_SLICE_STEP, value="", index=-1, path="[:]"),
        ],
    ),
    Case(
        description="empty slice empty step",
        path="[::]",
        want=[
            Token(kind=TOKEN_SLICE_START, value="", index=1, path="[::]"),
            Token(kind=TOKEN_SLICE_STOP, value="", index=2, path="[::]"),
            Token(kind=TOKEN_SLICE_STEP, value="", index=3, path="[::]"),
        ],
    ),
    Case(
        description="slice empty stop",
        path="[1:]",
        want=[
            Token(kind=TOKEN_SLICE_START, value="1", index=1, path="[1:]"),
            Token(kind=TOKEN_SLICE_STOP, value="", index=3, path="[1:]"),
            Token(kind=TOKEN_SLICE_STEP, value="", index=-1, path="[1:]"),
        ],
    ),
    Case(
        description="slice empty start",
        path="[:-1]",
        want=[
            Token(kind=TOKEN_SLICE_START, value="", index=1, path="[:-1]"),
            Token(kind=TOKEN_SLICE_STOP, value="-1", index=2, path="[:-1]"),
            Token(kind=TOKEN_SLICE_STEP, value="", index=-1, path="[:-1]"),
        ],
    ),
    Case(
        description="slice start and stop",
        path="[1:7]",
        want=[
            Token(kind=TOKEN_SLICE_START, value="1", index=1, path="[1:7]"),
            Token(kind=TOKEN_SLICE_STOP, value="7", index=3, path="[1:7]"),
            Token(kind=TOKEN_SLICE_STEP, value="", index=-1, path="[1:7]"),
        ],
    ),
    Case(
        description="slice start, stop and step",
        path="[1:7:2]",
        want=[
            Token(kind=TOKEN_SLICE_START, value="1", index=1, path="[1:7:2]"),
            Token(kind=TOKEN_SLICE_STOP, value="7", index=3, path="[1:7:2]"),
            Token(kind=TOKEN_SLICE_STEP, value="2", index=5, path="[1:7:2]"),
        ],
    ),
    Case(
        description="root dot wild",
        path="$.*",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.*"),
            Token(kind=TOKEN_WILD, value=".*", index=1, path="$.*"),
        ],
    ),
    Case(
        description="root bracket wild",
        path="$[*]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$[*]"),
            Token(kind=TOKEN_WILD, value="[*]", index=1, path="$[*]"),
        ],
    ),
    Case(
        description="root dot bracket wild",
        path="$.[*]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.[*]"),
            Token(kind=TOKEN_WILD, value=".[*]", index=1, path="$.[*]"),
        ],
    ),
    Case(
        description="root descend",
        path="$..",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.."),
            Token(kind=TOKEN_DDOT, value="..", index=1, path="$.."),
        ],
    ),
    Case(
        description="root descend property",
        path="$..thing",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$..thing"),
            Token(kind=TOKEN_DDOT, value="..", index=1, path="$..thing"),
            Token(kind=TOKEN_BARE_PROPERTY, value="thing", index=3, path="$..thing"),
        ],
    ),
    Case(
        description="root descend dot property",
        path="$...thing",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$...thing"),
            Token(kind=TOKEN_DDOT, value="..", index=1, path="$...thing"),
            Token(kind=TOKEN_PROPERTY, value="thing", index=4, path="$...thing"),
        ],
    ),
    Case(
        description="root selector list of indices",
        path="$[1,4,5]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$[1,4,5]"),
            Token(kind=TOKEN_LIST_START, value="[", index=1, path="$[1,4,5]"),
            Token(kind=TOKEN_INT, value="1", index=2, path="$[1,4,5]"),
            Token(kind=TOKEN_COMMA, value=",", index=3, path="$[1,4,5]"),
            Token(kind=TOKEN_INT, value="4", index=4, path="$[1,4,5]"),
            Token(kind=TOKEN_COMMA, value=",", index=5, path="$[1,4,5]"),
            Token(kind=TOKEN_INT, value="5", index=6, path="$[1,4,5]"),
            Token(kind=TOKEN_RBRACKET, value="]", index=7, path="$[1,4,5]"),
        ],
    ),
    Case(
        description="root selector list with a slice",
        path="$[1,4:9]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$[1,4:9]"),
            Token(kind=TOKEN_LIST_START, value="[", index=1, path="$[1,4:9]"),
            Token(kind=TOKEN_INT, value="1", index=2, path="$[1,4:9]"),
            Token(kind=TOKEN_COMMA, value=",", index=3, path="$[1,4:9]"),
            Token(kind=TOKEN_SLICE_START, value="4", index=4, path="$[1,4:9]"),
            Token(kind=TOKEN_SLICE_STOP, value="9", index=6, path="$[1,4:9]"),
            Token(kind=TOKEN_SLICE_STEP, value="", index=-1, path="$[1,4:9]"),
            Token(kind=TOKEN_RBRACKET, value="]", index=7, path="$[1,4:9]"),
        ],
    ),
    Case(
        description="root selector list of properties",
        path="$[some,thing]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$[some,thing]"),
            Token(kind=TOKEN_LIST_START, value="[", index=1, path="$[some,thing]"),
            Token(
                kind=TOKEN_BARE_PROPERTY, value="some", index=2, path="$[some,thing]"
            ),
            Token(kind=TOKEN_COMMA, value=",", index=6, path="$[some,thing]"),
            Token(
                kind=TOKEN_BARE_PROPERTY, value="thing", index=7, path="$[some,thing]"
            ),
            Token(kind=TOKEN_RBRACKET, value="]", index=12, path="$[some,thing]"),
        ],
    ),
    Case(
        description="root dot filter on self dot property",
        path="$.[?(@.some)]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.[?(@.some)]"),
            Token(kind=TOKEN_FILTER_START, value="[?(", index=2, path="$.[?(@.some)]"),
            Token(kind=TOKEN_SELF, value="@", index=5, path="$.[?(@.some)]"),
            Token(kind=TOKEN_PROPERTY, value="some", index=7, path="$.[?(@.some)]"),
            Token(kind=TOKEN_FILTER_END, value=")]", index=11, path="$.[?(@.some)]"),
        ],
    ),
    Case(
        description="root dot filter on root dot property",
        path="$.[?($.some)]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.[?($.some)]"),
            Token(kind=TOKEN_FILTER_START, value="[?(", index=2, path="$.[?($.some)]"),
            Token(kind=TOKEN_ROOT, value="$", index=5, path="$.[?($.some)]"),
            Token(kind=TOKEN_PROPERTY, value="some", index=7, path="$.[?($.some)]"),
            Token(kind=TOKEN_FILTER_END, value=")]", index=11, path="$.[?($.some)]"),
        ],
    ),
    Case(
        description="root dot filter on self index",
        path="$.[?(@[1])]",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.[?(@[1])]"),
            Token(kind=TOKEN_FILTER_START, value="[?(", index=2, path="$.[?(@[1])]"),
            Token(kind=TOKEN_SELF, value="@", index=5, path="$.[?(@[1])]"),
            Token(kind=TOKEN_INDEX, value="1", index=7, path="$.[?(@[1])]"),
            Token(kind=TOKEN_FILTER_END, value=")]", index=9, path="$.[?(@[1])]"),
        ],
    ),
    Case(
        description="filter self dot property equality with float",
        path="[?(@.some == 1.1)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START, value="[?(", index=0, path="[?(@.some == 1.1)]"
            ),
            Token(kind=TOKEN_SELF, value="@", index=3, path="[?(@.some == 1.1)]"),
            Token(
                kind=TOKEN_PROPERTY, value="some", index=5, path="[?(@.some == 1.1)]"
            ),
            Token(kind=TOKEN_EQ, value="==", index=10, path="[?(@.some == 1.1)]"),
            Token(kind=TOKEN_FLOAT, value="1.1", index=13, path="[?(@.some == 1.1)]"),
            Token(
                kind=TOKEN_FILTER_END, value=")]", index=16, path="[?(@.some == 1.1)]"
            ),
        ],
    ),
    Case(
        description=(
            "filter self dot property equality with float in scientific notation"
        ),
        path="[?(@.some == 1.1e10)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some == 1.1e10)]",
            ),
            Token(kind=TOKEN_SELF, value="@", index=3, path="[?(@.some == 1.1e10)]"),
            Token(
                kind=TOKEN_PROPERTY, value="some", index=5, path="[?(@.some == 1.1e10)]"
            ),
            Token(kind=TOKEN_EQ, value="==", index=10, path="[?(@.some == 1.1e10)]"),
            Token(
                kind=TOKEN_FLOAT, value="1.1e10", index=13, path="[?(@.some == 1.1e10)]"
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=19,
                path="[?(@.some == 1.1e10)]",
            ),
        ],
    ),
    Case(
        description="filter self index equality with float",
        path="[?(@[1] == 1.1)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START, value="[?(", index=0, path="[?(@[1] == 1.1)]"
            ),
            Token(kind=TOKEN_SELF, value="@", index=3, path="[?(@[1] == 1.1)]"),
            Token(kind=TOKEN_INDEX, value="1", index=5, path="[?(@[1] == 1.1)]"),
            Token(kind=TOKEN_EQ, value="==", index=8, path="[?(@[1] == 1.1)]"),
            Token(kind=TOKEN_FLOAT, value="1.1", index=11, path="[?(@[1] == 1.1)]"),
            Token(kind=TOKEN_FILTER_END, value=")]", index=14, path="[?(@[1] == 1.1)]"),
        ],
    ),
    Case(
        description="filter self dot property equality with int",
        path="[?(@.some == 1)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START, value="[?(", index=0, path="[?(@.some == 1)]"
            ),
            Token(kind=TOKEN_SELF, value="@", index=3, path="[?(@.some == 1)]"),
            Token(kind=TOKEN_PROPERTY, value="some", index=5, path="[?(@.some == 1)]"),
            Token(kind=TOKEN_EQ, value="==", index=10, path="[?(@.some == 1)]"),
            Token(kind=TOKEN_INT, value="1", index=13, path="[?(@.some == 1)]"),
            Token(kind=TOKEN_FILTER_END, value=")]", index=14, path="[?(@.some == 1)]"),
        ],
    ),
    Case(
        description="filter self dot property equality with int in scientific notation",
        path="[?(@.some == 1e10)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some == 1e10)]",
            ),
            Token(kind=TOKEN_SELF, value="@", index=3, path="[?(@.some == 1e10)]"),
            Token(
                kind=TOKEN_PROPERTY, value="some", index=5, path="[?(@.some == 1e10)]"
            ),
            Token(kind=TOKEN_EQ, value="==", index=10, path="[?(@.some == 1e10)]"),
            Token(kind=TOKEN_INT, value="1e10", index=13, path="[?(@.some == 1e10)]"),
            Token(
                kind=TOKEN_FILTER_END, value=")]", index=17, path="[?(@.some == 1e10)]"
            ),
        ],
    ),
    Case(
        description="filter self dot property regex",
        path="[?(@.some =~ /foo|bar/i)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some =~ /foo|bar/i)]",
            ),
            Token(
                kind=TOKEN_SELF, value="@", index=3, path="[?(@.some =~ /foo|bar/i)]"
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=5,
                path="[?(@.some =~ /foo|bar/i)]",
            ),
            Token(
                kind=TOKEN_RE,
                value="=~",
                index=10,
                path="[?(@.some =~ /foo|bar/i)]",
            ),
            Token(
                kind=TOKEN_RE_PATTERN,
                value="foo|bar",
                index=14,
                path="[?(@.some =~ /foo|bar/i)]",
            ),
            Token(
                kind=TOKEN_RE_FLAGS,
                value="i",
                index=22,
                path="[?(@.some =~ /foo|bar/i)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=23,
                path="[?(@.some =~ /foo|bar/i)]",
            ),
        ],
    ),
    Case(
        description="union of two paths",
        path="$.some | $.thing",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.some | $.thing"),
            Token(kind=TOKEN_PROPERTY, value="some", index=2, path="$.some | $.thing"),
            Token(kind=TOKEN_UNION, value="|", index=7, path="$.some | $.thing"),
            Token(kind=TOKEN_ROOT, value="$", index=9, path="$.some | $.thing"),
            Token(
                kind=TOKEN_PROPERTY, value="thing", index=11, path="$.some | $.thing"
            ),
        ],
    ),
    Case(
        description="union of three paths",
        path="$.some | $.thing | $.other",
        want=[
            Token(
                kind=TOKEN_ROOT, value="$", index=0, path="$.some | $.thing | $.other"
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=2,
                path="$.some | $.thing | $.other",
            ),
            Token(
                kind=TOKEN_UNION, value="|", index=7, path="$.some | $.thing | $.other"
            ),
            Token(
                kind=TOKEN_ROOT, value="$", index=9, path="$.some | $.thing | $.other"
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="thing",
                index=11,
                path="$.some | $.thing | $.other",
            ),
            Token(
                kind=TOKEN_UNION, value="|", index=17, path="$.some | $.thing | $.other"
            ),
            Token(
                kind=TOKEN_ROOT, value="$", index=19, path="$.some | $.thing | $.other"
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="other",
                index=21,
                path="$.some | $.thing | $.other",
            ),
        ],
    ),
    Case(
        description="intersection two paths",
        path="$.some & $.thing",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$.some & $.thing"),
            Token(kind=TOKEN_PROPERTY, value="some", index=2, path="$.some & $.thing"),
            Token(kind=TOKEN_INTERSECTION, value="&", index=7, path="$.some & $.thing"),
            Token(kind=TOKEN_ROOT, value="$", index=9, path="$.some & $.thing"),
            Token(
                kind=TOKEN_PROPERTY, value="thing", index=11, path="$.some & $.thing"
            ),
        ],
    ),
    Case(
        description="filter expression with logical and",
        path="[?(@.some > 1 and @.some < 5)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=3,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=5,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_GT,
                value=">",
                index=10,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="1",
                index=12,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_AND,
                value="and",
                index=14,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=18,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=20,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_LT,
                value="<",
                index=25,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="5",
                index=27,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=28,
                path="[?(@.some > 1 and @.some < 5)]",
            ),
        ],
    ),
    Case(
        description="filter expression with logical or",
        path="[?(@.some == 1 or @.some == 5)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=3,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=5,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=10,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="1",
                index=13,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_OR,
                value="or",
                index=15,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=18,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=20,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=25,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="5",
                index=28,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=29,
                path="[?(@.some == 1 or @.some == 5)]",
            ),
        ],
    ),
    Case(
        description="filter expression with logical ||",
        path="[?(@.some == 1 || @.some == 5)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=3,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=5,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=10,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="1",
                index=13,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_OR,
                value="||",
                index=15,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=18,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=20,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=25,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="5",
                index=28,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=29,
                path="[?(@.some == 1 || @.some == 5)]",
            ),
        ],
    ),
    Case(
        description="filter self dot property in list literal",
        path="[?(@.thing in [1, '1'])]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.thing in [1, '1'])]",
            ),
            Token(kind=TOKEN_SELF, value="@", index=3, path="[?(@.thing in [1, '1'])]"),
            Token(
                kind=TOKEN_PROPERTY,
                value="thing",
                index=5,
                path="[?(@.thing in [1, '1'])]",
            ),
            Token(kind=TOKEN_IN, value="in", index=11, path="[?(@.thing in [1, '1'])]"),
            Token(
                kind=TOKEN_LIST_START,
                value="[",
                index=14,
                path="[?(@.thing in [1, '1'])]",
            ),
            Token(kind=TOKEN_INT, value="1", index=15, path="[?(@.thing in [1, '1'])]"),
            Token(
                kind=TOKEN_COMMA, value=",", index=16, path="[?(@.thing in [1, '1'])]"
            ),
            Token(
                kind=TOKEN_STRING, value="1", index=19, path="[?(@.thing in [1, '1'])]"
            ),
            Token(
                kind=TOKEN_RBRACKET,
                value="]",
                index=21,
                path="[?(@.thing in [1, '1'])]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=22,
                path="[?(@.thing in [1, '1'])]",
            ),
        ],
    ),
    Case(
        description="filter expression with logical not",
        path="[?(@.some == 1 or not @.some < 5)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=3,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=5,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=10,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="1",
                index=13,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_OR,
                value="or",
                index=15,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_NOT,
                value="not",
                index=18,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=22,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=24,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_LT,
                value="<",
                index=29,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="5",
                index=31,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=32,
                path="[?(@.some == 1 or not @.some < 5)]",
            ),
        ],
    ),
    Case(
        description="filter expression with logical not using '!'",
        path="[?(@.some == 1 or !@.some < 5)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=3,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=5,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=10,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="1",
                index=13,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_OR,
                value="or",
                index=15,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_NOT,
                value="!",
                index=18,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=19,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=21,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_LT,
                value="<",
                index=26,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="5",
                index=28,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=29,
                path="[?(@.some == 1 or !@.some < 5)]",
            ),
        ],
    ),
    Case(
        description="filter true and false",
        path="[?(true == false)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(true == false)]",
            ),
            Token(kind=TOKEN_TRUE, value="true", index=3, path="[?(true == false)]"),
            Token(kind=TOKEN_EQ, value="==", index=8, path="[?(true == false)]"),
            Token(kind=TOKEN_FALSE, value="false", index=11, path="[?(true == false)]"),
            Token(
                kind=TOKEN_FILTER_END, value=")]", index=16, path="[?(true == false)]"
            ),
        ],
    ),
    Case(
        description="filter true and false",
        path="[?(nil == none && nil == null)]",
        want=[
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=0,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_NIL,
                value="nil",
                index=3,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=7,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_NIL,
                value="none",
                index=10,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_AND,
                value="&&",
                index=15,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_NIL,
                value="nil",
                index=18,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_EQ,
                value="==",
                index=22,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_NIL,
                value="null",
                index=25,
                path="[?(nil == none && nil == null)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=29,
                path="[?(nil == none && nil == null)]",
            ),
        ],
    ),
    Case(
        description="list of quoted properties",
        path="$['some', 'thing']",
        want=[
            Token(kind=TOKEN_ROOT, value="$", index=0, path="$['some', 'thing']"),
            Token(kind=TOKEN_LIST_START, value="[", index=1, path="$['some', 'thing']"),
            Token(kind=TOKEN_STRING, value="some", index=3, path="$['some', 'thing']"),
            Token(kind=TOKEN_COMMA, value=",", index=8, path="$['some', 'thing']"),
            Token(
                kind=TOKEN_STRING, value="thing", index=11, path="$['some', 'thing']"
            ),
            Token(kind=TOKEN_RBRACKET, value="]", index=17, path="$['some', 'thing']"),
        ],
    ),
    Case(
        description="call a function",
        path="$.some[?(length(@.thing) < 2)]",
        want=[
            Token(
                kind=TOKEN_ROOT,
                value="$",
                index=0,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="some",
                index=2,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_FILTER_START,
                value="[?(",
                index=6,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_FUNCTION,
                value="length",
                index=9,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_SELF,
                value="@",
                index=16,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_PROPERTY,
                value="thing",
                index=18,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_RPAREN,
                value=")",
                index=23,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_LT,
                value="<",
                index=25,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_INT,
                value="2",
                index=27,
                path="$.some[?(length(@.thing) < 2)]",
            ),
            Token(
                kind=TOKEN_FILTER_END,
                value=")]",
                index=28,
                path="$.some[?(length(@.thing) < 2)]",
            ),
        ],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_default_lexer(env: JSONPathEnvironment, case: Case) -> None:
    tokens = list(env.lexer.tokenize(case.path))
    assert tokens == case.want


def test_illegal_token(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError):
        list(env.lexer.tokenize("^"))
