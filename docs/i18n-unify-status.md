# i18n-unify — execution status

Branch `chore/i18n-unify` (app-translation from `main`; both apps from `dev`).
Companion to [`localization-audit.md`](localization-audit.md). Driven by
`tools/i18n_unify_migrate.py` (idempotent, value-preserving).

## ✅ Phase 1 — DONE (value-preserving, zero app-code change, pushed)

| Change | Count | Audit § |
|---|---|---|
| Deleted confirmed-dead `shared` keys | 27 | §2 |
| Relocated platform-neutral `apple` → `shared` | 56 | §4a/§4b |
| Kept in `apple` (real OS primitives + brand forks) | 16 | §4c |

**Why it's safe (verified, no app build needed):**

- Apple bundle = `shared ∪ apple`; moving a key between those sets leaves the
  union identical. Confirmed: Apple `Localizable.strings` diff has **0 additions**
  and only removes the 27 dead keys (which the iOS/macOS/watchOS code references
  nowhere — grep-verified in `tigerduck-app`).
- Android bundle = `shared ∪ android`; it loses the same 27 dead keys (grep-verified
  unused, incl. no `R.string.*` ref → no compile break) and gains the 56 relocated
  keys (unused for now, available for future Android features).
- **No `.swift` / `.kt` call site changes were required**, because no key was renamed
  and no key the apps actually use was removed.

**Translation status:** the migration introduced **0 English placeholders** — every
relocated key was already translated in all 55 locales, so values carried over
verbatim. No Sonnet translation pass was needed for Phase 1.

### The 16 keys intentionally kept in `apple`

7 brand forks (Apple "Live Activity" vs Android "Live Updates", see CONVENTIONS):
`live_activity_settings_description`, `live_activity_settings_enable`,
`live_activity_settings_reset_confirm_title`, `live_activity_settings_sound_hint`,
`notification_setup_description`, `permission_notifications_description`,
`permission_warning_description`.

9 Apple-only OS primitives: `live_activity_settings_enable_toggle`,
`live_activity_settings_footer`, `live_activity_settings_nav_title`,
`live_activity_status_assignment_short`, `live_activity_status_in_class_short`,
`push_server_status_live_activities`, `push_server_status_settings_hint`,
`onboarding_watchos_title`, `onboarding_watchos_description`.

## ⏸️ Phase 2 — DEFERRED (needs app-code edits + a build to verify)

These were intentionally **not** done autonomously: each renames a key and must
repoint call sites in both `tigerduck-app` (Swift) and `tigerduck-app-android`
(Kotlin). They are value-preserving (translations carry over → still no Sonnet
needed), but a missed Apple call site fails *silently* (shows the raw key), so they
should land with a build + smoke test in the loop.

| Change | Keys | Audit § | Notes |
|---|---|---|---|
| Name-dedup of identical-value pairs | ~9 | §3b/§3c | `watch_weekday_*_short`→`weekday_*_short`; `score_credit_*_label`→`score_credit_*`; `score_ranking_class_label`→`score_rank_class`; `home_section_custom`→`home_custom_section` |
| Apple dup-keys → existing shared key | ~5 | §4a | `calendar_event_source_exam/school`→`calendar_source_*`; `class_table_add_course`→`add_course_title` |
| Unify the two push-status enums | ~10 | §5a | `bulletin_push_status_*` + `push_server_notification_status_*` → one `push_status_*` family |
| `login`/`logged_in` → `sign_in`/`signed_in` | ~12 | §5b | key↔value vocabulary parity |
| `org`/`orgs` → `dept` in bulletin rules | ~3 | §5c | |
| `desktop_*` → `mac_*` | 61 | §5d | large cosmetic churn; do as one isolated sweep |

**When executing Phase 2:** mind the dynamic key families (grep won't find them) —
`weekday_*_short` and `notification_assignment_reminder_body_*` are built at runtime
in `AssignmentReminderOffset.swift`, `WeekGridView.swift`, `TodayListView.swift`,
`MacCalendarView.swift`. After any rename: regenerate, grep both repos for zero stale
references, build both apps, then bump submodule pins.
