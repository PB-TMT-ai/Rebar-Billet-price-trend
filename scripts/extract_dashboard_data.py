"""
Extract 12MM sheet data for Raipur, Delhi/NCR, and Durgapur into JSON for the dashboard.

Usage:
    python scripts/extract_dashboard_data.py

Output:
    src/data/prices.json
"""

import json
import os
from datetime import datetime

import openpyxl

EXCEL_DIR = "daily rebar prices"
EXCEL_FILENAME = "Rebar & Billet price trend (2).xlsx"
OUTPUT_PATH = "src/data/prices.json"

# Column indices in 12MM sheet (0-based)
COL_DATE = 0
CITY_COLUMNS = {
    "Raipur": 16,
    "Delhi/NCR": 3,
    "Durgapur": 4,
}

HEADER_ROW = 20  # Row 20 has city names (1-indexed)
DATA_START_ROW = 21  # Data starts at row 21 (1-indexed)


def parse_price(value) -> float | None:
    """Parse a price value, returning None for non-numeric."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in ('-', 'H', '', '#DIV/0!', '#REF!'):
            return None
        try:
            return float(stripped.replace(',', ''))
        except ValueError:
            return None
    return None


def main() -> None:
    excel_path = os.path.join(EXCEL_DIR, EXCEL_FILENAME)

    if not os.path.exists(excel_path):
        print(f"[ERROR] Excel file not found: {excel_path}")
        return

    print(f"[INFO] Reading {excel_path}...")
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    ws = wb["12MM"]

    records = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=DATA_START_ROW, values_only=True), DATA_START_ROW):
        date_val = row[COL_DATE]
        if date_val is None:
            continue
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%Y-%m-%d")
        elif isinstance(date_val, str):
            date_str = date_val.strip()
            if not date_str or date_str in ('H', '-'):
                continue
        else:
            continue

        record = {"date": date_str}
        has_any_price = False

        for city_name, col_idx in CITY_COLUMNS.items():
            price = parse_price(row[col_idx]) if col_idx < len(row) else None
            record[city_name] = price
            if price is not None:
                has_any_price = True

        if has_any_price:
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
