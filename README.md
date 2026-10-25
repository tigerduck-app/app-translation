# Localization Submodule Folder

This folder is the shared translation source for Android, Apple and the backend.

## Structure

- `source/`
    - `en.json`
    - `zh-Hant.json`
- `generated/` (checked in)
    - `apple/en.lproj/Localizable.strings`
    - `apple/en.lproj/InfoPlist.strings` (Info.plist purpose strings)
    - `apple/zh-Hant.lproj/Localizable.strings`
    - `backend/en.json`

Android's `strings.xml` files are not checked in: the Android app's Gradle build
generates them from `source/` every build, with
`--platform android --output-dir <dir>`.

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

If you want to publish only translations in a separate repository, push this folder.
