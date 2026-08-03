// 认证相关 API
import request from '@/utils/request'
import type { LoginResult, RegisterPayload, UserInfo } from '@/types/auth'

// 登录（后端使用 OAuth2 表单格式）
export function loginApi(username: string, password: string): Promise<LoginResult> {
  const body = new URLSearchParams({ username, password })
  return request.post('/v1/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }) as unknown as Promise<LoginResult>
}

// 注册
export function registerApi(data: RegisterPayload): Promise<UserInfo> {
  return request.post('/v1/auth/register', data) as unknown as Promise<UserInfo>
}

// 获取当前登录用户信息
export function getMeApi(): Promise<UserInfo> {
  return request.get('/v1/users/me') as unknown as Promise<UserInfo>
}
