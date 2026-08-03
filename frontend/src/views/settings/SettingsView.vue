<template>
  <div class="page">
    <el-alert
      v-if="!isAdmin"
      type="warning"
      :closable="false"
      title="系统设置仅管理员可访问"
      description="当前账号为普通用户，无法查看和修改系统设置。"
      show-icon
    />

    <el-card v-else shadow="never">
      <template #header>
        <span class="page-title">系统设置</span>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 模型配置 / API Key -->
        <el-tab-pane label="模型配置" name="model">
          <el-form :model="modelForm" label-width="160px" style="max-width: 640px">
            <el-form-item label="AI 供应商">
              <el-select v-model="modelForm.ai_provider" style="width: 100%">
                <el-option label="OpenAI" value="openai" />
                <el-option label="DeepSeek" value="deepseek" />
                <el-option label="演示模式（无需 Key）" value="demo" />
              </el-select>
            </el-form-item>
            <el-divider content-position="left">OpenAI</el-divider>
            <el-form-item label="API Key">
              <el-input v-model="modelForm.openai_api_key" type="password" show-password placeholder="sk-..." />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="modelForm.openai_base_url" />
            </el-form-item>
            <el-form-item label="模型">
              <el-input v-model="modelForm.openai_model" />
            </el-form-item>
            <el-divider content-position="left">DeepSeek</el-divider>
            <el-form-item label="API Key">
              <el-input v-model="modelForm.deepseek_api_key" type="password" show-password placeholder="sk-..." />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="modelForm.deepseek_base_url" />
            </el-form-item>
            <el-form-item label="模型">
              <el-input v-model="modelForm.deepseek_model" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingModel" @click="handleSaveModel">
                保存模型配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Prompt 模板 -->
        <el-tab-pane label="Prompt 模板" name="prompt">
          <el-form label-width="160px" style="max-width: 900px">
            <el-form-item label="需求解析模板">
              <el-input v-model="promptForm.prompt_requirement" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item label="测试点模板">
              <el-input v-model="promptForm.prompt_testpoint" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item label="测试用例模板">
              <el-input v-model="promptForm.prompt_testcase" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item label="聊天助手模板">
              <el-input v-model="promptForm.prompt_chat" type="textarea" :rows="6" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingPrompt" @click="handleSavePrompt">
                保存 Prompt 模板
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 操作日志 -->
        <el-tab-pane label="操作日志" name="operations">
          <div class="toolbar">
            <el-input
              v-model="opKeyword"
              placeholder="搜索动作 / 模块 / 详情"
              clearable
              style="width: 260px"
              @keyup.enter="loadOperations"
              @clear="loadOperations"
            />
            <el-button type="primary" @click="loadOperations">搜索</el-button>
          </div>
          <el-table v-loading="loadingOps" :data="opItems" border stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="created_at" label="时间" width="170" />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="module" label="模块" width="100" />
            <el-table-column prop="action" label="动作" min-width="180" />
            <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
            <el-table-column prop="ip" label="IP" width="130" />
          </el-table>
          <div class="pager">
            <el-pagination
              v-model:current-page="opQuery.page"
              v-model:page-size="opQuery.page_size"
              :total="opTotal"
              layout="total, prev, pager, next"
              @current-change="loadOperations"
            />
          </div>
        </el-tab-pane>

        <!-- AI 调用日志 -->
        <el-tab-pane label="AI 调用日志" name="ai">
          <el-table v-loading="loadingAi" :data="aiItems" border stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="created_at" label="时间" width="170" />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="agent" label="Agent" width="110" />
            <el-table-column prop="provider" label="供应商" width="90" />
            <el-table-column prop="prompt_length" label="输入长度" width="90" />
            <el-table-column prop="response_length" label="输出长度" width="90" />
            <el-table-column prop="duration_ms" label="耗时(ms)" width="90" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" min-width="180" show-overflow-tooltip />
          </el-table>
          <div class="pager">
            <el-pagination
              v-model:current-page="aiQuery.page"
              v-model:page-size="aiQuery.page_size"
              :total="aiTotal"
              layout="total, prev, pager, next"
              @current-change="loadAiLogs"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  getSystemSettingsApi,
  listAiCallLogsApi,
  listOperationLogsApi,
  updateSystemSettingsApi,
} from '@/api/system'
import type { AiCallLogItem, OperationLogItem } from '@/types/system'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')
const activeTab = ref('model')

// ---------- 模型配置 ----------
const modelForm = reactive({
  ai_provider: 'demo',
  openai_api_key: '',
  openai_base_url: '',
  openai_model: '',
  deepseek_api_key: '',
  deepseek_base_url: '',
  deepseek_model: '',
})
const savingModel = ref(false)

// ---------- Prompt 模板 ----------
const promptForm = reactive({
  prompt_requirement: '',
  prompt_testpoint: '',
  prompt_testcase: '',
  prompt_chat: '',
})
const savingPrompt = ref(false)

// ---------- 操作日志 ----------
const loadingOps = ref(false)
const opItems = ref<OperationLogItem[]>([])
const opTotal = ref(0)
const opKeyword = ref('')
const opQuery = reactive({ page: 1, page_size: 10 })

// ---------- AI 调用日志 ----------
const loadingAi = ref(false)
const aiItems = ref<AiCallLogItem[]>([])
const aiTotal = ref(0)
const aiQuery = reactive({ page: 1, page_size: 10 })

async function loadSettings() {
  if (!isAdmin.value) return
  const { settings } = await getSystemSettingsApi()
  for (const key of Object.keys(modelForm)) {
    modelForm[key as keyof typeof modelForm] = settings[key] ?? ''
  }
  for (const key of Object.keys(promptForm)) {
    promptForm[key as keyof typeof promptForm] = settings[key] ?? ''
  }
}

async function handleSaveModel() {
  savingModel.value = true
  try {
    await updateSystemSettingsApi({ ...modelForm })
    ElMessage.success('模型配置已保存')
  } finally {
    savingModel.value = false
  }
}

async function handleSavePrompt() {
  savingPrompt.value = true
  try {
    await updateSystemSettingsApi({ ...promptForm })
    ElMessage.success('Prompt 模板已保存')
  } finally {
    savingPrompt.value = false
  }
}

async function loadOperations() {
  loadingOps.value = true
  try {
    const data = await listOperationLogsApi({
      page: opQuery.page,
      page_size: opQuery.page_size,
      keyword: opKeyword.value || undefined,
    })
    opItems.value = data.items
    opTotal.value = data.total
  } finally {
    loadingOps.value = false
  }
}

async function loadAiLogs() {
  loadingAi.value = true
  try {
    const data = await listAiCallLogsApi({
      page: aiQuery.page,
      page_size: aiQuery.page_size,
    })
    aiItems.value = data.items
    aiTotal.value = data.total
  } finally {
    loadingAi.value = false
  }
}

onMounted(async () => {
  await loadSettings()
  await loadOperations()
  await loadAiLogs()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
