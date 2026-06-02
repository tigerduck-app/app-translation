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

## ✅ Phase 2 — DONE (key renames; app call sites repointed; pushed)

Done as 3 reviewable commit-sets (one per group, each = app-translation commit +
matching Apple + Android commits). All renames are **value-preserving** (existing
translations carry over → still 0 Sonnet translation needed). Applied via
`tools/rename_keys_json.py` (source) + `tools/rename_keys_code.py` (code, with a
built-in *stale-reference guard* that fails if any old key survives the pass).
**Final sweep: 0 stale references for all 110 renamed keys across both repos.**

| Group | Change | Keys | Audit § | Code sites repointed |
|---|---|---|---|---|
| 2.1 | Dedup identical-value + merge apple dups + `org`→`dept` | 16 | §3b/§4a/§5c | 12 Swift · 15 Kotlin |
| 2.2 | `login`/`logged_in` → `sign_in`/`signed_in` | 35 | §5b | 52 Swift · 37 Kotlin |
| 2.3 | `desktop_*` → `desktop_*` (macOS-only keys) | 59 | §5d | 60 Swift · 0 Kotlin |

Group 2.1 detail: `watch_weekday_*_short`→`weekday_*_short` (wear now uses the
shared base), `score_credit_*_label`→`score_credit_*`, `score_ranking_class_label`→
`score_rank_class`, `home_section_custom`→`home_custom_section`,
`calendar_event_source_*`→`calendar_source_*`, `class_table_add_course`→
`add_course_title`, `bulletin_rule_all_orgs`→`bulletin_rule_all_depts`,
`bulletin_rule_orgs_prefix`→`bulletin_rule_dept_prefix`. Group 2.2 maps
`relogin`→`re_sign_in` (not "resign").

> ⚠️ **Still needs a build + smoke test before merge.** Renames were grep-verified
> exhaustively (static refs only; the one dynamic family, `weekday_*_short` via
> `weekdayKey()`, is a rename *target* and stays valid), but a missed Apple literal
> would fail *silently*. Launch both apps and check: auth / onboarding / library /
> score screens (2.2), the Mac app (2.3), and watch Now&Next weekday labels (2.1).

## ⏸️ Still deferred — needs a product decision, not a mechanical rename

| Change | Audit § | Why not done |
|---|---|---|
| Unify the two push-status enums | §5a | `bulletin_push_status_*` and `push_server_notification_status_*` carry **different** values per state (e.g. "Denied" vs "Denied (open system Settings to re-enable)"), so collapsing them changes displayed text and would need fresh translations — not value-preserving. Pick the canonical wording per state first; then it can follow the same map-driven flow. |
