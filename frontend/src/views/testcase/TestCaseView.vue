<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <span class="page-title">测试用例管理</span>
      </template>

      <!-- 选择项目与需求 + 生成 -->
      <div class="toolbar">
        <el-select
          v-model="projectId"
          placeholder="选择项目"
          style="width: 200px"
          @change="handleProjectChange"
        >
          <el-option
            v-for="p in projects"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>
        <el-select
          v-model="requirementId"
          placeholder="选择需求文档（可空）"
          clearable
          style="width: 240px"
          @change="handleRequirementChange"
        >
          <el-option
            v-for="r in requirements"
            :key="r.id"
            :label="r.file_name"
            :value="r.id"
          />
        </el-select>
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!projectId || !requirementId"
          @click="handleGenerate"
        >
          生成 / 重新生成测试用例
        </el-button>
      </div>

      <!-- AI 生成进度 -->
      <el-alert
        v-if="generating"
        type="info"
        :closable="false"
        :title="generateProgress"
        show-icon
        style="margin-top: 12px"
      />

      <!-- 筛选 -->
      <div class="toolbar" style="margin-top: 10px">
        <el-select
          v-model="priority"
          placeholder="全部优先级"
          clearable
          style="width: 140px"
          @change="handleSearch"
        >
          <el-option label="高" value="高" />
          <el-option label="中" value="中" />
          <el-option label="低" value="低" />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索编号 / 功能 / 测试点"
          clearable
          style="width: 260px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button
          type="success"
          :disabled="!projectId"
          :loading="exporting"
          @click="handleExport"
        >
          导出 Excel
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">测试用例列表（{{ total }}）</span>
      </template>
      <el-table v-loading="loading" :data="items" border stripe>
        <el-table-column prop="case_no" label="编号" width="90" />
        <el-table-column prop="title" label="功能" min-width="140" show-overflow-tooltip />
        <el-table-column
          prop="test_point"
          label="测试点"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="priorityMeta[row.priority]?.type || 'info'">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module_name" label="模块" width="120">
          <template #default="{ row }">{{ row.module_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag type="info">{{ row.status === 'draft' ? '草稿' : row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="165" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该测试用例吗？" @confirm="handleDelete(row)">
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

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑测试用例" width="640px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="90px">
        <el-form-item label="编号">
          <el-input :model-value="editForm.case_no" disabled />
        </el-form-item>
        <el-form-item label="功能" prop="title">
          <el-input v-model="editForm.title" maxlength="200" />
        </el-form-item>
        <el-form-item label="测试点" prop="test_point">
          <el-input v-model="editForm.test_point" maxlength="500" />
        </el-form-item>
        <el-form-item label="测试数据" prop="test_data">
          <el-input v-model="editForm.test_data" maxlength="500" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="editForm.priority" style="width: 100%">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="前置条件" prop="preconditions">
          <el-input v-model="editForm.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="测试步骤" prop="steps">
          <el-input
            v-model="editForm.steps"
            type="textarea"
            :rows="4"
            placeholder="每行一个步骤，可包含测试数据"
          />
        </el-form-item>
        <el-form-item label="预期结果" prop="expected_result">
          <el-input v-model="editForm.expected_result" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="editForm.remark" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProjectsApi } from '@/api/project'
import { listRequirementsApi } from '@/api/requirement'
import {
  deleteTestCaseApi,
  exportTestCasesApi,
  generateTestCasesStreamApi,
  listTestCasesApi,
  updateTestCaseApi,
} from '@/api/testcase'
import type { Project } from '@/types/project'
import type { Requirement } from '@/types/requirement'
import type { TestCase, TestCasePriority } from '@/types/testcase'

const projects = ref<Project[]>([])
const requirements = ref<Requirement[]>([])
const projectId = ref<number | null>(null)
const requirementId = ref<number | null>(null)
const priority = ref('')
const keyword = ref('')

const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const exporting = ref(false)
const items = ref<TestCase[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10 })
const generateProgress = ref('正在调用 TestCase Agent 生成测试用例...')

// 优先级展示映射
const priorityMeta: Record<string, { type: 'danger' | 'warning' | 'info' }> = {
  高: { type: 'danger' },
  中: { type: 'warning' },
  低: { type: 'info' },
}

async function loadProjects() {
  const data = await listProjectsApi({ page: 1, page_size: 100 })
  projects.value = data.items
}

async function handleProjectChange() {
  requirementId.value = null
  requirements.value = []
  query.page = 1
  if (projectId.value) {
    const data = await listRequirementsApi(projectId.value, { page: 1, page_size: 50 })
    requirements.value = data.items
  }
  loadList()
}

function handleRequirementChange() {
  query.page = 1
  loadList()
}

async function loadList() {
  if (!projectId.value) return
  loading.value = true
  try {
    const data = await listTestCasesApi(projectId.value, {
      page: query.page,
      page_size: query.page_size,
      requirement_id: requirementId.value || undefined,
      priority: priority.value || undefined,
      keyword: keyword.value || undefined,
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  loadList()
}

function handleSizeChange() {
  query.page = 1
  loadList()
}

// 生成 / 重新生成
async function handleGenerate() {
  if (!projectId.value || !requirementId.value) {
    ElMessage.warning('请先选择项目和需求文档')
    return
  }
  generating.value = true
  generateProgress.value = '正在调用 TestCase Agent 生成测试用例（含测试数据）...'
  try {
    await generateTestCasesStreamApi(
      projectId.value,
      requirementId.value,
      {
        onEvent(event, data) {
          if (event === 'status') {
            const stage = data as { message?: string }
            if (stage?.message) generateProgress.value = stage.message
          } else if (event === 'result') {
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
    loadList()
  } finally {
    generating.value = false
  }
}

// 编辑
const editVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  id: 0,
  case_no: '',
  title: '',
  test_point: '',
  test_data: '',
  priority: '中' as TestCasePriority,
  preconditions: '',
  steps: '',
  expected_result: '',
  remark: '',
})
const editRules: FormRules = {
  title: [{ required: true, message: '请输入功能名称', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
}

function openEdit(row: TestCase) {
  editForm.id = row.id
  editForm.case_no = row.case_no
  editForm.title = row.title
  editForm.test_point = row.test_point || ''
  editForm.test_data = row.test_data || ''
  editForm.priority = row.priority as TestCasePriority
  editForm.preconditions = row.preconditions || ''
  editForm.steps = row.steps || ''
  editForm.expected_result = row.expected_result || ''
  editForm.remark = row.remark || ''
  editVisible.value = true
}

async function handleUpdate() {
  if (!editFormRef.value || !projectId.value) return
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await updateTestCaseApi(projectId.value, editForm.id, {
      title: editForm.title,
      test_point: editForm.test_point || undefined,
      test_data: editForm.test_data || undefined,
      priority: editForm.priority,
      preconditions: editForm.preconditions || undefined,
      steps: editForm.steps || undefined,
      expected_result: editForm.expected_result || undefined,
      remark: editForm.remark || undefined,
    })
    ElMessage.success('保存成功')
    editVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

// 导出 Excel（按当前筛选批量导出）
async function handleExport() {
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  exporting.value = true
  try {
    const blob = await exportTestCasesApi(projectId.value, {
      requirement_id: requirementId.value || undefined,
      priority: priority.value || undefined,
      keyword: keyword.value || undefined,
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `测试用例_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

// 删除
async function handleDelete(row: TestCase) {
  if (!projectId.value) return
  await deleteTestCaseApi(projectId.value, row.id)
  ElMessage.success('删除成功')
  if (items.value.length === 1 && query.page > 1) {
    query.page -= 1
  }
  loadList()
}

onMounted(loadProjects)
</script>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
