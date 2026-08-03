<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <h2 class="login-title">AITestAgent</h2>
      <p class="login-desc">基于 AI Agent 的软件测试辅助平台</p>
      <el-alert
        type="info"
        :closable="false"
        title="登录功能将在第二阶段（JWT 认证）开发"
      />
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, #1f3b73 0%, #409eff 100%);
}

.login-card {
  width: 420px;
  text-align: center;
}

.login-title {
  margin: 8px 0;
  color: #303133;
}

.login-desc {
  margin: 0 0 24px;
  color: #909399;
}
</style>
