"""Tests that every JSON value type is parsed correctly, including
deeply nested structures."""

import unittest

from jsonlib import loads


class TestPrimitives(unittest.TestCase):
    def test_parse_null(self):
        self.assertIsNone(loads("null"))

    def test_parse_true(self):
        self.assertIs(loads("true"), True)

    def test_parse_false(self):
        self.assertIs(loads("false"), False)

    def test_parse_empty_object(self):
        self.assertEqual(loads("{}"), {})

    def test_parse_empty_array(self):
        self.assertEqual(loads("[]"), [])

    def test_parse_simple_object(self):
        self.assertEqual(loads('{"a": 1, "b": 2}'), {"a": 1, "b": 2})

    def test_parse_simple_array(self):
        self.assertEqual(loads("[1, 2, 3]"), [1, 2, 3])


class TestStrings(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(loads('"hello world"'), "hello world")

    def test_escape_newline_tab_quote_backslash(self):
        self.assertEqual(loads('"a\\nb\\tc\\"d\\\\e"'), 'a\nb\tc"d\\e')

    def test_escape_forward_slash(self):
        self.assertEqual(loads('"a\\/b"'), "a/b")

    def test_escape_backspace_and_formfeed(self):
        self.assertEqual(loads('"a\\bb\\fc"'), "a\bb\fc")

    def test_unicode_escape(self):
        self.assertEqual(loads('"\\u00e9"'), "é")

    def test_unicode_escape_cjk(self):
        self.assertEqual(loads('"\\u4e2d\\u6587"'), "中文")

    def test_surrogate_pair_escape(self):
        # U+1F600 GRINNING FACE, encoded as a UTF-16 surrogate pair.
        self.assertEqual(loads('"\\ud83d\\ude00"'), "\U0001F600")

    def test_literal_unicode_in_source(self):
        self.assertEqual(loads('"café"'), "café")


class TestNumbers(unittest.TestCase):
    def test_integer(self):
        self.assertEqual(loads("42"), 42)

    def test_negative_integer(self):
        self.assertEqual(loads("-42"), -42)

    def test_zero(self):
        self.assertEqual(loads("0"), 0)

    def test_decimal(self):
        self.assertEqual(loads("3.14159"), 3.14159)

    def test_negative_decimal(self):
        self.assertEqual(loads("-0.5"), -0.5)

    def test_exponent_positive(self):
        self.assertEqual(loads("1e10"), 1e10)

    def test_exponent_capital_e(self):
        self.assertEqual(loads("1E10"), 1e10)

    def test_exponent_with_plus(self):
        self.assertEqual(loads("1.5e+3"), 1.5e3)

    def test_exponent_negative(self):
        self.assertEqual(loads("1.5e-3"), 1.5e-3)

    def test_large_integer_beyond_float_precision(self):
        self.assertEqual(loads("123456789012345678901234567890"),
                          123456789012345678901234567890)

    def test_integer_result_type_is_int(self):
        self.assertIsInstance(loads("5"), int)

    def test_decimal_result_type_is_float(self):
        self.assertIsInstance(loads("5.0"), float)


class TestNesting(unittest.TestCase):
    def test_nested_object_in_array(self):
        self.assertEqual(loads('[{"a": 1}, {"b": 2}]'), [{"a": 1}, {"b": 2}])

    def test_deeply_nested_structure(self):
        text = '{"a": [1, {"b": [2, 3, {"c": [4, [5, 6, [7, [8, [9]]]]]}]}]}'
        expected = {"a": [1, {"b": [2, 3, {"c": [4, [5, 6, [7, [8, [9]]]]]}]}]}
        self.assertEqual(loads(text), expected)

    def test_deeply_nested_arrays(self):
        depth = 50
        text = "[" * depth + "1" + "]" * depth
        result = loads(text)
        for _ in range(depth):
            self.assertEqual(len(result), 1)
            result = result[0]
        self.assertEqual(result, 1)

    def test_whitespace_is_ignored(self):
        text = '{\n  "a" :  1 ,\n  "b": [ 1,  2,3 ]\n}\n'
        self.assertEqual(loads(text), {"a": 1, "b": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()
