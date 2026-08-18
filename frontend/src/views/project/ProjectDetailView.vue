<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <span class="page-title">项目详情</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>

      <!-- 项目基本信息 -->
      <el-descriptions v-if="project" title="项目信息" :column="2" border>
        <el-descriptions-item label="项目名称">{{ project.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusMeta[project.status]?.type || 'info'">
            {{ statusMeta[project.status]?.label || project.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="项目描述" :span="2">
          {{ project.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
      </el-descriptions>

      <!-- 被测系统信息 -->
      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <div class="list-header">
            <span class="section-title">被测系统信息</span>
            <div>
              <el-button size="small" @click="openSutDialog">
                {{ sut ? '编辑' : '配置' }}
              </el-button>
            </div>
          </div>
        </template>

        <el-empty
          v-if="!sut"
          description="该项目尚未配置被测系统，点击右上角「配置」"
        />

        <template v-else>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统名称">{{ sut.system_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="系统类型">{{ sut.system_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="测试网址">
              <span class="url-text">{{ sut.test_url || '-' }}</span>
              <el-button
                v-if="sut.test_url"
                link
                type="primary"
                size="small"
                @click="copyUrl"
              >
                复制网址
              </el-button>
            </el-descriptions-item>
            <el-descriptions-item label="浏览器">{{ sut.browser_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="测试账号">{{ sut.login_username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="系统描述">{{ sut.system_description || '-' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button type="primary" :loading="testing" @click="handleTestConnection">
              测试连接
            </el-button>
            <el-button @click="openSite">打开网站</el-button>
            <el-button type="success" @click="goParse">AI解析需求</el-button>
            <el-button type="warning" :loading="generatingPoints" @click="handleGeneratePoints">
              生成测试点
            </el-button>
            <el-button type="danger" :loading="generatingCases" @click="handleGenerateCases">
              生成测试用例
            </el-button>
          </div>

          <el-alert
            v-if="connectionResult"
            :type="connectionResult.success ? 'success' : 'error'"
            :closable="false"
            :title="connectionResult.message"
            style="margin-top: 12px"
          />
        </template>
      </el-card>
    </el-card>

    <!-- 被测系统编辑弹窗 -->
    <el-dialog
      v-model="sutDialogVisible"
      :title="sut ? '编辑被测系统' : '配置被测系统'"
      width="560px"
    >
      <el-form ref="sutFormRef" :model="sutForm" :rules="sutRules" label-width="110px">
        <el-form-item label="系统名称" prop="system_name">
          <el-input v-model="sutForm.system_name" maxlength="100" />
        </el-form-item>
        <el-form-item label="测试网址(URL)" prop="test_url">
          <el-input v-model="sutForm.test_url" maxlength="500" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="系统类型" prop="system_type">
          <el-select v-model="sutForm.system_type" style="width: 100%">
            <el-option v-for="t in systemTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器" prop="browser_type">
          <el-select v-model="sutForm.browser_type" style="width: 100%">
            <el-option v-for="b in browserTypes" :key="b" :label="b" :value="b" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试账号" prop="login_username">
          <el-input v-model="sutForm.login_username" maxlength="100" />
        </el-form-item>
        <el-form-item label="测试密码" prop="login_password">
          <el-input
            v-model="sutForm.login_password"
            type="password"
            show-password
            maxlength="200"
            placeholder="留空表示保持原密码"
          />
        </el-form-item>
        <el-form-item label="系统描述" prop="system_description">
          <el-input v-model="sutForm.system_description" type="textarea" :rows="3" maxlength="2000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sutDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSut" @click="handleSaveSut">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { getProjectApi } from '@/api/project'
import { listRequirementsApi } from '@/api/requirement'
import { generateTestCasesStreamApi } from '@/api/testcase'
import { generateTestPointsStreamApi } from '@/api/testpoint'
import {
  createSutApi,
  getSutApi,
  testConnectionApi,
  updateSutApi,
} from '@/api/sut'
import type { Project } from '@/types/project'
import type { TestCase } from '@/types/testcase'
import type { TestPoint } from '@/types/testpoint'
import type { SutInfo, SystemType, BrowserType, TestConnectionResult } from '@/types/sut'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.projectId)

const project = ref<Project | null>(null)
const sut = ref<SutInfo | null>(null)
const connectionResult = ref<TestConnectionResult | null>(null)
const testing = ref(false)
const generatingPoints = ref(false)
const generatingCases = ref(false)

const systemTypes: SystemType[] = ['Web后台', 'Web网站', '微信小程序', 'Android', 'iOS']
const browserTypes: BrowserType[] = ['Chrome', 'Edge', 'Firefox']

const statusMeta: Record<string, { label: string; type: 'success' | 'info' | 'warning' }> = {
  active: { label: '进行中', type: 'success' },
  finished: { label: '已完成', type: 'info' },
  archived: { label: '已归档', type: 'warning' },
}

async function loadProject() {
  project.value = await getProjectApi(projectId)
}

async function loadSut() {
  try {
    sut.value = await getSutApi(projectId)
  } catch {
    sut.value = null
  }
}

// ---------- 测试连接 / 打开 / 复制 ----------
async function handleTestConnection() {
  testing.value = true
  try {
    connectionResult.value = await testConnectionApi(projectId)
    ElMessage[connectionResult.value.success ? 'success' : 'error'](
      connectionResult.value.message,
    )
  } finally {
    testing.value = false
  }
}

function openSite() {
  if (sut.value?.test_url) {
    window.open(sut.value.test_url, '_blank', 'noopener')
  }
}

async function copyUrl() {
  if (!sut.value?.test_url) return
  try {
    await navigator.clipboard.writeText(sut.value.test_url)
    ElMessage.success('网址已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// ---------- AI 操作 ----------
function goParse() {
  router.push(`/projects/${projectId}/requirement/result`)
}

async function ensureRequirement(): Promise<number | null> {
  const data = await listRequirementsApi(projectId, { page: 1, page_size: 1 })
  if (data.items.length === 0) {
    ElMessage.warning('该项目还没有需求文档，请先上传')
    return null
  }
  return data.items[0].id
}

async function handleGeneratePoints() {
  const rid = await ensureRequirement()
  if (!rid) return
  generatingPoints.value = true
  try {
    await generateTestPointsStreamApi(
      projectId,
      rid,
      {
        onEvent(event, data) {
          if (event === 'result') {
            ElMessage.success(`已生成 ${(data as TestPoint[]).length} 条测试点`)
          }
        },
        onError(message) {
          ElMessage.error(message || '测试点生成失败，请重试')
        },
      },
    )
  } finally {
    generatingPoints.value = false
  }
}

async function handleGenerateCases() {
  const rid = await ensureRequirement()
  if (!rid) return
  generatingCases.value = true
  try {
    await generateTestCasesStreamApi(
      projectId,
      rid,
      {
        onEvent(event, data) {
          if (event === 'result') {
            const created = data as TestCase[]
            const range =
              created.length > 1
                ? `${created[0].case_no} - ${created[created.length - 1].case_no}`
                : created[0]?.case_no || ''
            ElMessage.success(`已生成 ${created.length} 条测试用例${range ? `（${range}）` : ''}`)
          }
        },
        onError(message) {
          ElMessage.error(message || '测试用例生成失败，请重试')
        },
      },
    )
  } finally {
    generatingCases.value = false
  }
}

// ---------- 被测系统编辑 ----------
const sutDialogVisible = ref(false)
const sutFormRef = ref<FormInstance>()
const savingSut = ref(false)
const sutForm = reactive({
  system_name: '',
  test_url: '',
  system_type: 'Web网站' as SystemType,
  browser_type: 'Chrome' as BrowserType,
  login_username: '',
  login_password: '',
  system_description: '',
})
const sutRules: FormRules = {
  system_name: [{ required: true, message: '请输入系统名称', trigger: 'blur' }],
  test_url: [
    { required: true, message: '请输入测试网址', trigger: 'blur' },
    {
      validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
        if (value && !/^https?:\/\/.+/i.test(value)) {
          callback(new Error('测试网址必须以 http:// 或 https:// 开头'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  system_type: [{ required: true, message: '请选择系统类型', trigger: 'change' }],
  browser_type: [{ required: true, message: '请选择浏览器', trigger: 'change' }],
}

function openSutDialog() {
  sutForm.system_name = sut.value?.system_name || ''
  sutForm.test_url = sut.value?.test_url || ''
  sutForm.system_type = (sut.value?.system_type as SystemType) || 'Web网站'
  sutForm.browser_type = (sut.value?.browser_type as BrowserType) || 'Chrome'
  sutForm.login_username = sut.value?.login_username || ''
  sutForm.login_password = ''
  sutForm.system_description = sut.value?.system_description || ''
  sutDialogVisible.value = true
}

async function handleSaveSut() {
  if (!sutFormRef.value) return
  const valid = await sutFormRef.value.validate().catch(() => false)
  if (!valid) return
  savingSut.value = true
  try {
    const payload = {
      system_name: sutForm.system_name,
      test_url: sutForm.test_url,
      system_type: sutForm.system_type,
      browser_type: sutForm.browser_type,
      login_username: sutForm.login_username || undefined,
      login_password: sutForm.login_password || undefined,
      system_description: sutForm.system_description || undefined,
    }
    if (sut.value) {
      sut.value = await updateSutApi(projectId, payload)
    } else {
      sut.value = await createSutApi(projectId, payload)
    }
    ElMessage.success('被测系统已保存')
    sutDialogVisible.value = false
  } finally {
    savingSut.value = false
  }
}

onMounted(() => {
  loadProject()
  loadSut()
})
</script>

<style scoped>
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
}

.url-text {
  margin-right: 8px;
  word-break: break-all;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}
</style>
