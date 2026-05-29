import type { UnifiedColumnGroup, UnifiedRow } from '../types/unified'

interface UnifiedTableProps {
  columns: string[]
  columnGroups: UnifiedColumnGroup[]
  rows: UnifiedRow[]
  date: string
}

function formatCell(value: string | number | null): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') return value.toLocaleString('en-IN')
  return value
}

function buildGroupHeader(
  columnCount: number,
  groups: UnifiedColumnGroup[],
): Array<{ name: string; span: number }> {
  const cells: Array<{ name: string; span: number }> = []
  let idx = 0
  const sorted = [...groups].sort((a, b) => a.start - b.start)
  for (const g of sorted) {
    if (idx < g.start) {
      cells.push({ name: '', span: g.start - idx })
      idx = g.start
    }
    cells.push({ name: g.name, span: g.end - g.start + 1 })
    idx = g.end + 1
  }
  if (idx < columnCount) {
    cells.push({ name: '', span: columnCount - idx })
  }
  return cells
}

export function UnifiedTable({ columns, columnGroups, rows, date }: UnifiedTableProps): React.ReactElement {
  if (rows.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-500">
        No data available for {date || 'selected date'}.
      </div>
    )
  }

  const groupHeader = buildGroupHeader(columns.length, columnGroups)

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-xs">
        <thead>
          <tr className="bg-slate-100">
            {groupHeader.map((g, i) => (
              <th
                key={i}
                colSpan={g.span}
                className={`border border-slate-200 px-2 py-1.5 text-center font-semibold text-slate-700 ${
                  g.name ? 'bg-indigo-50' : ''
                }`}
              >
                {g.name}
              </th>
            ))}
          </tr>
          <tr className="bg-slate-50">
            {columns.map((c, i) => (
              <th
                key={i}
                className="border border-slate-200 px-2 py-1.5 text-left font-medium text-slate-700"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="hover:bg-slate-50">
              {row.values.map((v, ci) => (
                <td
                  key={ci}
                  className={`border border-slate-200 px-2 py-1 ${
                    typeof v === 'number'
                      ? 'text-right font-mono tabular-nums text-slate-900'
                      : 'text-slate-700'
                  }`}
                >
                  {formatCell(v)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
