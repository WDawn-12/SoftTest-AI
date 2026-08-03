// 系统管理相关 API（管理员）
import request from '@/utils/request'
import type {
  AiCallLogListResult,
  OperationLogListResult,
} from '@/types/system'

export interface SettingsResult {
  settings: Record<string, string>
}

// 获取系统设置
export function getSystemSettingsApi(): Promise<SettingsResult> {
  return request.get('/v1/system/settings') as unknown as Promise<SettingsResult>
}

// 更新系统设置
export function updateSystemSettingsApi(
  values: Record<string, string>,
): Promise<SettingsResult> {
  return request.put('/v1/system/settings', {
    values,
  }) as unknown as Promise<SettingsResult>
}

// 操作日志（分页 + 关键字）
export function listOperationLogsApi(params: {
  page: number
  page_size: number
  keyword?: string
}): Promise<OperationLogListResult> {
  return request.get('/v1/system/logs/operations', {
    params,
  }) as unknown as Promise<OperationLogListResult>
}

// AI 调用日志（分页）
export function listAiCallLogsApi(params: {
  page: number
  page_size: number
}): Promise<AiCallLogListResult> {
  return request.get('/v1/system/logs/ai', {
    params,
  }) as unknown as Promise<AiCallLogListResult>
}
