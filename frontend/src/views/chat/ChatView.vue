<template>
  <div class="page">
    <el-card shadow="never" class="chat-card">
      <template #header>
        <div class="list-header">
          <span class="page-title">AI 聊天助手</span>
          <div class="header-actions">
            <el-select
              v-model="projectId"
              placeholder="选择项目（用于知识问答）"
              clearable
              style="width: 240px"
              @change="handleProjectChange"
            >
              <el-option
                v-for="p in projects"
                :key="p.id"
                :label="p.name"
                :value="p.id"
              />
            </el-select>
            <el-button :disabled="!projectId || messages.length === 0" @click="handleClear">
              清空聊天
            </el-button>
          </div>
        </div>
      </template>

      <!-- 消息区 -->
      <div ref="messageListRef" v-loading="loadingHistory" class="message-list">
        <el-empty
          v-if="messages.length === 0"
          description="开始和 AI 助手对话吧（可基于需求文档与测试用例问答，支持 Markdown）"
        />
        <div
          v-for="m in messages"
          :key="m.id"
          class="message-row"
          :class="m.role"
        >
          <div class="bubble" :class="m.role">
            <div v-if="m.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(m.content)" />
            <div v-else class="user-text">{{ m.content }}</div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="draft"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="输入问题，Enter 发送，Shift+Enter 换行"
          @keydown.enter.exact.prevent="handleSend"
        />
        <div class="input-actions">
          <el-button
            type="primary"
            :loading="sending"
            :disabled="!draft.trim() || !projectId"
            @click="handleSend"
          >
            发送
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { listProjectsApi } from '@/api/project'
import {
  clearChatHistoryApi,
  getChatHistoryApi,
  sendChatMessageApi,
} from '@/api/chat'
import type { ChatMessage } from '@/types/chat'
import type { Project } from '@/types/project'

const projects = ref<Project[]>([])
const projectId = ref<number | null>(null)
const messages = ref<ChatMessage[]>([])
const draft = ref('')
const sending = ref(false)
const loadingHistory = ref(false)
const messageListRef = ref<HTMLElement>()

// 渲染 Markdown（先解析再消毒，防止 XSS）
function renderMarkdown(text: string): string {
  return DOMPurify.sanitize(marked.parse(text) as string)
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

async function loadProjects() {
  const data = await listProjectsApi({ page: 1, page_size: 100 })
  projects.value = data.items
}

async function handleProjectChange() {
  messages.value = []
  if (!projectId.value) return
  loadingHistory.value = true
  try {
    const data = await getChatHistoryApi(projectId.value, {
      page: 1,
      page_size: 100,
    })
    messages.value = data.items
    scrollToBottom()
  } finally {
    loadingHistory.value = false
  }
}

async function handleSend() {
  const content = draft.value.trim()
  if (!content || !projectId.value || sending.value) return
  draft.value = ''
  sending.value = true
  try {
    await sendChatMessageApi(projectId.value, content)
    const data = await getChatHistoryApi(projectId.value, {
      page: 1,
      page_size: 100,
    })
    messages.value = data.items
    scrollToBottom()
  } finally {
    sending.value = false
  }
}

async function handleClear() {
  if (!projectId.value) return
  try {
    await ElMessageBox.confirm('确定清空当前项目的聊天记录吗？', '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  await clearChatHistoryApi(projectId.value)
  messages.value = []
  ElMessage.success('聊天记录已清空')
}

onMounted(loadProjects)
</script>

<style scoped>
.chat-card {
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.message-list {
  height: 56vh;
  overflow-y: auto;
  padding: 8px 4px;
}

.message-row {
  display: flex;
  margin-bottom: 14px;
}

.message-row.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.7;
}

.bubble.user {
  background-color: #409eff;
  color: #fff;
}

.bubble.assistant {
  background-color: #f4f4f5;
  color: #303133;
}

.user-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.input-area {
  margin-top: 12px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>

<style>
/* Markdown 回复样式（非 scoped，作用于 v-html 内容） */
.markdown-body p {
  margin: 4px 0;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin: 10px 0 6px;
}

.markdown-body ul,
.markdown-body ol {
  margin: 4px 0;
  padding-left: 22px;
}

.markdown-body code {
  padding: 2px 5px;
  background-color: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  font-family: Consolas, Monaco, monospace;
}

.markdown-body pre {
  padding: 10px;
  overflow-x: auto;
  background-color: #282c34;
  border-radius: 6px;
}

.markdown-body pre code {
  padding: 0;
  background: none;
  color: #e6e6e6;
}

.markdown-body blockquote {
  margin: 6px 0;
  padding-left: 10px;
  color: #909399;
  border-left: 3px solid #dcdfe6;
}

.markdown-body table {
  border-collapse: collapse;
}

.markdown-body th,
.markdown-body td {
  padding: 4px 10px;
  border: 1px solid #dcdfe6;
}
</style>
