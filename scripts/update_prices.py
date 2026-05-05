"""
Update daily prices in the main Excel file from a ZIP archive.

Usage:
    python scripts/update_prices.py <path_to_zip>

Rules:
    - Old data is NEVER deleted or edited
    - Only new dates/weeks are appended
    - No new Excel file is created — updates the existing one in place
"""

import sys
import os
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Any

import xlrd
import openpyxl


# --- Configuration ---

EXCEL_DIR = "daily rebar prices"
EXCEL_FILENAME = "Rebar & Billet price trend (2).xlsx"

# Mapping: (source_xls_filename_substring, source_sheet) -> (target_sheet, date_col_index_in_target)
SHEET_MAPPINGS = [
    {
        "source_file": "rebar_dom",
        "source_sheet": "12MM",
        "target_sheet": "12MM",
        "header_rows": 2,       # rows 0-1 are headers in source
        "date_col": 0,          # date column index in source
        "date_type": "daily",
    },
    {
        "source_file": "billet_D_dom",
        "source_sheet": "BILLET",
        "target_sheet": "D-Billet",
        "header_rows": 2,
        "date_col": 0,
        "date_type": "daily",
    },
    # ingot_D_dom skipped — different column structure, no matching target sheet
    {
        "source_file": "rebar_dom",
        "source_sheet": "PRIMARY",
        "target_sheet": "PRIMARY",
        "header_rows": 2,
        "date_col": 2,          # monday column is the date key
        "date_type": "weekly",
    },
]


def log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def log_error(msg: str) -> None:
    print(f"[ERROR] {msg}")


def parse_date(value: Any) -> datetime | None:
    """Parse a date from various formats."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(value))
        except (ValueError, OverflowError):
            return None
    if isinstance(value, str):
        value = value.strip()
        if not value or value in ('-', 'H', ''):
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def is_data_row(row: list[Any], date_col: int) -> bool:
    """Check if a row contains actual data (not header, disclaimer, or empty)."""
    if not row:
        return False
    date_val = row[date_col]
    if date_val is None or date_val == '':
        return False
    if isinstance(date_val, str):
        stripped = date_val.strip()
        if stripped == '' or stripped.startswith('DISCLAIMER') or stripped.startswith('NOTE'):
            return False
        if stripped in ('Date', 'year', 'date'):
            return False
    return parse_date(date_val) is not None


def get_existing_dates(ws: openpyxl.worksheet.worksheet.Worksheet, date_col: int) -> set[str]:
    """Get all existing dates from a target sheet column (as YYYY-MM-DD strings)."""
    dates: set[str] = set()
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=date_col + 1, max_col=date_col + 1, values_only=True):
        cell_val = row[0]
        dt = parse_date(cell_val)
        if dt:
            dates.add(dt.strftime("%Y-%m-%d"))
    return dates


def convert_cell_value(value: Any) -> Any:
    """Convert source cell values for writing to target."""
    if isinstance(value, float) and value == int(value):
        return int(value)
    return value


def extract_zip(zip_path: str, extract_to: str) -> str:
    """Extract ZIP and return the path to the extracted folder."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)

    # Find the extracted subfolder containing .xls files
    for item in os.listdir(extract_to):
        item_path = os.path.join(extract_to, item)
        if os.path.isdir(item_path):
            xls_files = [f for f in os.listdir(item_path) if f.endswith('.xls')]
            if xls_files:
                return item_path

    # If no subfolder, check root of extract
    xls_files = [f for f in os.listdir(extract_to) if f.endswith('.xls')]
    if xls_files:
        return extract_to

    raise FileNotFoundError("No .xls files found in ZIP archive")


def find_source_file(extract_dir: str, name_substring: str) -> str | None:
    """Find a .xls file in the extracted directory matching the substring."""
    for f in os.listdir(extract_dir):
        if f.endswith('.xls') and name_substring in f:
            return os.path.join(extract_dir, f)
    return None


def read_source_sheet(file_path: str, sheet_name: str, header_rows: int, date_col: int) -> tuple[list[list[Any]], list[int] | None]:
    """Read data rows from a source .xls sheet.

    Returns (rows, col_remap) where col_remap maps source col → target col
    based on header names, or None if headers match the expected layout.
    """
    wb = xlrd.open_workbook(file_path, ignore_workbook_corruption=True)

    if sheet_name not in wb.sheet_names():
        log_warn(f"Sheet '{sheet_name}' not found in {os.path.basename(file_path)}. Available: {wb.sheet_names()}")
        return [], None

    sheet = wb.sheet_by_name(sheet_name)

    # Build column remapping by matching header city names
    # Read the city header row (row index 1 for most sheets)
    col_remap: list[int] | None = None
    if header_rows >= 2:
        city_row_idx = header_rows - 1  # last header row has city names
        src_headers = [sheet.cell_value(city_row_idx, c) for c in range(sheet.ncols)]

        # Detect if there's a column shift by finding where 'Date' or first city appears
        # Build a map: for each source column, find where that city header is in the
        # "standard" layout (where Date is at col 0)
        # Standard: the target Excel has fixed column positions.
        # We remap source to match the target by aligning city names.

        # Find where the date column is in the source
        src_date_col = 0
        for i, h in enumerate(src_headers):
            if isinstance(h, str) and h.strip().lower() in ('date', ''):
                continue
            # First non-empty, non-date header indicates data starts
            break

        # Check if source has the expected number of columns
        # If source has more columns than expected, there's a shift
        # Build a name->source_col map from source headers
        src_name_to_col: dict[str, int] = {}
        for i, h in enumerate(src_headers):
            if isinstance(h, str) and h.strip():
                name = h.strip()
                if name not in src_name_to_col:
                    src_name_to_col[name] = i

        # Check the standard (expected) header positions by looking at earlier data
        # Standard billet: Hindpur=10, Ramgarh=11, Ahmedabad=12, ..., Durgapur=16, ..., Raipur=25
        # If source has Durgapur at col 17 instead of 16, we need to remap

        # Build expected name->target_col from the FIRST occurrence of each city
        # We do this by reading row 0 (category) and row 1 (cities) of the source
        # but mapping to the STANDARD positions

        # Standard positions for D-Billet target sheet:
        STANDARD_BILLET_CITIES = {
            "Hindpur": 10, "Ramgarh": 11, "Ahmedabad": 12, "Bellary": 13,
            "Bhavnagar": 14, "Chennai": 15, "Durgapur": 16, "Goa": 17,
            "Hyderabad": 18, "Jalna": 19, "Jharsugda": 20, "Kolkata": 21,
            "Mandi Gobindgarh": 22, "Mumbai": 23, "Raigarh": 24, "Raipur": 25,
            "Rourkela": 26,
        }

        # Check if any city is at a different column than standard
        shifted = False
        for city, expected_col in STANDARD_BILLET_CITIES.items():
            src_col = src_name_to_col.get(city)
            if src_col is not None and src_col != expected_col:
                shifted = True
                break

        if shifted:
            # Detect the column offset using a unique city name (Hindpur is always unique)
            hindpur_src = src_name_to_col.get("Hindpur")
            hindpur_tgt = STANDARD_BILLET_CITIES.get("Hindpur", 10)
            offset = (hindpur_src - hindpur_tgt) if hindpur_src is not None else 1

            log_info(f"  Column shift detected (offset={offset})! Building remap...")

            max_target_col = max(STANDARD_BILLET_CITIES.values()) + 1  # 27
            remap = list(range(max_target_col + offset + 1))

            # Date col stays at 0
            remap[0] = 0

            # Early columns (BSE futures etc.) before the city block: shift back by offset
            # Skip mapping to col 0 (reserved for date)
            for i in range(1, hindpur_tgt + offset):
                target = i - offset
                if target > 0:  # never overwrite date col
                    remap[i] = target

            # City block: shift each source col back by offset
            for tgt_col in range(hindpur_tgt, max_target_col):
                src_col = tgt_col + offset
                if src_col < len(remap):
                    remap[src_col] = tgt_col

            col_remap = remap
            log_info(f"  Remap: src col {hindpur_tgt + offset}→{hindpur_tgt}(Hindpur), src col {16 + offset}→16(Durgapur), src col {25 + offset}→25(Raipur)")

    rows: list[list[Any]] = []
    for row_idx in range(header_rows, sheet.nrows):
        row = [sheet.cell_value(row_idx, col) for col in range(sheet.ncols)]
        if is_data_row(row, date_col):
            if col_remap:
                # Remap columns to standard positions
                max_col = max(col_remap) + 1
                remapped = [''] * max(max_col, len(row))
                for src_i, tgt_i in enumerate(col_remap):
                    if src_i < len(row):
                        remapped[tgt_i] = row[src_i]
                rows.append(remapped)
            else:
                rows.append(row)

    return rows, col_remap


def append_new_rows(
    ws: openpyxl.worksheet.worksheet.Worksheet,
    source_rows: list[list[Any]],
    existing_dates: set[str],
    date_col: int,
    date_type: str,
) -> int:
    """Append rows with new dates to the target sheet. Returns count of rows added."""
    added = 0

    for row in source_rows:
        date_val = row[date_col]
        dt = parse_date(date_val)

        if dt is None:
            continue

        date_key = dt.strftime("%Y-%m-%d")

        if date_key in existing_dates:
            continue

        # Build the row to append
        out_row: list[Any] = []
        for i, val in enumerate(row):
            if i == date_col or (date_type == "weekly" and i in (date_col, date_col + 1)):
                # Convert date strings to datetime objects
                parsed = parse_date(val)
                if parsed:
                    out_row.append(parsed)
                else:
                    out_row.append(convert_cell_value(val))
            else:
                out_row.append(convert_cell_value(val))

        ws.append(out_row)
        existing_dates.add(date_key)
        added += 1

    return added


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_zip>")
        sys.exit(1)

    zip_path = sys.argv[1]

    if not os.path.exists(zip_path):
        log_error(f"ZIP file not found: {zip_path}")
        sys.exit(1)

    excel_path = os.path.join(EXCEL_DIR, EXCEL_FILENAME)

    if not os.path.exists(excel_path):
        log_error(f"Main Excel file not found: {excel_path}")
        log_error("The Excel file must already exist. No new file will be created.")
        sys.exit(1)

    # Extract ZIP
    temp_dir = tempfile.mkdtemp(prefix="price_update_")
    try:
        log_info(f"Extracting ZIP: {zip_path}")
        extract_dir = extract_zip(zip_path, temp_dir)
        xls_files = [f for f in os.listdir(extract_dir) if f.endswith('.xls')]
        log_info(f"Found {len(xls_files)} .xls files: {xls_files}")

        # Open main Excel (preserve formulas and formatting)
        log_info(f"Opening Excel: {excel_path}")
        wb = openpyxl.load_workbook(excel_path)

        total_added = 0

        for mapping in SHEET_MAPPINGS:
            source_file = find_source_file(extract_dir, mapping["source_file"])
            if not source_file:
                if mapping.get("skip_if_no_sheet"):
                    log_info(f"Source file for '{mapping['source_file']}' not found, skipping.")
                else:
                    log_warn(f"Source file for '{mapping['source_file']}' not found in ZIP!")
                continue

            target_sheet_name = mapping["target_sheet"]
            if target_sheet_name not in wb.sheetnames:
                if mapping.get("skip_if_no_sheet"):
                    log_info(f"Target sheet '{target_sheet_name}' not found, skipping.")
                    continue
                log_warn(f"Target sheet '{target_sheet_name}' not found in Excel!")
                continue

            log_info(f"Processing: {os.path.basename(source_file)} [{mapping['source_sheet']}] → [{target_sheet_name}]")

            # Read source data (with auto column remap if source has shifted columns)
            source_rows, col_remap = read_source_sheet(
                source_file,
                mapping["source_sheet"],
                mapping["header_rows"],
                mapping["date_col"],
            )
            if col_remap:
                log_info(f"  Column shift detected and remapped")
            log_info(f"  Source rows with data: {len(source_rows)}")

            if not source_rows:
                continue

            # Get existing dates from target
            ws = wb[target_sheet_name]
            target_date_col = mapping["date_col"]

            # For D-Billet, date is always in column A (index 0) in the target
            if target_sheet_name == "D-Billet":
                target_date_col = 0

            existing_dates = get_existing_dates(ws, target_date_col)
            log_info(f"  Existing dates in target: {len(existing_dates)}")

            # Append new rows
            added = append_new_rows(ws, source_rows, existing_dates, mapping["date_col"], mapping["date_type"])
            total_added += added

            if added > 0:
                log_info(f"  ✓ Added {added} new rows to [{target_sheet_name}]")
            else:
                log_info(f"  No new dates to add to [{target_sheet_name}]")

        if total_added > 0:
            log_info(f"Saving Excel file... ({total_added} total new rows)")
            wb.save(excel_path)
            log_info("Done! Excel file updated successfully.")
        else:
            log_info("No new data to add. Excel file unchanged.")

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
