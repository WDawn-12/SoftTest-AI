// 用户状态管理（Pinia）：登录态、用户信息与登录/注册/退出动作
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMeApi, loginApi, registerApi } from '@/api/auth'
import type { LoginResult, RegisterPayload, UserInfo } from '@/types/auth'

const TOKEN_KEY = 'token'
const USER_KEY = 'userInfo'

function readStoredUser(): UserInfo | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as UserInfo
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref<UserInfo | null>(readStoredUser())

  function saveSession(result: LoginResult) {
    token.value = result.access_token
    userInfo.value = result.user
    localStorage.setItem(TOKEN_KEY, result.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(result.user))
  }

  // 登录
  async function login(username: string, password: string) {
    const result = await loginApi(username, password)
    saveSession(result)
  }

  // 注册
  async function register(data: RegisterPayload) {
    await registerApi(data)
  }

  // 刷新当前用户信息
  async function fetchMe() {
    const user = await getMeApi()
    userInfo.value = user
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }

  // 退出登录
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return { token, userInfo, login, register, fetchMe, logout }
})
