# German-text leak audit

Nine locales once carried German text. This file records what leaked, what
fixed it, and what has not been checked — so nobody re-derives it.

## What leaked, and where it stands

**Fixed on `feat/v2.1.0`, before the pin every app currently uses.**

| | |
|---|---|
| Locales | `hr` `hu` `is` `lt` `pl` `ro` `sk` `sr` `th` — nine |
| Scale | 48 keys shared by all nine; 99 distinct keys overall; `lt` worst at 96 |
| Keys | Mostly the whole `bulletin_*` block, plus the library sign-in QR prompt that made this visible on phone and watch |
| Where | **Generated output only** (`generated/android/values-*`, `generated/apple/*.lproj`) — `source/` was never wrong |
| Fixed by | `039daaab` *fix(i18n): replace the German text leaked into nine locales* |
| Guarded by | `a5fcbdd6` *feat(i18n): fail generation when one locale carries another's text* |

Both are ancestors of `3c8d7b84`, the pin the backend, iOS and Android all
carry, so **v2.1.0 ships correct text**. The released 2.0.2 build still shows
German in those nine languages; whether that warrants a 2.0.x hotfix is a
release decision, not a translation one.

The guard (see `CONVENTIONS.md`) fails generation when two unrelated locales
share 20 or more identical non-English values. Legitimately overlapping pairs
are allowlisted in `_RELATED_LOCALE_PAIRS` in the generator.

## Fresh scan at `3c8d7b84` — nothing left to fix

Method, re-runnable: flatten every `source/*.json`; for every locale other
than `de*`, flag a key whose value is byte-identical to `de`'s, is not also
identical to `en`'s, and is at least 8 characters. Deliberately looser than
the generator's guard, which needs 20 shared values before it fires.

16 keys matched. Every one is a **legitimate cognate** — the word really is
spelled that way in the target language. Listed so a future scan does not
re-litigate them:

| Key | Locales | German value |
|---|---|---|
| `android.account_id_use_standard_keyboard` | da, no | Standardtastatur |
| `shared.bulletin_filter_tag` | cs | Kategorie |
| `shared.bulletin_rule_editor_tag_section` | cs | Kategorie |
| `shared.bulletin_rule_tags_prefix` | cs | Kategorie: |
| `shared.class_table_rename_default_label` | da, no, sv | Standard: %1$s |
| `shared.common_automatic` | nl | Automatisch |
| `shared.feature_calendar` | da, et, id, no, sv | Kalender |
| `shared.feature_calendar_short` | da, et, id, no, sv | Kalender |
| `shared.feature_scholarship` | cs, da, et, sv | Stipendium |
| `shared.feature_scholarship_short` | cs, da, et, sv | Stipendium |
| `shared.score_gpa_term_label` | no | Semester-GPA (%1$s) |
| `shared.score_info_term` | id, sk, sl | Semester |
| `shared.score_semester_ranking` | nl | Rang %1$s(%2$s) |
| `shared.source_code_picker_org_description` | da, en-GB, fr, sv | Organisation |
| `shared.watch_tomorrow_at` | nl | Morgen · %1$s |
| `shared.widget_tomorrow_time` | nl | Morgen %1$s |

## Not checked

- Leaks between language pairs **other than German** — the guard covers them
  going forward, but no one has swept the existing generated output for them.
- Whether the nine locales' replacement text reads naturally to a native
  speaker. It is no longer German; it has not been proofread.
