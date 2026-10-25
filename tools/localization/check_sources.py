#!/usr/bin/env python3
"""Checks source/*.json before a pull request merges. CI runs both commands.

keys
    Every locale has exactly en's keys in each of the four groups: the same
    keys, not just as many, each a string with something in it, none twice in
    a file, and none both in `shared` and a platform group.

untranslated
    No locale but English itself has a value that is still en's. A value
    that is right as English (a name, a unit, a loanword the language uses)
    goes in config/same-as-english.json with the reason it's right; anything
    else is a placeholder waiting for a translation, which a working branch
    may carry but a pull request can't merge with. Values with nothing to
    translate (placeholders, digits, punctuation only) aren't checked.

Needs Python 3.9 or newer, as the generator does.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# The oldest Python the tools run on, and CI tests: macOS's own python3.
MINIMUM_PYTHON = (3, 9)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_GROUPS = ("shared", "android", "apple", "backend")
ALLOWLIST_PATH = Path("config") / "same-as-english.json"

# The format specifiers the source uses (%1$s, %2$@, %1$d, %1$lld, %@) and the
# others printf-style formats allow: flags, width, precision and length, and %%.
# No space flag, so "50% off" keeps its word.
_PLACEHOLDER = re.compile(r"%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?(?:hh|h|ll|l|q|z|t|j)?[@%diouxXeEfFgGcsS]")


def _display(locale: str) -> str:
    return f"source/{locale}.json"


def load_sources(source_dir: Path) -> tuple[dict[str, dict], list[str]]:
    """Every source/<locale>.json, and what's wrong with reading them: a file
    that isn't JSON, or a key a file holds twice (JSON keeps the last)."""
    sources: dict[str, dict] = {}
    problems: list[str] = []
    for path in sorted(source_dir.glob("*.json")):
        locale = path.stem

        def no_twice(pairs, locale=locale):
            seen = set()
            for key, _ in pairs:
                if key in seen:
                    problems.append(f"{_display(locale)}: {key} appears twice")
                seen.add(key)
            return dict(pairs)

        try:
            with path.open("r", encoding="utf-8") as handle:
                sources[locale] = json.load(handle, object_pairs_hook=no_twice)
        except UnicodeDecodeError as error:
            problems.append(f"{_display(locale)}: not UTF-8 ({error})")
        except json.JSONDecodeError as error:
            problems.append(f"{_display(locale)}: not valid JSON ({error})")
    return sources, problems


def _groups(source: object) -> dict[str, dict]:
    if not isinstance(source, dict):
        return {}
    return {name: keys for name, keys in source.items() if name in SOURCE_GROUPS and isinstance(keys, dict)}


def check_keys(sources: dict[str, dict], canonical: str) -> list[str]:
    """What keeps a locale from having exactly en's keys, for every locale at once."""
    if canonical not in sources:
        return [f"{_display(canonical)}: missing; it's the canonical locale every other one follows"]
    problems: list[str] = []
    canonical_groups = _groups(sources[canonical])
    for locale in sorted(sources):
        source = sources[locale]
        where = _display(locale)
        if not isinstance(source, dict):
            problems.append(f"{where}: not an object of groups")
            continue
        for name in source:
            if name not in SOURCE_GROUPS:
                problems.append(f"{where}: unknown group {name}")
        for name in SOURCE_GROUPS:
            if name not in source:
                problems.append(f"{where}: no {name} group")
            elif not isinstance(source[name], dict):
                problems.append(f"{where}: {name} is not an object of keys")
        groups = _groups(source)
        for name in SOURCE_GROUPS:
            for key, value in groups.get(name, {}).items():
                if not isinstance(value, str):
                    problems.append(f"{where} {name}: {key} is not a string")
                elif not value.strip():
                    problems.append(f"{where} {name}: {key} is empty")
        shared = set(groups.get("shared", {}))
        for platform in SOURCE_GROUPS[1:]:
            for key in sorted(shared & set(groups.get(platform, {}))):
                problems.append(f"{where}: {key} is in both shared and {platform}")
        if locale == canonical:
            continue
        for name in SOURCE_GROUPS:
            expected = set(canonical_groups.get(name, {}))
            present = set(groups.get(name, {}))
            problems.extend(f"{where} {name}: missing {key}" for key in sorted(expected - present))
            problems.extend(f"{where} {name}: extra {key}" for key in sorted(present - expected))
    return problems


def has_words(value: str) -> bool:
    """Whether [value] has anything to translate once its placeholders, digits,
    punctuation and symbols are left out."""
    return any(ch.isalpha() for ch in _PLACEHOLDER.sub("", value))


def _language(locale: str) -> str:
    return locale.split("-")[0].lower()


def _flatten(source: dict) -> dict[str, object]:
    """Each key as `group.key`, so a key forked into two groups stays two."""
    return {f"{name}.{key}": value for name, keys in _groups(source).items() for key, value in keys.items()}


def _same(value: object, english: object) -> bool:
    return isinstance(value, str) and isinstance(english, str) and value.strip() == english.strip()


@dataclass(frozen=True)
class Finding:
    locale: str
    key: str
    value: str


class Allowlist:
    """config/same-as-english.json: values that are right as English, each entry
    with its reason, its `keys` and `prefixes` (as `group.key`), and the locales
    it covers: `locales`, a list or "*", or every locale but its `except`."""

    def __init__(self, entries: list):
        self.entries = entries

    @classmethod
    def load(cls, path: Path) -> tuple["Allowlist", list[str]]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                entries = json.load(handle)
        except FileNotFoundError:
            return cls([]), []
        except json.JSONDecodeError as error:
            return cls([]), [f"{ALLOWLIST_PATH}: not valid JSON ({error})"]
        if not isinstance(entries, list):
            return cls([]), [f"{ALLOWLIST_PATH}: not a list of entries"]
        return cls(entries), []

    @staticmethod
    def _strings(entry: dict, field: str) -> list[str]:
        value = entry.get(field, [])
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    @staticmethod
    def _covers_key(entry: dict, key: str) -> bool:
        return key in Allowlist._strings(entry, "keys") or any(
            key.startswith(prefix) for prefix in Allowlist._strings(entry, "prefixes")
        )

    @staticmethod
    def _covers_locale(entry: dict, locale: str) -> bool:
        locales = entry.get("locales")
        if locales == "*":
            return True
        if isinstance(locales, list):
            return locale in locales
        if "except" in entry:
            return locale not in Allowlist._strings(entry, "except")
        return False

    def allows(self, key: str, locale: str) -> bool:
        return any(
            isinstance(entry, dict) and self._covers_key(entry, key) and self._covers_locale(entry, locale)
            for entry in self.entries
        )

    def problems(self, sources: dict[str, dict], canonical: str) -> list[str]:
        english = _flatten(sources.get(canonical, {}))
        flat = {locale: _flatten(source) for locale, source in sources.items()}
        problems: list[str] = []
        for number, entry in enumerate(self.entries, start=1):
            if not isinstance(entry, dict):
                problems.append(f"entry {number}: not an object")
                continue
            reason = entry.get("reason")
            label = f"entry {number} ({reason.strip()})" if isinstance(reason, str) and reason.strip() else f"entry {number}"
            if label == f"entry {number}":
                problems.append(f"{label}: no reason")
            for field in ("keys", "prefixes", "except"):
                if field in entry and not (
                    isinstance(entry[field], list) and all(isinstance(item, str) for item in entry[field])
                ):
                    problems.append(f"{label}: {field} must be a list of strings")
            if "locales" in entry and entry["locales"] != "*" and not (
                isinstance(entry["locales"], list) and all(isinstance(item, str) for item in entry["locales"])
            ):
                problems.append(f'{label}: locales must be "*" or a list of strings')
            keys = self._strings(entry, "keys")
            prefixes = self._strings(entry, "prefixes")
            if not keys and not prefixes:
                problems.append(f"{label}: no keys or prefixes")
            if "locales" in entry and "except" in entry:
                problems.append(f"{label}: give locales or except, not both")
            elif "locales" not in entry and "except" not in entry:
                problems.append(f"{label}: give locales or except")
            for key in keys:
                if key not in english:
                    problems.append(f"{label}: {key} is not a key in {canonical}")
            for prefix in prefixes:
                if not any(key.startswith(prefix) for key in english):
                    problems.append(f"{label}: no key in {canonical} starts with {prefix}")
            listed = self._strings(entry, "locales") + self._strings(entry, "except")
            for locale in listed:
                if _language(locale) == _language(canonical):
                    problems.append(f"{label}: {locale} is English")
                elif locale not in sources:
                    problems.append(f"{label}: {locale} is not a locale")
            for field in ("keys", "prefixes", "locales", "except"):
                items = self._strings(entry, field)
                if items != sorted(items):
                    problems.append(f"{label}: {field} are not sorted")
                for item in sorted({item for item in items if items.count(item) > 1}):
                    problems.append(f"{label}: {item} is listed twice")
            # A locale named one by one, whose value has since been translated:
            # the entry would quietly allow it to go back to English.
            for locale in self._strings(entry, "locales"):
                if locale not in flat or _language(locale) == _language(canonical):
                    continue
                for key in sorted(k for k in english if self._covers_key(entry, k)):
                    if key in flat[locale] and not _same(flat[locale][key], english[key]):
                        problems.append(
                            f"{label}: {locale}'s {key} is no longer the same as English; drop it from the entry"
                        )
        return problems


def find_untranslated(sources: dict[str, dict], canonical: str, allowlist: Allowlist) -> list[Finding]:
    """Each value, outside English, that is still en's and that the allowlist doesn't explain."""
    english = _flatten(sources.get(canonical, {}))
    findings: list[Finding] = []
    for locale in sorted(sources):
        if _language(locale) == _language(canonical):
            continue
        for key, value in sorted(_flatten(sources[locale]).items()):
            source_value = english.get(key)
            if not _same(value, source_value) or not has_words(source_value):
                continue
            if allowlist.allows(key, locale):
                continue
            findings.append(Finding(locale, key, value))
    return findings


def _line_of(root: Path, locale: str, key: str) -> int | None:
    """The line [key] (`group.key`) is on in [locale]'s file, for a CI annotation."""
    group, _, name = key.partition(".")
    try:
        lines = (root / "source" / f"{locale}.json").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    in_group = False
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if line.startswith("  ") and not line.startswith("   ") and stripped.startswith('"'):
            in_group = stripped.startswith(f'"{group}"')
        elif in_group and stripped.startswith(json.dumps(name, ensure_ascii=False) + ":"):
            return number
    return None


def _escape(data: str) -> str:
    """[data] as a GitHub workflow command's message: %, CR and LF would be read as the command's own."""
    return data.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _annotate(root: Path, findings: list[Finding]) -> None:
    """One error annotation per finding, on its line, when running in GitHub Actions."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    for finding in findings:
        line = _line_of(root, finding.locale, finding.key)
        where = f"file=source/{finding.locale}.json" + (f",line={line}" if line else "")
        message = f"{finding.key} is still English: {json.dumps(finding.value, ensure_ascii=False)}"
        print(f"::error {where},title=Same as English::{_escape(message)}")


def _canonical_locale(root: Path) -> str:
    try:
        with (root / "config" / "locales.json").open("r", encoding="utf-8") as handle:
            return json.load(handle).get("canonicalLocale", "en")
    except (OSError, json.JSONDecodeError):
        return "en"


def _run_keys(root: Path, sources: dict[str, dict], problems: list[str], canonical: str) -> int:
    problems = problems + check_keys(sources, canonical)
    if not problems:
        print(f"keys: every locale has {canonical}'s keys ({len(sources)} locales).")
        return 0
    for problem in problems:
        print(problem)
    print(
        f"\n{len(problems)} problem(s). Every source/<locale>.json needs exactly {canonical}'s keys in each group, "
        "each with a value. A translation that isn't ready yet keeps the English value on a working branch "
        "until it is, but the key is never left out."
    )
    return 1


def _run_untranslated(root: Path, sources: dict[str, dict], problems: list[str], canonical: str) -> int:
    if canonical not in sources:
        problems = problems + [f"{_display(canonical)}: missing; it's what every other locale is compared with"]
    allowlist, allowlist_problems = Allowlist.load(root / ALLOWLIST_PATH)
    problems = problems + allowlist_problems + allowlist.problems(sources, canonical)
    findings = find_untranslated(sources, canonical, allowlist)
    if not problems and not findings:
        print(f"untranslated: no value is still {canonical}'s outside {ALLOWLIST_PATH}.")
        return 0
    for problem in problems:
        print(f"{ALLOWLIST_PATH}: {problem}" if problem.startswith("entry ") else problem)
    if findings:
        english = _flatten(sources[canonical])
        by_key: dict[str, list[str]] = {}
        for finding in findings:
            by_key.setdefault(finding.key, []).append(finding.locale)
        print(f"{len(findings)} value(s) are still {canonical}'s:")
        for key in sorted(by_key):
            print(f"  {key} {json.dumps(english[key], ensure_ascii=False)}: {' '.join(by_key[key])}")
        print(
            "\nTranslate each of them. If one is right as it is (a name, a unit, a word the language takes "
            f"from English), add it to {ALLOWLIST_PATH} with the reason, for the locales it's right in."
        )
        _annotate(root, findings)
    return 1


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    if sys.version_info < MINIMUM_PYTHON:
        print(
            "check_sources.py needs Python %d.%d or newer; this is %s."
            % (MINIMUM_PYTHON + (".".join(str(part) for part in sys.version_info[:3]),)),
            file=sys.stderr,
        )
        return 1
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("check", choices=("keys", "untranslated"))
    args = parser.parse_args(argv)
    canonical = _canonical_locale(root)
    sources, problems = load_sources(root / "source")
    if args.check == "keys":
        return _run_keys(root, sources, problems, canonical)
    return _run_untranslated(root, sources, problems, canonical)


if __name__ == "__main__":
    raise SystemExit(main())
