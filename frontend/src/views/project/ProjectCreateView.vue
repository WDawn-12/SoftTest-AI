<template>
  <div class="page">
    <el-card shadow="never" style="max-width: 640px">
      <template #header>
        <span class="page-title">新建项目</span>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="form.name"
            maxlength="100"
            placeholder="请输入项目名称"
          />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            maxlength="2000"
            placeholder="请输入项目描述（选填）"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleCreate">
            创建
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
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createProjectApi } from '@/api/project'

const router = useRouter()
const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ name: '', description: '' })
const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

async function handleCreate() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await createProjectApi({
      name: form.name,
      description: form.description || undefined,
    })
    ElMessage.success('项目创建成功')
    router.push('/projects')
  } finally {
    saving.value = false
  }
}
</script>
