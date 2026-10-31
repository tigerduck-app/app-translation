# Localization Submodule Folder

This folder is the shared translation source for Android, Apple and the backend.

## Structure

- `source/`
    - `en.json`
    - `zh-Hant.json`
- `config/`
    - `locales.json` (canonical locale, platform aliases)
    - `same-as-english.json` (values that are right as English, and why)
- `generated/` (checked in)
    - `backend/en.json`

Android's `strings.xml` files and Apple's `<locale>.lproj` folders are not
checked in. The Android app's Gradle build generates its files from `source/`
every build, with `--platform android --output-dir <dir>`, and every Apple
target's build does the same with `--platform apple --output-dir <dir>`.

## Requirements

Python 3.9 or newer, standard library only. 3.9 is macOS's own `python3`; CI
tests 3.9 and the newest release.

## Update workflow

1. Edit `source/*.json`.
2. Run:

```bash
python3 tools/localization/generate_localizations.py
```

This regenerates the backend artifacts under `generated/`. Commit them with the
source change. Android and Apple need nothing more: their next build reads
`source/` once their submodule pin moves.

To see Android's or Apple's output, write it somewhere outside `generated/`:

```bash
python3 tools/localization/generate_localizations.py --platform android --output-dir /tmp/android-res
python3 tools/localization/generate_localizations.py --platform apple --output-dir /tmp/apple-lproj
```

## Checks before merging

Every pull request runs two checks of `source/`, described in
[CONVENTIONS.md](CONVENTIONS.md#checks-before-merging):

```bash
python3 tools/localization/check_sources.py keys          # every locale has exactly en's keys
python3 tools/localization/check_sources.py untranslated  # no value still in English that should be translated
```

A value that is right as English (a name, a unit, a word the language uses)
goes in `config/same-as-english.json` with its reason.

If you want to publish only translations in a separate repository, push this folder.
