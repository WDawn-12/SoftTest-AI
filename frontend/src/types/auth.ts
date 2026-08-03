// 认证与用户相关类型定义
export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  email: string | null
  role: string
  status: number
  created_at: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export interface RegisterPayload {
  username: string
  password: string
  nickname?: string
  email?: string
}
