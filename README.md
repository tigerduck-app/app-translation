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
    - `apple/en.lproj/Localizable.strings`
    - `apple/en.lproj/InfoPlist.strings` (Info.plist purpose strings)
    - `apple/zh-Hant.lproj/Localizable.strings`
    - `backend/en.json`

Android's `strings.xml` files are not checked in: the Android app's Gradle build
generates them from `source/` every build, with
`--platform android --output-dir <dir>`.

## Requirements

Python 3.9 or newer, standard library only. 3.9 is macOS's own `python3`; CI
tests 3.9 and the newest release.

## Update workflow

1. Edit `source/*.json`.
2. Run:

```bash
python3 tools/localization/generate_localizations.py
```

This regenerates the Apple and backend artifacts under `generated/`. Commit
them with the source change. Android needs nothing more: its next build reads
`source/` once its submodule pin moves.

To see Android's output, write it somewhere outside `generated/`:

```bash
python3 tools/localization/generate_localizations.py --platform android --output-dir /tmp/android-res
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
