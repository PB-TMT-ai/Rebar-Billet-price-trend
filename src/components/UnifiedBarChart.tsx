import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import type { UnifiedRow } from '../types/unified'

interface UnifiedBarChartProps {
  rows: UnifiedRow[]
  columns: string[]
  selectedColumnIndex: number
  date: string
}

function formatPrice(value: number): string {
  return value.toLocaleString('en-IN')
}

export function UnifiedBarChart({
  rows,
  columns,
  selectedColumnIndex,
  date,
}: UnifiedBarChartProps): React.ReactElement {
  if (rows.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        No data available for {date || 'selected date'}.
      </div>
    )
  }

  const chartData = rows
    .map((r) => ({
      city: r.city,
      value: typeof r.values[selectedColumnIndex] === 'number' ? (r.values[selectedColumnIndex] as number) : null,
    }))
    .filter((d) => d.value !== null)

  const label = columns[selectedColumnIndex] || 'Value'

  if (chartData.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        Selected column "{label}" has no numeric values for {date}.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={560}>
      <BarChart data={chartData} margin={{ top: 8, right: 24, left: 16, bottom: 140 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="city"
          tick={{ fontSize: 11, fill: '#64748b' }}
          angle={-45}
          textAnchor="end"
          interval={0}
        />
        <YAxis
          tickFormatter={formatPrice}
          tick={{ fontSize: 12, fill: '#64748b' }}
          domain={['auto', 'auto']}
          width={80}
        />
        <Tooltip
          formatter={(value) => [`INR ${formatPrice(Number(value))}`, label]}
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            fontSize: '13px',
          }}
        />
        <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} name={label} />
      </BarChart>
    </ResponsiveContainer>
  )
}
