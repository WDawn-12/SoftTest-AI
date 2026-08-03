// 需求文档相关类型定义
export interface Requirement {
  id: number
  project_id: number
  file_name: string
  file_type: string
  file_size: number
  parse_status: string
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface RequirementDetail extends Requirement {
  content: string | null
}

export interface RequirementListResult {
  total: number
  page: number
  page_size: number
  items: Requirement[]
}

// ---------- AI 解析结果 ----------
export interface RequirementModule {
  name: string
  description: string
  functions: string[]
}

export interface BusinessFlow {
  name: string
  steps: string[]
}

export interface RiskPoint {
  type: string
  description: string
  level: string
}

export interface ParseResultData {
  summary: string
  modules: RequirementModule[]
  roles: string[]
  business_flows: BusinessFlow[]
  risks: RiskPoint[]
}

export interface ParseResultResponse {
  requirement_id: number
  parse_status: string
  error_message: string | null
  result: ParseResultData | null
}
