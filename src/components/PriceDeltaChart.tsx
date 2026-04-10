import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts'
import type { DeltaRecord } from '../types/prices'

interface PriceDeltaChartProps {
  data: DeltaRecord[]
  startDate: string
  endDate: string
}

function formatPrice(value: number): string {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toLocaleString('en-IN')}`
}

export function PriceDeltaChart({ data, startDate, endDate }: PriceDeltaChartProps): React.ReactElement {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500 text-sm">
        No data available for the selected range.
      </div>
    )
  }

  const formatDateLabel = (d: string): string => {
    const dt = new Date(d)
    return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  return (
    <div>
      <p className="mb-4 text-sm text-slate-600">
        Price change from <span className="font-medium text-slate-900">{formatDateLabel(startDate)}</span> to{' '}
        <span className="font-medium text-slate-900">{formatDateLabel(endDate)}</span>
      </p>

      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data} margin={{ top: 8, right: 24, left: 16, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="city" tick={{ fontSize: 13, fill: '#334155', fontWeight: 500 }} />
          <YAxis tickFormatter={formatPrice} tick={{ fontSize: 12, fill: '#64748b' }} width={80} />
          <Tooltip
            formatter={(value, _name, props) => {
              const rec = props.payload as unknown as DeltaRecord
              const numVal = Number(value)
              return [
                `Delta: INR ${formatPrice(numVal)} (${rec.percentChange >= 0 ? '+' : ''}${rec.percentChange.toFixed(1)}%)`,
                'Price Change',
              ]
            }}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              fontSize: '13px',
            }}
          />
          <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1} />
          <Bar dataKey="delta" radius={[6, 6, 0, 0]} barSize={80}>
            {data.map((entry) => (
              <Cell key={entry.city} fill={entry.delta >= 0 ? '#059669' : '#dc2626'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Summary table */}
      <div className="mt-6 overflow-hidden rounded-lg border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-700">City</th>
              <th className="px-4 py-3 text-right font-medium text-slate-700">Start Price</th>
              <th className="px-4 py-3 text-right font-medium text-slate-700">End Price</th>
              <th className="px-4 py-3 text-right font-medium text-slate-700">Delta (INR)</th>
              <th className="px-4 py-3 text-right font-medium text-slate-700">Change %</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {data.map((rec) => (
              <tr key={rec.city}>
                <td className="px-4 py-3 font-medium text-slate-900">{rec.city}</td>
                <td className="px-4 py-3 text-right text-slate-700">
                  {rec.startPrice.toLocaleString('en-IN')}
                </td>
                <td className="px-4 py-3 text-right text-slate-700">
                  {rec.endPrice.toLocaleString('en-IN')}
                </td>
                <td
                  className={`px-4 py-3 text-right font-medium ${rec.delta >= 0 ? 'text-emerald-600' : 'text-red-600'}`}
                >
                  {formatPrice(rec.delta)}
                </td>
                <td
                  className={`px-4 py-3 text-right font-medium ${rec.percentChange >= 0 ? 'text-emerald-600' : 'text-red-600'}`}
                >
                  {rec.percentChange >= 0 ? '+' : ''}
                  {rec.percentChange.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
