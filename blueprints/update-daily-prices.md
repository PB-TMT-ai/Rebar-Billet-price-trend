# Blueprint: Update Daily Prices from ZIP

## Goal
Append new daily rebar, billet, and ingot prices from a ZIP archive into the main Excel file without modifying or deleting existing data.

## Inputs Required
- zip_file: .zip file containing .xls files (rebar_dom.xls, billet_D_dom.xls, ingot_D_dom.xls)
- The main Excel file must already exist at: `daily rebar prices/Rebar & Billet price trend (2).xlsx`

## Scripts to Use
1. `scripts/update_prices.py` - Extracts ZIP, reads .xls files, appends new rows to Excel

## Data Flow
```
ZIP file
├── rebar_dom.xls
│   ├── 12MM sheet    → Excel "12MM" sheet (daily rebar prices by city)
│   └── PRIMARY sheet → Excel "PRIMARY" sheet (weekly rebar prices)
├── billet_D_dom.xls
│   └── BILLET sheet  → Excel "D-Billet" sheet (daily billet prices by city)
└── ingot_D_dom.xls
    └── INGOT sheet   → (skipped if no matching target sheet)
```

## Steps
1. Place ZIP file in `daily rebar prices/` folder
2. Run: `python scripts/update_prices.py "daily rebar prices/<zip_filename>.zip"`
3. Script extracts, compares dates, appends only new rows
4. Verify output in logs

## Rules
- Old data is NEVER deleted or edited
- No new Excel file is created
- Only dates not already in the target sheet are appended
- Holidays ('H') and '-' values are preserved as-is
- Date strings from source are converted to datetime objects

## Edge Cases
- **Duplicate dates**: Skipped — only new dates are appended
- **Missing source file in ZIP**: Warning logged, other files still processed
- **Missing target sheet**: Warning logged, skipped
- **Holidays**: Rows with 'H' values are appended (they have valid dates)
- **Corrupted .xls**: Uses `ignore_workbook_corruption=True` for xlrd

## Known Issues
- The .xls files from the ZIP use OLE2 format and may trigger corruption warnings — this is handled
- ingot_D_dom.xls has no dedicated target sheet currently — skipped by default
