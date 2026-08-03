// 项目管理相关类型定义
export type ProjectStatus = 'active' | 'finished' | 'archived'

export interface Project {
  id: number
  name: string
  description: string | null
  status: string
  owner_id: number | null
  created_at: string
  updated_at: string
}

export interface ProjectListResult {
  total: number
  page: number
  page_size: number
  items: Project[]
}

export interface ProjectCreatePayload {
  name: string
  description?: string
  system_name?: string
  test_url?: string
  system_type?: string
  browser_type?: string
  login_username?: string
  login_password?: string
  system_description?: string
}

export interface ProjectUpdatePayload {
  name?: string
  description?: string | null
  status?: ProjectStatus
}
