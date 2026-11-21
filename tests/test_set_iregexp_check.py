import jsonpath
from jsonpath.function_extensions import Match


def test_enable_iregexp_check() -> None:
    env = jsonpath.JSONPathEnvironment()
    env.function_extensions["match"] = Match(check_iregexp=True)
    # Character classes are OK.
    query = "$[?match(@, '[0-9]+')]"
    data = ["123", "abc", "abc123"]
    assert env.findall(query, data) == ["123"]

    # Multi character escapes are not.
    query = "$[?match(@, '\\\\d+')]"
    assert env.findall(query, data) == []


def test_disable_iregexp_check() -> None:
    env = jsonpath.JSONPathEnvironment()
    env.function_extensions["match"] = Match(check_iregexp=False)
    # Character classes are OK.
    query = "$[?match(@, '[0-9]+')]"
    data = ["123", "abc", "abc123"]
    assert env.findall(query, data) == ["123"]

    # Multi character escapes are OK too.
    query = "$[?match(@, '\\\\d+')]"
    assert env.findall(query, data) == ["123"]
