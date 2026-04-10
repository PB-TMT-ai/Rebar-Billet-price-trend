export interface PriceRecord {
  date: string
  Raipur: number | null
  "Delhi/NCR": number | null
  Durgapur: number | null
}

export type CityKey = "Raipur" | "Delhi/NCR" | "Durgapur"

export interface DeltaRecord {
  city: string
  startPrice: number
  endPrice: number
  delta: number
  percentChange: number
}

export type FrequencyOption = "last5" | "last10" | "last15" | "custom"
