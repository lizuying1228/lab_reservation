
# 第一阶段：构建 Vue 项目
FROM node:22-alpine AS builder

WORKDIR /app

# 先复制依赖文件
COPY package.json package-lock.json ./

# 安装前端依赖
RUN npm ci

# 复制前端源代码
COPY . .

# 生产环境 API 地址
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 构建 Vue 项目
RUN npm run build


# 第二阶段：使用 Nginx 提供静态文件
FROM nginx:stable-alpine

# 删除 Nginx 默认页面
RUN rm -rf /usr/share/nginx/html/*

# 复制 Vue 构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 使用自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
