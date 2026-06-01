# Localization Strings Audit

> Audit of the shared translation source (`source/<locale>.json`) and how its keys
> are actually consumed by the TigerDuck **Apple** and **Android** apps.
>
> **Date:** 2026-06-01 · **Author:** Sam · **Canonical locale audited:** `en.json`
> (825 keys) · **Repos scanned:** `tigerduck-app` (iOS / macOS / watchOS / widgets),
> `tigerduck-app-android` (phone + Wear OS).

This document is a *recommendations* report. It does **not** change any keys — see
[§7 Migration playbook](#7-migration-playbook) for how to apply the changes safely
(remember: every key edit must be mirrored across all 55 `source/*.json` locales and
regenerated, per `CONVENTIONS.md`).

---

## 1. How strings are consumed today

| | Apple | Android |
|---|---|---|
| **Lookup API** | `String(localized: "key")` (a few legacy `NSLocalizedString`) | `stringResource(R.string.key)` / `context.getString(R.string.key)` |
| **Accessor** | **None** — raw snake_case string literals, no generated `L10n` enum | `R.string.*` (compile-time checked) |
| **Key → symbol** | 1:1, no transform | 1:1, no transform |
| **Compile-time safety** | ❌ a typo'd key silently falls back to the literal | ✅ unknown `R.string.x` fails to compile |

**Group → platform mapping** (from `CONVENTIONS.md`):
`shared` → both · `android` → Android bundle only · `apple` → Apple bundle only.

| Group | Keys | Notes |
|---|---|---|
| `shared` | 711 | Consumed by iOS, macOS (`desktop_*`), watchOS/Wear (`watch_*`), widgets (`widget_*`), and Android phone |
| `android` | 42 | Almost all genuine OS primitives (notif channels, exact alarm, battery, haptics/vibration, back-to-exit, F-Droid/Play flavors) — **correctly placed** |
| `apple` | 72 | **Mixed** — only ~10 are real Apple OS primitives; the rest are platform-neutral strings that just happened to be wired up on iOS first (see §4) |

### Dynamically-constructed keys (defeat naive grep — do **not** treat as unused)

These are built at runtime, so they have no literal call site:

- `weekday_{mon..sun}_short` — built from a weekday index in `WeekGridView.swift`,
  `TodayListView.swift`, `MacCalendarView.swift`.
- `notification_assignment_reminder_body_{5m,15m,16h,24h,30m,48h,multi_hour}` — selected
  by enum in `AssignmentReminderOffset.swift`.
- `widget_no_classes_{today,weekend}` — ternary-selected in `TodayListView.swift`.

No `resources.getIdentifier()` / reflection lookups exist on Android (all `R.string.*`
references are static), so the Android grep results are exact.

---

## 2. Dead keys — present in source, referenced **nowhere** in either repo

These 27 `shared` keys appear in **no** `.swift` / `.kt` source in either app (verified by
literal search across both repos, accounting for the dynamic families above). They are the
safest deletions. **Deleting a key means removing it from all 55 `source/*.json` files**, then
regenerating.

| Key | Value | Why it's dead |
|---|---|---|
| `widget_next_class_dark_desc` | "Current or next class…" | Widgets only ever read the `_light_` variant; `_dark_` is vestigial — value is identical |
| `widget_next_class_dark_label` | "Next Class" | ″ |
| `widget_today_dark_desc` | "Today's class list…" | ″ |
| `widget_today_dark_label` | "Schedule (Today)" | ″ |
| `widget_week_dark_desc` | "Full schedule for this week…" | ″ |
| `widget_week_dark_label` | "Schedule (Week)" | ″ |
| `watch_library_title` | "Library" | watchOS library screen never built; Wear `LibraryQRScreen` uses other keys |
| `watch_library_loading` | "Generating…" | ″ |
| `watch_library_refresh_in_seconds` | "%lld s" | ″ |
| `watch_library_signin_prompt` | "Sign in on iPhone" | ″ |
| `watch_ends_at` | "Ends %1$s" | superseded by `watch_now_ends_at` |
| `class_table_course_no_value` | "Course code: %1$s" | replaced by `course_detail_*` labels |
| `class_table_course_time_value` | "Class time: %1$s" | ″ |
| `class_table_enrolled_count_value` | "Enrollment: %1$d/%2$d" | ″ |
| `desktop_course_detail_course_no_label` | "Course no." | unreferenced Mac string |
| `desktop_widget_up_next` | "Up next" | ″ |
| `course_color_picker_reset_action` | "Restore default color" | superseded by `course_color_picker_*` on Apple |
| `bulletin_push_requesting` | "Requesting…" | bulletin push UI refactor leftover |
| `bulletin_rule_editor_all_depts` | "All departments" | duplicate of `bulletin_rule_all_orgs` (see §3) |
| `bulletin_rule_editor_all_tags` | "All categories" | duplicate of `bulletin_rule_all_tags` |
| `a11y_dropdown_action_hint` | "Double tap to choose another option" | unreferenced a11y hint |
| `error_no_response` | "No response" | generic error never surfaced |
| `error_unknown` | "Unknown error" | ″ (Apple uses the `error_*_format` family instead) |
| `settings_token_valid_until` | "Token valid until %1$s" | debug string, not shown |
| `update_ready_message` | "An update is ready to install." | iOS uses App Store flow, not in-app install |
| `update_restart_action` | "Restart" | ″ |
| `whats_new_title` | "What's new" | duplicate of `settings_whats_new`; UI uses the latter |

> ⚠️ **Caveat:** "dead" = no source reference *as of this commit*. Confirm none are behind an
> unreleased feature branch before deleting. The 200+ "unused" figures a naive per-platform grep
> produces are **false positives** — a `desktop_*` key looks unused to Android but is live on Mac,
> and the dynamic families above look unused everywhere. The 27 above survived a cross-repo check.

---

## 3. Duplicates

### 3a. Platform forks — same key in both `apple` and `android`

These 7 keys are **intentionally** forked because Apple brands the feature **"Live Activity"** and
Android brands it **"Live Updates"** — the copy must match each OS's own term. This is an accepted
convention, now documented under *"OS-branded feature names (intentional forks)"* in
`CONVENTIONS.md`. **Do not deduplicate these back into `shared`.**

| Key | Apple | Android |
|---|---|---|
| `live_activity_settings_description` | "Live activity shows…" | "Live Updates shows…" |
| `live_activity_settings_enable` | "Enable live activity" | "Enable Live Updates" |
| `live_activity_settings_reset_confirm_title` | "Reset all live activity settings?" | "Reset all Live Updates settings?" |
| `live_activity_settings_sound_hint` | "…the \"Live activity\" notification channel…" | "…the \"Live Updates\" notification channel…" |
| `notification_setup_description` | "…and live activity arrive…" | "…and Live Updates arrive…" |
| `permission_notifications_description` | "…notifications and live activity will not appear." | "…notifications and Live Updates will not appear." |
| `permission_warning_description` | "…notifications and live activity may not display…" | "…notifications and Live Updates may not display…" |

**Recommendation:** **Keep the fork as-is.** The brand names are real OS terminology and the fork is
the intended pattern (see `CONVENTIONS.md`). No action required.

*Optional* cost optimization only if the live-activity copy grows: factor the brand term into its own
forked key and reference it from otherwise-shared sentences —

```jsonc
// apple:   "term_live_activity": "Live Activity"
// android: "term_live_activity": "Live Updates"
// shared:  "live_activity_settings_enable": "Enable %1$s"   // pass term_live_activity
```

This trades 7 forked sentences for 1 forked word + 7 shared sentences. Only worth it if the surrounding
copy is expected to stay identical between platforms; today's 7 keys are small enough that leaving them
forked is perfectly fine.

### 3b. Identical-value clusters worth consolidating

Many keys share a value legitimately (a button reused in different contexts *should* have its own
key so it can diverge later). The clusters below, however, are **redundant** — same value, same
semantic role, no plausible reason to diverge:

| Keep | Drop (alias to "Keep") | Value |
|---|---|---|
| `weekday_{d}_short` | `watch_weekday_{d}_short` (×7) | "Mon"…"Sun" — watch can read the base key |
| `score_credit_earned` | `score_credit_earned_label` | "Earned" |
| `score_credit_enrolled` | `score_credit_enrolled_label` | "Enrolled" |
| `score_rank_class` | `score_ranking_class_label` | "Class rank" |
| `bulletin_rule_all_orgs` | `bulletin_rule_editor_all_depts` | "All departments" (also dead, §2) |
| `bulletin_rule_all_tags` | `bulletin_rule_editor_all_tags` | "All categories" (also dead, §2) |
| `bulletin_rule_add_title` | `bulletin_rule_add_action` *(or vice-versa)* | "Add rule" |
| `home_custom_section` | `home_section_custom` | "Custom section" |
| `settings_whats_new` | `whats_new_title` (dead, §2) | "What's new" |

> **Not** recommended for merge (genuinely distinct contexts despite equal English value — they may
> diverge in other locales, e.g. CJK): `feature_*` vs `feature_*_short`, `a11y_*` vs visible labels,
> `calendar_source_exam` vs `calendar_event_source_exam`, `action_*` button verbs reused across screens.

### 3c. `feature_X` vs `feature_X_short` that are byte-identical

All 8 of these have `_short == long` in English, yet a `_short` slot exists so abbreviations can be
set per-locale (e.g. CJK can shorten). They are **not** dead — but worth flagging that for English
they're pure duplicates, so a missing `_short` translation is invisible until a long locale overflows:

`feature_calendar`, `feature_class_table`, `feature_clubs`, `feature_home`, `feature_library`,
`feature_more`, `feature_score`, `feature_settings` (each `== feature_X_short`).

**Recommendation:** keep the slots, but document that `_short` defaults to the long form, and only
override it where a locale actually needs a shorter label.

---

## 4. Keys that should be **merged into `shared`** (Apple↔Android)

`CONVENTIONS.md` is explicit: *"UI labels that exist on both platforms but happen to be wired up
first on one go in `shared`, not in the platform group."* The `apple` group currently violates this
for ~60 of its 72 keys — they're plain UI/error strings with nothing Apple-specific about them.
Leaving them under `apple` guarantees Android will re-create near-duplicate keys when it implements
the same feature (Moodle errors, color names, semester labels, etc.).

### 4a. `apple` keys that already duplicate a `shared` value → delete the apple copy, use shared

| `apple` key | = existing `shared` key | Value |
|---|---|---|
| `action_reset` | `live_activity_settings_reset` (or a new `action_reset` promoted to shared) | "Reset" |
| `calendar_event_source_exam` | `calendar_source_exam` | "Exam" |
| `calendar_event_source_school` | `calendar_source_school` | "School" |
| `class_table_add_course` | `add_course_title` | "Add course" |
| `home_no_courses_today` | `widget_no_classes_today` | "No classes today" |
| `score_credit_type_not_earned_short` | `score_grade_failed` | "Fail" |
| `score_semester_first_short` | `score_semester_upper` | "Fall" |
| `score_semester_second_short` | `score_semester_lower` | "Spring" |

### 4b. `apple` keys that should **move to `shared`** (platform-neutral, will be needed on Android)

These reference no Apple OS primitive; promote them so Android can reuse them instead of forking:

- **All Moodle / SSO / network errors** (24 keys): `error_moodle_*`, `error_sso_*`,
  `error_bulletin_*`, `error_courses_unavailable`, `error_invalid_server_response`,
  `error_library_credentials_not_found`, `error_library_login_failed_format`,
  `error_network_format`, `error_qr_generation_failed_format`, `error_session_expired`.
  *(Moodle/SSO/QR are shared backend concepts, not Apple OS features.)*
- **Color names** (8 keys): `color_name_blue/cyan/green/indigo/orange/pink/purple/red`.
- **Semester labels** (4 keys): `score_semester_first`, `score_semester_first_short`,
  `score_semester_second`, `score_semester_second_short` — though prefer merging with the existing
  `score_semester_upper/lower` (§4a).
- **Score credit-type shorts** (3): `score_credit_type_education_program_short`,
  `score_credit_type_not_counted_short`, `score_credit_type_not_required_short`.
- **Misc UI**: `add_course_searching`, `calendar_date_today_suffix`, `calendar_no_events_today`,
  `course_color_picker_title`, `home_assignments_login_required_message`,
  `home_assignments_none_incomplete`, `home_time_slider_login_required_message`,
  `more_edit_mode_in_development`, `bulletin_subscription_device_not_registered`,
  `score_course_credits_meta`, `settings_notifications_disabled_warning`.

### 4c. `apple` keys that **correctly stay** under `apple` (real OS primitives)

`live_activity_status_assignment_short`, `live_activity_status_in_class_short`,
`live_activity_settings_enable_toggle`, `live_activity_settings_footer`,
`live_activity_settings_nav_title`, `push_server_status_live_activities`,
`push_server_status_settings_hint`, `onboarding_watchos_title`, `onboarding_watchos_description`
— these name Apple-only constructs (Live Activity / Dynamic Island, Apple Watch, the iOS Settings
deep-link). The 7 forked `live_activity_settings_*` from §3a also legitimately stay forked.

> The `android` group is, by contrast, almost entirely correct — every key is a notification
> channel, exact-alarm/battery permission, haptic/vibration setting, back-to-exit toast, or
> F-Droid/Play flavor string. No changes recommended there except the §3a term-extraction.

---

## 5. Keys to **rename** for maintainability

### 5a. Two parallel push-status enums that overlap — unify the vocabulary

There are **two** notification-status key families with overlapping values:

| Concept | `bulletin_push_status_*` (shared) | `push_server_notification_status_*` (shared/apple) |
|---|---|---|
| Provisional | `bulletin_push_status_provisional` | `push_server_notification_status_provisional` |
| Ephemeral | `bulletin_push_status_ephemeral` | `push_server_notification_status_ephemeral` |
| Unknown | `bulletin_push_status_unknown` | `push_server_notification_status_unknown` |
| Undetermined | `bulletin_push_status_undetermined` | `push_server_notification_status_undetermined` |
| Denied | `bulletin_push_status_denied` | `push_server_notification_status_denied_hint` |

**Recommendation:** collapse to one family, e.g. `push_status_<state>`, and have both the bulletin
screen and the server-push settings screen read it. ~10 keys removed.

### 5b. Terminology drift between key names and values: `login` vs `sign in`

Key vocabulary says **login / logout / logged_in**; the English values say **Sign in / Sign out /
Signed in**. Examples: `action_login` = "Sign in", `action_logout` = "Sign out",
`common_not_logged_in` = "Not signed in", `library_status_logged_in` = "Signed in",
`onboarding_login_*`, `score_error_login_expired` = "Login expired".

**Recommendation:** pick one. Since the user-facing copy standardized on **"sign in"**, rename the
keys to match (`action_sign_in`, `common_not_signed_in`, …). Improves greppability — today you can't
find a string by the word users actually see.

### 5c. `org` vs `dept` vs `department` inconsistency (bulletin rules)

Within one feature: `bulletin_rule_all_orgs` / `bulletin_rule_orgs_prefix` ("Dept: ") use **orgs**,
while `bulletin_rule_editor_dept_section` / `bulletin_rule_dept_only_title` use **dept**, and values
say **"Department"**. Standardize the key token on `dept` (matches the values and the other keys).

### 5d. `desktop_*` is the macOS app — consider `mac_*`

61 `desktop_*` keys live in `shared` but are consumed **only by the macOS target** (Apple).
"desktop" is ambiguous (the project has no web-desktop). Renaming to `mac_*` would make the platform
obvious. *(Lower priority — large rename, purely cosmetic. If done, do it in one sweep.)*

### 5e. `live_activity_status_*` (shared) vs `live_activity_status_*_short` (apple)

The base statuses (`live_activity_status_in_class`, `…_class_preparing`, `…_assignment_urgent`) are
shared; the `_short` forms are apple-only. That's fine, but note `live_activity_status_assignment_urgent`
== `notification_assignment_due_title` == "Assignment due soon" (3b territory) — verify they're meant
to track together or give the notification its own intent.

---

## 6. Summary scorecard

| Finding | Count | Action |
|---|---|---|
| Total canonical keys (`en`) | 825 | — |
| Confirmed dead (both repos) | **27** | Delete from all 55 locales (§2) |
| `live_activity` brand-forked pairs | 7 | **Keep** — intentional OS-brand fork, documented in CONVENTIONS (§3a) |
| Redundant identical-value pairs | ~14 | Alias/merge (§3b, §3c) |
| `apple` keys duplicating a `shared` value | 8 | Delete apple copy, use shared (§4a) |
| `apple` keys that should be `shared` | ~50 | Promote to `shared` (§4b) |
| Parallel push-status enum overlap | ~10 | Unify to `push_status_*` (§5a) |
| `login`→`sign_in` key renames | ~12 | Rename for value/key parity (§5b) |

**Net:** ~35–40 keys removable outright, ~60 keys relocatable to `shared`, plus two vocabulary
cleanups (`login`/`sign in`, `org`/`dept`). Doing §4 alone roughly halves the `apple` group and
prevents the next round of Android-side duplicate keys.

---

## 7. Migration playbook

Every change below touches **all 55 `source/*.json` locales** (the generator validates that every
locale has an identical key set per group). Suggested order, lowest-risk first:

1. **Delete dead keys (§2).** Remove the 27 keys from every `source/*.json`. Run
   `python3 tools/localization/generate_localizations.py`; build both apps to confirm nothing breaks.
2. **Merge §4a duplicates.** Delete the 8 `apple` copies; repoint the iOS call sites to the existing
   `shared` key. iOS-only change, no Android impact.
3. **Promote §4b to `shared`.** Move keys from the `apple` object to `shared` in each locale (value
   unchanged). No code change needed on iOS; Android can start consuming them next time it implements
   the feature.
4. **Consolidate §3b / §5a.** Alias the redundant keys, update call sites, delete the losers.
5. **Renames (§5b–5d).** Highest churn — do each as its own commit/PR so the diff is reviewable, and
   update both repos' call sites in the same change. Use the §6 cross-platform branch workflow from
   `CONVENTIONS.md` (push a `feature/<name>` branch here, point both submodules at it, fast-forward
   to `main` when done).
6. After each step: regenerate, build **both** apps, and for the CJK trio (`zh-Hant`, `zh-Hans`,
   `yue-HK`) re-check wording per the reference-locale policy.

> **Watch out for the dynamic families** (§1): when renaming `weekday_*_short` or
> `notification_assignment_reminder_body_*`, grep won't catch the call sites — fix
> `AssignmentReminderOffset.swift`, `WeekGridView.swift`, `TodayListView.swift`, and
> `MacCalendarView.swift` by hand.
