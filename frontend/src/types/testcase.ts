// 测试用例相关类型定义
export type TestCasePriority = '高' | '中' | '低'

export interface TestCase {
  id: number
  project_id: number
  requirement_id: number | null
  module_id: number | null
  module_name: string | null
  case_no: string
  title: string
  test_point: string | null
  priority: string
  preconditions: string | null
  steps: string | null
  expected_result: string | null
  remark: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface TestCaseListResult {
  total: number
  page: number
  page_size: number
  items: TestCase[]
}

export interface TestCaseUpdatePayload {
  title?: string
  test_point?: string
  priority?: TestCasePriority
  preconditions?: string
  steps?: string
  expected_result?: string
  remark?: string
}
