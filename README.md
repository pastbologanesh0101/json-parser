# JSON Parser

[![tests](https://github.com/pastbologanesh0101/json-parser/actions/workflows/tests.yml/badge.svg)](https://github.com/pastbologanesh0101/json-parser/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A JSON parser and serializer built entirely from scratch in pure Python —
no `json` module, no third-party dependencies. It tokenizes and parses
JSON by hand with a recursive-descent parser, serializes native Python
objects back to JSON (compact or pretty-printed), and — the main point of
the project — reports malformed input with precise **line and column**
numbers instead of a generic "invalid JSON" message.

The standard library's `json` module is used *only* inside the test
suite, as an oracle to cross-check correctness. It is never imported by
the implementation itself (`jsonlib/`).

## Why build this

Most JSON libraries hide the interesting part: how do you turn a stream
of bytes into structured data, and how do you tell a user *exactly*
where their document went wrong? This project implements that pipeline
end to end: tokenizer -> parser -> in-memory Python value, and the
reverse: Python value -> serializer -> JSON text.

## Design

### Grammar

The parser implements the JSON grammar from RFC 8259:

```
value    := object | array | string | number | "true" | "false" | "null"
object   := "{" ( member ( "," member )* )? "}"
member   := string ":" value
array    := "[" ( value ( "," value )* )? "]"
string   := '"' char* '"'
number   := "-"? int frac? exp?
```

### Tokenizer (`jsonlib/tokenizer.py`)

A single-pass scanner (`Tokenizer`) walks the source text character by
character and emits a flat list of `Token(type, value, line, col)`
objects. It tracks a `(line, col)` cursor manually: every character
consumed advances the column, and every `\n` advances the line and
resets the column to 1. This is the foundation the whole error-reporting
story rests on — every token knows exactly where it started.

The tokenizer handles:

- Structural characters: `{ } [ ] : ,`
- Strings, with escapes `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`,
  and `\uXXXX` unicode escapes (including UTF-16 surrogate pairs, e.g.
  `😀` for an emoji outside the BMP)
- Numbers in every JSON form: integers, negative numbers, decimals,
  and exponents (`1e10`, `1.5e-3`, `1.5E+3`), rejecting malformed forms
  like a bare `-`, a `.` with no following digit, or an empty exponent
- Literals `true`, `false`, `null`
- Whitespace (spaces, tabs, newlines, carriage returns) between tokens

Unterminated strings, invalid escapes, invalid `\u` sequences, and
unrecognized characters all raise `JSONDecodeError` at the exact
position where the problem was detected.

### Parser (`jsonlib/parser.py`)

A recursive-descent `Parser` walks the token list and builds native
Python values: `dict`, `list`, `str`, `int`/`float`, `bool`, `None`.
Each grammar production (`_parse_value`, `_parse_object`, `_parse_array`)
maps directly to a method. Every place the grammar can be violated —
a missing `:`, a missing `,`, a trailing comma, a bad property name, an
unexpected token where a value was expected, trailing data after the
document ends — raises `JSONDecodeError` using the *current token's*
line/col, so the message points at the actual offending character, not
just "somewhere in your file."

### Serializer (`jsonlib/serializer.py`)

`dumps(obj, indent=None, minify=False)` walks a Python value and builds
a JSON string:

- Strings are escaped for `"`, `\`, and all control characters
  (including `\n`, `\t`, `\r`, `\b`, `\f`, and `\u00XX` for anything
  else below `0x20`).
- `indent=None` (default) produces compact, readable output with
  `", "` / `": "` separators.
- `indent=<n>` produces pretty-printed output indented `n` spaces per
  nesting level, with empty objects/arrays collapsed to `{}` / `[]`.
- `minify=True` strips all separator whitespace for the smallest
  possible output.
- Floats are rendered with `repr()`, which gives the shortest string
  that still round-trips to the exact same float — this is what keeps
  `parse(serialize(x)) == x` true for numbers like `1.5e-3`.

### Error reporting

`JSONDecodeError` (in `jsonlib/errors.py`) always carries `.msg`,
`.line`, and `.col`, and its string form reads like:

```
Expecting property name enclosed in double quotes at line 4, column 1
```

Example — parsing this malformed file (a trailing comma after the last
object member):

```json
{
  "a": 1,
  "b": 2,
}
```

produces:

```
$ python json_tool.py validate bad.json
INVALID: Expecting property name enclosed in double quotes at line 4, column 1
```

The column points at the `}` on line 4 — the exact character the parser
was looking at when it discovered the trailing comma was illegal.

## CLI usage

```
python json_tool.py parse file.json      # pretty-print the parsed structure
python json_tool.py validate file.json   # print VALID, or INVALID + line/col
python json_tool.py minify file.json     # print compact JSON
```

Examples:

```
$ python json_tool.py parse good.json
{
  "name": "test",
  "values": [
    1,
    2.5,
    true,
    null
  ]
}

$ python json_tool.py minify good.json
{"name":"test","values":[1,2.5,true,null]}

$ python json_tool.py validate good.json
VALID
```

## Library usage

```python
from jsonlib import loads, dumps, JSONDecodeError

data = loads('{"a": [1, 2, 3]}')
text = dumps(data, indent=2)

try:
    loads('{"a": 1,}')
except JSONDecodeError as e:
    print(e.line, e.col, e.msg)
```

## Testing

The suite (in `tests/`, built on `unittest`) has 69 tests across five
files:

- `test_parsing.py` — every JSON type (object, array, string with every
  escape sequence including `\uXXXX` and surrogate pairs, numbers in
  every numeric form, `true`/`false`/`null`), plus deeply nested
  structures.
- `test_serialization.py` — string escaping, compact vs. pretty-print
  indentation, and round-tripping complex nested structures through our
  own parser and serializer.
- `test_errors.py` — malformed input (trailing comma in object/array,
  missing colon, unterminated string, unexpected token, empty input,
  unexpected character, a multi-line document) each asserted against
  the **exact** expected line and column, not just "raises an
  exception."
- `test_cross_check.py` — parses/serializes a wide variety of documents
  (empty containers, unicode, very large/small numbers, deep nesting)
  and asserts semantic equivalence against Python's real `json` module
  in both directions (our parser vs. `json.loads`, our serializer's
  output reparsed by both parsers).

Run everything:

```
python -m unittest discover -s tests -v
```

All 69 tests pass locally on Python 3.11+ and in CI
(`.github/workflows/tests.yml`, matrix over Python 3.11 and 3.12).

## Project layout

```
jsonlib/
  errors.py       JSONDecodeError (msg, line, col)
  tokenizer.py     Tokenizer, Token
  parser.py        Parser, parse_text
  serializer.py    dumps()
  __init__.py      public API: loads, dumps, JSONDecodeError
json_tool.py       CLI: parse / validate / minify
tests/             unittest suite (69 tests)
```

## License

MIT - see [LICENSE](LICENSE).
