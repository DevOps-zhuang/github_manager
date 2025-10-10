"""Collect rate-limit failures and generate per-organization retry batches.

Usage:
    python invitation/bin/retry_failed.py --input invitation/reports/invitation_results.csv

Behavior:
- Reads the report CSV and finds rows where Status is 'failure' and Message contains 'rate limit' or 'Over invitation rate limit'.
- Groups by Organization, sorts by Timestamp ascending, and creates batch CSVs under
  `invitation/reports/retry_batches/<Organization>/batch_<n>.csv`.
- Each batch contains at most 50 invites per 24-hour window. If there are more than 50 failed
  invites in the last 24 hours, the extra invites are written to subsequent batch files.

This script does not re-run invitations; it only prepares batch files for manual rerun later.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

RATE_LIMIT_KEYWORDS = ("rate limit", "over invitation rate limit", "Over invitation rate limit")
BATCH_DIR = Path("invitation") / "reports" / "retry_batches"
MAX_PER_24H = 50


def parse_timestamp(value: str) -> datetime:
    try:
        # ISO format with timezone
        return datetime.fromisoformat(value)
    except Exception:
        # Fallback: try to parse without timezone
        return datetime.fromisoformat(value)


def load_failures(input_path: Path) -> List[dict]:
    rows: List[dict] = []
    with input_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            status = (row.get("Status") or "").strip().lower()
            message = (row.get("Message") or "").strip()
            if status != "failure":
                continue
            lower_msg = message.lower()
            if not any(k in lower_msg for k in RATE_LIMIT_KEYWORDS):
                continue
            # ensure timestamp exists
            ts_val = (row.get("Timestamp") or "").strip()
            try:
                ts = parse_timestamp(ts_val)
            except Exception:
                ts = datetime.now(timezone.utc)
            row["_parsed_ts"] = ts
            rows.append(row)
    return rows


def chunk_by_24h_limit(sorted_rows: List[dict]) -> List[List[dict]]:
    """Given rows sorted by timestamp asc, produce batches obeying MAX_PER_24H per batch window.

    Strategy: slide a 24h window starting at first item's timestamp; fill up to MAX_PER_24H items that fall
    within that window. Remaining items start a new window at their own timestamp.
    """
    batches: List[List[dict]] = []
    i = 0
    n = len(sorted_rows)
    while i < n:
        start_ts = sorted_rows[i]["_parsed_ts"]
        window_end = start_ts + timedelta(hours=24)
        batch = []
        j = i
        while j < n and len(batch) < MAX_PER_24H:
            row_ts = sorted_rows[j]["_parsed_ts"]
            if row_ts <= window_end:
                batch.append(sorted_rows[j])
                j += 1
            else:
                break
        if not batch:
            # If the single item is beyond 24h window but batch empty (shouldn't happen), take one
            batch.append(sorted_rows[i])
            j = i + 1
        batches.append(batch)
        i = j
    return batches


def write_batches(org: str, batches: List[List[dict]], out_dir: Path) -> None:
    org_dir = out_dir / org
    org_dir.mkdir(parents=True, exist_ok=True)
    for idx, batch in enumerate(batches, start=1):
        path = org_dir / f"batch_{idx}.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Mail", "Organization", "Team", "Timestamp", "OriginalMessage"])
            for row in batch:
                writer.writerow([
                    row.get("Mail", ""),
                    row.get("Organization", ""),
                    row.get("Team", ""),
                    row.get("Timestamp", ""),
                    row.get("Message", ""),
                ])
        print(f"Wrote retry batch: {path} (size={len(batch)})")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare retry batches for rate-limited invitation failures.")
    parser.add_argument("--input", type=Path, default=Path("invitation") / "reports" / "invitation_results.csv")
    parser.add_argument("--out", type=Path, default=BATCH_DIR)
    args = parser.parse_args(argv)

    rows = load_failures(args.input)
    if not rows:
        print("No rate-limit failures found in input.")
        return 0

    # Group by organization
    groups = defaultdict(list)
    for row in rows:
        org = (row.get("Organization") or "<unknown>").strip()
        groups[org].append(row)

    for org, items in groups.items():
        # sort by timestamp ascending
        sorted_rows = sorted(items, key=lambda r: r["_parsed_ts"])
        batches = chunk_by_24h_limit(sorted_rows)
        write_batches(org, batches, args.out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
