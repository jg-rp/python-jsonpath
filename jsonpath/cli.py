"""JSONPath, JSON Pointer and JSON Patch command line interface."""
import argparse
import json
import sys

import jsonpath
from jsonpath.__about__ import __version__
from jsonpath.exceptions import JSONPatchError
from jsonpath.exceptions import JSONPathIndexError
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.exceptions import JSONPathTypeError
from jsonpath.exceptions import JSONPointerError

INDENT = 2


def path_sub_command(parser: argparse.ArgumentParser) -> None:  # noqa: D103
    parser.set_defaults(func=handle_path_command)
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-q",
        "--query",
        help="JSONPath query string.",
    )

    group.add_argument(
        "-r",
        "--path-file",
        type=argparse.FileType(mode="r"),
        help="Text file containing a JSONPath query.",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType(mode="rb"),
        default=sys.stdin,
        help=(
            "File to read the target JSON document from. "
            "Defaults to reading from the standard input stream."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType(mode="w"),
        default=sys.stdout,
        help=(
            "File to write resulting objects to, as a JSON array. "
            "Defaults to the standard output stream."
        ),
    )


def pointer_sub_command(parser: argparse.ArgumentParser) -> None:  # noqa: D103
    parser.set_defaults(func=handle_pointer_command)
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-p",
        "--pointer",
        help="RFC 6901 formatted JSON Pointer string.",
    )

    group.add_argument(
        "-r",
        "--pointer-file",
        type=argparse.FileType(mode="r"),
        help="Text file containing an RFC 6901 formatted JSON Pointer string.",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType(mode="rb"),
        default=sys.stdin,
        help=(
            "File to read the target JSON document from. "
            "Defaults to reading from the standard input stream."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType(mode="w"),
        default=sys.stdout,
        help=(
            "File to write the resulting object to, in JSON format. "
            "Defaults to the standard output stream."
        ),
    )

    parser.add_argument(
        "-u",
        "--uri-decode",
        action="store_true",
        help="Unescape URI escape sequences found in JSON Pointers",
    )


def patch_sub_command(parser: argparse.ArgumentParser) -> None:  # noqa: D103
    parser.set_defaults(func=handle_patch_command)

    parser.add_argument(
        "patch",
        type=argparse.FileType(mode="rb"),
        metavar="PATCH",
        help="File containing an RFC 6902 formatted JSON Patch.",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType(mode="rb"),
        default=sys.stdin,
        help=(
            "File to read the target JSON document from. "
            "Defaults to reading from the standard input stream."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType(mode="w"),
        default=sys.stdout,
        help=(
            "File to write the resulting JSON document to. "
            "Defaults to the standard output stream."
        ),
    )

    parser.add_argument(
        "-u",
        "--uri-decode",
        action="store_true",
        help="Unescape URI escape sequences found in JSON Pointers",
    )


_EPILOG = """\
Use [json COMMAND --help] for command specific help.

Usage Examples:
  Find objects in source.json matching a JSONPath, write them to result.json.
  $ json path -q "$.foo['bar'][?@.baz > 1]" -f source.json -o result.json

  Resolve a JSON Pointer against source.json, pretty print the result to stdout.
  $ json --pretty pointer -p "/foo/bar/0" -f source.json

  Apply JSON Patch patch.json to JSON from stdin, output to result.json.
  $ cat source.json | json patch /path/to/patch.json -o result.json
"""


class DescriptionHelpFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """Raw epilog formatter with defaults."""


def setup_parser() -> argparse.ArgumentParser:  # noqa: D103
    parser = argparse.ArgumentParser(
        prog="json",
        formatter_class=DescriptionHelpFormatter,
        description="JSONPath, JSON Pointer and JSON Patch utilities.",
        epilog=_EPILOG,
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show stack traces.",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Add indents and newlines to output JSON.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"python-jsonpath, version {__version__}",
        help="Show the version and exit.",
    )

    parser.add_argument(
        "--no-unicode-escape",
        action="store_true",
        help="Disable decoding of UTF-16 escape sequence within paths and pointers.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="COMMAND",
    )

    path_sub_command(
        subparsers.add_parser(
            name="path",
            help="Find objects in a JSON document given a JSONPath.",
            description="Find objects in a JSON document given a JSONPath.",
        )
    )

    pointer_sub_command(
        subparsers.add_parser(
            name="pointer",
            help="Resolve a JSON Pointer against a JSON document.",
            description="Resolve a JSON Pointer against a JSON document.",
        )
    )

    patch_sub_command(
        subparsers.add_parser(
            name="patch",
            help="Apply a JSON Patch to a JSON document.",
            description="Apply a JSON Patch to a JSON document.",
        )
    )

    return parser


def handle_path_command(args: argparse.Namespace) -> None:  # noqa: PLR0912
    """Handle the `path` sub command."""
    # Empty string is OK.
    if args.query is not None:
        path = args.query
    else:
        path = args.query_file.read().strip()

    try:
        path = jsonpath.JSONPathEnvironment(
            unicode_escape=not args.no_unicode_escape
        ).compile(path)
    except JSONPathSyntaxError as err:
        if args.debug:
            raise
        sys.stderr.write(f"json path syntax error: {err}\n")
        sys.exit(1)
    except JSONPathTypeError as err:
        if args.debug:
            raise
        sys.stderr.write(f"json path type error: {err}\n")
        sys.exit(1)
    except JSONPathIndexError as err:
        if args.debug:
            raise
        sys.stderr.write(f"json path index error: {err}\n")
        sys.exit(1)

    try:
        matches = path.findall(args.file)
    except json.JSONDecodeError as err:
        if args.debug:
            raise
        sys.stderr.write(f"target document json decode error: {err}\n")
        sys.exit(1)
    except JSONPathTypeError as err:
        # Type errors are currently only occurring are compile-time.
        if args.debug:
            raise
        sys.stderr.write(f"json path type error: {err}\n")
        sys.exit(1)

    indent = INDENT if args.pretty else None
    json.dump(matches, args.output, indent=indent)


def handle_pointer_command(args: argparse.Namespace) -> None:
    """Handle the `pointer` sub command."""
    # Empty string is OK.
    if args.pointer is not None:
        pointer = args.pointer
    else:
        # TODO: is a property with a trailing newline OK?
        pointer = args.pointer_file.read().strip()

    try:
        match = jsonpath.pointer.resolve(
            pointer,
            args.file,
            unicode_escape=not args.no_unicode_escape,
            uri_decode=args.uri_decode,
        )
    except json.JSONDecodeError as err:
        if args.debug:
            raise
        sys.stderr.write(f"target document json decode error: {err}\n")
        sys.exit(1)
    except JSONPointerError as err:
        if args.debug:
            raise
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)

    indent = INDENT if args.pretty else None
    json.dump(match, args.output, indent=indent)


def handle_patch_command(args: argparse.Namespace) -> None:
    """Handle the `patch` sub command."""
    try:
        patch = json.load(args.patch)
    except json.JSONDecodeError as err:
        if args.debug:
            raise
        sys.stderr.write(f"patch document json decode error: {err}\n")
        sys.exit(1)

    if not isinstance(patch, list):
        sys.stderr.write(
            "error: patch file does not look like an array of patch operations"
        )
        sys.exit(1)

    try:
        patched = jsonpath.patch.apply(
            patch,
            args.file,
            unicode_escape=not args.no_unicode_escape,
            uri_decode=args.uri_decode,
        )
    except json.JSONDecodeError as err:
        if args.debug:
            raise
        sys.stderr.write(f"target document json decode error: {err}\n")
        sys.exit(1)
    except JSONPatchError as err:
        if args.debug:
            raise
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)

    indent = INDENT if args.pretty else None
    json.dump(patched, args.output, indent=indent)


def main() -> None:
    """CLI argument parser entry point."""
    parser = setup_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
