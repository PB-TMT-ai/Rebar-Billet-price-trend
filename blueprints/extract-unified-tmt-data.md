# Blueprint: Extract Unified TMT Price Flash data

## Goal
Read the `Master -2026` sheet from `Unified TMT price flash (1).xlsx` and produce
`src/data/unified-tmt-prices.json` for the dashboard's "Unified TMT Price Flash" tab.

## Inputs
- `daily rebar prices/margin dashboard/Unified TMT price flash (1).xlsx`
- Sheet name: `Master -2026` (auto-fuzzy-matched)
- Row 1: section headers (Distributor landed | Customer landed (direct) | Distr to dealer) — read from merged ranges
- Row 2: column headers (Sr No, Date, Zone, State, Major city, then brand columns)
- Row 3+: one row per (date, city), 32 cities × N dates

## Run
```
python scripts/extract_unified_tmt_data.py
# or pass a custom path:
python scripts/extract_unified_tmt_data.py path/to/file.xlsx
```

## Output schema (src/data/unified-tmt-prices.json)
```json
{
  "columns": ["Sr No", "Date", "Zone", "State", "Major city", "Neo", ...],
  "columnGroups": [
    { "name": "Distributor landed", "start": 5, "end": 9 },
    { "name": "Customer landed (direct)", "start": 10, "end": 11 },
    { "name": "Distr to dealer", "start": 12, "end": 18 }
  ],
  "rows": [
    { "date": "2026-01-01", "city": "DL/NCR", "values": [1, "2026-01-01", "North", "DL", "DL/NCR", 52400, ...] }
  ]
}
```

## How the dashboard consumes it
- `src/hooks/useUnifiedData.ts` loads the JSON via Vite static import
- `src/components/UnifiedTmtTab.tsx` renders the tab:
  - Date picker (defaults to today if present, else latest)
  - Table view: full row per city for selected date, with section column headers
  - Chart view: bar chart of a chosen numeric column across cities for selected date

## Updating data
1. Replace `daily rebar prices/margin dashboard/Unified TMT price flash (1).xlsx`
2. Run `python scripts/extract_unified_tmt_data.py`
3. Commit `src/data/unified-tmt-prices.json` and push
