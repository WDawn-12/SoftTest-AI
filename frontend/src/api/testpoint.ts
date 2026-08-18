// 测试点相关 API
import request from '@/utils/request'
import { fetchSSE, type SSEHandlers } from '@/utils/sse'
import type {
  TestPoint,
  TestPointListResult,
  TestPointUpdatePayload,
} from '@/types/testpoint'

// 测试点列表（分页 + 筛选）
export function listTestPointsApi(
  projectId: number,
  params: {
    page: number
    page_size: number
    requirement_id?: number
    module_id?: number
    category?: string
    keyword?: string
  },
): Promise<TestPointListResult> {
  return request.get(`/v1/projects/${projectId}/test-points`, {
    params,
  }) as unknown as Promise<TestPointListResult>
}

// 调用 TestPoint Agent 生成测试点
export function generateTestPointsApi(
  projectId: number,
  requirementId: number,
): Promise<TestPoint[]> {
  return request.post(
    `/v1/projects/${projectId}/requirements/${requirementId}/test-points/generate`,
  ) as unknown as Promise<TestPoint[]>
}

// 调用 TestPoint Agent 生成测试点（SSE 流式：阶段进度 + 测试点列表）
// 事件：status（阶段进度）/ result（测试点列表）/ error
export function generateTestPointsStreamApi(
  projectId: number,
  requirementId: number,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  return fetchSSE(
    `/v1/projects/${projectId}/requirements/${requirementId}/test-points/generate/stream`,
    { method: 'POST', signal },
    handlers,
  )
}

// 编辑测试点（人工编辑）
export function updateTestPointApi(
  projectId: number,
  id: number,
  data: TestPointUpdatePayload,
): Promise<TestPoint> {
  return request.patch(
    `/v1/projects/${projectId}/test-points/${id}`,
    data,
  ) as unknown as Promise<TestPoint>
}

// 删除测试点
export function deleteTestPointApi(projectId: number, id: number): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/test-points/${id}`,
  ) as unknown as Promise<void>
}
