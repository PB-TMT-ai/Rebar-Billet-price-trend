"""
Extract master 2026 sheet data from Unified TMT price flash xlsx into JSON
for the dashboard's Unified TMT Price Flash tab.

Usage:
    python scripts/extract_unified_tmt_data.py [path_to_xlsx]

Default input path:
    daily rebar prices/Unified TMT price flash.xlsx

Output:
    src/data/unified-tmt-prices.json
"""

import json
import os
import sys
from datetime import datetime

import openpyxl

DEFAULT_XLSX = "daily rebar prices/Unified TMT price flash.xlsx"
SHEET_NAME = "master 2026"
OUTPUT_PATH = "src/data/unified-tmt-prices.json"

CITIES = [
    "DL/NCR",
    "Bawal/Rewari/Faridabad",
    "Agra/Ghaziabad",
    "Gorakhpur",
    "Jaipur",
    "Srinagar",
    "Jammu",
    "Chandigarh",
    "Shimla",
    "Dehradun",
    "Ludhiana",
    "Ranchi",
    "Patna",
    "Siliguri, Jalpaiguri, Cooch behar",
    "Kolkata",
    "Bhubaneshwar",
    "Rourkela",
    "Mumbai",
    "Pune",
    "Nashik",
    "Nagpur",
    "Ahmedabad",
    "Raipur",
    "Indore",
    "North Karnataka-Hubli",
    "South karnataka- Bangalore",
    "Chennai",
    "Coimbatore",
    "Cochin",
    "Hyderabad",
    "Non Hyderabad",
    "AP- Vizag",
]


def parse_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if s in ("", "-", "H", "#DIV/0!", "#REF!", "N/A", "NA"):
            return None
        try:
            return float(s.replace(",", ""))
        except ValueError:
            return None
    return None


def find_header_row(ws, max_scan=30):
    """Find row containing 'DL/NCR' (case-insensitive) — the city header row."""
    for row in ws.iter_rows(min_row=1, max_row=max_scan, values_only=True):
        for cell in row:
            if isinstance(cell, str) and "dl/ncr" in cell.strip().lower():
                return row
    return None


def build_city_columns(header_row):
    """Map our canonical city names to column indices using fuzzy match."""
    by_norm = {}
    for i, cell in enumerate(header_row):
        if isinstance(cell, str) and cell.strip():
            key = cell.strip().lower().replace(" ", "").replace(",", "")
            by_norm.setdefault(key, i)

    city_cols = {}
    for city in CITIES:
        key = city.strip().lower().replace(" ", "").replace(",", "")
        if key in by_norm:
            city_cols[city] = by_norm[key]
    return city_cols


def find_date_column(header_row):
    for i, cell in enumerate(header_row):
        if isinstance(cell, str) and cell.strip().lower() in ("date", "dt"):
            return i
    return 0  # default to column A


def main():
    xlsx_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLSX

    if not os.path.exists(xlsx_path):
        print(f"[ERROR] xlsx not found: {xlsx_path}")
        print("[INFO] Upload 'Unified TMT price flash.xlsx' to the path above, then re-run.")
        return

    print(f"[INFO] Reading {xlsx_path}...")
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)

    if SHEET_NAME not in wb.sheetnames:
        # Try fuzzy match
        match = None
        for s in wb.sheetnames:
            if "master" in s.lower() and "2026" in s:
                match = s
                break
        if match:
            print(f"[WARN] Sheet '{SHEET_NAME}' not found; using '{match}' instead.")
            sheet_name = match
        else:
            print(f"[ERROR] Sheet '{SHEET_NAME}' not found. Available: {wb.sheetnames}")
            return
    else:
        sheet_name = SHEET_NAME

    ws = wb[sheet_name]

    # Locate header row
    header_row = find_header_row(ws)
    if header_row is None:
        print("[ERROR] Could not find header row (no cell matching 'DL/NCR').")
        return

    date_col = find_date_column(header_row)
    city_cols = build_city_columns(header_row)
    print(f"[INFO] Date column: {date_col}, matched {len(city_cols)}/{len(CITIES)} cities")

    missing = [c for c in CITIES if c not in city_cols]
    if missing:
        print(f"[WARN] Missing cities: {missing}")

    # Find the row index of header so data starts after
    header_row_idx = None
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if row == header_row:
            header_row_idx = i
            break

    records = []
    for row in ws.iter_rows(min_row=(header_row_idx or 1) + 1, values_only=True):
        if not row:
            continue
        date_val = row[date_col] if date_col < len(row) else None
        if date_val is None:
            continue
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%Y-%m-%d")
        elif isinstance(date_val, str):
            s = date_val.strip()
            if not s or s.lower() in ("date", "-", "h"):
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

        record = {"date": date_str}
        any_price = False
        for city in CITIES:
            col = city_cols.get(city)
            price = parse_price(row[col]) if (col is not None and col < len(row)) else None
            record[city] = price
            if price is not None:
                any_price = True

        if any_price:
            records.append(record)

    wb.close()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(records, f, indent=2)

    print(f"[INFO] Exported {len(records)} records to {OUTPUT_PATH}")
    if records:
        print(f"[INFO] Date range: {records[0]['date']} to {records[-1]['date']}")


if __name__ == "__main__":
    main()
