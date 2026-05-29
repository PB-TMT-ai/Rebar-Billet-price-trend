import { UNIFIED_CITIES } from '../types/unified'
import type { UnifiedRecord } from '../types/unified'

interface UnifiedTableProps {
  record: UnifiedRecord | null
  date: string
}

function formatPrice(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return value.toLocaleString('en-IN')
}

export function UnifiedTable({ record, date }: UnifiedTableProps): React.ReactElement {
  if (!record) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-slate-500">
        No data available for {date || 'selected date'}.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-2.5 text-left font-medium text-slate-700">City</th>
            <th className="px-4 py-2.5 text-right font-medium text-slate-700">Price (INR)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {UNIFIED_CITIES.map((city) => {
            const price = record[city]
            return (
              <tr key={city} className="hover:bg-slate-50">
                <td className="px-4 py-2 text-slate-700">{city}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-slate-900">
                  {formatPrice(price)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
