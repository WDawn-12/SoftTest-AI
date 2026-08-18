// 前端路由配置：定义全部页面路由
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: () => import('@/views/project/ProjectListView.vue'),
        meta: { title: '项目管理' },
      },
      {
        path: 'projects/new',
        name: 'ProjectCreate',
        component: () => import('@/views/project/ProjectCreateView.vue'),
        meta: { title: '新建项目' },
      },
      {
        path: 'projects/:projectId/detail',
        name: 'ProjectDetail',
        component: () => import('@/views/project/ProjectDetailView.vue'),
        meta: { title: '项目详情' },
      },
      {
        path: 'projects/:projectId/requirement/upload',
        name: 'UploadRequirement',
        component: () => import('@/views/requirement/UploadRequirementView.vue'),
        meta: { title: '上传需求文档' },
      },
      {
        path: 'projects/:projectId/requirement/result',
        name: 'ParseResult',
        component: () => import('@/views/requirement/ParseResultView.vue'),
        meta: { title: 'AI 解析结果' },
      },
      {
        path: 'test-points',
        name: 'TestPoint',
        component: () => import('@/views/testpoint/TestPointView.vue'),
        meta: { title: '测试点管理' },
      },
      {
        path: 'test-cases',
        name: 'TestCase',
        component: () => import('@/views/testcase/TestCaseView.vue'),
        meta: { title: '测试用例管理' },
      },
      {
        path: 'interfaces',
        name: 'InterfaceList',
        component: () => import('@/views/interface/InterfaceListView.vue'),
        meta: { title: '接口管理' },
      },
      {
        path: 'interface-cases',
        name: 'InterfaceCase',
        component: () => import('@/views/interface/InterfaceCaseView.vue'),
        meta: { title: '接口测试用例' },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatView.vue'),
        meta: { title: 'AI 聊天助手' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/SettingsView.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
  {
    // 未匹配路由统一回首页
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫：未登录跳转登录页；已登录访问登录页跳回首页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && token) {
    return { path: '/dashboard' }
  }
})

// 路由守卫：同步页面标题（登录鉴权将在第二阶段接入）
router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - AITestAgent` : 'AITestAgent'
})

export default router
