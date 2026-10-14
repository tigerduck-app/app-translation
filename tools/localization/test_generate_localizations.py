import importlib.util
import pathlib
import sys
import unittest

_SPEC = importlib.util.spec_from_file_location(
    "generate_localizations", pathlib.Path(__file__).with_name("generate_localizations.py")
)
gen = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = gen  # dataclasses look the module up while it loads
_SPEC.loader.exec_module(gen)


class EscapeAndroidEdgeSpacesTest(unittest.TestCase):
    def test_keeps_leading_and_trailing_spaces(self):
        self.assertEqual(gen._escape_android(" and "), "\\u0020and\\u0020")
        self.assertEqual(gen._escape_android("Dept: "), "Dept:\\u0020")
        self.assertEqual(gen._escape_android(" (Today)"), "\\u0020(Today)")

    def test_keeps_every_edge_space(self):
        self.assertEqual(gen._escape_android("  x  "), "\\u0020\\u0020x\\u0020\\u0020")

    def test_a_value_of_only_spaces_survives(self):
        self.assertEqual(gen._escape_android(" "), "\\u0020")

    def test_inner_spaces_and_other_escapes_are_unchanged(self):
        self.assertEqual(gen._escape_android("a b"), "a b")
        self.assertEqual(gen._escape_android("it's"), "it\\'s")
        self.assertEqual(gen._escape_android("@home"), "\\@home")


if __name__ == "__main__":
    unittest.main()
