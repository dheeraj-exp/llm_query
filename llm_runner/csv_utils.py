from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class QueryExpansionResult:
    generated_queries: List[str]


def _clean_cell(s: str) -> str:
    return (s or "").strip().strip("\ufeff")


def read_query_templates(csv_path: Path) -> List[Sequence[str]]:
    rows: List[Sequence[str]] = []
    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            row = [_clean_cell(c) for c in row]
            if not row or not row[0]:
                continue
            rows.append(row)
    return rows


def expand_queries(rows: Iterable[Sequence[str]]) -> QueryExpansionResult:
    generated: List[str] = []
    for row in rows:
        template = _clean_cell(row[0])
        values = [_clean_cell(v) for v in row[1:] if _clean_cell(v)]
        if not values:
            # No values: keep template as-is (useful for queries without %s).
            generated.append(template)
            continue
        for v in values:
            if "%s" in template:
                generated.append(template.replace("%s", v))
            else:
                # If template has no placeholder, append the value.
                generated.append(f"{template} {v}".strip())
    # De-duplicate but preserve order
    seen = set()
    deduped: List[str] = []
    for q in generated:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return QueryExpansionResult(generated_queries=deduped)


def write_single_column_csv(path: Path, header: str, rows: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([header])
        for r in rows:
            writer.writerow([r])


def read_single_column_csv(path: Path) -> List[str]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        out: List[str] = []
        for i, row in enumerate(reader):
            if i == 0 and row and _clean_cell(row[0]).lower() in {"query", "generated_query"}:
                continue
            if not row:
                continue
            val = _clean_cell(row[0])
            if val:
                out.append(val)
    return out


def write_responses_csv(
    path: Path,
    rows: Iterable[dict],
    fieldnames: Sequence[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
