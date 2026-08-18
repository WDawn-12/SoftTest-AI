<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <span class="page-title">接口管理</span>
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
        <el-input
          v-model="keyword"
          placeholder="搜索接口名称 / 路径"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button type="success" :disabled="!projectId" @click="showCreateDialog">
          新增接口
        </el-button>
        <el-button :disabled="!projectId" @click="showImportDialog">
          导入 OpenAPI
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">接口列表（{{ total }}）</span>
      </template>
      <el-table v-loading="loading" :data="items" border stripe>
        <el-table-column prop="name" label="接口名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="方法" width="90">
          <template #default="{ row }">
            <el-tag :type="methodTagType(row.method)">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="220" show-overflow-tooltip />
        <el-table-column prop="summary" label="描述" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.summary || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑接口' : '新增接口'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="接口名称" prop="name">
          <el-input v-model="form.name" placeholder="如：用户搜索接口" />
        </el-form-item>
        <el-form-item label="请求方法" prop="method">
          <el-select v-model="form.method" style="width: 160px">
            <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="接口路径" prop="path">
          <el-input v-model="form.path" placeholder="如：/api/users/search（路径参数用 {id}）" />
        </el-form-item>
        <el-form-item label="接口描述">
          <el-input v-model="form.summary" type="textarea" :rows="2" placeholder="接口用途说明" />
        </el-form-item>
        <el-form-item label="请求头">
          <el-input v-model="form.headers" type="textarea" :rows="2" placeholder='JSON 文本，如 {"Content-Type":"application/json"}' />
        </el-form-item>
        <el-form-item label="查询参数">
          <el-input v-model="form.params" type="textarea" :rows="2" placeholder='JSON 数组，如 [{"name":"keyword","in":"query","required":true}]' />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input v-model="form.body" type="textarea" :rows="3" placeholder='JSON 文本，如 {"username":"string","password":"string"}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- OpenAPI 导入弹窗 -->
    <el-dialog v-model="importVisible" title="导入 OpenAPI（Swagger）JSON" width="600px">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="粘贴 OpenAPI 3.x / Swagger 2.0 的 JSON 文档，系统将自动提取全部接口（方法 + 路径 + 参数）。"
        style="margin-bottom: 12px"
      />
      <el-input
        v-model="importSpec"
        type="textarea"
        :rows="12"
        placeholder='{"openapi":"3.0.0","paths":{"/api/users":{...}}}'
      />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProjectsApi } from '@/api/project'
import type { ApiInterface, ApiInterfacePayload } from '@/types/interfaceTest'
import {
  createInterfaceApi,
  deleteInterfaceApi,
  importOpenApiApi,
  listInterfacesApi,
  updateInterfaceApi,
} from '@/api/interfaceTest'

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] as const

const projects = ref<{ id: number; name: string }[]>([])
const projectId = ref<number | null>(null)
const keyword = ref('')
const items = ref<ApiInterface[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const dialogVisible = ref(false)
const importVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const importing = ref(false)
const importSpec = ref('')

const formRef = ref<FormInstance>()
const form = reactive<ApiInterfacePayload>({
  name: '',
  method: 'GET',
  path: '',
  summary: '',
  headers: '',
  params: '',
  body: '',
})
const formRules: FormRules = {
  name: [{ required: true, message: '请输入接口名称', trigger: 'blur' }],
  path: [{ required: true, message: '请输入接口路径', trigger: 'blur' }],
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
    }
  } catch {
    // 已由拦截器提示
  }
}

async function loadData() {
  if (!projectId.value) return
  loading.value = true
  try {
    const data = await listInterfacesApi(projectId.value, {
      page: page.value,
      page_size: pageSize.value,
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
}

function handleSearch() {
  page.value = 1
  loadData()
}

function showCreateDialog() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    method: 'GET',
    path: '',
    summary: '',
    headers: '',
    params: '',
    body: '',
  })
  dialogVisible.value = true
}

function openEdit(row: ApiInterface) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    method: row.method,
    path: row.path,
    summary: row.summary || '',
    headers: row.headers || '',
    params: row.params || '',
    body: row.body || '',
  })
  dialogVisible.value = true
}

async function handleSave() {
  if (!projectId.value) return
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      ...form,
      summary: form.summary || null,
      headers: form.headers || null,
      params: form.params || null,
      body: form.body || null,
    }
    if (editingId.value) {
      await updateInterfaceApi(projectId.value, editingId.value, payload)
      ElMessage.success('接口已更新')
    } else {
      await createInterfaceApi(projectId.value, payload)
      ElMessage.success('接口已创建')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: ApiInterface) {
  if (!projectId.value) return
  try {
    await ElMessageBox.confirm(
      `确定删除接口「${row.name}」吗？关联用例会保留但解绑。`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteInterfaceApi(projectId.value, row.id)
  ElMessage.success('接口已删除')
  loadData()
}

function showImportDialog() {
  importSpec.value = ''
  importVisible.value = true
}

async function handleImport() {
  if (!projectId.value) return
  let spec: Record<string, unknown>
  try {
    spec = JSON.parse(importSpec.value)
  } catch {
    ElMessage.error('JSON 解析失败，请检查格式')
    return
  }
  importing.value = true
  try {
    const data = await importOpenApiApi(projectId.value, spec)
    ElMessage.success(`导入成功，共 ${data.total} 个接口`)
    importVisible.value = false
    loadData()
  } finally {
    importing.value = false
  }
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
