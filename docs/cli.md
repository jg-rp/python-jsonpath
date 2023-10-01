# Command Line Interface

**_New in version 0.9.0_**

Python JSONPath includes a script called `json`, exposing [JSONPath](quickstart.md#findallpath-data), [JSON Pointer](quickstart.md#pointerresolvepointer-data) and [JSON Patch](quickstart.md#patchapplypatch-data) features on the command line. Use the `--version` argument to check the current version of Python JSONPath, and the `--help` argument to display command information.

```console
$ json --version
python-jsonpath, version 0.9.0
```

```console
$ json --help
usage: json [-h] [--debug] [--pretty] [-v] [--no-unicode-escape] COMMAND ...

JSONPath, JSON Pointer and JSON Patch utilities.

positional arguments:
  COMMAND
    path               Find objects in a JSON document given a JSONPath.
    pointer            Resolve a JSON Pointer against a JSON document.
    patch              Apply a JSON Patch to a JSON document.

optional arguments:
  -h, --help           show this help message and exit
  --debug              Show stack traces. (default: False)
  --pretty             Add indents and newlines to output JSON. (default: False)
  -v, --version        Show the version and exit.
  --no-unicode-escape  Disable decoding of UTF-16 escape sequence within paths and pointers. (default:
                       False)

Use [json COMMAND --help] for command specific help.

Usage Examples:
  Find objects in source.json matching a JSONPath, write them to result.json.
  $ json path -q "$.foo['bar'][?@.baz > 1]" -f source.json -o result.json

  Resolve a JSON Pointer against source.json, pretty print the result to stdout.
  $ json --pretty pointer -p "/foo/bar/0" -f source.json

  Apply JSON Patch patch.json to JSON from stdin, output to result.json.
  $ cat source.json | json patch /path/to/patch.json -o result.json
```

Use `json COMMAND --help` for command specific help.

```console
$ json path --help
usage: json path [-h] (-q QUERY | -r PATH_FILE) [-f FILE] [-o OUTPUT]

Find objects in a JSON document given a JSONPath.

optional arguments:
  -h, --help            show this help message and exit
  -q QUERY, --query QUERY
                        JSONPath query string.
  -r PATH_FILE, --path-file PATH_FILE
                        Text file containing a JSONPath query.
  -f FILE, --file FILE  File to read the target JSON document from. Defaults to reading from the
                        standard input stream.
  -o OUTPUT, --output OUTPUT
                        File to write resulting objects to, as a JSON array. Defaults to the standard
                        output stream.
  --no-type-checks      Disables filter expression well-typedness checks.
```

## Global Options

These arguments apply to any subcommand and must be listed before the command.

### `--debug`

Enable debugging. Display full stack traces, if available, when errors occur. Without the `--debug` option, the following example shows a short "json path syntax error" message.

```console
$ json path -q "$.1" -f /tmp/source.json
json path syntax error: unexpected token '1', line 1, column 2
```

With the `--debug` option, we get the stack trace triggered by `JSONPathSyntaxError`.

```console
$ json --debug path -q "$.1" -f /tmp/source.json
Traceback (most recent call last):
  File "/home/james/.local/share/virtualenvs/jsonpath_cli-8Tb3e-ir/bin/json", line 8, in <module>
    sys.exit(main())
  File "/home/james/.local/share/virtualenvs/jsonpath_cli-8Tb3e-ir/lib/python3.9/site-packages/jsonpath/cli.py", line 338, in main
    args.func(args)
  File "/home/james/.local/share/virtualenvs/jsonpath_cli-8Tb3e-ir/lib/python3.9/site-packages/jsonpath/cli.py", line 234, in handle_path_command
    path = jsonpath.compile(args.query or args.path_file.read())
  File "/home/james/.local/share/virtualenvs/jsonpath_cli-8Tb3e-ir/lib/python3.9/site-packages/jsonpath/env.py", line 148, in compile
    _path: Union[JSONPath, CompoundJSONPath] = JSONPath(
  File "/home/james/.local/share/virtualenvs/jsonpath_cli-8Tb3e-ir/lib/python3.9/site-packages/jsonpath/path.py", line 49, in __init__
    self.selectors = tuple(selectors)
  File "/home/james/.local/share/virtualenvs/jsonpath_cli-8Tb3e-ir/lib/python3.9/site-packages/jsonpath/parse.py", line 256, in parse
    raise JSONPathSyntaxError(
jsonpath.exceptions.JSONPathSyntaxError: unexpected token '1', line 1, column 2
```

### `--pretty`

Enable pretty formatting when outputting JSON. Adds newlines and indentation to output specified with the `-o` or `--output` option. Without the `--pretty` option, the following example output is on one line.

```console
$ json pointer -p "/categories/1/products/0" -f /tmp/source.json
{"title": "Cap", "description": "Baseball cap", "price": 15.0}
```

With the `--pretty` option, we get nicely formatted JSON output.

```console
$ json --pretty pointer -p "/categories/1/products/0" -f /tmp/source.json
{
  "title": "Cap",
  "description": "Baseball cap",
  "price": 15.0
}
```

### `--no-unicode-escape`

Disable decoding of UTF-16 escape sequences, including surrogate paris. This can improve performance if you know your paths and pointers don't contain UTF-16 escape sequences.

```console
$ json --no-unicode-escape path -q "$.price_cap" -f /tmp/source.json
```

## Commands

One of the subcommands `path`, `pointer` or `patch` must be specified, depending on whether you want to search a JSON document with a JSONPath, resolve a JSON Pointer against a JSON document or apply a JSON Patch to a JSON Document.

### `path`

Find objects in a JSON document given a JSONPath. One of `-q`/`--query` or `-r`/`--path-file` must be given. `-q` being a JSONPath given on the command line as a string, `-r` being the path to a file containing a JSONPath.

```
json path [-h] (-q QUERY | -r PATH_FILE) [-f FILE] [-o OUTPUT]
```

#### `-q` / `--query`

The JSONPath as a string.

```console
$ json path -q "$.price_cap" -f /tmp/source.json
```

```console
$ json path --query "$.price_cap" -f /tmp/source.json
```

#### `-r` / `--path-file`

The path to a file containing a JSONPath.

```console
$ json path -r /tmp/path.txt -f /tmp/source.json
```

```console
$ json path --path-file /tmp/path.txt -f /tmp/source.json
```

#### `-f` / `--file`

The path to a file containing the target JSON document. If omitted or a hyphen (`-`), the target JSON document will be read from the standard input stream.

```console
$ json path -q "$.price_cap" -f /tmp/source.json
```

```console
$ json path -q "$.price_cap" --file /tmp/source.json
```

#### `-o` / `--output`

The path to a file to write resulting objects to, as a JSON array. If omitted or a hyphen (`-`) is given, results will be written to the standard output stream.

```console
$ json path -q "$.price_cap" -f /tmp/source.json -o result.json
```

```console
$ json path -q "$.price_cap" -f /tmp/source.json --output result.json
```

#### `--no-type-checks`

_New in version 0.10.0_

Disables JSONPath filter expression well-typedness checks. The well-typedness of a filter expression is defined by the IETF JSONPath Draft specification.

### `pointer`

Resolve a JSON Pointer against a JSON document. One of `-p`/`--pointer` or `-r`/`--pointer-file` must be given. `-p` being a JSON Pointer given on the command line as a string, `-r` being the path to a file containing a JSON Pointer.

```
json pointer [-h] (-p POINTER | -r POINTER_FILE) [-f FILE] [-o OUTPUT] [-u]
```

#### `-p` / `--pointer`

An RFC 6901 formatted JSON Pointer string.

```console
$ json pointer -p "/categories/0/name" -f /tmp/source.json
```

```console
$ json pointer --pointer "/categories/0/name" -f /tmp/source.json
```

#### `-r` / `--pointer-file`

The path to a file containing a JSON Pointer.

```console
$ json pointer -r /tmp/pointer.txt -f /tmp/source.json
```

```console
$ json pointer --pointer-file /tmp/pointer.txt -f /tmp/source.json
```

#### `-f` / `--file`

The path to a file containing the target JSON document. If omitted or a hyphen (`-`), the target JSON document will be read from the standard input stream.

```console
$ json pointer -p "/categories/0/name" -f /tmp/source.json
```

```console
$ json pointer -p "/categories/0/name" --file /tmp/source.json
```

#### `-o` / `--output`

The path to a file to write the resulting object to. If omitted or a hyphen (`-`) is given, results will be written to the standard output stream.

```console
$ json pointer -p "/categories/0/name" -f /tmp/source.json -o result.json
```

```console
$ json pointer -p "/categories/0/name" -f /tmp/source.json --output result.json
```

#### `-u` / `--uri-decode`

Enable URI decoding of the JSON Pointer. In this example, we would look for a property called "hello world" in the root of the target document.

```console
$ json pointer -p "/hello%20world" -f /tmp/source.json -u
```

```console
$ json pointer -p "/hello%20world" -f /tmp/source.json --uri-decode
```

### `patch`

Apply a JSON Patch to a JSON document. Unlike `path` and `pointer` commands, a patch can't be given as a string argument. `PATCH` is a positional argument that should be a file path to a JSON Patch document or a hyphen (`-`), which means the patch document will be read from the standard input stream.

```
json patch [-h] [-f FILE] [-o OUTPUT] [-u] PATCH
```

These examples read the patch from `patch.json` and the document to modify from `target.json`

```console
$ json patch /tmp/patch.json -f /tmp/target.json
```

```console
$ cat /tmp/patch.json | json patch - -f /tmp/target.json
```

#### `-f` / `--file`

The path to a file containing the target JSON document. If omitted or a hyphen (`-`), the target JSON document will be read from the standard input stream.

```console
$ json patch /tmp/patch.json -f /tmp/target.json
```

```console
$ json patch /tmp/patch.json --file /tmp/target.json
```

#### `-o` / `--output`

The path to a file to write the resulting object to. If omitted or a hyphen (`-`) is given, results will be written to the standard output stream.

```console
$ json patch /tmp/patch.json -f /tmp/target.json -o result.json
```

```console
$ json patch /tmp/patch.json -f /tmp/target.json --output result.json
```

#### `-u` / `--uri-decode`

Enable URI decoding of JSON Pointers in the patch document.

```console
$ json patch /tmp/patch.json -f /tmp/target.json -u
```

```console
$ json patch /tmp/patch.json -f /tmp/target.json --uri-decode
```
