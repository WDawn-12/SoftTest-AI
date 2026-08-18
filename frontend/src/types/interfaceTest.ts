// 接口测试相关类型定义
export interface ApiInterface {
  id: number
  project_id: number
  name: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  path: string
  summary: string | null
  headers: string | null
  params: string | null
  body: string | null
  created_at: string
  updated_at: string
}

export interface ApiInterfaceListResult {
  total: number
  page: number
  page_size: number
  items: ApiInterface[]
}

export interface ApiInterfacePayload {
  name: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  path: string
  summary?: string | null
  headers?: string | null
  params?: string | null
  body?: string | null
}

export interface InterfaceCase {
  id: number
  project_id: number
  interface_id: number | null
  interface_name: string | null
  case_no: string
  title: string
  category: string
  method: string
  path: string
  test_data: string | null
  request_payload: string | null
  expected_status: string | null
  expected_result: string | null
  priority: string
  preconditions: string | null
  steps: string | null
  remark: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface InterfaceCaseListResult {
  total: number
  page: number
  page_size: number
  items: InterfaceCase[]
}

export interface InterfaceCaseUpdatePayload {
  title?: string
  category?: string
  test_data?: string
  request_payload?: string
  expected_status?: string
  expected_result?: string
  priority?: '高' | '中' | '低'
  preconditions?: string
  steps?: string
  remark?: string
}
