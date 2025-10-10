#!/usr/bin/env python
"""Scan public repository code for accidental enterprise leakage.

Usage:
    python scripts/scan_enterprise.py

Exit codes:
    0 - OK (no disallowed patterns outside customize/)
    1 - Violations detected

Add to a pre-commit hook, e.g. .git/hooks/pre-commit:
    #!/bin/sh
    python scripts/scan_enterprise.py || exit 1
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Keywords / patterns that should not appear outside customize/
_enterprise = "".join(["east", "money"])
BLOCK_PATTERNS = [
    rf"@{_enterprise}\.com",
    _enterprise,
    _enterprise.title(),
]

ALLOWED_DIR_FRAGMENT = "customize"  # Allowed containment path fragment
ROOT = Path(__file__).resolve().parents[1]

TEXT_FILE_EXT = {"py", "md", "csv", "txt", "json", "yml", "yaml"}

violations: list[str] = []
pattern_compiled = [re.compile(p, re.IGNORECASE) for p in BLOCK_PATTERNS]

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    if ALLOWED_DIR_FRAGMENT in path.parts:
        continue  # ignore anything under customize/
    ext = path.suffix.lstrip(".")
    if ext not in TEXT_FILE_EXT:
        continue
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for pat in pattern_compiled:
        if pat.search(content):
            rel = path.relative_to(ROOT)
            violations.append(f"{rel}: matched '{pat.pattern}'")
            break

if violations:
    print("[SCAN] Disallowed enterprise markers detected:")
    for v in violations:
        print("  -", v)
    print("\nPlease remove these references or move them under 'invitation/customize/'.")
    sys.exit(1)
else:
    print("[SCAN] OK - no enterprise markers outside 'customize/' directory.")
