// AI 聊天相关 API
import request from '@/utils/request'
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
