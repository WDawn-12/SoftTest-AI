// 被测系统（System Under Test）相关 API
import request from '@/utils/request'
import type { SutInfo, SutPayload, TestConnectionResult } from '@/types/sut'

// 获取被测系统
export function getSutApi(projectId: number): Promise<SutInfo> {
  return request.get(`/v1/projects/${projectId}/system`) as unknown as Promise<SutInfo>
}

// 创建被测系统
export function createSutApi(projectId: number, data: SutPayload): Promise<SutInfo> {
  return request.post(
    `/v1/projects/${projectId}/system`,
    data,
  ) as unknown as Promise<SutInfo>
}

// 更新被测系统
export function updateSutApi(
  projectId: number,
  data: Partial<SutPayload>,
): Promise<SutInfo> {
  return request.put(
    `/v1/projects/${projectId}/system`,
    data,
  ) as unknown as Promise<SutInfo>
}

// 删除被测系统
export function deleteSutApi(projectId: number): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/system`,
  ) as unknown as Promise<void>
}

// 测试连接
export function testConnectionApi(
  projectId: number,
): Promise<TestConnectionResult> {
  return request.post(
    `/v1/projects/${projectId}/system/test-connection`,
  ) as unknown as Promise<TestConnectionResult>
}
