# AITestAgent 后端镜像：Python 3.12
FROM python:3.12-slim

WORKDIR /app

# 环境变量：不生成 __pycache__、日志实时输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先复制依赖清单以利用 Docker 构建缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app ./app

EXPOSE 8000

# 启动 Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
