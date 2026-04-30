#!/usr/bin/env python3
"""Generate Android/apple localization artifacts from source JSON.

This repo is the source of truth: `source/<locale>.json`.

Outputs:
- `generated/android/values-*/strings.xml`
- `generated/apple/<locale>.lproj/Localizable.strings`

Generation is config-driven via `config/locales.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "source"
GENERATED_DIR = REPO_ROOT / "generated"
CONFIG_PATH = REPO_ROOT / "config" / "locales.json"


# ISO 639-1 language codes. Used to generate broad fallback resources so the app
# has a selectable language for most system languages even before real
# translations land. (Values will fall back to the canonical locale.)
ISO_639_1: tuple[str, ...] = (
    "aa", "ab", "ae", "af", "ak", "am", "an", "ar", "as", "av", "ay", "az",
    "ba", "be", "bg", "bh", "bi", "bm", "bn", "bo", "br", "bs",
    "ca", "ce", "ch", "co", "cr", "cs", "cu", "cv", "cy",
    "da", "de", "dv", "dz",
    "ee", "el", "en", "eo", "es", "et", "eu",
    "fa", "ff", "fi", "fj", "fo", "fr", "fy",
    "ga", "gd", "gl", "gn", "gu", "gv",
    "ha", "he", "hi", "ho", "hr", "ht", "hu", "hy", "hz",
    "ia", "id", "ie", "ig", "ii", "ik", "io", "is", "it", "iu",
    "ja", "jv",
    "ka", "kg", "ki", "kj", "kk", "kl", "km", "kn", "ko", "kr", "ks", "ku", "kv", "kw", "ky",
    "la", "lb", "lg", "li", "ln", "lo", "lt", "lu", "lv",
    "mg", "mh", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my",
    "na", "nb", "nd", "ne", "ng", "nl", "nn", "no", "nr", "nv", "ny",
    "oc", "oj", "om", "or", "os",
    "pa", "pi", "pl", "ps", "pt",
    "qu",
    "rm", "rn", "ro", "ru", "rw",
    "sa", "sc", "sd", "se", "sg", "si", "sk", "sl", "sm", "sn", "so", "sq", "sr", "ss", "st", "su", "sv", "sw",
    "ta", "te", "tg", "th", "ti", "tk", "tl", "tn", "to", "tr", "ts", "tt", "tw", "ty",
    "ug", "uk", "ur", "uz",
    "ve", "vi", "vo",
    "wa", "wo",
    "xh",
    "yi", "yo",
    "za", "zh", "zu",
)


def _load_json_ordered(path: Path) -> OrderedDict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)


# Source schema is grouped: each source/<locale>.json has top-level keys
# "shared", "android", "apple". Each group maps key -> value. The Android
# bundle gets shared ∪ android; the Apple bundle gets shared ∪ apple.
# Keys must be unique across groups within a locale.
SOURCE_GROUPS: tuple[str, ...] = ("shared", "android", "apple")


def _flatten_for_platform(grouped: OrderedDict, platform: str) -> OrderedDict[str, str]:
    """Merge `shared` + the platform-specific group, sorted by key."""
    merged: dict[str, str] = {}
    for group in ("shared", platform):
        for key, value in grouped.get(group, {}).items():
            merged[key] = value
    return OrderedDict((k, merged[k]) for k in sorted(merged))


def _validate_grouped_source(locale: str, grouped: OrderedDict) -> None:
    unknown = [g for g in grouped.keys() if g not in SOURCE_GROUPS]
    if unknown:
        raise SystemExit(
            f"source/{locale}.json has unknown top-level groups: {unknown}. "
            f"Expected only: {list(SOURCE_GROUPS)}"
        )
    seen: dict[str, str] = {}
    for group in SOURCE_GROUPS:
        for key in grouped.get(group, {}).keys():
            if key in seen:
                raise SystemExit(
                    f"source/{locale}.json key '{key}' appears in both "
                    f"'{seen[key]}' and '{group}' groups"
                )
            seen[key] = group


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
        prefix=path.name + ".",
        suffix=".tmp",
    ) as tf:
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())
        tmp_name = tf.name
    os.replace(tmp_name, path)


def _escape_android(value: str) -> str:
    # Note: order matters; escape ampersands first.
    value = value.replace("&", "&amp;")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    value = value.replace("'", "\\'")
    value = value.replace('"', "\\\"")
    value = value.replace("\n", "\\n")

    # If a string starts with @ or ?, Android treats it as a reference.
    if value.startswith(("@", "?")):
        value = "\\" + value

    return value


def _escape_apple(value: str) -> str:
    value = value.replace("\\", "\\\\")
    value = value.replace('"', "\\\"")
    value = value.replace("\n", "\\n")
    # Swift/ObjC uses %@ for strings; Android/C use %s. Convert positional and
    # bare %s specifiers so Apple format strings work with String(format:).
    value = re.sub(r"%(\d+\$)s", r"%\1@", value)
    value = re.sub(r"%s", r"%@", value)
    return value


ANDROID_LOCALE_RE = re.compile(
    r"^(?P<lang>[A-Za-z]{2,3})(?:-(?P<part2>[A-Za-z]{2,4}|[0-9]{3}))?(?:-(?P<part3>[A-Za-z]{2}|[0-9]{3}))?$"
)


@dataclass(frozen=True)
class LocaleConfig:
    canonical_locale: str
    android_default_dir_locale: str
    android_special_locale_to_dir: dict[str, str]
    android_aliases: dict[str, str]
    android_generate_all_iso_639_1: bool
    apple_aliases: dict[str, str]
    apple_generate_all_iso_639_1: bool


def _load_config() -> LocaleConfig:
    raw = _load_json_ordered(CONFIG_PATH)

    canonical = raw.get("canonicalLocale", "en")

    android = raw.get("android", {})
    apple = raw.get("apple", {})

    return LocaleConfig(
        canonical_locale=canonical,
        android_default_dir_locale=android.get("defaultDirLocale", "zh-Hant"),
        android_special_locale_to_dir=dict(android.get("specialLocaleToDir", {})),
        android_aliases=dict(android.get("aliases", {})),
        android_generate_all_iso_639_1=bool(android.get("generateAllIso639_1", False)),
        apple_aliases=dict(apple.get("aliases", {})),
        apple_generate_all_iso_639_1=bool(apple.get("generateAllIso639_1", False)),
    )


def _discover_source_locales() -> list[str]:
    locales: list[str] = []
    for p in sorted(SOURCE_DIR.glob("*.json")):
        locales.append(p.stem)
    return locales


def _validate_sources(sources: dict[str, OrderedDict], canonical_locale: str) -> None:
    if canonical_locale not in sources:
        raise SystemExit(f"Canonical locale '{canonical_locale}' not found in source/*.json")

    canonical = sources[canonical_locale]
    canonical_groups: dict[str, set[str]] = {
        g: set(canonical.get(g, {}).keys()) for g in SOURCE_GROUPS
    }

    for locale, grouped in sources.items():
        for group in SOURCE_GROUPS:
            keys = set(grouped.get(group, {}).keys())
            if keys != canonical_groups[group]:
                missing = sorted(canonical_groups[group] - keys)
                extra = sorted(keys - canonical_groups[group])
                raise SystemExit(
                    "Key mismatch in source/%s.json group '%s'\nMissing: %s\nExtra: %s"
                    % (locale, group, missing[:20], extra[:20])
                )


def _android_dir_for_locale(locale: str, cfg: LocaleConfig) -> str:
    if locale in cfg.android_special_locale_to_dir:
        return cfg.android_special_locale_to_dir[locale]

    m = ANDROID_LOCALE_RE.match(locale)
    if not m:
        raise SystemExit(f"Unsupported locale format for Android: {locale}")

    lang = m.group("lang")
    part2 = m.group("part2")
    part3 = m.group("part3")

    # Android uses some legacy ISO codes.
    legacy_lang = {
        "he": "iw",
        "id": "in",
        "yi": "ji",
    }.get(lang, lang)

    if not part2:
        return f"values-{legacy_lang}"

    # lang-REGION
    if len(part2) == 2 and part2.isalpha() and not part3:
        return f"values-{legacy_lang}-r{part2.upper()}"

    # lang-SCRIPT-REGION or lang-REGION-VARIANT: take the last region-like part.
    region: str | None = None
    if part3 and len(part3) == 2 and part3.isalpha():
        region = part3.upper()
    elif len(part2) == 2 and part2.isalpha():
        region = part2.upper()

    if region:
        return f"values-{legacy_lang}-r{region}"

    # If we reach here, we don't know how to map the tag.
    raise SystemExit(f"Unsupported locale format for Android: {locale}")


def _render_android_strings_xml(strings: OrderedDict) -> str:
    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="utf-8"?>')
    lines.append("<resources>")
    lines.append("    <!-- Generated from localization/source/*.json. Do not edit directly. -->")

    for key, raw_value in strings.items():
        value = _escape_android(raw_value)
        lines.append(f"    <string name=\"{key}\">{value}</string>")

    lines.append("</resources>")
    lines.append("")
    return "\n".join(lines)


def _render_apple_strings(strings: OrderedDict) -> str:
    lines: list[str] = []
    lines.append("/* Generated from localization/source/*.json. Do not edit directly. */")
    for key, raw_value in strings.items():
        value = _escape_apple(raw_value)
        lines.append(f"\"{key}\" = \"{value}\";")
    lines.append("")
    return "\n".join(lines)


def _resolve_output_locales(
    source_locales: Iterable[str],
    aliases: dict[str, str],
    extra_output_locales: Iterable[str],
    *,
    fallback_source_locale: str,
) -> dict[str, str]:
    # Returns outputLocale -> baseSourceLocale.
    resolved: dict[str, str] = {loc: loc for loc in source_locales}
    for out_loc, base in aliases.items():
        resolved[out_loc] = base
    for out_loc in extra_output_locales:
        # If it exists in sources or aliases already, keep it.
        if out_loc in resolved:
            continue
        # Otherwise, map to canonical fallback.
        resolved[out_loc] = fallback_source_locale
    return resolved


def generate(*, validate_only: bool) -> None:
    cfg = _load_config()

    source_locales = _discover_source_locales()
    sources: dict[str, OrderedDict] = {}
    for loc in source_locales:
        grouped = _load_json_ordered(SOURCE_DIR / f"{loc}.json")
        _validate_grouped_source(loc, grouped)
        sources[loc] = grouped

    _validate_sources(sources, canonical_locale=cfg.canonical_locale)

    android_flat: dict[str, OrderedDict[str, str]] = {
        loc: _flatten_for_platform(grouped, "android") for loc, grouped in sources.items()
    }
    apple_flat: dict[str, OrderedDict[str, str]] = {
        loc: _flatten_for_platform(grouped, "apple") for loc, grouped in sources.items()
    }

    android_extras: list[str] = []
    apple_extras: list[str] = []
    if cfg.android_generate_all_iso_639_1:
        android_extras.extend(ISO_639_1)
    if cfg.apple_generate_all_iso_639_1:
        apple_extras.extend(ISO_639_1)

    android_outputs = _resolve_output_locales(
        source_locales,
        cfg.android_aliases,
        android_extras,
        fallback_source_locale=cfg.canonical_locale,
    )
    apple_outputs = _resolve_output_locales(
        source_locales,
        cfg.apple_aliases,
        apple_extras,
        fallback_source_locale=cfg.canonical_locale,
    )

    if validate_only:
        print(
            "Validation OK. Source locales: %d, Android outputs: %d, apple outputs: %d"
            % (len(source_locales), len(android_outputs), len(apple_outputs))
        )
        return

    # Android
    for out_locale, base_locale in sorted(android_outputs.items()):
        if base_locale not in android_flat:
            raise SystemExit(f"Android alias '{out_locale}' points to missing source locale '{base_locale}'")
        out_dir_name = _android_dir_for_locale(out_locale, cfg)
        out_path = GENERATED_DIR / "android" / out_dir_name / "strings.xml"
        content = _render_android_strings_xml(android_flat[base_locale])
        _atomic_write_text(out_path, content)

    # apple
    for out_locale, base_locale in sorted(apple_outputs.items()):
        if base_locale not in apple_flat:
            raise SystemExit(f"apple alias '{out_locale}' points to missing source locale '{base_locale}'")
        out_path = GENERATED_DIR / "apple" / f"{out_locale}.lproj" / "Localizable.strings"
        content = _render_apple_strings(apple_flat[base_locale])
        _atomic_write_text(out_path, content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate source JSON files; do not write generated outputs",
    )
    args = parser.parse_args()

    generate(validate_only=args.validate_only)


if __name__ == "__main__":
    main()

