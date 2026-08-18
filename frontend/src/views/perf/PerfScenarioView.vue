<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <span class="page-title">性能测试场景</span>
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
          placeholder="搜索场景名称"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button type="success" :disabled="!projectId" @click="showCreateDialog">
          新建压测场景
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">场景列表（{{ total }}）</span>
      </template>
      <el-table v-loading="loading" :data="items" border stripe>
        <el-table-column prop="name" label="场景名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="并发" width="80" align="center">
          <template #default="{ row }">{{ row.thread_count }}</template>
        </el-table-column>
        <el-table-column label="循环" width="80" align="center">
          <template #default="{ row }">{{ row.loop_count }}</template>
        </el-table-column>
        <el-table-column label="Ramp-Up" width="90" align="center">
          <template #default="{ row }">{{ row.ramp_up }}s</template>
        </el-table-column>
        <el-table-column label="思考时间" width="110" align="center">
          <template #default="{ row }">{{ row.think_time_ms }}ms</template>
        </el-table-column>
        <el-table-column label="目标地址" min-width="150">
          <template #default="{ row }">
            <span class="mono">{{ row.base_url }}:{{ row.base_port }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="handleExport(row)">
              导出 JMeter
            </el-button>
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

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑压测场景' : '新建压测场景'"
      width="640px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="110px">
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="form.name" placeholder="如：登录接口 100 并发压测" />
        </el-form-item>
        <el-form-item label="场景描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="冒烟 / 负载 / 压力测试目标等（可选）"
          />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="并发用户" prop="thread_count">
              <el-input-number v-model="form.thread_count" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="循环次数" prop="loop_count">
              <el-input-number v-model="form.loop_count" :min="1" :max="100000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Ramp-Up(秒)">
              <el-input-number v-model="form.ramp_up" :min="1" :max="3600" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="思考时间(ms)">
          <el-input-number v-model="form.think_time_ms" :min="0" :max="600000" style="width: 200px" />
          <span class="tip">0 表示不模拟思考间隔</span>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="目标主机" prop="base_url">
              <el-input v-model="form.base_url" placeholder="localhost" class="mono" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="端口" prop="base_port">
              <el-input v-model="form.base_port" placeholder="8000" class="mono" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="压测接口">
          <el-select
            v-model="form.interface_ids"
            multiple
            clearable
            collapse-tags
            placeholder="不选 = 压测项目全部接口"
            style="width: 100%"
            :loading="interfacesLoading"
          >
            <el-option
              v-for="it in interfaces"
              :key="it.id"
              :label="`${it.method} ${it.path}（${it.name}）`"
              :value="it.id"
            />
          </el-select>
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
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { listProjectsApi } from '@/api/project'
import { listInterfacesApi } from '@/api/interfaceTest'
import {
  createPerfScenarioApi,
  deletePerfScenarioApi,
  exportPerfScenarioJmeterApi,
  listPerfScenariosApi,
  updatePerfScenarioApi,
} from '@/api/perfScenario'
import type { PerfScenario, PerfScenarioPayload } from '@/types/perfScenario'

const projects = ref<{ id: number; name: string }[]>([])
const projectId = ref<number | null>(null)
const keyword = ref('')
const items = ref<PerfScenario[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const saving = ref(false)

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const interfaces = ref<{ id: number; name: string; method: string; path: string }[]>([])
const interfacesLoading = ref(false)

const form = reactive({
  name: '',
  description: '',
  thread_count: 50,
  loop_count: 10,
  ramp_up: 10,
  think_time_ms: 500,
  base_url: 'localhost',
  base_port: '8000',
  interface_ids: [] as number[],
})

const formRules = {
  name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  thread_count: [{ required: true, message: '请输入并发数', trigger: 'blur' }],
  loop_count: [{ required: true, message: '请输入循环次数', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入目标主机（不含 http:// 或端口）', trigger: 'blur' }],
  base_port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
}

onMounted(async () => {
  const res = await listProjectsApi({ page: 1, page_size: 100 })
  projects.value = res.items
})

function handleProjectChange() {
  page.value = 1
  loadData()
  loadInterfaces()
}

async function loadData() {
  if (!projectId.value) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const res = await listPerfScenariosApi(projectId.value, {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadInterfaces() {
  if (!projectId.value) return
  interfacesLoading.value = true
  try {
    const res = await listInterfacesApi(projectId.value, { page: 1, page_size: 100 })
    interfaces.value = res.items
  } finally {
    interfacesLoading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadData()
}

function showCreateDialog() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    description: '',
    thread_count: 50,
    loop_count: 10,
    ramp_up: 10,
    think_time_ms: 500,
    base_url: 'localhost',
    base_port: '8000',
    interface_ids: [],
  })
  dialogVisible.value = true
  loadInterfaces()
}

function openEdit(row: PerfScenario) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    thread_count: row.thread_count,
    loop_count: row.loop_count,
    ramp_up: row.ramp_up,
    think_time_ms: row.think_time_ms,
    base_url: row.base_url,
    base_port: row.base_port,
    interface_ids: row.interface_ids || [],
  })
  dialogVisible.value = true
  loadInterfaces()
}

async function handleSave() {
  if (!projectId.value) return
  saving.value = true
  try {
    const payload: PerfScenarioPayload = {
      name: form.name,
      description: form.description || null,
      thread_count: form.thread_count,
      loop_count: form.loop_count,
      ramp_up: form.ramp_up,
      think_time_ms: form.think_time_ms,
      base_url: form.base_url,
      base_port: form.base_port,
      interface_ids: form.interface_ids?.length ? form.interface_ids : null,
    }
    if (editingId.value) {
      await updatePerfScenarioApi(projectId.value, editingId.value, payload)
      ElMessage.success('场景已更新')
    } else {
      await createPerfScenarioApi(projectId.value, payload)
      ElMessage.success('场景已创建')
    }
    dialogVisible.value = false
    loadData()
  } catch {
    // 已由拦截器提示
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: PerfScenario) {
  if (!projectId.value) return
  await ElMessageBox.confirm(`确定删除场景「${row.name}」？`, '提示', {
    type: 'warning',
  })
  await deletePerfScenarioApi(projectId.value, row.id)
  ElMessage.success('已删除')
  loadData()
}

async function handleExport(row: PerfScenario) {
  if (!projectId.value) return
  try {
    const blob = await exportPerfScenarioJmeterApi(projectId.value, row.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `perf_scenario_${row.id}.jmx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出 JMeter 压测脚本，用 JMeter 打开即可运行')
  } catch {
    // 已由拦截器提示
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}
.page-title {
  font-weight: 500;
}
.mono {
  font-family: var(--font-mono, monospace);
}
.tip {
  margin-left: 10px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
