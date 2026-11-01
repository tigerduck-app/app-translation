# Contributing

This repository holds every string of TigerDuck's Android app, Apple apps and backend, in 55
locales. Each app takes it as a git submodule, so a change here reaches every app that pins it.
[CONVENTIONS.md](CONVENTIONS.md) is the contract for how the strings are laid out and named; this
file is how a change gets in.

## Talk to us first

Before you open a pull request, talk the change over with @SamWang8891 and @xinshoutw in #devs-chat
on the TigerDuck Discord (https://discord.gg/Mxb344qKRu), so that they know the plan. A pull request
nobody heard about first may be closed, however good it is.

## Pull requests

- Every change is a pull request into `main`, which takes nothing else. A pull request needs a core
  developer's approval; one that adds or changes a key in `shared` needs both core developers',
  since both apps ship it.
- An app never edits its `app-translation/` submodule in place: the string change comes here
  first.
- Commit messages and pull request titles start with what the change is, as in the apps:
  `feat(strings): …`, `fix(strings): …`, `docs: …`.
- Reply to the core developers' comments within 3 days, or they may take over the pull request.

## Adding or changing a string

1. Read [CONVENTIONS.md](CONVENTIONS.md) before adding a key: which group it goes in (`shared`
   unless it names something only one platform has), how to name it, and the names that are never
   translated (TigerDuck's own product names, campus buildings, departments).
2. Edit `source/*.json`. Every locale's file must have exactly the same keys, so a new key goes in
   every locale, under the same group, in alphabetical order.
3. Translate at least English (`en`, or `en-GB`) or Traditional Chinese (`zh-Hant`). For each
   locale you don't translate, use a value you did translate as its placeholder, English if you
   have it; a core developer translates the rest before merging. When you change a key's value,
   you may likewise leave the locales you won't translate as they are.
   - Translate from the reference locales CONVENTIONS.md names: the three Chinese variants from
     each other, every other locale from `en`.
   - A value that is right as English goes in `config/same-as-english.json`, with its reason.
   - The `untranslated` check fails while a placeholder is left, which is expected until the core
     developers have finished.
4. Regenerate the backend bundle and commit what changes under `generated/` with the source
   change. No check catches a pull request that forgets this, and the backend would go without
   the new strings. The Android and Apple apps build their own from `source/`:

   ```bash
   python3 tools/localization/generate_localizations.py
   ```

   It also fails when two unrelated locales share 20 or more values that aren't English, which is
   how one language's text slips into another: check that each has its own language's wording.
   Locales that rightly share wording are listed in the script; see *Regenerating outputs* in
   CONVENTIONS.md.

5. Run the checks CI runs:

   ```bash
   python3 tools/localization/check_sources.py keys
   python3 tools/localization/check_sources.py untranslated
   python3 -m unittest discover -s tools/localization
   ```

The tools need Python 3.9 or newer and nothing outside its standard library.

## Removing or renaming a key

An app that still uses a key breaks once its pin moves past the key's removal: Android's build
fails, and the Apple app shows the key's name. Before removing a key, search the Android and Apple
repositories for it and make sure neither uses it any more. A rename is a new key first; the old
one goes once both apps have moved off it.

## Using new strings in an app

The app's pull request pins its `app-translation` submodule at this pull request's head commit and
links it. A core developer merges this pull request first, then moves the app's pin to the new
`main` before merging the app's pull request.

## AI

Using AI, translation included, is fine. Say which models in the pull request's "AI use" section.
You answer for every value, as if you had written it.
