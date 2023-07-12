"""Test cases for the command line interface."""
import argparse
import json
import pathlib

import pytest

from jsonpath.__about__ import __version__
from jsonpath.cli import handle_path_command
from jsonpath.cli import setup_parser
from jsonpath.exceptions import JSONPathIndexError
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.exceptions import JSONPathTypeError


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return setup_parser()


@pytest.fixture()
def invalid_target(tmp_path: pathlib.Path) -> str:
    target_path = tmp_path / "source.json"
    with open(target_path, "w") as fd:
        fd.write(r"}}invalid")
    return str(target_path)


@pytest.fixture()
def outfile(tmp_path: pathlib.Path) -> str:
    output_path = tmp_path / "result.json"
    return str(output_path)


@pytest.fixture()
def sample_target(tmp_path: pathlib.Path) -> str:
    sample_data = {
        "categories": [
            {
                "name": "footwear",
                "products": [
                    {
                        "title": "Trainers",
                        "description": "Fashionable trainers.",
                        "price": 89.99,
                    },
                    {
                        "title": "Barefoot Trainers",
                        "description": "Running trainers.",
                        "price": 130.00,
                    },
                ],
            },
            {
                "name": "headwear",
                "products": [
                    {
                        "title": "Cap",
                        "description": "Baseball cap",
                        "price": 15.00,
                    },
                    {
                        "title": "Beanie",
                        "description": "Winter running hat.",
                        "price": 9.00,
                    },
                ],
            },
        ],
        "price_cap": 10,
    }

    target_path = tmp_path / "source.json"
    with open(target_path, "w") as fd:
        json.dump(sample_data, fd)
    return str(target_path)


def test_no_sub_command(
    parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that the CLI exits without a sub command."""
    with pytest.raises(SystemExit) as err:
        parser.parse_args([])

    captured = capsys.readouterr()
    assert err.value.code == 2  # noqa: PLR2004
    assert (
        captured.err.strip()
        == parser.format_usage()
        + "json: error: the following arguments are required: COMMAND"
    )


def test_help(
    parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that the CLI can display a help message without a command."""
    with pytest.raises(SystemExit) as err:
        parser.parse_args(["-h"])

    captured = capsys.readouterr()
    assert err.value.code == 0
    assert captured.out == parser.format_help()


def test_version(
    parser: argparse.ArgumentParser, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that the CLI can display a version number without a command."""
    with pytest.raises(SystemExit) as err:
        parser.parse_args(["--version"])

    captured = capsys.readouterr()
    assert err.value.code == 0
    assert captured.out.strip() == f"python-jsonpath, version {__version__}"


def test_path_command_invalid_target(
    parser: argparse.ArgumentParser,
    invalid_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle invalid JSON with the _path_ command."""
    args = parser.parse_args(["path", "-q", "$.foo", "-f", invalid_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("target document json decode error:")


def test_path_command_invalid_target_debug(
    parser: argparse.ArgumentParser,
    invalid_target: str,
) -> None:
    """Test that we handle invalid JSON with the _path_ command."""
    args = parser.parse_args(["--debug", "path", "-q", "$.foo", "-f", invalid_target])
    with pytest.raises(json.JSONDecodeError):
        handle_path_command(args)


def test_json_path_syntax_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["path", "-q", "$.1", "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    assert err.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("json path syntax error")


def test_json_path_syntax_error_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["--debug", "path", "-q", "$.1", "-f", sample_target])
    with pytest.raises(JSONPathSyntaxError):
        handle_path_command(args)


def test_json_path_type_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(
        ["path", "-q", "$.foo[?count(@.bar, 'baz')]", "-f", sample_target]
    )

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("json path type error")


def test_json_path_type_error_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(
        ["--debug", "path", "-q", "$.foo[?count(@.bar, 'baz')]", "-f", sample_target]
    )

    with pytest.raises(JSONPathTypeError):
        handle_path_command(args)


def test_json_path_index_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(["path", "-q", f"$.foo[{2**53}]", "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("json path index error")


def test_json_path_index_error_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
) -> None:
    """Test that we handle a JSONPath with a syntax error."""
    args = parser.parse_args(
        ["--debug", "path", "-q", f"$.foo[{2**53}]", "-f", sample_target]
    )

    with pytest.raises(JSONPathIndexError):
        handle_path_command(args)


def test_json_path(
    parser: argparse.ArgumentParser,
    sample_target: str,
    outfile: str,
) -> None:
    """Test a valid JSONPath."""
    args = parser.parse_args(
        ["path", "-q", "$..products.*", "-f", sample_target, "-o", outfile]
    )

    handle_path_command(args)
    args.output.flush()

    with open(outfile, "r") as fd:
        assert len(json.load(fd)) == 4  # noqa: PLR2004
