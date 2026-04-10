import { useMemo } from 'react'
import rawData from '../data/prices.json'
import type { PriceRecord, CityKey, DeltaRecord, FrequencyOption } from '../types/prices'

const allData: PriceRecord[] = rawData as PriceRecord[]

const CITIES: CityKey[] = ['Raipur', 'Delhi/NCR', 'Durgapur']

function getLastNTradingDays(n: number): { start: string; end: string } {
  const withPrices = allData.filter(
    (r) => r.Raipur !== null || r['Delhi/NCR'] !== null || r.Durgapur !== null
  )
  const end = withPrices[withPrices.length - 1]?.date ?? ''
  const startIdx = Math.max(0, withPrices.length - n)
  const start = withPrices[startIdx]?.date ?? ''
  return { start, end }
}

export function useDateRange(): { minDate: string; maxDate: string } {
  return useMemo(() => {
    if (allData.length === 0) return { minDate: '', maxDate: '' }
    return { minDate: allData[0].date, maxDate: allData[allData.length - 1].date }
  }, [])
}

export function useResolvedDates(
  frequency: FrequencyOption,
  customStart: string,
  customEnd: string
): { startDate: string; endDate: string } {
  return useMemo(() => {
    if (frequency === 'custom') {
      return { startDate: customStart, endDate: customEnd }
    }
    const n = frequency === 'last5' ? 5 : frequency === 'last10' ? 10 : 15
    const { start, end } = getLastNTradingDays(n)
    return { startDate: start, endDate: end }
  }, [frequency, customStart, customEnd])
}

export function useFilteredData(startDate: string, endDate: string): PriceRecord[] {
  return useMemo(() => {
    if (!startDate || !endDate) return []
    return allData.filter((r) => r.date >= startDate && r.date <= endDate)
  }, [startDate, endDate])
}

export function useDeltaData(startDate: string, endDate: string): DeltaRecord[] {
  return useMemo(() => {
    if (!startDate || !endDate) return []

    const filtered = allData.filter((r) => r.date >= startDate && r.date <= endDate)
    if (filtered.length < 2) return []

    return CITIES.map((city) => {
      // Find first non-null price from start
      let startPrice: number | null = null
      for (const row of filtered) {
        const val = row[city]
        if (val !== null) {
          startPrice = val
          break
        }
      }

      // Find last non-null price from end
      let endPrice: number | null = null
      for (let i = filtered.length - 1; i >= 0; i--) {
        const val = filtered[i][city]
        if (val !== null) {
          endPrice = val
          break
        }
      }

      if (startPrice === null || endPrice === null) {
        return { city, startPrice: 0, endPrice: 0, delta: 0, percentChange: 0 }
      }

      const delta = endPrice - startPrice
      const percentChange = startPrice !== 0 ? (delta / startPrice) * 100 : 0

      return { city, startPrice, endPrice, delta, percentChange }
    })
  }, [startDate, endDate])
}
