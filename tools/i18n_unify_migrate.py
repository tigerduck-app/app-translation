#!/usr/bin/env python3
"""chore/i18n-unify migration (value-preserving).

Phase 1:
  (A) Delete 27 confirmed-dead `shared` keys (referenced in neither app).
  (B) Relocate platform-neutral `apple` keys -> `shared` so both platforms can
      consume them. Apple's generated bundle is `shared ∪ apple`, so the Apple
      output is byte-identical; Android gains the keys. Per-locale values are
      preserved (carried over from each locale's existing `apple` entry).

Keys that name a genuine Apple OS primitive (Live Activity / Dynamic Island /
Apple Watch / iOS Settings deep-link) and the 7 intentional Live Activity vs
Live Updates brand forks STAY in `apple`.

The script is idempotent and preserves source formatting (indent=4,
ensure_ascii=False, groups ordered shared/android/apple, keys sorted within).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "source"
GROUP_ORDER = ["shared", "android", "apple"]

DEAD = {
    "widget_next_class_dark_desc", "widget_next_class_dark_label",
    "widget_today_dark_desc", "widget_today_dark_label",
    "widget_week_dark_desc", "widget_week_dark_label",
    "watch_library_title", "watch_library_loading",
    "watch_library_refresh_in_seconds", "watch_library_signin_prompt",
    "watch_ends_at", "class_table_course_no_value",
    "class_table_course_time_value", "class_table_enrolled_count_value",
    "desktop_course_detail_course_no_label", "desktop_widget_up_next",
    "course_color_picker_reset_action", "bulletin_push_requesting",
    "bulletin_rule_editor_all_depts", "bulletin_rule_editor_all_tags",
    "a11y_dropdown_action_hint", "error_no_response", "error_unknown",
    "settings_token_valid_until", "update_ready_message",
    "update_restart_action", "whats_new_title",
}

# Real Apple OS primitives + intentional brand forks -> stay in `apple`.
KEEP_APPLE = {
    # intentional "Live Activity" (Apple) vs "Live Updates" (Android) forks
    "live_activity_settings_description", "live_activity_settings_enable",
    "live_activity_settings_reset_confirm_title", "live_activity_settings_sound_hint",
    "notification_setup_description", "permission_notifications_description",
    "permission_warning_description",
    # Apple-only OS primitives
    "live_activity_settings_enable_toggle", "live_activity_settings_footer",
    "live_activity_settings_nav_title", "live_activity_status_assignment_short",
    "live_activity_status_in_class_short", "push_server_status_live_activities",
    "push_server_status_settings_hint", "onboarding_watchos_title",
    "onboarding_watchos_description",
}


def load(p): return json.loads(p.read_text(encoding="utf-8"))


def dump(p, data):
    out = {g: dict(sorted(data.get(g, {}).items())) for g in GROUP_ORDER}
    p.write_text(json.dumps(out, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    en = load(SRC / "en.json")
    relocate = sorted(set(en["apple"]) - KEEP_APPLE)
    placeholders = []  # (locale, key) where we had to fall back to en

    for p in sorted(SRC.glob("*.json")):
        loc = p.stem
        d = load(p)
        shared, android, apple = d.get("shared", {}), d.get("android", {}), d.get("apple", {})

        # (A) delete dead
        for k in DEAD:
            shared.pop(k, None)

        # (B) relocate apple -> shared (preserve this locale's value)
        for k in relocate:
            if k in apple:
                val = apple.pop(k)
            elif k in en["apple"]:
                val = en["apple"][k]  # locale missing it: en placeholder, track
                placeholders.append((loc, k))
            else:
                continue
            shared[k] = val

        dump(p, {"shared": shared, "android": android, "apple": apple})

    # Report
    print(f"deleted dead keys: {len(DEAD)}")
    print(f"relocated apple->shared: {len(relocate)}")
    print(f"kept in apple: {len(KEEP_APPLE)}")
    if placeholders:
        print(f"\nEN-PLACEHOLDERS introduced (locale missing key): {len(placeholders)}")
        for loc, k in placeholders:
            print(f"  {loc}\t{k}")
    else:
        print("\nEN-PLACEHOLDERS introduced: 0 (all locales already had every relocated key)")


if __name__ == "__main__":
    main()
