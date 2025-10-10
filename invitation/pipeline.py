"""Utilities for normalizing enterprise CSV datasets into invite-ready exports."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from invitation.constants import StandardColumns
from invitation.data_transformation import transform_invitation_data

STANDARD_FIELDNAMES: Sequence[str] = (
    StandardColumns.MAIL,
    StandardColumns.ORGANIZATION,
    StandardColumns.TEAM,
)


def load_csv_rows(path: Path) -> List[dict[str, str]]:
    """Load raw rows from a CSV file as dictionaries."""

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: List[dict[str, str]] = []
        for raw_row in reader:
            row = {key: (value.strip() if isinstance(value, str) else "") for key, value in raw_row.items()}
            if not any(value for value in row.values()):
                continue
            rows.append(row)
        return rows


def derive_normalized_path(input_path: Path) -> Path:
    """Derive the default normalized output path based on the input file."""

    return input_path.with_name(f"normalized_{input_path.name}")


def _load_existing_normalized_rows(path: Path) -> tuple[List[dict[str, str]], List[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [
            {key: (value.strip() if isinstance(value, str) else "") for key, value in raw_row.items()}
            for raw_row in reader
        ]
        header = list(reader.fieldnames or [])
    return rows, header


def _merge_invitation_results(
    normalized_rows: Iterable[Mapping[str, str]],
    existing_rows: Iterable[Mapping[str, str]],
) -> List[dict[str, str]]:
    existing_map: dict[tuple[str, str, str], Mapping[str, str]] = {}
    for row in existing_rows:
        key = (
            row.get(StandardColumns.MAIL, "").strip().lower(),
            row.get(StandardColumns.ORGANIZATION, "").strip().lower(),
            row.get(StandardColumns.TEAM, "").strip().lower(),
        )
        existing_map[key] = row

    merged_rows: List[dict[str, str]] = []
    for row in normalized_rows:
        mutable: dict[str, str] = dict(row)
        key = (
            mutable.get(StandardColumns.MAIL, "").strip().lower(),
            mutable.get(StandardColumns.ORGANIZATION, "").strip().lower(),
            mutable.get(StandardColumns.TEAM, "").strip().lower(),
        )
        existing = existing_map.get(key)
        if existing:
            invitation_result = existing.get("invitation_result", "")
            if invitation_result:
                mutable["invitation_result"] = invitation_result
        merged_rows.append(mutable)

    return merged_rows


def write_normalized_csv(
    rows: Iterable[Mapping[str, str]],
    path: Path,
    fieldnames: Sequence[str] | None = None,
) -> None:
    """Write normalized rows to disk, preserving original columns and appending standard ones."""

    row_list = list(rows)

    if fieldnames is None:
        ordered_keys: list[str] = []
        seen: set[str] = set()
        for row in row_list:
            for key in row.keys():
                if key not in seen:
                    ordered_keys.append(key)
                    seen.add(key)
        for key in STANDARD_FIELDNAMES:
            if key not in seen:
                ordered_keys.append(key)
                seen.add(key)
        resolved_fieldnames = ordered_keys or list(STANDARD_FIELDNAMES)
    else:
        resolved_fieldnames = list(fieldnames)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=resolved_fieldnames)
        writer.writeheader()
        for row in row_list:
            writer.writerow({key: row.get(key, "") for key in resolved_fieldnames})


def normalize_csv_file(
    enterprise_key: str,
    *,
    input_path: Path,
    output_path: Path | None = None,
    fieldnames: Sequence[str] | None = None,
) -> Sequence[Mapping[str, str]]:
    """Normalize a raw CSV file and persist the invite-ready output."""

    resolved_output = output_path or derive_normalized_path(input_path)
    raw_rows = load_csv_rows(input_path)
    normalized_rows = list(transform_invitation_data(enterprise_key, raw_rows))

    existing_rows: List[dict[str, str]] | None = None
    existing_fieldnames: List[str] | None = None
    if resolved_output.exists():
        existing_rows, existing_fieldnames = _load_existing_normalized_rows(resolved_output)
        if existing_rows:
            normalized_rows = _merge_invitation_results(normalized_rows, existing_rows)

    final_fieldnames = fieldnames or existing_fieldnames
    write_normalized_csv(normalized_rows, resolved_output, fieldnames=final_fieldnames)
    return normalized_rows


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Normalize enterprise invitation CSV data into standard schema."
    )
    parser.add_argument("enterprise", help="Registry key for the enterprise normalizer.")
    parser.add_argument("input", type=Path, help="Path to the raw CSV file.")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Optional destination for the normalized CSV file (default: normalized_<input-name> in same directory).",
    )

    args = parser.parse_args(argv)
    output_path = args.output or derive_normalized_path(args.input)
    normalize_csv_file(args.enterprise, input_path=args.input, output_path=output_path)


if __name__ == "__main__":
    main()
