<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <span class="page-title">上传需求文档</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>
      <p class="page-desc">
        项目：{{ projectName || projectId }}（ID {{ projectId }}）— 支持
        Word(docx)、PDF、TXT、Markdown
      </p>

      <el-upload
        drag
        :accept="ACCEPT"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击选择文件</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .docx / .pdf / .txt / .md / .markdown，单个文件不超过 20MB
          </div>
        </template>
      </el-upload>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">已上传文档（{{ total }}）</span>
      </template>
      <el-table v-loading="loading" :data="items" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column
          prop="file_name"
          label="文件名"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag>{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.parse_status]?.type || 'info'">
              {{ statusMeta[row.parse_status]?.label || row.parse_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看</el-button>
            <el-popconfirm title="确定删除该文档吗？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadList"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 文档内容详情 -->
    <el-dialog
      v-model="detailVisible"
      :title="detail?.file_name || '文档内容'"
      width="720px"
    >
      <el-alert
        v-if="detail?.parse_status === 'failed'"
        type="error"
        :title="detail?.error_message || '文档解析失败'"
        :closable="false"
        style="margin-bottom: 10px"
      />
      <pre class="content-pre">{{ detail?.content || '（暂无文本内容）' }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type UploadRequestOptions } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getProjectApi } from '@/api/project'
import {
  deleteRequirementApi,
  getRequirementApi,
  listRequirementsApi,
  uploadRequirementApi,
} from '@/api/requirement'
import type { Requirement, RequirementDetail } from '@/types/requirement'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.projectId)

const ACCEPT = '.docx,.pdf,.txt,.md,.markdown'
const MAX_SIZE = 20 * 1024 * 1024

const projectName = ref('')
const loading = ref(false)
const items = ref<Requirement[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10 })

// 解析状态展示映射
const statusMeta: Record<
  string,
  { label: string; type: 'info' | 'warning' | 'success' | 'danger' }
> = {
  pending: { label: '待解析', type: 'info' },
  parsing: { label: '解析中', type: 'warning' },
  completed: { label: '已解析', type: 'success' },
  failed: { label: '解析失败', type: 'danger' },
}

async function loadProject() {
  const project = await getProjectApi(projectId)
  projectName.value = project.name
}

async function loadList() {
  loading.value = true
  try {
    const data = await listRequirementsApi(projectId, query)
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleSizeChange() {
  query.page = 1
  loadList()
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return bytes + ' B'
}

// 上传前校验：类型与大小
function beforeUpload(file: File) {
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
  if (!ACCEPT.split(',').includes(ext)) {
    ElMessage.error('仅支持 Word(docx)、PDF、TXT、Markdown 文件')
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error('文件大小不能超过 20MB')
    return false
  }
  return true
}

async function handleUpload(options: UploadRequestOptions) {
  try {
    const result = await uploadRequirementApi(projectId, options.file)
    ElMessage.success(`上传成功：${result.file_name}`)
    loadList()
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

// 查看文档内容
const detailVisible = ref(false)
const detail = ref<RequirementDetail | null>(null)
async function openDetail(row: Requirement) {
  detail.value = await getRequirementApi(projectId, row.id)
  detailVisible.value = true
}

// 删除文档
async function handleDelete(row: Requirement) {
  await deleteRequirementApi(projectId, row.id)
  ElMessage.success('删除成功')
  if (items.value.length === 1 && query.page > 1) {
    query.page -= 1
  }
  loadList()
}

onMounted(() => {
  loadProject()
  loadList()
})
</script>

<style scoped>
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.content-pre {
  max-height: 60vh;
  margin: 0;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  background-color: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
}
</style>
