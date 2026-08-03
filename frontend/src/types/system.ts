// 系统管理相关类型定义
export interface OperationLogItem {
  id: number
  user_id: number | null
  username: string | null
  action: string
  module: string
  detail: string | null
  ip: string | null
  created_at: string
}

export interface OperationLogListResult {
  total: number
  page: number
  page_size: number
  items: OperationLogItem[]
}

export interface AiCallLogItem {
  id: number
  user_id: number | null
  username: string | null
  agent: string
  provider: string | null
  prompt_length: number
  response_length: number
  duration_ms: number
  status: string
  error_message: string | null
  created_at: string
}

export interface AiCallLogListResult {
  total: number
  page: number
  page_size: number
  items: AiCallLogItem[]
}
