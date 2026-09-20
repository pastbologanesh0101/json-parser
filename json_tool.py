#!/usr/bin/env python3
"""Command-line interface for the from-scratch JSON parser/serializer.

Usage:
    python json_tool.py parse file.json      # pretty-print the parsed structure
    python json_tool.py validate file.json   # report valid/invalid + line/col on error
    python json_tool.py minify file.json     # output compact JSON
"""

import argparse
import sys

from jsonlib import loads, dumps, JSONDecodeError


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as exc:
        print(f"Error: could not read {path!r}: {exc}", file=sys.stderr)
        sys.exit(2)


def cmd_parse(path):
    text = _read_file(path)
    try:
        data = loads(text)
    except JSONDecodeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(dumps(data, indent=2))


def cmd_validate(path):
    text = _read_file(path)
    try:
        loads(text)
    except JSONDecodeError as exc:
        print(f"INVALID: {exc}")
        sys.exit(1)
    print("VALID")


def cmd_minify(path):
    text = _read_file(path)
    try:
        data = loads(text)
    except JSONDecodeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(dumps(data, minify=True))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="json_tool.py",
        description="Parse, validate, or minify JSON files using a from-scratch parser.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_parse = sub.add_parser("parse", help="Parse a JSON file and pretty-print the result")
    p_parse.add_argument("file")

    p_validate = sub.add_parser("validate", help="Validate a JSON file (reports line/col on error)")
    p_validate.add_argument("file")

    p_minify = sub.add_parser("minify", help="Output compact/minified JSON")
    p_minify.add_argument("file")

    args = parser.parse_args(argv)

    if args.command == "parse":
        cmd_parse(args.file)
    elif args.command == "validate":
        cmd_validate(args.file)
    elif args.command == "minify":
        cmd_minify(args.file)


if __name__ == "__main__":
    main()
