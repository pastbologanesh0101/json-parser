"""Cross-check our from-scratch parser/serializer against Python's
standard library `json` module.

IMPORTANT: `json` is used here ONLY as an oracle to validate correctness
in tests. The implementation under test (jsonlib/*) never imports it.

For a wide variety of valid JSON documents we assert that:
  - our parser produces a value structurally equal to what `json.loads`
    produces, and
  - re-parsing our serializer's output (with either parser) yields a
    semantically equivalent structure back.
"""

import json as stdjson
import math
import unittest

from jsonlib import loads, dumps


DOCUMENTS = [
    "null",
    "true",
    "false",
    "0",
    "-0",
    "42",
    "-42",
    "3.14159",
    "-3.14159",
    "1e10",
    "1E10",
    "1.5e-3",
    "1.5e+3",
    "2.2250738585072014e-308",   # near float min
    "1.7976931348623157e+308",   # near float max
    '""',
    '"hello world"',
    '"line1\\nline2"',
    '"tab\\ttab"',
    '"quote\\"quote"',
    '"backslash\\\\backslash"',
    '"unicode\\u00e9"',
    '"cjk\\u4e2d\\u6587"',
    '"emoji\\ud83d\\ude00"',
    "[]",
    "{}",
    "[1, 2, 3]",
    '["a", "b", "c"]',
    '{"a": 1, "b": 2, "c": 3}',
    '{"nested": {"a": [1, 2, {"b": null}]}}',
    '[[1, 2], [3, 4], [[5, 6], [7, 8]]]',
    '{"empty_obj": {}, "empty_arr": [], "n": null, "t": true, "f": false}',
    '[1, "two", 3.0, null, true, false, {"six": 6}]',
    '{"unicode_key_\\u00e9": "value", "plain": "\\u4e2d\\u6587 text"}',
    '  {  "a" :  1 ,  "b" :  [ 1 , 2 , 3 ]  }  ',
    '{"a": [1,2,3,[4,5,[6,7,[8,9]]]], "b": {"c": {"d": {"e": "deep"}}}}',
]


class TestCrossCheckParsing(unittest.TestCase):
    """our loads(text) should structurally match json.loads(text)."""

    def test_documents_match_stdlib(self):
        for text in DOCUMENTS:
            with self.subTest(text=text):
                ours = loads(text)
                theirs = stdjson.loads(text)
                self.assertEqual(ours, theirs, f"mismatch for {text!r}")

    def test_large_integer_matches_stdlib(self):
        text = "123456789012345678901234567890123456789"
        self.assertEqual(loads(text), stdjson.loads(text))

    def test_negative_zero_matches_stdlib_numerically(self):
        self.assertEqual(loads("-0"), stdjson.loads("-0"))

    def test_very_small_float_matches_stdlib(self):
        text = "1e-300"
        self.assertAlmostEqual(loads(text), stdjson.loads(text))

    def test_very_large_float_matches_stdlib(self):
        text = "1e300"
        self.assertEqual(loads(text), stdjson.loads(text))

    def test_type_of_integer_vs_float_matches_stdlib(self):
        for text in ["5", "5.0", "5e2", "-5", "-5.5"]:
            with self.subTest(text=text):
                ours = loads(text)
                theirs = stdjson.loads(text)
                self.assertIs(type(ours), type(theirs))


class TestCrossCheckSerialization(unittest.TestCase):
    """Round trip: our dumps(obj), re-parsed by both parsers, should
    agree with each other and with the original object."""

    OBJECTS = [
        None, True, False, 0, -1, 123456, -3.5, 1e10, 1.5e-3,
        "", "plain string", "with\nnewline", "with\ttab", 'with"quote',
        "unicode é中文",
        [], {}, [1, 2, 3], {"a": 1, "b": 2},
        {"nested": {"list": [1, 2, {"deep": True}], "n": None}},
        [1, "two", 3.0, None, True, False, {"six": 6}],
        {"empty_obj": {}, "empty_arr": [], "unicode": "éèê"},
        list(range(50)),
        {"k%d" % i: i for i in range(20)},
    ]

    def test_our_dump_reparsed_by_stdlib_matches_object(self):
        for obj in self.OBJECTS:
            with self.subTest(obj=obj):
                text = dumps(obj)
                self.assertEqual(stdjson.loads(text), obj)

    def test_our_dump_reparsed_by_ours_matches_object(self):
        for obj in self.OBJECTS:
            with self.subTest(obj=obj):
                text = dumps(obj)
                self.assertEqual(loads(text), obj)

    def test_stdlib_dump_reparsed_by_ours_matches_object(self):
        for obj in self.OBJECTS:
            with self.subTest(obj=obj):
                text = stdjson.dumps(obj)
                self.assertEqual(loads(text), obj)

    def test_pretty_output_reparses_to_same_value_both_parsers(self):
        obj = {"a": [1, 2, {"b": "c", "d": [3, 4]}], "e": None}
        pretty = dumps(obj, indent=2)
        self.assertEqual(stdjson.loads(pretty), obj)
        self.assertEqual(loads(pretty), obj)


if __name__ == "__main__":
    unittest.main()
