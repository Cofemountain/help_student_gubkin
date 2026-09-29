# ==============================================================================
# Multi-stage Dockerfile: Frontend Builder + Python 3.11 Backend & Mini App
# ==============================================================================

# STAGE 1: Сборка фронтенда (Vue 3 + Vite)
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Копируем package.json и устанавливаем зависимости фронтенда
COPY blobs-front/package*.json ./
RUN npm ci --prefer-offline --no-audit

# Копируем исходный код фронтенда и выполняем сборку в dist
COPY blobs-front/ ./
RUN npm run build

# ------------------------------------------------------------------------------

# STAGE 2: Финальный легковесный Python runtime
FROM python:3.11-slim AS runner

# Системные зависимости для сборки sqlite/asyncpg и базовых утилит
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение бэкенда
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY main.py ./
COPY bot_max.py ./

# Копируем собранный фронтенд из Stage 1 в blobs-front/dist
COPY --from=frontend-builder /build/dist ./blobs-front/dist

# Создаем директорию для загрузки файлов
RUN mkdir -p /app/uploads

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

# По умолчанию запускаем FastAPI WebApp сервер
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
