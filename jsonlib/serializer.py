"""Serialize native Python objects back into JSON text.

Supports both compact and pretty-printed (indented) output, with proper
string escaping. No use of the standard library ``json`` module.
"""

_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
    "\b": "\\b",
    "\f": "\\f",
}


def _escape_string(s):
    out = ['"']
    for ch in s:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _format_float(n):
    if n != n:  # NaN
        raise ValueError("Out of range float values (NaN) are not JSON serializable")
    if n == float("inf") or n == float("-inf"):
        raise ValueError("Out of range float values (Infinity) are not JSON serializable")
    return repr(n)


def _dump(obj, indent, depth, item_sep, key_sep):
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return _escape_string(obj)
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        return _format_float(obj)
    if isinstance(obj, dict):
        return _dump_object(obj, indent, depth, item_sep, key_sep)
    if isinstance(obj, (list, tuple)):
        return _dump_array(obj, indent, depth, item_sep, key_sep)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _dump_object(obj, indent, depth, item_sep, key_sep):
    if not obj:
        return "{}"
    entries = []
    for key, value in obj.items():
        if not isinstance(key, str):
            raise TypeError("JSON object keys must be strings")
        entries.append((_escape_string(key), _dump(value, indent, depth + 1, item_sep, key_sep)))

    if indent is None:
        body = item_sep.join(f"{k}{key_sep}{v}" for k, v in entries)
        return "{" + body + "}"

    pad = " " * (indent * (depth + 1))
    closing_pad = " " * (indent * depth)
    body = (",\n").join(f"{pad}{k}{key_sep}{v}" for k, v in entries)
    return "{\n" + body + "\n" + closing_pad + "}"


def _dump_array(arr, indent, depth, item_sep, key_sep):
    if not arr:
        return "[]"
    values = [_dump(v, indent, depth + 1, item_sep, key_sep) for v in arr]

    if indent is None:
        return "[" + item_sep.join(values) + "]"

    pad = " " * (indent * (depth + 1))
    closing_pad = " " * (indent * depth)
    body = (",\n").join(f"{pad}{v}" for v in values)
    return "[\n" + body + "\n" + closing_pad + "]"


def dumps(obj, indent=None, minify=False):
    """Serialize ``obj`` to a JSON string.

    - ``indent=None`` (default): compact single-line output with
      ``", "``/``": "`` separators (matches the readable default most
      JSON serializers use).
    - ``indent=<int>``: pretty-printed output indented by that many
      spaces per nesting level.
    - ``minify=True``: no whitespace at all around separators
      (overrides the default separators; ignored together with indent).
    """
    key_sep = ":" if minify else ": "
    item_sep = "," if minify else ", "
    return _dump(obj, indent, 0, item_sep, key_sep)
