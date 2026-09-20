"""jsonlib: a JSON parser and serializer built entirely from scratch.

No use of Python's built-in ``json`` module anywhere in this package -
tokenizing, parsing, and serializing are all hand-written. The public
API intentionally mirrors ``json.loads`` / ``json.dumps`` so it is a
drop-in mental model, but the implementation underneath is ours.
"""

from .errors import JSONDecodeError
from .tokenizer import Tokenizer, Token
from .parser import Parser, parse_text
from .serializer import dumps

__all__ = [
    "loads",
    "dumps",
    "JSONDecodeError",
    "Tokenizer",
    "Token",
    "Parser",
]


def loads(text):
    """Parse a JSON document (``str``) into native Python objects."""
    return parse_text(text)
