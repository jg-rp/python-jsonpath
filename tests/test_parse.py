import dataclasses
import operator

import pytest

from jsonpath import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    path: str
    want: str


TEST_CASES = [
    Case(description="empty", path="", want="$"),
    Case(description="just root", path="$", want="$"),
    Case(description="root dot", path="$.", want="$"),
    Case(description="implicit root dot property", path=".thing", want="$['thing']"),
    Case(description="root dot property", path="$.thing", want="$['thing']"),
    Case(description="root bracket property", path="$[thing]", want="$['thing']"),
    Case(
        description="root double quoted property", path='$["thing"]', want="$['thing']"
    ),
    Case(
        description="root single quoted property", path="$['thing']", want="$['thing']"
    ),
    Case(
        description="root quoted property with non-ident chars",
        path="$['anything{!%']",
        want="$['anything{!%']",
    ),
    Case(description="root dot bracket property", path="$.[thing]", want="$['thing']"),
    Case(description="root bracket index", path="$[1]", want="$[1]"),
    Case(description="root slice", path="$[1:-1]", want="$[1:-1:1]"),
    Case(description="root dot slice", path="$.[1:-1]", want="$[1:-1:1]"),
    Case(description="root slice with step", path="$[1:-1:2]", want="$[1:-1:2]"),
    Case(description="root slice with empty start", path="$[:-1]", want="$[:-1:1]"),
    Case(description="root slice with empty stop", path="$[1:]", want="$[1::1]"),
    Case(description="root dot wild", path="$.*", want="$[*]"),
    Case(description="root bracket wild", path="$[*]", want="$[*]"),
    Case(description="root dot bracket wild", path="$.[*]", want="$[*]"),
    Case(description="root descend", path="$..", want="$.."),
    Case(description="root dot descend", path="$...", want="$.."),
    Case(description="root selector list", path="$[1,2]", want="$[1, 2]"),
    Case(description="root dot selector list", path="$.[1,2]", want="$[1, 2]"),
    Case(
        description="root selector list with slice",
        path="$[1,5:-1:1]",
        want="$[1, 5:-1:1]",
    ),
    Case(
        description="root selector list with properties",
        path="$[some,thing]",
        want="$['some', 'thing']",
    ),
    Case(
        description="root selector list with quoted properties",
        path="$[\"some\",'thing']",
        want="$['some', 'thing']",
    ),
    Case(
        description="implicit root selector list with mixed selectors",
        path='$["some",thing, 1, 2:-2:2]',
        want="$['some', 'thing', 1, 2:-2:2]",
    ),
    Case(
        description="filter self dot property",
        path="[?(@.thing)]",
        want="$[?(@['thing'])]",
    ),
    Case(
        description="filter root dot property",
        path="$.some[?($.thing)]",
        want="$['some'][?($['thing'])]",
    ),
    Case(
        description="filter with equality test",
        path="$.some[?(@.thing == 7)]",
        want="$['some'][?(@['thing'] == 7)]",
    ),
    Case(
        description="filter with >=",
        path="$.some[?(@.thing >= 7)]",
        want="$['some'][?(@['thing'] >= 7)]",
    ),
    Case(
        description="filter with >=",
        path="$.some[?(@.thing >= 7)]",
        want="$['some'][?(@['thing'] >= 7)]",
    ),
    Case(
        description="filter with !=",
        path="$.some[?(@.thing != 7)]",
        want="$['some'][?(@['thing'] != 7)]",
    ),
    Case(
        description="filter with <>",
        path="$.some[?(@.thing != 7)]",
        want="$['some'][?(@['thing'] != 7)]",
    ),
    Case(
        description="filter with regex",
        path="$.some[?(@.thing =~ /(foo|bar)/i)]",
        want="$['some'][?(@['thing'] =~ /(foo|bar)/i)]",
    ),
    Case(
        description="filter with list membership test",
        path="$.some[?(@.thing in ['foo', 'bar', 42])]",
        want="$['some'][?(@['thing'] in ['foo', 'bar', 42])]",
    ),
    Case(
        description="filter with boolean literals",
        path="$.some[?(true == false)]",
        want="$['some'][?(true == false)]",
    ),
    Case(
        description="filter with nil literal",
        path="$.some[?(@.thing == nil)]",
        want="$['some'][?(@['thing'] == nil)]",
    ),
    Case(
        description="null is the same as nil",
        path="$.some[?(@.thing == null)]",
        want="$['some'][?(@['thing'] == nil)]",
    ),
    Case(
        description="none is the same as nil",
        path="$.some[?(@.thing == none)]",
        want="$['some'][?(@['thing'] == nil)]",
    ),
    Case(
        description="filter with test for undefined",
        path="$.some[?(@.thing == undefined)]",
        want="$['some'][?(@['thing'] == undefined)]",
    ),
    Case(
        description="missing is the same as undefined",
        path="$.some[?(@.thing == missing)]",
        want="$['some'][?(@['thing'] == undefined)]",
    ),
    Case(
        description="filter with string literal",
        path="$.some[?(@.thing == 'foo')]",
        want="$['some'][?(@['thing'] == 'foo')]",
    ),
    Case(
        description="filter with integer literal",
        path="$.some[?(@.thing == 1)]",
        want="$['some'][?(@['thing'] == 1)]",
    ),
    Case(
        description="filter with float literal",
        path="$.some[?(@.thing == 1.1)]",
        want="$['some'][?(@['thing'] == 1.1)]",
    ),
    Case(
        description="filter with logical not",
        path="$.some[?(@.thing > 1 and not $.other)]",
        want="$['some'][?(@['thing'] > 1 && !$['other'])]",
    ),
    Case(
        description="filter with grouped expression",
        path="$.some[?(@.thing > 1 and ($.foo or $.bar))]",
        want="$['some'][?(@['thing'] > 1 && $['foo'] || $['bar'])]",
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_default_parser(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert str(path) == case.want
