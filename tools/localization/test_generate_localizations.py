import importlib.util
import pathlib
import sys
import tempfile
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


class PlatformOutputTest(unittest.TestCase):
    """Which platforms a run writes, and where: Android builds its own from source."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_a_default_run_writes_apple_and_backend_but_not_android(self):
        gen.generate(validate_only=False, generated_dir=self.tmp)

        self.assertTrue((self.tmp / "apple" / "en.lproj" / "Localizable.strings").exists())
        self.assertTrue((self.tmp / "backend" / "en.json").exists())
        self.assertFalse((self.tmp / "android").exists())

    def test_android_alone_into_a_directory_of_its_own(self):
        out = self.tmp / "res"

        gen.main(["--platform", "android", "--output-dir", str(out)])

        self.assertTrue((out / "values" / "strings.xml").exists())
        self.assertTrue((out / "values-de" / "strings.xml").exists())
        self.assertFalse((out / "android").exists())
        self.assertEqual([], [p for p in self.tmp.iterdir() if p != out])

    def test_an_output_directory_takes_one_platform(self):
        with self.assertRaises(SystemExit):
            gen.main(["--platform", "android", "--platform", "apple", "--output-dir", str(self.tmp)])
        with self.assertRaises(SystemExit):
            gen.main(["--output-dir", str(self.tmp)])

    def test_the_committed_android_output_is_gone(self):
        self.assertFalse((gen.GENERATED_DIR / "android").exists())


if __name__ == "__main__":
    unittest.main()
