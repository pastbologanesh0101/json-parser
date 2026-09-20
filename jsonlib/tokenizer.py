"""A hand-written JSON tokenizer (lexer).

Turns raw JSON source text into a flat list of ``Token`` objects, tracking
1-indexed line and column numbers for every character it consumes so that
downstream parse errors can be reported precisely.
"""

from .errors import JSONDecodeError

_WHITESPACE = " \t\n\r"
_HEX_DIGITS = set("0123456789abcdefABCDEF")
_ESCAPE_MAP = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class Token:
    __slots__ = ("type", "value", "line", "col")

    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"


class Tokenizer:
    """Converts JSON source text into a list of tokens."""

    def __init__(self, text):
        self.text = text
        self.length = len(text)
        self.pos = 0
        self.line = 1
        self.col = 1

    # -- low level cursor helpers ------------------------------------------------

    def _error(self, msg, line=None, col=None):
        raise JSONDecodeError(msg, self.line if line is None else line,
                               self.col if col is None else col)

    def _advance(self):
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos] in _WHITESPACE:
            self._advance()

    # -- public entry point -------------------------------------------------------

    def tokenize(self):
        tokens = []
        while True:
            self._skip_whitespace()
            if self.pos >= self.length:
                tokens.append(Token("EOF", None, self.line, self.col))
                break

            ch = self.text[self.pos]
            line, col = self.line, self.col

            if ch == "{":
                self._advance()
                tokens.append(Token("LBRACE", "{", line, col))
            elif ch == "}":
                self._advance()
                tokens.append(Token("RBRACE", "}", line, col))
            elif ch == "[":
                self._advance()
                tokens.append(Token("LBRACKET", "[", line, col))
            elif ch == "]":
                self._advance()
                tokens.append(Token("RBRACKET", "]", line, col))
            elif ch == ":":
                self._advance()
                tokens.append(Token("COLON", ":", line, col))
            elif ch == ",":
                self._advance()
                tokens.append(Token("COMMA", ",", line, col))
            elif ch == '"':
                tokens.append(self._read_string(line, col))
            elif ch == "-" or ch.isdigit():
                tokens.append(self._read_number(line, col))
            elif ch.isalpha():
                tokens.append(self._read_keyword(line, col))
            else:
                self._error(f"Unexpected character {ch!r}", line, col)

        return tokens

    # -- string literals -----------------------------------------------------------

    def _read_string(self, start_line, start_col):
        self._advance()  # opening quote
        chars = []
        while True:
            if self.pos >= self.length:
                self._error("Unterminated string", start_line, start_col)
            ch = self.text[self.pos]
            if ch == '"':
                self._advance()
                break
            if ch == "\\":
                chars.append(self._read_escape())
                continue
            if ord(ch) < 0x20:
                self._error(
                    f"Invalid control character {ch!r} in string literal",
                    self.line, self.col,
                )
            chars.append(ch)
            self._advance()
        return Token("STRING", "".join(chars), start_line, start_col)

    def _read_escape(self):
        esc_line, esc_col = self.line, self.col
        self._advance()  # consume backslash
        if self.pos >= self.length:
            self._error("Unterminated escape sequence in string", esc_line, esc_col)
        esc = self.text[self.pos]
        if esc in _ESCAPE_MAP:
            self._advance()
            return _ESCAPE_MAP[esc]
        if esc == "u":
            self._advance()
            code = self._read_hex4(esc_line, esc_col)
            if 0xD800 <= code <= 0xDBFF and self.text[self.pos:self.pos + 2] == "\\u":
                save = (self.pos, self.line, self.col)
                self._advance()
                self._advance()
                try:
                    low = self._read_hex4(esc_line, esc_col)
                except JSONDecodeError:
                    self.pos, self.line, self.col = save
                    return chr(code)
                if 0xDC00 <= low <= 0xDFFF:
                    combined = ((code - 0xD800) << 10) + (low - 0xDC00) + 0x10000
                    return chr(combined)
                # Not a valid low surrogate: emit both code points as-is.
                return chr(code) + chr(low)
            return chr(code)
        self._error(f"Invalid escape character '\\{esc}'", esc_line, esc_col)

    def _read_hex4(self, esc_line, esc_col):
        digits = []
        for _ in range(4):
            if self.pos >= self.length or self.text[self.pos] not in _HEX_DIGITS:
                self._error("Invalid \\u escape: expected 4 hex digits", esc_line, esc_col)
            digits.append(self.text[self.pos])
            self._advance()
        return int("".join(digits), 16)

    # -- numbers ---------------------------------------------------------------------

    def _read_number(self, start_line, start_col):
        start_pos = self.pos
        if self.text[self.pos] == "-":
            self._advance()
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                self._error("Invalid number: expected digit after '-'", self.line, self.col)

        if self.pos >= self.length or not self.text[self.pos].isdigit():
            self._error("Invalid number literal", start_line, start_col)

        if self.text[self.pos] == "0":
            self._advance()
        else:
            while self.pos < self.length and self.text[self.pos].isdigit():
                self._advance()

        is_float = False

        if self.pos < self.length and self.text[self.pos] == ".":
            is_float = True
            self._advance()
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                self._error("Invalid number: expected digit after decimal point",
                             self.line, self.col)
            while self.pos < self.length and self.text[self.pos].isdigit():
                self._advance()

        if self.pos < self.length and self.text[self.pos] in "eE":
            is_float = True
            self._advance()
            if self.pos < self.length and self.text[self.pos] in "+-":
                self._advance()
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                self._error("Invalid number: expected digit in exponent",
                             self.line, self.col)
            while self.pos < self.length and self.text[self.pos].isdigit():
                self._advance()

        raw = self.text[start_pos:self.pos]
        value = float(raw) if is_float else int(raw)
        return Token("NUMBER", value, start_line, start_col)

    # -- literals: true / false / null ------------------------------------------------

    def _read_keyword(self, start_line, start_col):
        start_pos = self.pos
        while self.pos < self.length and self.text[self.pos].isalpha():
            self._advance()
        word = self.text[start_pos:self.pos]
        if word == "true":
            return Token("TRUE", True, start_line, start_col)
        if word == "false":
            return Token("FALSE", False, start_line, start_col)
        if word == "null":
            return Token("NULL", None, start_line, start_col)
        self._error(f"Unexpected token {word!r}", start_line, start_col)
