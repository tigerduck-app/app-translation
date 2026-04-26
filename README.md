# Localization Submodule Folder

This folder is the shared translation source for both Android and iOS.

## Structure

- `source/`
  - `en.json`
  - `zh-Hant.json`
- `generated/`
  - `android/values/strings.xml`
  - `android/values-en/strings.xml`
  - `ios/en.lproj/Localizable.strings`
  - `ios/zh-Hant.lproj/Localizable.strings`

## Update workflow

1. Edit `source/*.json`.
2. Run:

```bash
python3 tools/localization/sync_localizations.py
```

This regenerates shared Android/iOS files under `generated/`, and also syncs Android app runtime files under `app/src/main/res/values*/strings.xml`.

If you want to publish only translations in a separate repository, push this `localization/` folder.
