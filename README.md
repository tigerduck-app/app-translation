# Localization Submodule Folder

This folder is the shared translation source for both Android and Apple.

## Structure

- `source/`
  - `en.json`
  - `zh-Hant.json`
- `generated/`
  - `android/values/strings.xml`
  - `android/values-en/strings.xml`
  - `apple/en.lproj/Localizable.strings`
  - `apple/zh-Hant.lproj/Localizable.strings`

## Update workflow

1. Edit `source/*.json`.
2. Run:

```bash
python3 tools/localization/generate_localizations.py
```

This regenerates Android/Apple localization artifacts under `generated/`.

If you want to publish only translations in a separate repository, push this folder.
