import { useMemo } from 'react'
import rawData from '../data/unified-tmt-prices.json'
import type { UnifiedDataset, UnifiedRow } from '../types/unified'

const dataset: UnifiedDataset = rawData as UnifiedDataset

export function useUnifiedDataset(): UnifiedDataset {
  return dataset
}

export function useUnifiedDates(): { minDate: string; maxDate: string; availableDates: string[] } {
  return useMemo(() => {
    const dates = Array.from(new Set(dataset.rows.map((r) => r.date))).sort()
    return {
      minDate: dates[0] ?? '',
      maxDate: dates[dates.length - 1] ?? '',
      availableDates: dates,
    }
  }, [])
}

export function useUnifiedRowsForDate(date: string): UnifiedRow[] {
  return useMemo(() => {
    if (!date) return []
    return dataset.rows.filter((r) => r.date === date)
  }, [date])
}
