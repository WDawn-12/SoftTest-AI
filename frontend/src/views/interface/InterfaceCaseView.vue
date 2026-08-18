<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <span class="page-title">接口测试用例</span>
      </template>

      <!-- 工具栏 -->
      <div class="toolbar">
        <el-select
          v-model="projectId"
          placeholder="选择项目"
          style="width: 220px"
          @change="handleProjectChange"
        >
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!projectId"
          @click="handleGenerate"
        >
          生成 / 重新生成接口用例
        </el-button>
        <el-button type="success" :disabled="!projectId" @click="handleExport">
          导出 Excel
        </el-button>
        <el-button type="warning" :disabled="!projectId" @click="handleExportPostman">
          导出 Postman / Apifox
        </el-button>
      </div>

      <!-- AI 生成进度 -->
      <el-alert
        v-if="generating"
        type="info"
        :closable="false"
        title="正在生成接口测试用例，请稍候..."
        show-icon
        style="margin-top: 12px"
      />

      <!-- 筛选 -->
      <div class="toolbar" style="margin-top: 10px">
        <el-select
          v-model="interfaceId"
          placeholder="全部接口"
          clearable
          style="width: 200px"
          @change="handleSearch"
        >
          <el-option
            v-for="api in interfaces"
            :key="api.id"
            :label="api.name"
            :value="api.id"
          />
        </el-select>
        <el-select
          v-model="category"
          placeholder="全部类别"
          clearable
          style="width: 140px"
          @change="handleSearch"
        >
          <el-option v-for="c in categoryOptions" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索编号 / 标题 / 路径"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">接口测试用例列表（{{ total }}）</span>
      </template>
      <el-table v-loading="loading" :data="items" border stripe>
        <el-table-column prop="case_no" label="编号" width="90" />
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="类别" width="100">
          <template #default="{ row }">
            <el-tag :type="categoryTagType(row.category)">{{ categoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="请求" width="120">
          <template #default="{ row }">
            <el-tag :type="methodTagType(row.method)" size="small">{{ row.method }}</el-tag>
            <span style="margin-left: 4px">{{ row.path }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="expected_status" label="预期状态码" width="100">
          <template #default="{ row }">{{ row.expected_status || '-' }}</template>
        </el-table-column>
        <el-table-column label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="priorityMeta[row.priority]?.type || 'info'">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="interface_name" label="来源接口" width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.interface_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 12px"
        @change="loadData"
      />
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" title="编辑接口测试用例" width="620px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="editForm.category" style="width: 160px">
            <el-option v-for="c in categoryOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="editForm.priority" style="width: 120px">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="预期状态码">
          <el-input v-model="editForm.expected_status" placeholder="如：200 / 400 / 401" />
        </el-form-item>
        <el-form-item label="测试数据">
          <el-input v-model="editForm.test_data" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="请求参数/体">
          <el-input v-model="editForm.request_payload" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="editForm.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="测试步骤">
          <el-input v-model="editForm.steps" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="预期结果">
          <el-input v-model="editForm.expected_result" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProjectsApi } from '@/api/project'
import { listInterfacesApi } from '@/api/interfaceTest'
import type { ApiInterface, InterfaceCase } from '@/types/interfaceTest'
import {
  deleteInterfaceCaseApi,
  exportInterfaceCasesApi,
  exportInterfaceCasesPostmanApi,
  generateInterfaceCasesApi,
  listInterfaceCasesApi,
  updateInterfaceCaseApi,
} from '@/api/interfaceTest'

const projects = ref<{ id: number; name: string }[]>([])
const interfaces = ref<ApiInterface[]>([])
const projectId = ref<number | null>(null)
const interfaceId = ref<number | null>(null)
const category = ref('')
const keyword = ref('')
const items = ref<InterfaceCase[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)

const dialogVisible = ref(false)
const editForm = reactive({
  title: '',
  category: 'normal',
  priority: '中' as '高' | '中' | '低',
  expected_status: '',
  test_data: '',
  request_payload: '',
  preconditions: '',
  steps: '',
  expected_result: '',
  remark: '',
})
let editingId: number | null = null

const categoryOptions = [
  { value: 'normal', label: '正常流程' },
  { value: 'exception', label: '异常流程' },
  { value: 'boundary', label: '边界值' },
  { value: 'security', label: '安全测试' },
  { value: 'parameter', label: '参数组合' },
]

const priorityMeta: Record<string, { type: string }> = {
  高: { type: 'danger' },
  中: { type: 'warning' },
  低: { type: 'info' },
}

function categoryLabel(cat: string) {
  return categoryOptions.find((c) => c.value === cat)?.label || cat
}

function categoryTagType(cat: string) {
  const map: Record<string, string> = {
    normal: 'success',
    exception: 'danger',
    boundary: 'warning',
    security: 'danger',
    parameter: 'info',
  }
  return map[cat] || 'info'
}

function methodTagType(method: string) {
  const map: Record<string, string> = {
    GET: 'success',
    POST: 'warning',
    PUT: 'primary',
    DELETE: 'danger',
    PATCH: 'info',
  }
  return map[method] || 'info'
}

async function loadProjects() {
  try {
    const data = await listProjectsApi({ page: 1, page_size: 100 })
    projects.value = data.items
    if (data.items.length && !projectId.value) {
      projectId.value = data.items[0].id
      loadData()
      loadInterfaces()
    }
  } catch {
    // 已由拦截器提示
  }
}

async function loadInterfaces() {
  if (!projectId.value) return
  try {
    const data = await listInterfacesApi(projectId.value, { page: 1, page_size: 100 })
    interfaces.value = data.items
  } catch {
    // 已由拦截器提示
  }
}

async function loadData() {
  if (!projectId.value) return
  loading.value = true
  try {
    const data = await listInterfaceCasesApi(projectId.value, {
      page: page.value,
      page_size: pageSize.value,
      interface_id: interfaceId.value || undefined,
      category: category.value || undefined,
      keyword: keyword.value || undefined,
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleProjectChange() {
  page.value = 1
  loadData()
  loadInterfaces()
}

function handleSearch() {
  page.value = 1
  loadData()
}

async function handleGenerate() {
  if (!projectId.value) return
  generating.value = true
  try {
    const result = await generateInterfaceCasesApi(projectId.value)
    ElMessage.success(`生成成功，共 ${result.length} 条接口用例`)
    page.value = 1
    loadData()
  } catch {
    // 已由拦截器提示
  } finally {
    generating.value = false
  }
}

async function handleExport() {
  if (!projectId.value) return
  try {
    const blob = await exportInterfaceCasesApi(projectId.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'interface_test_cases.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    // 已由拦截器提示
  }
}

async function handleExportPostman() {
  if (!projectId.value) return
  try {
    const blob = await exportInterfaceCasesPostmanApi(projectId.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'interface_test_cases.postman_collection.json'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(
      '已导出 Postman Collection，导入后配置环境变量 base_url 即可使用',
    )
  } catch {
    // 已由拦截器提示
  }
}

function openEdit(row: InterfaceCase) {
  editingId = row.id
  Object.assign(editForm, {
    title: row.title,
    category: row.category,
    priority: (row.priority as '高' | '中' | '低') || '中',
    expected_status: row.expected_status || '',
    test_data: row.test_data || '',
    request_payload: row.request_payload || '',
    preconditions: row.preconditions || '',
    steps: row.steps || '',
    expected_result: row.expected_result || '',
    remark: row.remark || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!projectId.value || editingId === null) return
  saving.value = true
  try {
    await updateInterfaceCaseApi(projectId.value, editingId, {
      ...editForm,
      expected_status: editForm.expected_status || undefined,
      test_data: editForm.test_data || undefined,
      request_payload: editForm.request_payload || undefined,
      preconditions: editForm.preconditions || undefined,
      steps: editForm.steps || undefined,
      expected_result: editForm.expected_result || undefined,
      remark: editForm.remark || undefined,
    })
    ElMessage.success('已保存')
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: InterfaceCase) {
  if (!projectId.value) return
  try {
    await ElMessageBox.confirm(`确定删除用例「${row.case_no} ${row.title}」吗？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  await deleteInterfaceCaseApi(projectId.value, row.id)
  ElMessage.success('用例已删除')
  loadData()
}

onMounted(loadProjects)
</script>

<style scoped>
.page {
  padding: 16px;
}
.page-title {
  font-weight: 600;
}
.toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
