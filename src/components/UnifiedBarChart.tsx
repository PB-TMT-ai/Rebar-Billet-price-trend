import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import { UNIFIED_CITIES } from '../types/unified'
import type { UnifiedRecord } from '../types/unified'

interface UnifiedBarChartProps {
  record: UnifiedRecord | null
  date: string
}

function formatPrice(value: number): string {
  return value.toLocaleString('en-IN')
}

export function UnifiedBarChart({ record, date }: UnifiedBarChartProps): React.ReactElement {
  if (!record) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        No data available for {date || 'selected date'}.
      </div>
    )
  }

  const chartData = UNIFIED_CITIES.map((city) => ({
    city,
    price: record[city] ?? null,
  })).filter((d) => d.price !== null)

  return (
    <ResponsiveContainer width="100%" height={520}>
      <BarChart
        data={chartData}
        margin={{ top: 8, right: 24, left: 16, bottom: 120 }}
      >
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
          formatter={(value) => [`INR ${formatPrice(Number(value))}`, 'Price']}
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            fontSize: '13px',
          }}
        />
        <Bar dataKey="price" fill="#4f46e5" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
