export const UNIFIED_CITIES = [
  'DL/NCR',
  'Bawal/Rewari/Faridabad',
  'Agra/Ghaziabad',
  'Gorakhpur',
  'Jaipur',
  'Srinagar',
  'Jammu',
  'Chandigarh',
  'Shimla',
  'Dehradun',
  'Ludhiana',
  'Ranchi',
  'Patna',
  'Siliguri, Jalpaiguri, Cooch behar',
  'Kolkata',
  'Bhubaneshwar',
  'Rourkela',
  'Mumbai',
  'Pune',
  'Nashik',
  'Nagpur',
  'Ahmedabad',
  'Raipur',
  'Indore',
  'North Karnataka-Hubli',
  'South karnataka- Bangalore',
  'Chennai',
  'Coimbatore',
  'Cochin',
  'Hyderabad',
  'Non Hyderabad',
  'AP- Vizag',
] as const

export type UnifiedCity = typeof UNIFIED_CITIES[number]

export type UnifiedRecord = {
  date: string
} & {
  [K in UnifiedCity]: number | null
}
