<template>
  <div class="page">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats?.project_count ?? '-' }}</div>
          <div class="stat-label">项目总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats?.requirement_count ?? '-' }}</div>
          <div class="stat-label">需求文档</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats?.test_point_count ?? '-' }}</div>
          <div class="stat-label">测试点</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats?.test_case_count ?? '-' }}</div>
          <div class="stat-label">测试用例</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span class="page-title">最近项目</span>
      </template>
      <el-table v-loading="loading" :data="stats?.recent_projects || []" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status]?.type || 'info'">
              {{ statusMeta[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="110" fixed="right">
          <template #default>
            <el-button link type="primary" @click="router.push('/projects')">
              进入项目管理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStatsApi } from '@/api/dashboard'
import type { DashboardStats } from '@/types/dashboard'

const router = useRouter()
const loading = ref(false)
const stats = ref<DashboardStats | null>(null)

const statusMeta: Record<string, { label: string; type: 'success' | 'info' | 'warning' }> = {
  active: { label: '进行中', type: 'success' },
  finished: { label: '已完成', type: 'info' },
  archived: { label: '已归档', type: 'warning' },
}

onMounted(async () => {
  loading.value = true
  try {
    stats.value = await getDashboardStatsApi()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  margin-top: 6px;
  color: #909399;
}
</style>
