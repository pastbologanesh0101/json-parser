"""Tests that malformed JSON produces clear errors with the *exact*
line and column at which the problem was detected.

These values were derived by manually counting characters (1-indexed,
newlines increment the line and reset the column to 1) in each crafted
input, then confirmed against the implementation.
"""

import unittest

from jsonlib import loads
from jsonlib.errors import JSONDecodeError


class TestErrorPositions(unittest.TestCase):
    def test_trailing_comma_in_object(self):
        # {"a": 1,}
        #  123456789
        # The '}' that follows the illegal trailing comma sits at column 9.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads('{"a": 1,}')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 9)
        self.assertIn("property name", ctx.exception.msg)

    def test_trailing_comma_in_array(self):
        # [1, 2,]
        #  1234567
        # After the trailing comma, ']' sits at column 7.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads("[1, 2,]")
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 7)

    def test_missing_colon(self):
        # {"a" 1}
        #  1234567
        # The NUMBER token '1' (expected ':' instead) starts at column 6.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads('{"a" 1}')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 6)
        self.assertIn("':'", ctx.exception.msg)

    def test_unterminated_string(self):
        # {"a": "hello}
        #  1234567
        # The opening quote of the unterminated string is at column 7.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads('{"a": "hello}')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 7)
        self.assertIn("Unterminated string", ctx.exception.msg)

    def test_unexpected_token(self):
        # {"a": tru}
        #  1234567
        # The bogus keyword 'tru' starts at column 7.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads('{"a": tru}')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 7)
        self.assertIn("Unexpected token", ctx.exception.msg)

    def test_empty_input(self):
        with self.assertRaises(JSONDecodeError) as ctx:
            loads("")
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 1)
        self.assertIn("Expecting value", ctx.exception.msg)

    def test_multiline_trailing_comma_reports_correct_line(self):
        text = '{\n  "a": 1,\n  "b": 2,\n}'
        # line 1: '{'
        # line 2: '  "a": 1,'
        # line 3: '  "b": 2,'
        # line 4: '}'   <- the closing brace right after the trailing comma
        with self.assertRaises(JSONDecodeError) as ctx:
            loads(text)
        self.assertEqual(ctx.exception.line, 4)
        self.assertEqual(ctx.exception.col, 1)

    def test_missing_comma_between_array_elements(self):
        # [1 2]
        #  12345
        # The unexpected NUMBER '2' sits at column 4.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads("[1 2]")
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 4)

    def test_error_message_str_contains_line_and_column(self):
        try:
            loads('{"a": 1,}')
        except JSONDecodeError as exc:
            self.assertIn("line 1", str(exc))
            self.assertIn("column 9", str(exc))
        else:
            self.fail("expected JSONDecodeError")

    def test_unexpected_character(self):
        # {"a": @}
        #  12345678
        # The illegal '@' character sits at column 7.
        with self.assertRaises(JSONDecodeError) as ctx:
            loads('{"a": @}')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.col, 7)


if __name__ == "__main__":
    unittest.main()
