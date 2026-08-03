// 被测系统（System Under Test）相关类型定义
export type SystemType = 'Web后台' | 'Web网站' | '微信小程序' | 'Android' | 'iOS'
export type BrowserType = 'Chrome' | 'Edge' | 'Firefox'

export interface SutInfo {
  system_name: string | null
  test_url: string | null
  system_type: string | null
  browser_type: string | null
  login_username: string | null
  login_password: string | null
  system_description: string | null
}

export interface SutPayload {
  system_name: string
  test_url: string
  system_type: SystemType
  browser_type: BrowserType
  login_username?: string
  login_password?: string
  system_description?: string
}

export interface TestConnectionResult {
  success: boolean
  http_status: number | null
  response_time_ms: number | null
  message: string
}
