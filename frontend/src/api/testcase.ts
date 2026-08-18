// 测试用例相关 API
import request from '@/utils/request'
import { fetchSSE, type SSEHandlers } from '@/utils/sse'
import type {
  TestCase,
  TestCaseListResult,
  TestCaseUpdatePayload,
} from '@/types/testcase'

// 测试用例列表（分页 + 筛选）
export function listTestCasesApi(
  projectId: number,
  params: {
    page: number
    page_size: number
    requirement_id?: number
    module_id?: number
    priority?: string
    keyword?: string
  },
): Promise<TestCaseListResult> {
  return request.get(`/v1/projects/${projectId}/test-cases`, {
    params,
  }) as unknown as Promise<TestCaseListResult>
}

// 调用 TestCase Agent 生成测试用例
export function generateTestCasesApi(
  projectId: number,
  requirementId: number,
): Promise<TestCase[]> {
  return request.post(
    `/v1/projects/${projectId}/requirements/${requirementId}/test-cases/generate`,
  ) as unknown as Promise<TestCase[]>
}

// 调用 TestCase Agent 生成测试用例（SSE 流式：阶段进度 + 测试用例列表）
// 事件：status（阶段进度）/ result（测试用例列表）/ error
export function generateTestCasesStreamApi(
  projectId: number,
  requirementId: number,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  return fetchSSE(
    `/v1/projects/${projectId}/requirements/${requirementId}/test-cases/generate/stream`,
    { method: 'POST', signal },
    handlers,
  )
}

// 编辑测试用例（人工编辑）
export function updateTestCaseApi(
  projectId: number,
  id: number,
  data: TestCaseUpdatePayload,
): Promise<TestCase> {
  return request.patch(
    `/v1/projects/${projectId}/test-cases/${id}`,
    data,
  ) as unknown as Promise<TestCase>
}

// 删除测试用例
export function deleteTestCaseApi(projectId: number, id: number): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/test-cases/${id}`,
  ) as unknown as Promise<void>
}

// 批量导出测试用例 Excel（按筛选条件）
export function exportTestCasesApi(
  projectId: number,
  params: {
    requirement_id?: number
    module_id?: number
    priority?: string
    keyword?: string
  },
): Promise<Blob> {
  return request.get(`/v1/projects/${projectId}/test-cases/export`, {
    params,
    responseType: 'blob',
  }) as unknown as Promise<Blob>
}
