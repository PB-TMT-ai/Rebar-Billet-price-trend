import type { FrequencyOption } from '../types/prices'

interface DateControlsProps {
  frequency: FrequencyOption
  onFrequencyChange: (f: FrequencyOption) => void
  startDate: string
  endDate: string
  onStartDateChange: (d: string) => void
  onEndDateChange: (d: string) => void
  minDate: string
  maxDate: string
}

const FREQUENCY_OPTIONS: { value: FrequencyOption; label: string }[] = [
  { value: 'last5', label: 'Last 5 Days' },
  { value: 'last10', label: 'Last 10 Days' },
  { value: 'last15', label: 'Last 15 Days' },
  { value: 'custom', label: 'Custom Range' },
]

export function DateControls({
  frequency,
  onFrequencyChange,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  minDate,
  maxDate,
}: DateControlsProps): React.ReactElement {
  const isCustom = frequency === 'custom'

  return (
    <div className="flex flex-wrap items-end gap-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Frequency</label>
        <select
          value={frequency}
          onChange={(e) => onFrequencyChange(e.target.value as FrequencyOption)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        >
          {FREQUENCY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Start Date</label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          disabled={!isCustom}
          min={minDate}
          max={maxDate}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-100 disabled:text-slate-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">End Date</label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          disabled={!isCustom}
          min={minDate}
          max={maxDate}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-100 disabled:text-slate-500"
        />
      </div>
    </div>
  )
}
