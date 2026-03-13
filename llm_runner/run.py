from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Dict, List

from llm_runner.csv_utils import read_single_column_csv, write_responses_csv
from llm_runner.selenium_utils import DriverConfig, build_chrome_driver
from llm_runner.sites.chatgpt import ChatGPTAdapter


def build_site(site_name: str, driver):
    site_name = site_name.lower().strip()
    if site_name == "chatgpt":
        return ChatGPTAdapter(driver=driver)
    raise SystemExit(f"Unknown site: {site_name}. (supported: chatgpt)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run generated queries against LLM websites.")
    ap.add_argument("--site", action="append", required=True, help="Site name (repeatable). Example: --site chatgpt")
    ap.add_argument("--queries", default="generated_queries.csv", help="Path to generated_queries.csv (single column)")
    ap.add_argument("--out", default="responses.csv", help="Output CSV path")
    ap.add_argument("--headful", action="store_true", help="Run with visible browser window (recommended for login)")
    ap.add_argument("--profile-root", default=".browser_profiles", help="Where to store persistent browser profiles")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of queries (0 = no limit)")
    args = ap.parse_args()

    queries_path = Path(args.queries).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    profile_root = Path(args.profile_root).expanduser().resolve()

    queries = read_single_column_csv(queries_path)
    if args.limit and args.limit > 0:
        queries = queries[: args.limit]

    all_rows: List[Dict[str, str]] = []

    for site_name in args.site:
        cfg = DriverConfig(
            headless=not args.headful,
            profile_dir=profile_root / site_name,
        )
        driver = build_chrome_driver(cfg)
        try:
            site = build_site(site_name, driver)
            site.open()

            for q in queries:
                row: Dict[str, str] = {
                    "site": site_name,
                    "generated_query": q,
                    "response": "",
                    "status": "ok",
                    "error": "",
                    "timestamp_utc": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                }
                try:
                    result = site.submit_and_get_response(q)
                    row["response"] = result.response_text
                except Exception as e:
                    row["status"] = "error"
                    row["error"] = repr(e)
                all_rows.append(row)
        finally:
            driver.quit()

    # Requirement: store generated_query,response pair.
    # We include extra fields for scalability/debugging; you can ignore them.
    fieldnames = ["site", "generated_query", "response", "status", "error", "timestamp_utc"]
    write_responses_csv(out_path, all_rows, fieldnames=fieldnames)
    print(f"Wrote {len(all_rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

