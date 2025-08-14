import dataclasses
import json
import operator
from typing import List, Any

import pytest

import jsonpath.token as tokmod
from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.token import Token


@dataclasses.dataclass
class Case:
    description: str
    path: str
    want: List[Token]

@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def cases() -> List[Case]:
    # Deserialize tests/test_lex.json into Case objects with want as List[Token]
    # Build mapping from token constant names used in JSON (e.g., "TOKEN_ROOT")
    # to actual token kind values (e.g., "ROOT").
    kind_map = {name: getattr(tokmod, name) for name in dir(tokmod) if name.startswith("TOKEN_")}
    # Backward-compatibility alias: some test data may use PSEUDO_ROOT to mean FAKE_ROOT
    kind_map.setdefault("TOKEN_PSEUDO_ROOT", tokmod.TOKEN_FAKE_ROOT)
    
    def to_token(obj: dict[str, Any]) -> Token:
        try:
            kind_value = kind_map[obj["kind"]]
        except KeyError as e:
            raise KeyError(f"Unknown token kind in test_lex.json: {obj.get('kind')}\nKnown kinds: {sorted(kind_map.keys())}") from e
        return Token(
            kind=kind_value,
            value=obj["value"],
            index=obj["index"],
            path=obj["path"],
        )
    
    with open("tests/test_lex.json", encoding="utf8") as fd:
        data = json.load(fd)
    
    cases_list: List[Case] = []
    for case in data["tests"]:
        want_tokens = [to_token(tok) for tok in case["want"]]
        cases_list.append(
            Case(
                description=case["description"],
                path=case["path"],
                want=want_tokens,
            )
        )
    return cases_list

@pytest.mark.parametrize("case", cases(), ids=operator.attrgetter("description"))
def test_default_lexer(env: JSONPathEnvironment, case: Case) -> None:
    tokens = list(env.lexer.tokenize(case.path))
    assert tokens == case.want


def test_illegal_token(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError):
        list(env.lexer.tokenize("%"))
