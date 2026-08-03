// 仪表盘相关 API
import request from '@/utils/request'
import type { DashboardStats } from '@/types/dashboard'

// 仪表盘统计
export function getDashboardStatsApi(): Promise<DashboardStats> {
  return request.get('/v1/dashboard/stats') as unknown as Promise<DashboardStats>
}
