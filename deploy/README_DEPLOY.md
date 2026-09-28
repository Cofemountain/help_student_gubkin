# 🚀 Руководство по развертыванию проекта на сервере (VPS)

Проект состоит из:
1. **Backend API** на FastAPI (`main.py`)
2. **Frontend Mini App** на Vue 3 + Vite (`blobs-front/dist`), встроенный прямо в FastAPI
3. **MAX Messenger Bot** на Python (`bot_max.py`) с поддержкой Mini App, банка задач и ролевой модели
4. **База данных** SQLite (или PostgreSQL) с кодификатором тем ОГЭ и банком задач

---

## 📋 Требования к серверу
- **ОС**: Ubuntu 22.04 / 24.04 LTS (или Debian 11/12)
- **Память**: от 1 GB RAM (рекомендуется 2 GB)
- **Домен**: Привязанный к IP сервера (например `oge-physics.ru`), так как **мессенджер МАКС требует HTTPS** для работы Mini App.

---

## ⚡ Способ 1: Быстрый запуск через Docker Compose (Рекомендуется)

Это самый надежный способ: зависимости Node.js и Python изолированы внутри контейнеров.

### 1. Установите Docker на сервер (если еще не установлен):
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. Загрузите проект на сервер:
```bash
git clone <ваш_репозиторий> /var/www/oge_physics
cd /var/www/oge_physics
```

### 3. Настройте файл окружения:
```bash
cp .env.example .env
nano .env
```
Укажите ваш токен:
```env
DATABASE_URL=sqlite+aiosqlite:///./oge_physics.db
MAX_BOT_TOKEN=ваш_токен_из_dev.max.ru
DEBUG=False
```

### 4. Запустите проект в Docker:
```bash
docker compose up -d --build
```
Проверить статус работы:
```bash
docker compose ps
docker compose logs -f
```

---

## 🛠️ Способ 2: Запуск без Docker (через Systemd)

### 1. Установите системные пакеты:
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm nginx certbot python3-certbot-nginx
```

### 2. Запустите скрипт автоматического развертывания:
```bash
cd /var/www/oge_physics
chmod +x deploy.sh
./deploy.sh
```

### 3. Зарегистрируйте службы в systemd:
```bash
sudo cp deploy/oge-web.service /etc/systemd/system/
sudo cp deploy/oge-bot.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now oge-web oge-bot
```

### Проверка статуса служб:
```bash
sudo systemctl status oge-web
sudo systemctl status oge-bot
```

---

## 🔒 Настройка HTTPS и Nginx (Обязательно для МАКС)

Платформа МАКС открывает Mini App только по защищенному протоколу **HTTPS**.

### 1. Скопируйте конфигурацию Nginx:
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/oge-physics
```

Отредактируйте ваш домен в файле `/etc/nginx/sites-available/oge-physics` (замените `your-domain.ru` на ваш реальный домен):
```bash
sudo nano /etc/nginx/sites-available/oge-physics
```

### 2. Активируйте сайт:
```bash
sudo ln -s /etc/nginx/sites-available/oge-physics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Получите бесплатный SSL-сертификат Let's Encrypt:
```bash
sudo certbot --nginx -d your-domain.ru
```

После этого ваш Mini App и API будут доступны по адресу: `https://your-domain.ru/`

---

## 📱 Настройка Mini App в кабинете разработчика МАКС (`dev.max.ru`)

1. Перейдите в [dev.max.ru](https://dev.max.ru) и выберите вашего бота.
2. В разделе **Настройки бота**:
   - **URL мини-приложения**: укажите ваш HTTPS-адрес, например `https://your-domain.ru/`
   - **Вид кнопки у поля ввода**: выберите «Открыть» или «Старт».
3. Сохраните изменения.
4. Теперь у пользователей:
   - В чате с ботом в левом нижнем углу всегда будет отображаться кнопка запуска Mini App.
   - По команде `/start` бот присылает сообщение с красивой встроенной кнопкой `open_app`, открывающей Mini App прямо внутри мессенджера.
   - Работают разделы: Банк задач ОГЭ (с автопроверкой ответов и XP), Создание заявок на помощь, Лента репетитора, Достижения и Профиль.

---

## 🔄 Обновление проекта на сервере

Когда вы вносите правки в репозиторий:

```bash
cd /var/www/oge_physics
git pull

# Если используется Docker:
docker compose up -d --build

# Если используется Systemd:
cd blobs-front && npm run build && cd ..
sudo systemctl restart oge-web oge-bot
```
