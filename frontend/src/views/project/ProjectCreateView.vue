<template>
  <div class="page">
    <el-card shadow="never" style="max-width: 720px">
      <template #header>
        <span class="page-title">新建项目</span>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
      >
        <el-divider content-position="left">项目信息</el-divider>
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" maxlength="100" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="2000"
            placeholder="请输入项目描述（选填）"
          />
        </el-form-item>

        <el-divider content-position="left">被测系统信息</el-divider>
        <el-form-item label="系统名称" prop="system_name">
          <el-input v-model="form.system_name" maxlength="100" placeholder="请输入被测系统名称" />
        </el-form-item>
        <el-form-item label="测试网址(URL)" prop="test_url">
          <el-input v-model="form.test_url" maxlength="500" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="系统类型" prop="system_type">
          <el-select v-model="form.system_type" style="width: 100%">
            <el-option v-for="t in systemTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器" prop="browser_type">
          <el-select v-model="form.browser_type" style="width: 100%">
            <el-option v-for="b in browserTypes" :key="b" :label="b" :value="b" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试账号" prop="login_username">
          <el-input v-model="form.login_username" maxlength="100" placeholder="选填" />
        </el-form-item>
        <el-form-item label="测试密码" prop="login_password">
          <el-input
            v-model="form.login_password"
            type="password"
            show-password
            maxlength="200"
            placeholder="选填（加密保存）"
          />
        </el-form-item>
        <el-form-item label="系统描述" prop="system_description">
          <el-input
            v-model="form.system_description"
            type="textarea"
            :rows="2"
            maxlength="2000"
            placeholder="选填"
          />
        </el-form-item>

        <el-divider content-position="left">需求文档（选填）</el-divider>
        <el-form-item label="需求文档" prop="requirementFile">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :accept="ACCEPT"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleExceed"
          >
            <el-button type="primary" plain>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 .docx / .pdf / .txt / .md / .markdown，不超过 20MB</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleCreate">
            创建项目
          </el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { createProjectApi } from '@/api/project'
import { uploadRequirementApi } from '@/api/requirement'
import type { BrowserType, SystemType } from '@/types/sut'

const router = useRouter()
const saving = ref(false)
const formRef = ref<FormInstance>()
const selectedFile = ref<File | null>(null)

const ACCEPT = '.docx,.pdf,.txt,.md,.markdown'
const MAX_SIZE = 20 * 1024 * 1024
const systemTypes: SystemType[] = ['Web后台', 'Web网站', '微信小程序', 'Android', 'iOS']
const browserTypes: BrowserType[] = ['Chrome', 'Edge', 'Firefox']

const form = reactive({
  name: '',
  description: '',
  system_name: '',
  test_url: '',
  system_type: 'Web网站' as SystemType,
  browser_type: 'Chrome' as BrowserType,
  login_username: '',
  login_password: '',
  system_description: '',
})

const urlRule = {
  validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
    if (value && !/^https?:\/\/.+/i.test(value)) {
      callback(new Error('测试网址必须以 http:// 或 https:// 开头'))
    } else {
      callback()
    }
  },
  trigger: 'blur',
}

const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  system_name: [{ required: true, message: '请输入系统名称', trigger: 'blur' }],
  test_url: [{ required: true, message: '请输入测试网址', trigger: 'blur' }, urlRule],
  system_type: [{ required: true, message: '请选择系统类型', trigger: 'change' }],
  browser_type: [{ required: true, message: '请选择浏览器', trigger: 'change' }],
}

function handleFileChange(file: UploadFile) {
  if (!file.raw) return
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
  if (!ACCEPT.split(',').includes(ext)) {
    ElMessage.error('仅支持 Word/PDF/TXT/Markdown 文件')
    return
  }
  if ((file.size ?? 0) > MAX_SIZE) {
    ElMessage.error('文件大小不能超过 20MB')
    return
  }
  selectedFile.value = file.raw
}

function handleFileRemove() {
  selectedFile.value = null
}

function handleExceed() {
  ElMessage.warning('只能选择一个需求文档')
}

async function handleCreate() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const project = await createProjectApi({
      name: form.name,
      description: form.description || undefined,
      system_name: form.system_name,
      test_url: form.test_url,
      system_type: form.system_type,
      browser_type: form.browser_type,
      login_username: form.login_username || undefined,
      login_password: form.login_password || undefined,
      system_description: form.system_description || undefined,
    })
    if (selectedFile.value) {
      await uploadRequirementApi(project.id, selectedFile.value)
    }
    ElMessage.success('项目创建成功')
    router.push(`/projects/${project.id}/detail`)
  } finally {
    saving.value = false
  }
}
</script>
