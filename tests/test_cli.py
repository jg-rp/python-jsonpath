"""Test cases for the command line interface."""

import argparse
import json
import pathlib

import pytest

from jsonpath.__about__ import __version__
from jsonpath.cli import handle_patch_command
from jsonpath.cli import handle_path_command
from jsonpath.cli import handle_pointer_command
from jsonpath.cli import setup_parser
from jsonpath.exceptions import JSONPatchTestFailure
from jsonpath.exceptions import JSONPathIndexError
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.exceptions import JSONPathTypeError
from jsonpath.exceptions import JSONPointerResolutionError
from jsonpath.patch import JSONPatch

SAMPLE_DATA = {
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
    target_path = tmp_path / "source.json"
    with open(target_path, "w") as fd:
        json.dump(SAMPLE_DATA, fd)
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
    """Test that we handle a JSONPath with a type error."""
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
    """Test that we handle a JSONPath with a type error."""
    args = parser.parse_args(
        ["--debug", "path", "-q", "$.foo[?count(@.bar, 'baz')]", "-f", sample_target]
    )

    with pytest.raises(JSONPathTypeError):
        handle_path_command(args)


def test_json_path_no_well_typed_checks(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we can disable well-typedness checks."""
    # `count()` must be compared
    query = "$[?count(@..*)]"

    args = parser.parse_args(
        [
            "path",
            "-q",
            query,
            "-f",
            sample_target,
        ]
    )

    with pytest.raises(SystemExit) as err:
        handle_path_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("json path type error")

    args = parser.parse_args(
        [
            "path",
            "-q",
            query,
            "--no-type-checks",
            "-f",
            sample_target,
        ]
    )

    # does not raise
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


def test_json_path_strict(
    parser: argparse.ArgumentParser,
    sample_target: str,
    outfile: str,
) -> None:
    """Test a valid JSONPath."""
    args = parser.parse_args(
        [
            "--debug",
            "path",
            "-q",
            "price_cap",  # No root identifier is an error in strict mode.
            "-f",
            sample_target,
            "-o",
            outfile,
            "--strict",
        ]
    )

    with pytest.raises(JSONPathSyntaxError):
        handle_path_command(args)

    args = parser.parse_args(
        [
            "path",
            "-q",
            "$.price_cap",  # With a root identifier is OK.
            "-f",
            sample_target,
            "-o",
            outfile,
            "--strict",
        ]
    )

    handle_path_command(args)
    args.output.flush()

    with open(outfile, "r") as fd:
        rv = json.load(fd)
        assert rv == [10]


def test_pointer_command_invalid_target(
    parser: argparse.ArgumentParser,
    invalid_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle invalid JSON with the _pointer_ command."""
    args = parser.parse_args(["pointer", "-p", "/foo/bar", "-f", invalid_target])

    with pytest.raises(SystemExit) as err:
        handle_pointer_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("target document json decode error:")


def test_pointer_command_invalid_target_debug(
    parser: argparse.ArgumentParser,
    invalid_target: str,
) -> None:
    """Test that we handle invalid JSON with the _pointer_ command."""
    args = parser.parse_args(
        ["--debug", "pointer", "-p", "/foo/bar", "-f", invalid_target]
    )
    with pytest.raises(json.JSONDecodeError):
        handle_pointer_command(args)


def test_pointer_command_resolution_error(
    parser: argparse.ArgumentParser,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle pointer resolution errors."""
    args = parser.parse_args(["pointer", "-p", "/foo/bar", "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_pointer_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("pointer key error: 'foo'")


def test_pointer_command_resolution_error_debug(
    parser: argparse.ArgumentParser, sample_target: str
) -> None:
    """Test that we handle pointer resolution errors."""
    args = parser.parse_args(
        ["--debug", "pointer", "-p", "/foo/bar", "-f", sample_target]
    )
    with pytest.raises(JSONPointerResolutionError):
        handle_pointer_command(args)


def test_json_pointer(
    parser: argparse.ArgumentParser, sample_target: str, outfile: str
) -> None:
    """Test a valid JSON Pointer."""
    args = parser.parse_args(
        ["pointer", "-p", "/categories/0/name", "-f", sample_target, "-o", outfile]
    )

    handle_pointer_command(args)
    args.output.flush()

    with open(outfile, "r") as fd:
        assert json.load(fd) == "footwear"


def test_json_pointer_empty_string(
    parser: argparse.ArgumentParser, sample_target: str, outfile: str
) -> None:
    """Test an empty JSON Pointer is valid."""
    args = parser.parse_args(["pointer", "-p", "", "-f", sample_target, "-o", outfile])

    handle_pointer_command(args)
    args.output.flush()

    with open(outfile, "r") as fd:
        assert json.load(fd) == SAMPLE_DATA


def test_read_pointer_from_file(
    parser: argparse.ArgumentParser,
    sample_target: str,
    outfile: str,
    tmp_path: pathlib.Path,
) -> None:
    """Test an empty JSON Pointer is valid."""
    pointer_file_path = tmp_path / "pointer.txt"
    with pointer_file_path.open("w") as fd:
        fd.write("/price_cap")

    args = parser.parse_args(
        ["pointer", "-r", str(pointer_file_path), "-f", sample_target, "-o", outfile]
    )

    handle_pointer_command(args)
    args.output.flush()

    with open(outfile, "r") as fd:
        assert json.load(fd) == SAMPLE_DATA["price_cap"]


def test_patch_command_invalid_patch(
    parser: argparse.ArgumentParser,
    sample_target: str,
    invalid_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle invalid patch JSON."""
    args = parser.parse_args(["patch", invalid_target, "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_patch_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("patch document json decode error:")


def test_patch_command_invalid_patch_debug(
    parser: argparse.ArgumentParser,
    sample_target: str,
    invalid_target: str,
) -> None:
    """Test that we handle invalid patch JSON."""
    args = parser.parse_args(["--debug", "patch", invalid_target, "-f", sample_target])
    with pytest.raises(json.JSONDecodeError):
        handle_patch_command(args)


def test_patch_not_an_array(
    parser: argparse.ArgumentParser,
    tmp_path: pathlib.Path,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle a patch that is not an array."""
    mock_patch_path = tmp_path / "patch.json"
    with mock_patch_path.open("w") as fd:
        json.dump({"foo": "bar"}, fd)

    args = parser.parse_args(["patch", str(mock_patch_path), "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_patch_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err == (
        "error: patch file does not look like an array of patch operations"
    )


def test_patch_command_invalid_target(
    parser: argparse.ArgumentParser,
    tmp_path: pathlib.Path,
    invalid_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle invalid JSON with the _patch_ command."""
    mock_patch_path = tmp_path / "patch.json"
    with mock_patch_path.open("w") as fd:
        json.dump([], fd)

    args = parser.parse_args(["patch", str(mock_patch_path), "-f", invalid_target])

    with pytest.raises(SystemExit) as err:
        handle_patch_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("target document json decode error:")


def test_patch_command_invalid_target_debug(
    parser: argparse.ArgumentParser,
    tmp_path: pathlib.Path,
    invalid_target: str,
) -> None:
    """Test that we handle invalid JSON with the _patch_ command."""
    mock_patch_path = tmp_path / "patch.json"
    with mock_patch_path.open("w") as fd:
        json.dump([], fd)

    args = parser.parse_args(
        ["--debug", "patch", str(mock_patch_path), "-f", invalid_target]
    )

    with pytest.raises(json.JSONDecodeError):
        handle_patch_command(args)


def test_patch_error(
    parser: argparse.ArgumentParser,
    tmp_path: pathlib.Path,
    sample_target: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that we handle patch errors."""
    mock_patch_path = tmp_path / "patch.json"
    patch = JSONPatch().test("/categories/0/name", "foo")
    with mock_patch_path.open("w") as fd:
        json.dump(patch.asdicts(), fd)

    args = parser.parse_args(["patch", str(mock_patch_path), "-f", sample_target])

    with pytest.raises(SystemExit) as err:
        handle_patch_command(args)

    captured = capsys.readouterr()
    assert err.value.code == 1
    assert captured.err.startswith("test failed")


def test_patch_error_debug(
    parser: argparse.ArgumentParser,
    tmp_path: pathlib.Path,
    sample_target: str,
) -> None:
    """Test that we handle patch errors."""
    mock_patch_path = tmp_path / "patch.json"
    patch = JSONPatch().test("/categories/0/name", "foo")
    with mock_patch_path.open("w") as fd:
        json.dump(patch.asdicts(), fd)

    args = parser.parse_args(
        ["--debug", "patch", str(mock_patch_path), "-f", sample_target]
    )

    with pytest.raises(JSONPatchTestFailure):
        handle_patch_command(args)


def test_json_patch(
    parser: argparse.ArgumentParser,
    tmp_path: pathlib.Path,
    sample_target: str,
    outfile: str,
) -> None:
    """Test a valid JSON patch."""
    mock_patch_path = tmp_path / "patch.json"
    patch = JSONPatch().replace("/categories/0/name", "foo")
    with mock_patch_path.open("w") as fd:
        json.dump(patch.asdicts(), fd)

    args = parser.parse_args(
        ["patch", str(mock_patch_path), "-f", sample_target, "-o", outfile]
    )

    handle_patch_command(args)
    args.output.flush()

    with open(outfile, "r") as fd:
        patched = json.load(fd)

    assert patched["categories"][0]["name"] == "foo"
