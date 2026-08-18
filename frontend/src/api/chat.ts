// AI 聊天相关 API
import request from '@/utils/request'
import { fetchSSE, type SSEHandlers } from '@/utils/sse'
import type { ChatHistoryResult, ChatMessage } from '@/types/chat'

// 发送消息（AI 对话，保存用户消息与回复）
export function sendChatMessageApi(
  projectId: number,
  content: string,
): Promise<ChatMessage> {
  return request.post(`/v1/projects/${projectId}/chat/messages`, {
    content,
  }) as unknown as Promise<ChatMessage>
}

// 发送消息（SSE 流式：AI 回复逐字返回，打字机效果）
// 事件：delta（文本增量）/ result（完整回复）/ error
export function sendChatMessageStreamApi(
  projectId: number,
  content: string,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  return fetchSSE(
    `/v1/projects/${projectId}/chat/messages/stream`,
    { method: 'POST', body: { content }, signal },
    handlers,
  )
}

// 获取聊天历史
export function getChatHistoryApi(
  projectId: number,
  params: { page: number; page_size: number },
): Promise<ChatHistoryResult> {
  return request.get(`/v1/projects/${projectId}/chat/history`, {
    params,
  }) as unknown as Promise<ChatHistoryResult>
}

// 清空聊天记录
export function clearChatHistoryApi(projectId: number): Promise<void> {
  return request.delete(
    `/v1/projects/${projectId}/chat/history`,
  ) as unknown as Promise<void>
}
