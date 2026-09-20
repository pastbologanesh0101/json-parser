"""A recursive-descent JSON parser built on top of ``jsonlib.tokenizer``.

Grammar (roughly, following RFC 8259)::

    value    := object | array | string | number | "true" | "false" | "null"
    object   := "{" ( member ( "," member )* )? "}"
    member   := string ":" value
    array    := "[" ( value ( "," value )* )? "]"

The parser walks the token stream produced by ``Tokenizer`` and builds
native Python objects (dict, list, str, int/float, bool, None). Every
error path raises ``JSONDecodeError`` with the exact line/column of the
token that violated the grammar.
"""

from .errors import JSONDecodeError
from .tokenizer import Tokenizer


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _current(self):
        return self.tokens[self.pos]

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self):
        tok = self._current()
        if tok.type == "EOF":
            raise JSONDecodeError("Expecting value", tok.line, tok.col)
        value = self._parse_value()
        tok = self._current()
        if tok.type != "EOF":
            raise JSONDecodeError("Extra data after JSON document", tok.line, tok.col)
        return value

    def _parse_value(self):
        tok = self._current()
        if tok.type == "LBRACE":
            return self._parse_object()
        if tok.type == "LBRACKET":
            return self._parse_array()
        if tok.type == "STRING":
            self._advance()
            return tok.value
        if tok.type == "NUMBER":
            self._advance()
            return tok.value
        if tok.type == "TRUE":
            self._advance()
            return True
        if tok.type == "FALSE":
            self._advance()
            return False
        if tok.type == "NULL":
            self._advance()
            return None
        raise JSONDecodeError("Expecting value", tok.line, tok.col)

    def _parse_object(self):
        self._advance()  # consume '{'
        obj = {}
        if self._current().type == "RBRACE":
            self._advance()
            return obj

        while True:
            key_tok = self._current()
            if key_tok.type != "STRING":
                raise JSONDecodeError(
                    "Expecting property name enclosed in double quotes",
                    key_tok.line, key_tok.col,
                )
            key = key_tok.value
            self._advance()

            colon_tok = self._current()
            if colon_tok.type != "COLON":
                raise JSONDecodeError("Expecting ':' delimiter", colon_tok.line, colon_tok.col)
            self._advance()

            obj[key] = self._parse_value()

            sep_tok = self._current()
            if sep_tok.type == "COMMA":
                self._advance()
                next_tok = self._current()
                if next_tok.type == "RBRACE":
                    raise JSONDecodeError(
                        "Expecting property name enclosed in double quotes",
                        next_tok.line, next_tok.col,
                    )
                continue
            if sep_tok.type == "RBRACE":
                self._advance()
                return obj
            raise JSONDecodeError("Expecting ',' delimiter or '}'", sep_tok.line, sep_tok.col)

    def _parse_array(self):
        self._advance()  # consume '['
        arr = []
        if self._current().type == "RBRACKET":
            self._advance()
            return arr

        while True:
            arr.append(self._parse_value())

            sep_tok = self._current()
            if sep_tok.type == "COMMA":
                self._advance()
                next_tok = self._current()
                if next_tok.type == "RBRACKET":
                    raise JSONDecodeError("Expecting value", next_tok.line, next_tok.col)
                continue
            if sep_tok.type == "RBRACKET":
                self._advance()
                return arr
            raise JSONDecodeError("Expecting ',' delimiter or ']'", sep_tok.line, sep_tok.col)


def parse_text(text):
    """Tokenize and parse ``text``, returning the native Python value."""
    tokens = Tokenizer(text).tokenize()
    return Parser(tokens).parse()
