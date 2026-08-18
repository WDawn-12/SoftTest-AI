// AI 聊天相关类型定义
export interface ChatToolUse {
  name: string
  args: Record<string, unknown>
}

export interface ChatMessage {
  id: number
  role: string
  content: string
  created_at: string
  /** 本次回复过程中调用的工具（仅流式响应时前端填充，不持久化） */
  tool_uses?: ChatToolUse[]
}

export interface ChatHistoryResult {
  total: number
  items: ChatMessage[]
}
