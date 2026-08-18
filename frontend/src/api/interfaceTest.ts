// 接口测试相关 API
import request from '@/utils/request'
import type {
  ApiInterface,
  ApiInterfaceListResult,
  ApiInterfacePayload,
  InterfaceCase,
  InterfaceCaseListResult,
  InterfaceCaseUpdatePayload,
} from '@/types/interfaceTest'

// ---------- 接口定义 ----------
// 接口列表（分页 + 搜索）
export function listInterfacesApi(
  projectId: number,
  params: { page: number; page_size: number; keyword?: string },
): Promise<ApiInterfaceListResult> {
  return request.get(`/v1/projects/${projectId}/interfaces`, {
    params,
  }) as unknown as Promise<ApiInterfaceListResult>
}

// 新增接口
export function createInterfaceApi(
  projectId: number,
  data: ApiInterfacePayload,
): Promise<ApiInterface> {
  return request.post(
    `/v1/projects/${projectId}/interfaces`,
    data,
  ) as unknown as Promise<ApiInterface>
}

// 从 OpenAPI JSON 导入
export function importOpenApiApi(
  projectId: number,
  spec: Record<string, unknown>,
): Promise<ApiInterfaceListResult> {
  return request.post(
    `/v1/projects/${projectId}/interfaces/import-openapi`,
    { spec },
  ) as unknown as Promise<ApiInterfaceListResult>
}

// 编辑接口
export function updateInterfaceApi(
  projectId: number,
  id: number,
  data: Partial<ApiInterfacePayload>,
): Promise<ApiInterface> {
  return request.patch(
    `/v1/projects/${projectId}/interfaces/${id}`,
    data,
  ) as unknown as Promise<ApiInterface>
}

// 删除接口
export function deleteInterfaceApi(projectId: number, id: number): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/interfaces/${id}`,
  ) as unknown as Promise<void>
}

// ---------- 接口用例 ----------
// 生成接口测试用例（AI）
export function generateInterfaceCasesApi(
  projectId: number,
  interfaceIds?: number[],
): Promise<InterfaceCase[]> {
  return request.post(
    `/v1/projects/${projectId}/interfaces/generate-cases`,
    interfaceIds?.length ? { interface_ids: interfaceIds } : {},
  ) as unknown as Promise<InterfaceCase[]>
}

// 接口用例列表（分页 + 筛选）
export function listInterfaceCasesApi(
  projectId: number,
  params: {
    page: number
    page_size: number
    interface_id?: number
    category?: string
    keyword?: string
  },
): Promise<InterfaceCaseListResult> {
  return request.get(`/v1/projects/${projectId}/interface-cases`, {
    params,
  }) as unknown as Promise<InterfaceCaseListResult>
}

// 编辑接口用例
export function updateInterfaceCaseApi(
  projectId: number,
  id: number,
  data: InterfaceCaseUpdatePayload,
): Promise<InterfaceCase> {
  return request.patch(
    `/v1/projects/${projectId}/interface-cases/${id}`,
    data,
  ) as unknown as Promise<InterfaceCase>
}

// 删除接口用例
export function deleteInterfaceCaseApi(
  projectId: number,
  id: number,
): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/interface-cases/${id}`,
  ) as unknown as Promise<void>
}

// 导出接口用例 Excel
export function exportInterfaceCasesApi(projectId: number): Promise<Blob> {
  return request.get(`/v1/projects/${projectId}/interface-cases/export`, {
    responseType: 'blob',
  }) as unknown as Promise<Blob>
}
