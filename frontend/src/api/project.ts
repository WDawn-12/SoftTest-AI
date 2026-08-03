// 项目管理相关 API
import request from '@/utils/request'
import type {
  Project,
  ProjectCreatePayload,
  ProjectListResult,
  ProjectUpdatePayload,
} from '@/types/project'

// 项目列表（分页 + 搜索）
export function listProjectsApi(params: {
  page: number
  page_size: number
  keyword?: string
}): Promise<ProjectListResult> {
  return request.get('/v1/projects', { params }) as unknown as Promise<ProjectListResult>
}

// 创建项目
export function createProjectApi(data: ProjectCreatePayload): Promise<Project> {
  return request.post('/v1/projects', data) as unknown as Promise<Project>
}

// 更新项目
export function updateProjectApi(
  id: number,
  data: ProjectUpdatePayload,
): Promise<Project> {
  return request.patch(`/v1/projects/${id}`, data) as unknown as Promise<Project>
}

// 删除项目
export function deleteProjectApi(id: number): Promise<void> {
  return request.delete(`/v1/projects/${id}`) as unknown as Promise<void>
}
