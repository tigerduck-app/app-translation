import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

_SPEC = importlib.util.spec_from_file_location(
    "check_sources", pathlib.Path(__file__).with_name("check_sources.py")
)
check = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = check
_SPEC.loader.exec_module(check)


def grouped(shared=None, android=None, apple=None, backend=None):
    """A locale's source, every group present, as source/<locale>.json holds it."""
    return {
        "shared": dict(shared or {}),
        "android": dict(android or {}),
        "apple": dict(apple or {}),
        "backend": dict(backend or {}),
    }


class KeysTest(unittest.TestCase):
    """Every locale has every key en has, in the same group, and nothing else."""

    def test_matching_locales_pass(self):
        sources = {
            "en": grouped(shared={"a": "One", "b": "Two"}, apple={"c": "Three"}),
            "de": grouped(shared={"a": "Eins", "b": "Zwei"}, apple={"c": "Drei"}),
        }

        self.assertEqual([], check.check_keys(sources, "en"))

    def test_the_same_number_of_keys_is_not_enough(self):
        sources = {
            "en": grouped(shared={"a": "One", "b": "Two"}),
            "de": grouped(shared={"a": "Eins", "x": "Zwei"}),
        }

        problems = check.check_keys(sources, "en")

        self.assertIn("source/de.json shared: missing b", problems)
        self.assertIn("source/de.json shared: extra x", problems)

    def test_a_key_in_another_group_is_missing_from_its_own(self):
        sources = {
            "en": grouped(shared={"a": "One"}),
            "de": grouped(android={"a": "Eins"}),
        }

        problems = check.check_keys(sources, "en")

        self.assertIn("source/de.json shared: missing a", problems)
        self.assertIn("source/de.json android: extra a", problems)

    def test_every_locale_and_every_key_is_reported_at_once(self):
        en_keys = {f"key_{n:02d}": "Value" for n in range(30)}
        sources = {
            "en": grouped(shared=en_keys),
            "de": grouped(),
            "fr": grouped(shared={"key_00": "Valeur"}),
        }

        problems = check.check_keys(sources, "en")

        self.assertEqual(30, sum(p.startswith("source/de.json shared: missing ") for p in problems))
        self.assertEqual(29, sum(p.startswith("source/fr.json shared: missing ") for p in problems))

    def test_a_value_is_a_string_with_something_in_it(self):
        sources = {
            "en": grouped(shared={"a": "One", "b": "Two", "c": "Three"}),
            "de": grouped(shared={"a": "", "b": "   ", "c": 3}),
        }

        problems = check.check_keys(sources, "en")

        self.assertIn("source/de.json shared: a is empty", problems)
        self.assertIn("source/de.json shared: b is empty", problems)
        self.assertIn("source/de.json shared: c is not a string", problems)

    def test_english_itself_is_checked_for_empty_values(self):
        sources = {"en": grouped(shared={"a": ""})}

        self.assertIn("source/en.json shared: a is empty", check.check_keys(sources, "en"))

    def test_groups_are_the_four_known_ones(self):
        de = grouped(shared={"a": "Eins"})
        del de["backend"]
        de["web"] = {}
        sources = {"en": grouped(shared={"a": "One"}), "de": de}

        problems = check.check_keys(sources, "en")

        self.assertIn("source/de.json: unknown group web", problems)
        self.assertIn("source/de.json: no backend group", problems)

    def test_a_shared_key_is_not_also_a_platform_key(self):
        both = grouped(shared={"a": "One"}, android={"a": "Uno"})
        sources = {"en": both}

        self.assertIn("source/en.json: a is in both shared and android", check.check_keys(sources, "en"))

    def test_a_key_twice_in_one_group_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "source").mkdir()
            (root / "source" / "en.json").write_text(
                '{"shared": {"a": "One", "a": "Again"}, "android": {}, "apple": {}, "backend": {}}',
                encoding="utf-8",
            )

            sources, problems = check.load_sources(root / "source")

        self.assertIn("source/en.json: a appears twice", problems)
        self.assertEqual("Again", sources["en"]["shared"]["a"])

    def test_a_file_that_is_not_utf8_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "source").mkdir()
            (root / "source" / "de.json").write_bytes('{"shared": {"a": "Gr\u00fc\u00dfe"}}'.encode("latin-1"))

            sources, problems = check.load_sources(root / "source")

        self.assertNotIn("de", sources)
        self.assertEqual(1, len(problems))
        self.assertTrue(problems[0].startswith("source/de.json: not UTF-8"))

    def test_a_file_that_is_not_json_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "source").mkdir()
            (root / "source" / "de.json").write_text('{"shared": {"a": "Eins",}}', encoding="utf-8")

            sources, problems = check.load_sources(root / "source")

        self.assertNotIn("de", sources)
        self.assertEqual(1, len(problems))
        self.assertTrue(problems[0].startswith("source/de.json: not valid JSON"))


class UntranslatedTest(unittest.TestCase):
    """A value the same as English is untranslated, unless that's right and the config says why."""

    def findings(self, sources, allowlist=()):
        return [(f.locale, f.key) for f in check.find_untranslated(sources, "en", check.Allowlist(list(allowlist)))]

    def test_a_value_copied_from_english_is_found(self):
        sources = {
            "en": grouped(shared={"send": "Send", "done": "Done"}),
            "de": grouped(shared={"send": "Senden", "done": "Done"}),
        }

        self.assertEqual([("de", "shared.done")], self.findings(sources))

    def test_the_same_key_in_another_group_is_compared_with_its_own_group(self):
        sources = {
            "en": grouped(android={"title": "Live Updates"}, apple={"title": "Live Activity"}),
            "de": grouped(android={"title": "Live Activity"}, apple={"title": "Live-Aktivität"}),
        }

        self.assertEqual([], self.findings(sources))

    def test_surrounding_whitespace_doesnt_hide_a_copy(self):
        sources = {
            "en": grouped(shared={"prefix": "Dept: "}),
            "fil": grouped(shared={"prefix": "Dept:"}),
        }

        self.assertEqual([("fil", "shared.prefix")], self.findings(sources))

    def test_english_locales_are_not_checked(self):
        sources = {
            "en": grouped(shared={"title": "Settings"}),
            "en-GB": grouped(shared={"title": "Settings"}),
            "en-AU": grouped(shared={"title": "Settings"}),
        }

        self.assertEqual([], self.findings(sources))

    def test_a_value_with_nothing_to_translate_is_not_checked(self):
        values = {
            "pair": "%1$@ · %2$@",
            "count": "%1$lld/%2$d",
            "term": "114-1",
            "plain": "%@",
            "percent": "%1$d%%",
            "named": "%1$s → %2$s",
            "precision": "%.1f%%",
            "padded": "%02d:%02d",
        }
        sources = {"en": grouped(shared=values), "de": grouped(shared=values)}

        self.assertEqual([], self.findings(sources))

    def test_words_around_a_placeholder_are_checked(self):
        values = {"walk": "%1$d min", "version": "Version %1$s"}
        sources = {"en": grouped(shared=values), "ja": grouped(shared=values)}

        self.assertEqual([("ja", "shared.version"), ("ja", "shared.walk")], self.findings(sources))

    def test_an_entry_for_every_locale_allows_it_everywhere(self):
        sources = {
            "en": grouped(shared={"app_name": "TigerDuck"}),
            "de": grouped(shared={"app_name": "TigerDuck"}),
            "ja": grouped(shared={"app_name": "TigerDuck"}),
        }
        entry = {"reason": "Our name", "keys": ["shared.app_name"], "locales": "*"}

        self.assertEqual([], self.findings(sources, [entry]))

    def test_an_entry_with_exceptions_still_checks_those_locales(self):
        sources = {
            "en": grouped(shared={"building_tr": "AAEON Building"}),
            "de": grouped(shared={"building_tr": "AAEON Building"}),
            "zh-Hant": grouped(shared={"building_tr": "AAEON Building"}),
        }
        entry = {"reason": "English name", "prefixes": ["shared.building_"], "except": ["zh-Hant"]}

        self.assertEqual([("zh-Hant", "shared.building_tr")], self.findings(sources, [entry]))

    def test_an_entry_for_some_locales_allows_only_those(self):
        sources = {
            "en": grouped(shared={"semester": "Semester"}),
            "de": grouped(shared={"semester": "Semester"}),
            "fr": grouped(shared={"semester": "Semester"}),
        }
        entry = {"reason": "German says Semester", "keys": ["shared.semester"], "locales": ["de"]}

        self.assertEqual([("fr", "shared.semester")], self.findings(sources, [entry]))


class AllowlistTest(unittest.TestCase):
    """config/same-as-english.json says why each allowed value is right; a wrong or stale entry fails."""

    sources = {
        "en": grouped(shared={"app_name": "TigerDuck", "ok": "OK", "semester": "Semester"}),
        "de": grouped(shared={"app_name": "TigerDuck", "ok": "OK", "semester": "Semester"}),
        "fr": grouped(shared={"app_name": "TigerDuck", "ok": "OK", "semester": "Semestre"}),
    }

    def problems(self, *entries):
        return check.Allowlist(list(entries)).problems(self.sources, "en")

    def test_a_good_entry_passes(self):
        self.assertEqual([], self.problems(
            {"reason": "Our name", "keys": ["shared.app_name"], "locales": "*"},
            {"reason": "OK is the button's word", "keys": ["shared.ok"], "except": ["fr"]},
            {"reason": "German says Semester", "keys": ["shared.semester"], "locales": ["de"]},
        ))

    def test_an_entry_needs_a_reason(self):
        self.assertEqual(
            ["entry 1: no reason"],
            self.problems({"keys": ["shared.app_name"], "locales": "*"}),
        )
        self.assertEqual(
            ["entry 1: no reason"],
            self.problems({"reason": " ", "keys": ["shared.app_name"], "locales": "*"}),
        )

    def test_an_entry_names_keys_or_prefixes(self):
        self.assertEqual(["entry 1 (Nothing): no keys or prefixes"], self.problems({"reason": "Nothing", "locales": "*"}))

    def test_an_entry_says_which_locales_one_way(self):
        self.assertEqual(
            ["entry 1 (Both): give locales or except, not both"],
            self.problems({"reason": "Both", "keys": ["shared.ok"], "locales": "*", "except": ["fr"]}),
        )
        self.assertEqual(
            ["entry 1 (Neither): give locales or except"],
            self.problems({"reason": "Neither", "keys": ["shared.ok"]}),
        )

    def test_a_key_or_prefix_english_doesnt_have_fails(self):
        self.assertEqual(
            ["entry 1 (Gone): shared.gone is not a key in en", "entry 1 (Gone): no key in en starts with shared.old_"],
            self.problems({"reason": "Gone", "keys": ["shared.gone"], "prefixes": ["shared.old_"], "locales": "*"}),
        )

    def test_a_locale_that_isnt_one_fails(self):
        self.assertEqual(
            ["entry 1 (Typo): en is English", "entry 1 (Typo): xx is not a locale"],
            self.problems({"reason": "Typo", "keys": ["shared.ok"], "locales": ["en", "xx"]}),
        )

    def test_a_listed_locale_that_has_since_been_translated_is_stale(self):
        self.assertEqual(
            ["entry 1 (Semester): fr's shared.semester is no longer the same as English; drop it from the entry"],
            self.problems({"reason": "Semester", "keys": ["shared.semester"], "locales": ["de", "fr"]}),
        )

    def test_keys_are_listed_in_order_once(self):
        self.assertEqual(
            ["entry 1 (Order): keys are not sorted", "entry 1 (Order): locales are not sorted"],
            self.problems({"reason": "Order", "keys": ["shared.ok", "shared.app_name"], "locales": ["fr", "de"]}),
        )
        self.assertEqual(
            ["entry 1 (Twice): shared.ok is listed twice"],
            self.problems({"reason": "Twice", "keys": ["shared.ok", "shared.ok"], "locales": "*"}),
        )


class MainTest(unittest.TestCase):
    """The two commands CI runs, against a repository on disk."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "source").mkdir()
        (self.root / "config").mkdir()
        (self.root / "config" / "locales.json").write_text('{"canonicalLocale": "en"}', encoding="utf-8")
        self.write_allowlist([])

    def write_source(self, locale, source):
        (self.root / "source" / f"{locale}.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_allowlist(self, entries):
        (self.root / "config" / "same-as-english.json").write_text(json.dumps(entries), encoding="utf-8")

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = check.main(list(argv), root=self.root)
        return code, out.getvalue() + err.getvalue()

    def test_keys_passes_a_complete_source(self):
        self.write_source("en", grouped(shared={"a": "One"}))
        self.write_source("de", grouped(shared={"a": "Eins"}))

        self.assertEqual(0, self.run_main("keys")[0])

    def test_keys_fails_and_names_what_is_missing(self):
        self.write_source("en", grouped(shared={"a": "One"}))
        self.write_source("de", grouped())

        code, output = self.run_main("keys")

        self.assertEqual(1, code)
        self.assertIn("source/de.json shared: missing a", output)

    def test_untranslated_passes_translated_and_allowed_values(self):
        self.write_source("en", grouped(shared={"a": "One", "name": "TigerDuck"}))
        self.write_source("de", grouped(shared={"a": "Eins", "name": "TigerDuck"}))
        self.write_allowlist([{"reason": "Our name", "keys": ["shared.name"], "locales": "*"}])

        self.assertEqual(0, self.run_main("untranslated")[0])

    def test_untranslated_fails_and_says_how_to_fix_it(self):
        self.write_source("en", grouped(shared={"a": "One"}))
        self.write_source("de", grouped(shared={"a": "One"}))
        self.write_source("fr", grouped(shared={"a": "One"}))

        code, output = self.run_main("untranslated")

        self.assertEqual(1, code)
        self.assertIn('shared.a "One": de fr', output)
        self.assertIn("config/same-as-english.json", output)

    def test_untranslated_fails_on_a_bad_allowlist_entry(self):
        self.write_source("en", grouped(shared={"a": "One"}))
        self.write_source("de", grouped(shared={"a": "Eins"}))
        self.write_allowlist([{"keys": ["shared.a"], "locales": "*"}])

        code, output = self.run_main("untranslated")

        self.assertEqual(1, code)
        self.assertIn("entry 1: no reason", output)

    def test_untranslated_fails_without_english_to_compare_with(self):
        self.write_source("de", grouped(shared={"a": "One"}))

        code, output = self.run_main("untranslated")

        self.assertEqual(1, code)
        self.assertIn("source/en.json: missing", output)

    def test_a_ci_annotation_escapes_what_github_would_read_as_commands(self):
        self.write_source("en", grouped(shared={"a": "%1$d min"}))
        self.write_source("ja", grouped(shared={"a": "%1$d min"}))

        with mock.patch.dict(check.os.environ, {"GITHUB_ACTIONS": "true"}):
            code, output = self.run_main("untranslated")

        self.assertEqual(1, code)
        annotation = next(line for line in output.splitlines() if line.startswith("::error "))
        self.assertTrue(annotation.startswith("::error file=source/ja.json,line=3,title=Same as English::"))
        self.assertIn("%251$d min", annotation)
        self.assertNotIn("%1$d", annotation)

    def test_an_older_python_is_refused_with_the_version_it_needs(self):
        with mock.patch.object(check.sys, "version_info", (3, 8, 10, "final", 0)):
            code, output = self.run_main("keys")

        self.assertEqual(1, code)
        self.assertIn("Python 3.9 or newer", output)
        self.assertIn("3.8.10", output)


if __name__ == "__main__":
    unittest.main()
