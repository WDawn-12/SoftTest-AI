// 性能测试场景相关 API
import request from '@/utils/request'
import type {
  PerfScenario,
  PerfScenarioListResult,
  PerfScenarioPayload,
} from '@/types/perfScenario'

// 场景列表（分页 + 搜索）
export function listPerfScenariosApi(
  projectId: number,
  params: { page: number; page_size: number; keyword?: string },
): Promise<PerfScenarioListResult> {
  return request.get(`/v1/projects/${projectId}/perf-scenarios`, {
    params,
  }) as unknown as Promise<PerfScenarioListResult>
}

// 新建场景
export function createPerfScenarioApi(
  projectId: number,
  data: PerfScenarioPayload,
): Promise<PerfScenario> {
  return request.post(
    `/v1/projects/${projectId}/perf-scenarios`,
    data,
  ) as unknown as Promise<PerfScenario>
}

// 编辑场景
export function updatePerfScenarioApi(
  projectId: number,
  id: number,
  data: Partial<PerfScenarioPayload>,
): Promise<PerfScenario> {
  return request.patch(
    `/v1/projects/${projectId}/perf-scenarios/${id}`,
    data,
  ) as unknown as Promise<PerfScenario>
}

// 删除场景
export function deletePerfScenarioApi(
  projectId: number,
  id: number,
): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/perf-scenarios/${id}`,
  ) as unknown as Promise<void>
}

// 导出场景为 JMeter 压测脚本（.jmx）
export function exportPerfScenarioJmeterApi(
  projectId: number,
  id: number,
): Promise<Blob> {
  return request.get(
    `/v1/projects/${projectId}/perf-scenarios/${id}/export/jmeter`,
    { responseType: 'blob' },
  ) as unknown as Promise<Blob>
}
