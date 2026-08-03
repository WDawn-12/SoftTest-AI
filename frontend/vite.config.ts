import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 配置：路径别名 + 开发代理（/api -> 后端 FastAPI）
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 开发环境将 /api 请求转发到后端服务
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // 第三方库分包，减少首屏加载体积
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return
          if (id.includes('element-plus') || id.includes('@element-plus')) {
            return 'element-plus'
          }
          if (id.includes('vue') || id.includes('pinia')) {
            return 'vue-vendor'
          }
          if (id.includes('axios')) {
            return 'axios'
          }
          if (id.includes('marked') || id.includes('dompurify')) {
            return 'markdown'
          }
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
})
