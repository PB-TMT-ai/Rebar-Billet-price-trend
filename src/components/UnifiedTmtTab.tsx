import { useState, useMemo } from 'react'
import { UnifiedTable } from './UnifiedTable'
import { UnifiedBarChart } from './UnifiedBarChart'
import { useUnifiedDataset, useUnifiedDates, useUnifiedRowsForDate } from '../hooks/useUnifiedData'

type View = 'table' | 'chart'

function todayISO(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function UnifiedTmtTab(): React.ReactElement {
  const { columns, columnGroups } = useUnifiedDataset()
  const { minDate, maxDate, availableDates } = useUnifiedDates()

  const defaultDate = useMemo(() => {
    const today = todayISO()
    if (availableDates.includes(today)) return today
    return maxDate || today
  }, [availableDates, maxDate])

  const [selectedDate, setSelectedDate] = useState<string>(defaultDate)
  const [view, setView] = useState<View>('table')

  // Pick a sensible default numeric column for the chart (first column after metadata)
  const defaultChartColumn = useMemo(() => {
    for (let i = 5; i < columns.length; i++) {
      if (columns[i]) return i
    }
    return 5
  }, [columns])
  const [chartColumn, setChartColumn] = useState<number>(defaultChartColumn)

  const rows = useUnifiedRowsForDate(selectedDate)

  // Build a label for each column: "Group: ColumnName"
  const columnOptions = useMemo(() => {
    return columns.map((col, idx) => {
      const group = columnGroups.find((g) => idx >= g.start && idx <= g.end)
      const prefix = group ? `${group.name} · ` : ''
      return { idx, label: `${prefix}${col || `Col ${idx}`}` }
    })
  }, [columns, columnGroups])

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-medium text-slate-900">
          Unified TMT Price Flash — {selectedDate || '—'}
        </h2>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <span>Date:</span>
            <input
              type="date"
              value={selectedDate}
              min={minDate || undefined}
              max={maxDate || undefined}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="rounded border border-slate-300 px-2 py-1 text-sm"
            />
          </label>
          <div className="inline-flex overflow-hidden rounded border border-slate-300 text-sm">
            <button
              onClick={() => setView('table')}
              className={`px-3 py-1 ${
                view === 'table'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-slate-700 hover:bg-slate-50'
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setView('chart')}
              className={`px-3 py-1 ${
                view === 'chart'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-slate-700 hover:bg-slate-50'
              }`}
            >
              Chart
            </button>
          </div>
        </div>
      </div>

      {view === 'chart' && (
        <div className="mb-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <span>Chart column:</span>
            <select
              value={chartColumn}
              onChange={(e) => setChartColumn(Number(e.target.value))}
              className="rounded border border-slate-300 px-2 py-1 text-sm"
            >
              {columnOptions
                .filter((o) => o.idx >= 5)
                .map((o) => (
                  <option key={o.idx} value={o.idx}>
                    {o.label}
                  </option>
                ))}
            </select>
          </label>
        </div>
      )}

      {view === 'table' ? (
        <UnifiedTable
          columns={columns}
          columnGroups={columnGroups}
          rows={rows}
          date={selectedDate}
        />
      ) : (
        <UnifiedBarChart
          rows={rows}
          columns={columns}
          selectedColumnIndex={chartColumn}
          date={selectedDate}
        />
      )}

      {availableDates.length > 0 && (
        <p className="mt-4 text-xs text-slate-400">
          Data available from {minDate} to {maxDate} ({availableDates.length} dates · {rows.length}{' '}
          rows for selected date)
        </p>
      )}
    </div>
  )
}
