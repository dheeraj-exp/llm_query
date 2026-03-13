from __future__ import annotations

import argparse
from pathlib import Path

from llm_runner.csv_utils import expand_queries, read_query_templates, write_single_column_csv


def main() -> int:
    ap = argparse.ArgumentParser(description="Expand query.csv templates to generated_queries.csv")
    ap.add_argument("--input", default="query.csv", help="Path to query.csv")
    ap.add_argument("--output", default="generated_queries.csv", help="Path to generated_queries.csv")
    args = ap.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    rows = read_query_templates(input_path)
    result = expand_queries(rows)
    write_single_column_csv(output_path, header="generated_query", rows=result.generated_queries)
    print(f"Wrote {len(result.generated_queries)} queries to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

