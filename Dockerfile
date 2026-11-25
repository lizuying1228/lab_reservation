
# 第一阶段：构建 Python 环境
FROM python:3.14-slim AS builder

WORKDIR /app

# 安装 mysqlclient 编译所需的依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 先复制依赖文件，利用 Docker 构建缓存
COPY pyproject.toml uv.lock ./

# 安装生产环境依赖，不安装开发依赖
RUN uv sync --frozen --no-dev --no-install-project


# 第二阶段：运行 Django
FROM python:3.14-slim

WORKDIR /app

# mysqlclient 运行时需要的动态库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# 复制第一阶段创建的 Python 虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 让容器直接使用虚拟环境中的命令
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 复制 Django 项目代码
COPY . .

# Django 服务监听容器内部的 8000 端口
EXPOSE 8000

# 使用 Gunicorn 启动 Django
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
