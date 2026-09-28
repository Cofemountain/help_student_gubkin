#!/bin/bash
# ==============================================================================
# Скрипт автоматического развертывания проекта "ОГЭ Физика Mini App" на Linux VPS
# ==============================================================================

set -e

echo "🚀 Начинаем развертывание ОГЭ Физика (FastAPI + MAX Bot + Vue Mini App)..."

# 1. Проверяем наличие Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите python3, python3-venv и python3-pip:"
    echo "   sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip nodejs npm"
    exit 1
fi

# 2. Создание и активация виртуального окружения Python
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения venv..."
    python3 -m venv venv
fi

echo "📦 Установка Python зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Сборка фронтенда (Vue 3 + Vite)
if [ -d "blobs-front" ]; then
    echo "🎨 Сборка Vue 3 Mini App фронтенда..."
    cd blobs-front
    if command -v npm &> /dev/null; then
        npm install
        npm run build
        echo "✅ Фронтенд успешно собран в blobs-front/dist!"
    else
        echo "⚠️ npm не найден. Если dist уже собран, пропускаем. Иначе установите Node.js:"
        echo "   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs"
    fi
    cd ..
fi

# 4. Создаем директорию для медиа
mkdir -p uploads

# 5. Инициализация базы данных и банка задач
echo "🗄️ Инициализация базы данных и сидирование банка задач..."
python3 -c "
import asyncio
from scripts.seed_oge_topics import seed_topics
from scripts.seed_bank_tasks import seed_bank_tasks

async def init():
    await seed_topics()
    await seed_bank_tasks()

asyncio.run(init())
"

# 6. Проверка конфигурации .env
if [ ! -f ".env" ]; then
    echo "⚠️ Файл .env не найден! Создаю из .env.example..."
    cp .env.example .env
    echo "❗ Пожалуйста, откройте .env и укажите ваш MAX_BOT_TOKEN!"
fi

echo "=========================================================="
echo "🎉 Проект готов к запуску!"
echo ""
echo "Вариант 1 (Docker Compose - рекомендуется):"
echo "   docker compose up -d --build"
echo ""
echo "Вариант 2 (Прямой запуск через systemd):"
echo "   sudo cp deploy/oge-web.service /etc/systemd/system/"
echo "   sudo cp deploy/oge-bot.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now oge-web oge-bot"
echo ""
echo "Вариант 3 (Ручной запуск для отладки):"
echo "   Терминал 1: source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo "   Терминал 2: source venv/bin/activate && python bot_max.py"
echo "=========================================================="
