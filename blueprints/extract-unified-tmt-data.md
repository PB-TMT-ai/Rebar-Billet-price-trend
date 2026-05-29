# Blueprint: Extract Unified TMT Price Flash data

## Goal
Read the `master 2026` sheet from `Unified TMT price flash.xlsx` and produce
`src/data/unified-tmt-prices.json` for the dashboard's "Unified TMT Price Flash" tab.

## Inputs
- `daily rebar prices/Unified TMT price flash.xlsx` (upload here first)
- Sheet name: `master 2026`
- Date column: column A (auto-detected by header)
- 32 city columns (auto-matched by name)

## Scripts to use
1. `scripts/extract_unified_tmt_data.py`

## Run
```
python scripts/extract_unified_tmt_data.py
# or pass a custom path:
python scripts/extract_unified_tmt_data.py path/to/file.xlsx
```

## Output
- `src/data/unified-tmt-prices.json` — array of `{ date, <city>: price | null, ... }`

## How the dashboard consumes it
- `src/hooks/useUnifiedData.ts` loads the JSON at build time (Vite static import)
- `src/components/UnifiedTmtTab.tsx` renders the tab with:
  - Date picker (defaults to today if present, otherwise latest)
  - Table view (city → price)
  - Chart view (bar chart of prices across cities)

## Updating data
1. Replace/update `daily rebar prices/Unified TMT price flash.xlsx`
2. Run the script
3. Commit `src/data/unified-tmt-prices.json` and push
