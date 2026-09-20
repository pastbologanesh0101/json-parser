"""Error types for the from-scratch JSON parser."""


class JSONDecodeError(ValueError):
    """Raised when JSON source cannot be tokenized or parsed.

    Carries the human-readable message plus the exact 1-indexed line and
    column at which the problem was detected, so callers can point a user
    directly at the offending character.
    """

    def __init__(self, msg, line, col):
        self.msg = msg
        self.line = line
        self.col = col
        super().__init__(f"{msg} at line {line}, column {col}")

    def __repr__(self):
        return f"JSONDecodeError({self.msg!r}, line={self.line}, col={self.col})"
