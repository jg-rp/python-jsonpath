"""JSONPointer test cases."""
import jsonpath


def test_match_to_pointer() -> None:
    data = {"some": {"thing": "else"}}
    matches = list(jsonpath.finditer("$.some.thing", data))
    assert len(matches) == 1
    match = matches[0]
    pointer = match.pointer()
    assert pointer.resolve(data) == match.obj
    assert pointer.resolve({"some": {"thing": "foo"}}) == "foo"
