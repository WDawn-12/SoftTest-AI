// 仪表盘相关类型定义
export interface RecentProject {
  id: number
  name: string
  status: string
  created_at: string
}

export interface DashboardStats {
  project_count: number
  requirement_count: number
  test_point_count: number
  test_case_count: number
  chat_count: number
  recent_projects: RecentProject[]
}
