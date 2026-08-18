// 需求文档相关 API
import request from '@/utils/request'
import { fetchSSE, type SSEHandlers } from '@/utils/sse'
import type {
  ParseResultResponse,
  Requirement,
  RequirementDetail,
  RequirementListResult,
} from '@/types/requirement'

// 上传需求文档（multipart/form-data）
export function uploadRequirementApi(
  projectId: number,
  file: File,
): Promise<Requirement> {
  const form = new FormData()
  form.append('file', file)
  return request.post(`/v1/projects/${projectId}/requirements/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as unknown as Promise<Requirement>
}

// 需求文档列表（分页）
export function listRequirementsApi(
  projectId: number,
  params: { page: number; page_size: number },
): Promise<RequirementListResult> {
  return request.get(`/v1/projects/${projectId}/requirements`, {
    params,
  }) as unknown as Promise<RequirementListResult>
}

// 需求文档详情（含文本内容）
export function getRequirementApi(
  projectId: number,
  id: number,
): Promise<RequirementDetail> {
  return request.get(
    `/v1/projects/${projectId}/requirements/${id}`,
  ) as unknown as Promise<RequirementDetail>
}

// 删除需求文档
export function deleteRequirementApi(
  projectId: number,
  id: number,
): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/requirements/${id}`,
  ) as unknown as Promise<void>
}

// 调用 Requirement Agent 解析需求
export function parseRequirementApi(
  projectId: number,
  id: number,
): Promise<ParseResultResponse> {
  return request.post(
    `/v1/projects/${projectId}/requirements/${id}/parse`,
  ) as unknown as Promise<ParseResultResponse>
}

// 调用 Requirement Agent 解析需求（SSE 流式：阶段进度 + 最终结果）
// 事件：status（阶段进度）/ result（解析结果）/ error
export function parseRequirementStreamApi(
  projectId: number,
  id: number,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  return fetchSSE(
    `/v1/projects/${projectId}/requirements/${id}/parse/stream`,
    { method: 'POST', signal },
    handlers,
  )
}

// 获取 AI 解析结果
export function getParseResultApi(
  projectId: number,
  id: number,
): Promise<ParseResultResponse> {
  return request.get(
    `/v1/projects/${projectId}/requirements/${id}/parse-result`,
  ) as unknown as Promise<ParseResultResponse>
}
