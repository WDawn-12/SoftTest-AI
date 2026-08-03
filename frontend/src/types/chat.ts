// AI 聊天相关类型定义
export interface ChatMessage {
  id: number
  role: string
  content: string
  created_at: string
}

export interface ChatHistoryResult {
  total: number
  items: ChatMessage[]
}
