// 用户状态管理（Pinia store）单元测试：登录、注册、会话持久化与退出
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// Mock 认证 API，避免真实网络请求
const loginApi = vi.fn()
const registerApi = vi.fn()
const getMeApi = vi.fn()

vi.mock('@/api/auth', () => ({
  loginApi: (...args: unknown[]) => loginApi(...args),
  registerApi: (...args: unknown[]) => registerApi(...args),
  getMeApi: (...args: unknown[]) => getMeApi(...args),
}))

import { useUserStore } from '@/stores/user'

const TOKEN_KEY = 'token'
const USER_KEY = 'userInfo'

const mockUser = {
  id: 1,
  username: 'admin',
  nickname: '系统管理员',
  email: null,
  role: 'admin',
  status: 1,
}

const mockLoginResult = {
  access_token: 'jwt-token-123',
  token_type: 'bearer',
  expires_in: 86400,
  user: mockUser,
}

function mockLocalStorage() {
  const store = new Map<string, string>()
  Object.defineProperty(globalThis, 'localStorage', {
    value: {
      getItem: vi.fn((k: string) => store.get(k) ?? null),
      setItem: vi.fn((k: string, v: string) => void store.set(k, v)),
      removeItem: vi.fn((k: string) => void store.delete(k)),
      clear: vi.fn(() => store.clear()),
    },
    configurable: true,
  })
  return store
}

describe('useUserStore', () => {
  let store: ReturnType<typeof useUserStore>

  beforeEach(() => {
    mockLocalStorage()
    setActivePinia(createPinia())
    store = useUserStore()
    vi.clearAllMocks()
  })

  it('初始状态：无 token、无用户信息', () => {
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
  })

  it('login 成功后保存 token 与用户信息到内存和 localStorage', async () => {
    loginApi.mockResolvedValue(mockLoginResult)
    await store.login('admin', 'admin123')

    expect(loginApi).toHaveBeenCalledWith('admin', 'admin123')
    expect(store.token).toBe('jwt-token-123')
    expect(store.userInfo).toEqual(mockUser)
    expect(localStorage.getItem(TOKEN_KEY)).toBe('jwt-token-123')
    expect(localStorage.getItem(USER_KEY)).toBe(JSON.stringify(mockUser))
  })

  it('login 失败时抛错且不写入会话', async () => {
    loginApi.mockRejectedValue(new Error('用户名或密码错误'))
    await expect(store.login('admin', 'wrong')).rejects.toThrow('用户名或密码错误')
    expect(store.token).toBe('')
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('register 透传注册数据', async () => {
    registerApi.mockResolvedValue(mockUser)
    const payload = {
      username: 'tester',
      password: '123456',
      nickname: '测试员',
    }
    await store.register(payload)
    expect(registerApi).toHaveBeenCalledWith(payload)
  })

  it('fetchMe 刷新用户信息并持久化', async () => {
    const updated = { ...mockUser, nickname: '新昵称' }
    getMeApi.mockResolvedValue(updated)
    await store.fetchMe()
    expect(store.userInfo).toEqual(updated)
    expect(localStorage.getItem(USER_KEY)).toBe(JSON.stringify(updated))
  })

  it('logout 清空 token 与用户信息', async () => {
    loginApi.mockResolvedValue(mockLoginResult)
    await store.login('admin', 'admin123')
    expect(store.token).toBe('jwt-token-123')

    store.logout()
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(localStorage.getItem(USER_KEY)).toBeNull()
  })
})
