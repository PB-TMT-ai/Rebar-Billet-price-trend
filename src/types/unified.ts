export interface UnifiedColumnGroup {
  name: string
  start: number
  end: number
}

export interface UnifiedRow {
  date: string
  city: string
  values: (string | number | null)[]
}

export interface UnifiedDataset {
  columns: string[]
  columnGroups: UnifiedColumnGroup[]
  rows: UnifiedRow[]
}
