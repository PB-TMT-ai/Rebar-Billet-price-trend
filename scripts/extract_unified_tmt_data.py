"""
Extract Master -2026 sheet data from 'Unified TMT price flash (1).xlsx' into JSON
for the dashboard's Unified TMT Price Flash tab.

Sheet structure:
  Row 1: section headers (Distributor landed | Customer landed (direct) | Distr to dealer)
  Row 2: column headers (Sr No, Date, Zone, State, Major city, then brand columns)
  Row 3+: data rows — one row per (date, city)

Output: src/data/unified-tmt-prices.json
  {
    "columnGroups": [{name, span: [startIdx, endIdx]}, ...],
    "columns": ["Sr No", "Date", ...],
    "rows": [{"date": "YYYY-MM-DD", "city": "...", "values": [...]}, ...]
  }
"""

import json
import os
import sys
from datetime import datetime
from typing import Any

import openpyxl

DEFAULT_XLSX = "daily rebar prices/margin dashboard/Unified TMT price flash (1).xlsx"
SHEET_NAME = "Master -2026"
OUTPUT_PATH = "src/data/unified-tmt-prices.json"

DATE_COL = 1
CITY_COL = 4
MAX_COL = 26  # cols 0..25 inclusive


def cell_to_json(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float):
        if v != v:  # NaN
            return None
        if v == int(v):
            return int(v)
        return v
    if isinstance(v, str):
        s = v.strip()
        if s in ("", "-", "NA", "N/A", "#DIV/0!", "#REF!"):
            return None
        return s
    return v


def find_sheet_name(wb) -> str | None:
    if SHEET_NAME in wb.sheetnames:
        return SHEET_NAME
    for s in wb.sheetnames:
        norm = s.lower().replace(" ", "").replace("-", "")
        if "master" in norm and "2026" in norm:
            return s
    return None


def main() -> None:
    xlsx_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLSX

    if not os.path.exists(xlsx_path):
        print(f"[ERROR] xlsx not found: {xlsx_path}")
        return

    print(f"[INFO] Reading {xlsx_path}...")
    # First pass: load with merged-cell info to derive section groups
    wb_meta = openpyxl.load_workbook(xlsx_path, data_only=True)
    sheet_name = find_sheet_name(wb_meta)
    if not sheet_name:
        print(f"[ERROR] Could not find 'Master -2026' sheet. Available: {wb_meta.sheetnames}")
        return

    ws_meta = wb_meta[sheet_name]
    column_groups: list[dict[str, Any]] = []
    for mr in sorted(ws_meta.merged_cells.ranges, key=lambda r: r.min_col):
        if mr.min_row == 1 and mr.max_row == 1:
            label = ws_meta.cell(row=1, column=mr.min_col).value
            if isinstance(label, str) and label.strip():
                column_groups.append({
                    "name": label.strip(),
                    "start": mr.min_col - 1,
                    "end": mr.max_col - 1,
                })
    wb_meta.close()

    # Second pass: fast streaming read for the data
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    ws = wb[sheet_name]

    header_row: list[Any] | None = None
    rows: list[dict[str, Any]] = []

    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        row = list(row)[:MAX_COL]
        if i == 1:
            continue
        if i == 2:
            header_row = row
            continue
        if not row or row[DATE_COL] is None:
            continue

        date_val = row[DATE_COL]
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%Y-%m-%d")
        elif isinstance(date_val, str):
            s = date_val.strip()
            if not s or s.lower() in ("date", "-"):
                continue
            try:
                date_str = datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    date_str = datetime.strptime(s, "%d-%m-%Y").strftime("%Y-%m-%d")
                except ValueError:
                    continue
        else:
            continue

        city = row[CITY_COL]
        if not city:
            continue

        values = [cell_to_json(v) for v in row]
        # replace the date cell with the canonical string
        values[DATE_COL] = date_str

        rows.append({
            "date": date_str,
            "city": str(city).strip(),
            "values": values,
        })

    wb.close()

    if header_row is None:
        print("[ERROR] No header row found")
        return

    columns = [(str(h).strip() if h is not None else "") for h in header_row[:MAX_COL]]

    output = {
        "columns": columns,
        "columnGroups": column_groups,
        "rows": rows,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    dates = sorted({r["date"] for r in rows})
    cities = sorted({r["city"] for r in rows})
    print(f"[INFO] Exported {len(rows)} rows to {OUTPUT_PATH}")
    print(f"[INFO] {len(dates)} dates ({dates[0]} to {dates[-1]}), {len(cities)} cities")


if __name__ == "__main__":
    main()
