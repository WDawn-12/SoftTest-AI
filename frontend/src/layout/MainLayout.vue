<template>
  <el-container class="layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo">
        <el-icon :size="24"><Promotion /></el-icon>
        <span v-show="!isCollapse" class="logo-text">AITestAgent</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="layout-menu"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
          <Expand v-if="isCollapse" />
          <Fold v-else />
        </el-icon>
        <span class="header-title">{{ route.meta.title }}</span>
        <span class="header-right">基于 AI Agent 的软件测试辅助平台</span>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  Document,
  Expand,
  Fold,
  Folder,
  FolderAdd,
  Odometer,
  Promotion,
  Setting,
  Tickets,
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapse = ref(false)

// 侧边栏菜单配置（上传需求、AI 解析结果等按项目维度组织的页面，
// 将在项目管理模块开发时从项目详情页接入）
const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: Odometer },
  { path: '/projects', title: '项目管理', icon: Folder },
  { path: '/projects/new', title: '新建项目', icon: FolderAdd },
  { path: '/test-points', title: '测试点管理', icon: Tickets },
  { path: '/test-cases', title: '测试用例管理', icon: Document },
  { path: '/chat', title: 'AI 聊天助手', icon: ChatDotRound },
  { path: '/settings', title: '系统设置', icon: Setting },
]

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.layout {
  height: 100%;
}

.layout-aside {
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  transition: width 0.2s;
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 60px;
  color: #409eff;
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
}

.layout-menu {
  border-right: none;
}

.layout-header {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  margin-left: auto;
  color: #909399;
  font-size: 13px;
}

.layout-main {
  padding: 0;
  background-color: #f5f7fa;
}
</style>
