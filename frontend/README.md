# AITestAgent 前端

基于 Vue 3 + TypeScript + Vite + Element Plus 的前端工程。

## 技术栈

- Vue 3、Vue Router、Pinia
- Element Plus（中文语言包）
- Axios（统一请求封装：`src/utils/request.ts`）

## 开发命令

```bash
pnpm install   # 安装依赖
pnpm dev       # 启动开发服务器（默认 5173，/api 代理到 8000）
pnpm build     # 类型检查 + 生产构建（输出 dist/）
pnpm preview   # 本地预览构建产物
```

## 目录说明

```text
src/
├── layout/     # 主布局（侧边栏菜单 + 顶栏）
├── router/     # 路由配置（10 个页面）
├── utils/      # Axios 请求封装
└── views/      # 页面组件
```

环境变量：`VITE_API_BASE_URL`（API 基础路径，默认 `/api`）。
