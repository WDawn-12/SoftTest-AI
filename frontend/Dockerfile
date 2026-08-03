# AITestAgent 前端镜像：构建阶段（Node） + 运行阶段（Nginx）

# ---- 构建阶段 ----
FROM node:22-alpine AS build

WORKDIR /app

# 启用 pnpm 并安装依赖（利用 Docker 构建缓存）
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# 复制源码并构建
COPY . .
RUN pnpm build

# ---- 运行阶段 ----
FROM nginx:1.27-alpine

# 静态资源由 Nginx 托管
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
