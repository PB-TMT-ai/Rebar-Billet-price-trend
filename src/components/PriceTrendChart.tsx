import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import type { PriceRecord } from '../types/prices'

interface PriceTrendChartProps {
  data: PriceRecord[]
}

const CITY_COLORS: Record<string, string> = {
  Raipur: '#4f46e5',
  'Delhi/NCR': '#059669',
  Durgapur: '#dc2626',
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
}

function formatPrice(value: number): string {
  return value.toLocaleString('en-IN')
}

export function PriceTrendChart({ data }: PriceTrendChartProps): React.ReactElement {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500 text-sm">
        No data available for the selected range.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 8, right: 24, left: 16, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 12, fill: '#64748b' }}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={formatPrice}
          tick={{ fontSize: 12, fill: '#64748b' }}
          domain={['auto', 'auto']}
          width={70}
        />
        <Tooltip
          labelFormatter={(label) => {
            const d = new Date(String(label))
            return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
          }}
          formatter={(value, name) => [`INR ${formatPrice(Number(value))}`, String(name)]}
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            fontSize: '13px',
          }}
        />
        <Legend wrapperStyle={{ fontSize: '13px' }} />
        <Line
          type="monotone"
          dataKey="Raipur"
          stroke={CITY_COLORS.Raipur}
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="Delhi/NCR"
          stroke={CITY_COLORS['Delhi/NCR']}
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="Durgapur"
          stroke={CITY_COLORS.Durgapur}
          strokeWidth={2}
          dot={false}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
