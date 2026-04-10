import { useState } from 'react'
import { DateControls } from '../components/DateControls'
import { PriceTrendChart } from '../components/PriceTrendChart'
import { PriceDeltaChart } from '../components/PriceDeltaChart'
import { useDateRange, useResolvedDates, useFilteredData, useDeltaData } from '../hooks/usePriceData'
import type { FrequencyOption } from '../types/prices'

export function Dashboard(): React.ReactElement {
  const { minDate, maxDate } = useDateRange()
  const [frequency, setFrequency] = useState<FrequencyOption>('last10')
  const [customStart, setCustomStart] = useState(maxDate)
  const [customEnd, setCustomEnd] = useState(maxDate)
  const [activeTab, setActiveTab] = useState<'trend' | 'delta'>('trend')

  const { startDate, endDate } = useResolvedDates(frequency, customStart, customEnd)
  const filteredData = useFilteredData(startDate, endDate)
  const deltaData = useDeltaData(startDate, endDate)

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <h1 className="text-2xl font-semibold text-slate-900">Rebar & Billet Price Dashboard</h1>
          <p className="mt-1 text-sm text-slate-600">
            12MM rebar prices for Raipur, Delhi/NCR, and Durgapur
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Controls */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <DateControls
            frequency={frequency}
            onFrequencyChange={setFrequency}
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={setCustomStart}
            onEndDateChange={setCustomEnd}
            minDate={minDate}
            maxDate={maxDate}
          />
        </div>

        {/* Tab navigation */}
        <div className="mt-8 flex gap-1 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('trend')}
            className={`px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'trend'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Price Trend
          </button>
          <button
            onClick={() => setActiveTab('delta')}
            className={`px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'delta'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Price Delta
          </button>
        </div>

        {/* Chart panels */}
        <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          {activeTab === 'trend' ? (
            <div>
              <h2 className="mb-4 text-lg font-medium text-slate-900">
                Price Trend — {startDate} to {endDate}
              </h2>
              <PriceTrendChart data={filteredData} />
            </div>
          ) : (
            <div>
              <h2 className="mb-4 text-lg font-medium text-slate-900">Price Change (Delta)</h2>
              <PriceDeltaChart data={deltaData} startDate={startDate} endDate={endDate} />
            </div>
          )}
        </div>

        {/* Data info */}
        <p className="mt-4 text-xs text-slate-400">
          Data range: {minDate} to {maxDate} &middot; Showing {filteredData.length} trading days
        </p>
      </main>
    </div>
  )
}
