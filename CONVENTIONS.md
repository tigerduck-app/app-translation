# Translation Source Conventions

This file is the contract for how `source/<locale>.json` is structured and how
keys are named. Read this before adding or renaming keys.

## Source layout

Each `source/<locale>.json` has exactly three top-level groups:

```json
{
  "shared":  { "<key>": "<value>", ... },
  "android": { "<key>": "<value>", ... },
  "apple":   { "<key>": "<value>", ... }
}
```

Generation rule:

- Android bundle gets `shared ∪ android`
- Apple bundle gets `shared ∪ apple`

A key may appear in only one group at a time. Keys are **alphabetically sorted**
within each group; the rebucket / generator scripts depend on this for stable
diffs.

The canonical locale (`en`) defines the authoritative key inventory per group.
Every other source locale must match the canonical key set in each group; if a
translation isn't ready yet, copy the English value as a placeholder.

## Choosing a group

Default to `shared`. Only put a key under `android` or `apple` when the **string
references a platform-specific OS primitive** that the other platform doesn't
have. Examples:

- `android`: notification channel names/descriptions, exact-alarm permission,
  battery-optimization permission, "press back again to exit" toast
- `apple`: (none yet — add things like Siri shortcut prompts, App Clip
  invocation strings, or other Apple-only OS primitives here when they land)

UI labels that *exist on both platforms but happen to be wired up first on one*
go in `shared`, not in the platform group. "I haven't translated this on iOS
yet" is not a reason to put a key under `android`.

## Forking a shared key per platform

If a previously-shared string needs different wording on each platform, **move
it out of `shared`** and add it to both `android` and `apple` with the
respective values. This keeps the divergence explicit and reviewable in a
single diff. Don't leave the original in `shared` and shadow it from a platform
group — keys must be unique across groups within a locale.

## Naming keys

Keys are `snake_case` and lead with a stable feature/area prefix so related
strings cluster together when sorted. Existing prefixes (use one of these
before inventing a new one):

| Prefix | Area |
|---|---|
| `action_` | Generic verbs (Add, Cancel, Done, Confirm, …) reused across screens |
| `add_course_` | Add-course flow |
| `app_` | App-level state (`app_name`, reset, exit) |
| `assignment_` | Assignment list, filters, status, time formatting |
| `calendar_` | Calendar screen |
| `class_table_` | Class table screen |
| `color_picker_` | Color picker dialog |
| `coming_soon_` | "Coming soon" placeholder dialog |
| `common_` | Cross-feature small bits ("Not signed in" etc.) |
| `conflict_course_picker_` | Course-conflict picker dialog |
| `course_card_` / `course_*_value` | Course card / detail formatters |
| `error_` | Generic error messages |
| `feature_` / `feature_category_` | Feature names + grouping in launcher / more screen |
| `greeting_` | Time-of-day greetings |
| `home_` | Home screen sections |
| `library_` | Library feature |
| `live_activity_` | Live activity status text + iOS-style live-activity feature |
| `live_activity_settings_` | Live-activity settings screen |
| `login_` / `onboarding_` | Onboarding + login screens |
| `more_section_` | "More" tab grouping |
| `notification_` | Notifications (channels are android-only; titles/descriptions are shared) |
| `permission_` | OS permission prompts and explanations |
| `refreshing_message` | Pull-to-refresh + similar |
| `score_` | Scores screen |
| `settings_` / `settings_section_` | Settings screen |
| `sync_` | Sync indicators |
| `tab_editor_` | Tab editor screen |
| `weekday_*_short` | Short weekday labels |
| `widget_` | Home-screen widgets |

Suffix conventions:

- `_title`, `_description`, `_message`, `_subtitle`, `_hint` — distinguish heading vs body text
- `_short` — abbreviated form
- `_undo` — paired undo action
- `_confirm`, `_dismiss`, `_action` — for dialog buttons
- `_value` — for parameterized text used as a labeled field value
- `_with_<context>` — variant of a base key with extra context appended (e.g. `class_table_rename_with_course`)

Before adding a key, search the source for an existing one that fits. Avoid
near-duplicates like `error_network_unavailable` vs `network_error`.

## Cross-platform development workflow

Strings are co-developed across the Android and Apple repos, both of which
include this folder as a git submodule.

When you're iterating on a feature that adds strings on **one platform only**,
just add the keys, regenerate, commit on `main`, and bump the submodule pin in
that platform's repo.

When you're iterating on a feature that adds strings on **both platforms at
the same time**:

1. Push a `feature/<name>` branch in `app-translation` with the new keys.
2. In each platform repo, point its submodule at `feature/<name>` for the
   duration of the feature work (so both apps see the same in-flight keys).
3. When the feature lands, fast-forward `feature/<name>` into `main` here,
   then bump both platform repos' submodule pins to the new `main` SHA.

This keeps `main` shippable on both platforms and avoids the situation where
one app's submodule pin references a SHA the other app hasn't picked up yet.

## Regenerating outputs

```bash
python3 tools/localization/generate_localizations.py
```

The script validates the source schema (group structure, no cross-group key
collisions, identical key inventory across locales per group) before writing
anything. Outputs land in `generated/{android,apple}/...` and are checked in.
