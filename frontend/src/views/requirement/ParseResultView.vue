<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <span class="page-title">AI 解析结果</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>
      <p class="page-desc">
        项目：{{ projectName || projectId }}（ID {{ projectId }}）— Requirement
        Agent 从需求文档中识别模块、功能点、角色、业务流程与风险
      </p>

      <div class="toolbar">
        <el-select
          v-model="selectedId"
          placeholder="选择需求文档"
          style="width: 320px"
          @change="loadParseResult"
        >
          <el-option
            v-for="item in requirements"
            :key="item.id"
            :label="`${item.file_name}（#${item.id}）`"
            :value="item.id"
          />
        </el-select>
        <el-button
          v-if="parseResult?.parse_status === 'completed'"
          type="warning"
          :loading="parsing"
          @click="handleParse"
        >
          重新解析
        </el-button>
        <el-button
          v-else
          type="primary"
          :loading="parsing"
          :disabled="!selectedId"
          @click="handleParse"
        >
          开始解析
        </el-button>
      </div>

      <el-alert
        v-if="parseResult && parseResult.parse_status !== 'completed'"
        :type="parseResult.parse_status === 'failed' ? 'error' : 'info'"
        :closable="false"
        :title="
          parseResult.parse_status === 'failed'
            ? parseResult.error_message || '解析失败'
            : '该文档尚未解析，点击「开始解析」'
        "
        style="margin-top: 12px"
      />

      <el-empty
        v-if="requirements.length === 0"
        description="该项目还没有需求文档，请先上传"
      />
    </el-card>

    <!-- 解析结果可视化 -->
    <template v-if="parseResult?.result && parseResult.parse_status === 'completed'">
      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span class="section-title">需求概述</span>
        </template>
        <p class="summary-text">{{ parseResult.result.summary }}</p>
      </el-card>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span class="section-title">功能模块（{{ parseResult.result.modules.length }}）</span>
        </template>
        <el-collapse>
          <el-collapse-item
            v-for="(module, index) in parseResult.result.modules"
            :key="module.name"
            :name="String(index)"
          >
            <template #title>
              <span class="module-name">{{ module.name }}</span>
            </template>
            <p class="module-desc">{{ module.description }}</p>
            <div>
              <el-tag
                v-for="fn in module.functions"
                :key="fn"
                type="primary"
                class="fn-tag"
              >
                {{ fn }}
              </el-tag>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span class="section-title">用户角色（{{ parseResult.result.roles.length }}）</span>
        </template>
        <el-tag
          v-for="role in parseResult.result.roles"
          :key="role"
          type="success"
          size="large"
          class="role-tag"
        >
          {{ role }}
        </el-tag>
      </el-card>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span class="section-title">
            业务流程（{{ parseResult.result.business_flows.length }}）
          </span>
        </template>
        <div
          v-for="flow in parseResult.result.business_flows"
          :key="flow.name"
          class="flow-block"
        >
          <h4 class="flow-name">{{ flow.name }}</h4>
          <el-timeline>
            <el-timeline-item
              v-for="step in flow.steps"
              :key="step"
              :timestamp="`步骤 ${flow.steps.indexOf(step) + 1}`"
            >
              {{ step }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-card>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span class="section-title">风险点（{{ parseResult.result.risks.length }}）</span>
        </template>
        <el-table :data="parseResult.result.risks" border stripe>
          <el-table-column prop="type" label="风险类型" width="140" />
          <el-table-column label="等级" width="90">
            <template #default="{ row }">
              <el-tag :type="riskType(row.level)">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="风险描述" min-width="300" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProjectApi } from '@/api/project'
import {
  getParseResultApi,
  listRequirementsApi,
  parseRequirementApi,
} from '@/api/requirement'
import type { ParseResultResponse, Requirement } from '@/types/requirement'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.projectId)

const projectName = ref('')
const requirements = ref<Requirement[]>([])
const selectedId = ref<number | null>(null)
const loading = ref(false)
const parsing = ref(false)
const parseResult = ref<ParseResultResponse | null>(null)

async function loadProject() {
  const project = await getProjectApi(projectId)
  projectName.value = project.name
}

async function loadRequirements() {
  const data = await listRequirementsApi(projectId, { page: 1, page_size: 50 })
  requirements.value = data.items
  // 默认选中最新上传的文档（列表按 id 倒序）
  if (data.items.length > 0 && selectedId.value === null) {
    selectedId.value = data.items[0].id
    await loadParseResult()
  }
}

async function loadParseResult() {
  if (!selectedId.value) return
  loading.value = true
  try {
    parseResult.value = await getParseResultApi(projectId, selectedId.value)
  } finally {
    loading.value = false
  }
}

async function handleParse() {
  if (!selectedId.value) return
  parsing.value = true
  try {
    parseResult.value = await parseRequirementApi(projectId, selectedId.value)
    ElMessage.success(
      parseResult.value.parse_status === 'completed' ? '解析完成' : '解析未成功，请查看提示',
    )
  } finally {
    parsing.value = false
  }
}

// 风险等级 -> 标签颜色
function riskType(level: string): 'danger' | 'warning' | 'success' | 'info' {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  if (level === '低') return 'success'
  return 'info'
}

onMounted(() => {
  loadProject()
  loadRequirements()
})
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
}

.section-title {
  font-size: 15px;
  font-weight: 600;
}

.summary-text {
  margin: 0;
  line-height: 1.8;
}

.module-name {
  font-weight: 600;
}

.module-desc {
  margin: 0 0 10px;
  color: #606266;
  line-height: 1.8;
}

.fn-tag {
  margin: 0 8px 8px 0;
}

.role-tag {
  margin: 0 10px 10px 0;
}

.flow-block {
  margin-bottom: 18px;
}

.flow-block:last-child {
  margin-bottom: 0;
}

.flow-name {
  margin: 0 0 10px;
}
</style>
