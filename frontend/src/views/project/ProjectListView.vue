<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <span class="page-title">项目管理</span>
          <el-button type="primary" @click="router.push('/projects/new')">
            <el-icon><Plus /></el-icon>&nbsp;新建项目
          </el-button>
        </div>
      </template>

      <!-- 搜索 -->
      <div class="toolbar">
        <el-input
          v-model="query.keyword"
          placeholder="搜索项目名称 / 描述"
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
      </div>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="projects" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="项目名称" min-width="160" />
        <el-table-column
          prop="description"
          label="描述"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type || 'info'">
              {{ statusMeta[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm
              title="确定删除该项目吗？关联的需求与用例将一并删除"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadProjects"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑项目" width="480px">
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="90px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="editForm.name" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            maxlength="2000"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="进行中" value="active" />
            <el-option label="已完成" value="finished" />
            <el-option label="已归档" value="archived" />
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
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { deleteProjectApi, listProjectsApi, updateProjectApi } from '@/api/project'
import type { Project, ProjectStatus } from '@/types/project'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const projects = ref<Project[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '' })

// 状态展示映射
const statusMeta: Record<string, { label: string; type: 'success' | 'info' | 'warning' }> = {
  active: { label: '进行中', type: 'success' },
  finished: { label: '已完成', type: 'info' },
  archived: { label: '已归档', type: 'warning' },
}

async function loadProjects() {
  loading.value = true
  try {
    const data = await listProjectsApi({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
    })
    projects.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  loadProjects()
}

function handleSizeChange() {
  query.page = 1
  loadProjects()
}

// ---------- 编辑 ----------
const editVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  id: 0,
  name: '',
  description: '',
  status: 'active' as ProjectStatus,
})
const editRules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}

function openEdit(row: Project) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  editForm.status = row.status as ProjectStatus
  editVisible.value = true
}

async function handleUpdate() {
  if (!editFormRef.value) return
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await updateProjectApi(editForm.id, {
      name: editForm.name,
      description: editForm.description || null,
      status: editForm.status,
    })
    ElMessage.success('更新成功')
    editVisible.value = false
    loadProjects()
  } finally {
    saving.value = false
  }
}

// ---------- 删除 ----------
async function handleDelete(row: Project) {
  await deleteProjectApi(row.id)
  ElMessage.success('删除成功')
  if (projects.value.length === 1 && query.page > 1) {
    query.page -= 1
  }
  loadProjects()
}

onMounted(loadProjects)
</script>

<style scoped>
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

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
