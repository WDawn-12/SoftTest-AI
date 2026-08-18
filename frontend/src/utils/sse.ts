// SSE（Server-Sent Events）客户端工具
// axios 不支持流式响应，这里用原生 fetch + ReadableStream 消费 text/event-stream

export interface SSEHandlers {
  /** 收到任意事件：event 为事件名，data 为已解析的数据（JSON 或字符串） */
  onEvent?: (event: string, data: unknown) => void
  /** 请求失败或 HTTP 非 2xx */
  onError?: (message: string) => void
  /** 流正常结束 */
  onDone?: () => void
}

export interface SSEOptions {
  method?: 'POST' | 'GET'
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

/**
 * 发起 SSE 请求并按事件回调消费。
 *
 * 响应按空行（\n\n）切分为事件块，每块解析 `event:` 与 `data:` 行；
 * data 优先按 JSON 解析，失败时按纯文本处理。
 */
export async function fetchSSE(
  url: string,
  options: SSEOptions = {},
  handlers: SSEHandlers = {},
): Promise<void> {
  const { method = 'POST', body, headers = {}, signal } = options
  const token = localStorage.getItem('token')

  const resp = await fetch(`${API_BASE}${url}`, {
    method,
    signal,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!resp.ok) {
    let message = `请求失败（${resp.status}）`
    try {
      const data = await resp.json()
      message = data?.detail || message
    } catch {
      // 非 JSON 错误体，保留默认提示
    }
    handlers.onError?.(message)
    return
  }

  const contentType = resp.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    // 兜底：非流式响应（如网关代理了响应），按 JSON 处理
    try {
      const data = await resp.json()
      handlers.onEvent?.('result', data)
      handlers.onDone?.()
    } catch {
      const text = await resp.text()
      handlers.onEvent?.('result', text)
      handlers.onDone?.()
    }
    return
  }

  const reader = resp.body?.getReader()
  if (!reader) {
    handlers.onError?.('无法读取流式响应')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // 按空行切分事件块，保留尾部未完整块
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() || ''
      for (const block of blocks) {
        handleBlock(block, handlers)
      }
    }
    // 处理残留块
    if (buffer.trim()) {
      handleBlock(buffer, handlers)
    }
    handlers.onDone?.()
  } catch (err) {
    if ((err as Error)?.name === 'AbortError') return
    handlers.onError?.((err as Error)?.message || '流式请求中断')
  }
}

function handleBlock(block: string, handlers: SSEHandlers): void {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }
  const raw = dataLines.join('\n')
  if (!raw) return
  let data: unknown = raw
  if (raw.startsWith('{') || raw.startsWith('[')) {
    try {
      data = JSON.parse(raw)
    } catch {
      data = raw
    }
  }
  handlers.onEvent?.(event, data)
}
