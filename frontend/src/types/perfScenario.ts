// 性能测试场景类型定义
export interface PerfScenario {
  id: number
  project_id: number
  name: string
  description: string | null
  thread_count: number
  loop_count: number
  ramp_up: number
  think_time_ms: number
  base_url: string
  base_port: string
  interface_ids: number[]
  created_at: string
  updated_at: string
}

export interface PerfScenarioListResult {
  total: number
  page: number
  page_size: number
  items: PerfScenario[]
}

export interface PerfScenarioPayload {
  name: string
  description?: string | null
  thread_count: number
  loop_count: number
  ramp_up: number
  think_time_ms: number
  base_url: string
  base_port: string
  interface_ids?: number[] | null
}
