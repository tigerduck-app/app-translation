#!/usr/bin/env python3
"""Apply an explicit key-rename map to every source/<locale>.json.

Usage: rename_keys_json.py <map.json>
  map.json: {"old_key": "new_key", ...}

Rules (value-preserving):
- If new_key already exists (merge case): drop old_key, keep new_key's value.
  Refuses if the two values differ in en (guards accidental lossy merges).
- Else (pure rename): move old_key's value to new_key in the SAME group.
Groups stay shared/android/apple ordered, keys sorted within. Then regenerates.
"""
from __future__ import annotations
import json, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source"
GROUP_ORDER = ["shared", "android", "apple"]


def group_of(d, k):
    for g in GROUP_ORDER:
        if k in d.get(g, {}):
            return g
    return None


def main():
    mapping = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    en = json.loads((SRC / "en.json").read_text(encoding="utf-8"))

    # Guard: merge cases must have equal en values; pure renames must not collide.
    for old, new in mapping.items():
        og, ng = group_of(en, old), group_of(en, new)
        if og is None:
            sys.exit(f"ABORT: old key not found in en: {old}")
        if ng is not None:  # merge
            ov = en[og][old]; nv = en[ng][new]
            if ov != nv:
                sys.exit(f"ABORT: merge {old}->{new} but en values differ: {ov!r} != {nv!r}")

    for p in sorted(SRC.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for old, new in mapping.items():
            og = group_of(d, old)
            if og is None:
                continue
            val = d[og].pop(old)
            ng = group_of(d, new)
            if ng is None:  # pure rename -> same group as old
                d[og][new] = val
            # else merge: keep existing new value, drop old (already popped)
        out = {g: dict(sorted(d.get(g, {}).items())) for g in GROUP_ORDER}
        p.write_text(json.dumps(out, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")

    subprocess.check_call([sys.executable, str(ROOT / "tools/localization/generate_localizations.py")])
    print(f"renamed {len(mapping)} keys across {len(list(SRC.glob('*.json')))} locales + regenerated")


if __name__ == "__main__":
    main()
