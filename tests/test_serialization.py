"""Tests for the serializer: escaping, compact/pretty modes, and
round-tripping through our own parser."""

import unittest

from jsonlib import loads, dumps


class TestSerializerBasics(unittest.TestCase):
    def test_dump_null_true_false(self):
        self.assertEqual(dumps(None), "null")
        self.assertEqual(dumps(True), "true")
        self.assertEqual(dumps(False), "false")

    def test_dump_int(self):
        self.assertEqual(dumps(42), "42")
        self.assertEqual(dumps(-7), "-7")

    def test_dump_float(self):
        self.assertEqual(dumps(3.5), "3.5")

    def test_dump_string_escapes_quotes_and_backslash(self):
        self.assertEqual(dumps('a"b\\c'), '"a\\"b\\\\c"')

    def test_dump_string_escapes_control_chars(self):
        self.assertEqual(dumps("a\nb\tc\rd"), '"a\\nb\\tc\\rd"')

    def test_dump_string_escapes_low_control_char(self):
        self.assertEqual(dumps("\x01"), '"\\u0001"')

    def test_dump_empty_object_and_array(self):
        self.assertEqual(dumps({}), "{}")
        self.assertEqual(dumps([]), "[]")

    def test_dump_compact_object(self):
        self.assertEqual(dumps({"a": 1, "b": 2}), '{"a": 1, "b": 2}')

    def test_dump_minify_has_no_spaces(self):
        self.assertEqual(dumps({"a": 1, "b": [1, 2]}, minify=True), '{"a":1,"b":[1,2]}')

    def test_tuple_serializes_like_list(self):
        self.assertEqual(dumps((1, 2, 3)), "[1, 2, 3]")


class TestPrettyPrint(unittest.TestCase):
    def test_pretty_object_indentation(self):
        result = dumps({"a": 1, "b": 2}, indent=2)
        expected = '{\n  "a": 1,\n  "b": 2\n}'
        self.assertEqual(result, expected)

    def test_pretty_nested_indentation(self):
        result = dumps({"a": [1, 2]}, indent=2)
        expected = '{\n  "a": [\n    1,\n    2\n  ]\n}'
        self.assertEqual(result, expected)

    def test_pretty_indent_width_four(self):
        result = dumps({"x": 1}, indent=4)
        expected = '{\n    "x": 1\n}'
        self.assertEqual(result, expected)

    def test_pretty_empty_containers_stay_compact(self):
        result = dumps({"a": {}, "b": []}, indent=2)
        expected = '{\n  "a": {},\n  "b": []\n}'
        self.assertEqual(result, expected)


class TestRoundTrip(unittest.TestCase):
    def test_round_trip_complex_structure(self):
        data = {
            "name": "TransportLab",
            "active": True,
            "score": 98.6,
            "tags": ["json", "parser", None, False],
            "meta": {
                "nested": {"deep": [1, 2, {"x": "y\nz"}]},
                "empty_obj": {},
                "empty_arr": [],
            },
            "big_number": 123456789012345678901234567890,
            "small_number": 1.5e-10,
        }
        serialized = dumps(data)
        self.assertEqual(loads(serialized), data)

    def test_round_trip_pretty_matches_compact_semantically(self):
        data = {"a": [1, 2, {"b": "c"}], "d": None}
        compact = dumps(data)
        pretty = dumps(data, indent=2)
        self.assertEqual(loads(compact), loads(pretty))
        self.assertEqual(loads(pretty), data)

    def test_round_trip_all_primitive_types(self):
        for value in [None, True, False, 0, -1, 1.5, "", "hi", [], {}]:
            self.assertEqual(loads(dumps(value)), value)

    def test_round_trip_unicode_string(self):
        data = {"greeting": "你好, 世界! \U0001F600"}
        self.assertEqual(loads(dumps(data)), data)


if __name__ == "__main__":
    unittest.main()
