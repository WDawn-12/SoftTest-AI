// SSE 客户端工具单元测试：事件解析、JSON 数据、非流式兜底、错误与中断
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchSSE } from '@/utils/sse'

// ---- 测试辅助：构造 Stream 响应 ----
function createSSEResponse(chunks: string[], contentType = 'text/event-stream') {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': contentType },
  })
}

describe('fetchSSE 事件解析', () => {
  const originalFetch = globalThis.fetch
  const originalLocalStorage = globalThis.localStorage

  beforeEach(() => {
    globalThis.fetch = vi.fn()
    // jsdom 自带 localStorage，但为隔离测试可 mock
    Object.defineProperty(globalThis, 'localStorage', {
      value: {
        getItem: vi.fn(() => 'test-token'),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      configurable: true,
    })
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    Object.defineProperty(globalThis, 'localStorage', {
      value: originalLocalStorage,
      configurable: true,
    })
    vi.restoreAllMocks()
  })

  it('携带 Authorization 头（Bearer token）', async () => {
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      createSSEResponse([]),
    )
    await fetchSSE('/v1/chat/stream')
    const [url, init] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls[0] as unknown as [string, RequestInit]
    expect(url).toContain('/api/v1/chat/stream')
    expect(init.headers).toMatchObject({
      Authorization: 'Bearer test-token',
      'Content-Type': 'application/json',
    })
  })

  it('按 event/data 格式解析 delta 事件并拼接增量', async () => {
    const events: string[] = []
    const onEvent = (event: string, data: unknown) => {
      events.push(`${event}:${(data as { content?: string }).content ?? ''}`)
    }
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      createSSEResponse([
        'event: delta\ndata: {"content":"你"}\n\n',
        'event: delta\ndata: {"content":"好"}\n\n',
        'event: result\ndata: {"id":1,"content":"你好"}\n\n',
      ]),
    )
    await fetchSSE('/v1/chat/stream', {}, { onEvent })
    expect(events).toEqual(['delta:你', 'delta:好', 'result:你好'])
  })

  it('数据跨多个网络块（粘包/拆包）时仍正确解析', async () => {
    const events: string[] = []
    const onEvent = (event: string, data: unknown) => {
      events.push(event)
    }
    // 模拟一个事件被拆成两段到达，以及两个事件在同一个块中
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      createSSEResponse([
        'event: delta\ndata: {"content":"', // 前半段
        'a"}\n\nevent: delta\ndata: {"content":"b"}\n\n', // 补齐 + 第二个事件
      ]),
    )
    await fetchSSE('/v1/chat/stream', {}, { onEvent })
    expect(events).toEqual(['delta', 'delta'])
  })

  it('非 JSON 的 data 按纯文本处理', async () => {
    const events: unknown[] = []
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      createSSEResponse(['event: message\ndata: plain-text\n\n']),
    )
    await fetchSSE('/v1/chat/stream', {}, { onEvent: (_, data) => events.push(data) })
    expect(events).toEqual(['plain-text'])
  })

  it('响应非 text/event-stream 时按 JSON 兜底处理并触发 onDone', async () => {
    const events: unknown[] = []
    let done = false
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    await fetchSSE('/v1/chat/stream', {}, {
      onEvent: (_, data) => events.push(data),
      onDone: () => {
        done = true
      },
    })
    expect(events).toEqual([{ ok: true }])
    expect(done).toBe(true)
  })

  it('HTTP 非 2xx 时触发 onError 并解析 detail', async () => {
    const errors: string[] = []
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ detail: '用户名或密码错误' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    await fetchSSE('/v1/chat/stream', {}, { onError: (msg) => errors.push(msg) })
    expect(errors).toEqual(['用户名或密码错误'])
  })

  it('流正常结束时触发 onDone', async () => {
    let done = false
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      createSSEResponse(['event: delta\ndata: {"content":"x"}\n\n']),
    )
    await fetchSSE('/v1/chat/stream', {}, { onDone: () => (done = true) })
    expect(done).toBe(true)
  })

  it('Abort 信号中断时不触发 onError', async () => {
    const errors: string[] = []
    const abortController = new AbortController()
    const encoder = new TextEncoder()
    // 持有 stream controller 的引用，abort 时让流报 AbortError
    let streamController: ReadableStreamDefaultController<Uint8Array> | null = null
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        streamController = controller
        controller.enqueue(encoder.encode('event: delta\ndata: {"content":"x"}\n\n'))
      },
    })
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(stream, {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      }),
    )
    // abort 时让流报错（模拟浏览器 fetch abort 行为：reader.read() 抛 AbortError）
    abortController.signal.addEventListener('abort', () => {
      streamController?.error(new DOMException('Aborted', 'AbortError'))
    })
    const promise = fetchSSE(
      '/v1/chat/stream',
      { signal: abortController.signal },
      { onError: (msg) => errors.push(msg) },
    )
    setTimeout(() => abortController.abort(), 10)
    await promise
    expect(errors).toHaveLength(0)
  })
})
