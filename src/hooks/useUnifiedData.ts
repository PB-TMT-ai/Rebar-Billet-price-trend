import { useMemo } from 'react'
import rawData from '../data/unified-tmt-prices.json'
import { UNIFIED_CITIES } from '../types/unified'
import type { UnifiedRecord } from '../types/unified'

const allData: UnifiedRecord[] = rawData as UnifiedRecord[]

export function useUnifiedAllData(): UnifiedRecord[] {
  return allData
}

export function useUnifiedDateRange(): { minDate: string; maxDate: string; availableDates: string[] } {
  return useMemo(() => {
    if (allData.length === 0) return { minDate: '', maxDate: '', availableDates: [] }
    const dates = allData.map((r) => r.date).sort()
    return { minDate: dates[0], maxDate: dates[dates.length - 1], availableDates: dates }
  }, [])
}

export function useUnifiedRecordForDate(date: string): UnifiedRecord | null {
  return useMemo(() => {
    if (!date) return null
    return allData.find((r) => r.date === date) ?? null
  }, [date])
}

export function useUnifiedTrendData(startDate: string, endDate: string): UnifiedRecord[] {
  return useMemo(() => {
    if (!startDate || !endDate) return []
    return allData.filter((r) => r.date >= startDate && r.date <= endDate)
  }, [startDate, endDate])
}

export { UNIFIED_CITIES }
