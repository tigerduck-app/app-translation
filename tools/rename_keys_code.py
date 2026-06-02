#!/usr/bin/env python3
"""Whole-word rename of localization key tokens in app source code.

Usage: rename_keys_code.py <map.json> <repo_root> [--ext .swift,.kt,...]

Replaces every whole-word occurrence of each old key with its new key in code
files under <repo_root>, skipping the localization submodule, build dirs, and
.git. Whole-word (\bKEY\b) matching means `action_login` never matches inside
`action_login_button` (underscore is a word char, so no boundary there).

Prints, per file, how many replacements were made. Exits non-zero if any old
key from the map still appears anywhere after the pass (stale-reference guard).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DEFAULT_EXT = {".swift", ".kt", ".kts", ".java", ".xml", ".plist", ".strings",
               ".pbxproj", ".json", ".m", ".mm", ".h"}
SKIP_DIRS = {".git", "build", ".gradle", "DerivedData", "Pods", "node_modules"}
SKIP_PATH_PARTS = {"localization", "app-translation"}  # the translation submodule


def iter_files(root: Path, exts):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        parts = set(p.relative_to(root).parts)
        if parts & SKIP_DIRS or parts & SKIP_PATH_PARTS:
            continue
        yield p


def main():
    mapping = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(sys.argv[2]).resolve()
    exts = DEFAULT_EXT
    if len(sys.argv) > 3 and sys.argv[3] == "--ext":
        exts = set(sys.argv[4].split(","))

    patterns = {old: re.compile(rf"\b{re.escape(old)}\b") for old in mapping}
    total = 0
    files = list(iter_files(root, exts))
    for p in files:
        try:
            txt = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new = txt
        n = 0
        for old, pat in patterns.items():
            new, c = pat.subn(mapping[old], new)
            n += c
        if n:
            p.write_text(new, encoding="utf-8")
            print(f"  {n:3d}  {p.relative_to(root)}")
            total += n

    # stale guard
    stale = []
    for p in files:
        try:
            txt = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for old, pat in patterns.items():
            if pat.search(txt):
                stale.append((old, str(p.relative_to(root))))
    print(f"total replacements: {total}")
    if stale:
        print("STALE references remain:")
        for old, f in stale:
            print(f"  {old}  in  {f}")
        sys.exit(1)
    print("stale-reference guard: OK (0 old keys remain)")


if __name__ == "__main__":
    main()
