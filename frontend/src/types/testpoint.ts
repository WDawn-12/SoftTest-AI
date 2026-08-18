// 测试点相关类型定义
export type TestPointCategory =
  | 'normal'
  | 'exception'
  | 'boundary'
  | 'security'
  | 'compatibility'
  | 'performance'

export interface TestPoint {
  id: number
  project_id: number
  requirement_id: number | null
  module_id: number | null
  module_name: string | null
  name: string
  category: string
  created_at: string
  updated_at: string
}

export interface TestPointListResult {
  total: number
  page: number
  page_size: number
  items: TestPoint[]
}

export interface TestPointUpdatePayload {
  name?: string
  category?: TestPointCategory
}
