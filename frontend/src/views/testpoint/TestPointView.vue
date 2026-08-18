<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <span class="page-title">测试点管理</span>
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
          生成 / 重新生成测试点
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
          v-model="category"
          placeholder="全部类别"
          clearable
          style="width: 140px"
          @change="handleSearch"
        >
          <el-option
            v-for="(meta, key) in categoryMeta"
            :key="key"
            :label="meta.label"
            :value="key"
          />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索测试点内容"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">测试点列表（{{ total }}）</span>
      </template>
      <el-table v-loading="loading" :data="items" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column
          prop="name"
          label="测试点"
          min-width="300"
          show-overflow-tooltip
        />
        <el-table-column label="类别" width="110">
          <template #default="{ row }">
            <el-tag :type="categoryMeta[row.category]?.type || 'info'">
              {{ categoryMeta[row.category]?.label || row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module_name" label="所属模块" width="140">
          <template #default="{ row }">
            {{ row.module_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该测试点吗？" @confirm="handleDelete(row)">
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
    <el-dialog v-model="editVisible" title="编辑测试点" width="520px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="内容" prop="name">
          <el-input
            v-model="editForm.name"
            type="textarea"
            :rows="3"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="editForm.category" style="width: 100%">
            <el-option
              v-for="(meta, key) in categoryMeta"
              :key="key"
              :label="meta.label"
              :value="key"
            />
          </el-select>
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
  deleteTestPointApi,
  generateTestPointsStreamApi,
  listTestPointsApi,
  updateTestPointApi,
} from '@/api/testpoint'
import type { Project } from '@/types/project'
import type { Requirement } from '@/types/requirement'
import type { TestPoint, TestPointCategory } from '@/types/testpoint'

const projects = ref<Project[]>([])
const requirements = ref<Requirement[]>([])
const projectId = ref<number | null>(null)
const requirementId = ref<number | null>(null)
const category = ref('')
const keyword = ref('')

const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const items = ref<TestPoint[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10 })
const generateProgress = ref('正在调用 TestPoint Agent 生成测试点...')

// 类别展示映射
const categoryMeta: Record<
  string,
  { label: string; type: 'success' | 'danger' | 'warning' | 'info' | 'primary' }
> = {
  normal: { label: '正常流程', type: 'success' },
  exception: { label: '异常流程', type: 'danger' },
  boundary: { label: '边界值', type: 'warning' },
  security: { label: '安全测试', type: 'info' },
  compatibility: { label: '兼容性', type: 'primary' },
  performance: { label: '性能测试', type: 'warning' },
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
    const data = await listTestPointsApi(projectId.value, {
      page: query.page,
      page_size: query.page_size,
      requirement_id: requirementId.value || undefined,
      category: category.value || undefined,
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

// 生成 / 重新生成测试点
async function handleGenerate() {
  if (!projectId.value || !requirementId.value) {
    ElMessage.warning('请先选择项目和需求文档')
    return
  }
  generating.value = true
  generateProgress.value = '正在调用 TestPoint Agent 按五类维度生成测试点...'
  try {
    await generateTestPointsStreamApi(
      projectId.value,
      requirementId.value,
      {
        onEvent(event, data) {
          if (event === 'status') {
            const stage = data as { message?: string }
            if (stage?.message) generateProgress.value = stage.message
          } else if (event === 'result') {
            const created = data as TestPoint[]
            ElMessage.success(`已生成 ${created.length} 条测试点`)
          }
        },
        onError(message) {
          ElMessage.error(message || '测试点生成失败，请重试')
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
const editForm = reactive({ id: 0, name: '', category: 'normal' as TestPointCategory })
const editRules: FormRules = {
  name: [{ required: true, message: '请输入测试点内容', trigger: 'blur' }],
  category: [{ required: true, message: '请选择类别', trigger: 'change' }],
}

function openEdit(row: TestPoint) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.category = row.category as TestPointCategory
  editVisible.value = true
}

async function handleUpdate() {
  if (!editFormRef.value || !projectId.value) return
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await updateTestPointApi(projectId.value, editForm.id, {
      name: editForm.name,
      category: editForm.category,
    })
    ElMessage.success('保存成功')
    editVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

// 删除
async function handleDelete(row: TestPoint) {
  if (!projectId.value) return
  await deleteTestPointApi(projectId.value, row.id)
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
