# Monobank Finance Bot — Finance Tracker from UA Monobank

Простой Telegram-бот для автоматического учета личных финансов с интеграцией Monobank.
Использует Webhook для получения транзакций в реальном времени, локальную SQLite БД для хранения данных и Flask для Webhook-обработки.

## 📋 Архитектура и ключевые компоненты

- **Telegram Bot (aiogram)** – основной интерфейс пользователя с меню: балансы карт, отчеты, настройки.
- **Monobank API Integration** – получение информации о счетах и транзакциях.
- **Webhook** – автоматическое получение данных о транзакциях сразу после их совершения.
- **SQLite** – локальное хранилище данных (транзакции, категории, пользователи).
- **Flask** – веб-сервер для обработки Webhook-запросов от Monobank API.
- **Data Layer (SQLAlchemy)** – ORM для работы с БД.

---

## ⚙️ Настройка окружения

1. Скопируйте файл `.env.example` в `.env` и заполните значения:

   ```ini
   # Telegram Bot
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_TELEGRAM_ID=your_telegram_id

   # Monobank
   MONO_API_TOKEN=your_personal_api_token

   # Webhook Configuration
   WEBHOOK_BASE_URL=https://your-app-name.up.railway.app
   WEBHOOK_SECRET=your_secret_string

   # Database
   DATABASE_URL=sqlite+aiosqlite:///data/finance_bot.db
   ```

2. Развертывание на Railway:

   - Создайте приложение на [Railway](https://railway.app).
   - Добавьте все перечисленные переменные окружения в настройках.
   - При первом запуске бот сам создаст SQLite файл и категории.

---

## 📚 Технологии

| Компонент | Технология |
|-----------|-----------|
| **Bot Framework** | [aiogram](https://docs.aiogram.dev/) |
| **Web Framework** | [Flask](https://flask.palletsprojects.com/) |
| **DB** | [SQLite](https://www.sqlite.org/) |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) |
| **Runtime** | Python 3.11+ |

---

## 🏃 Запуск

```bash
# Установите зависимости
pip install -r requirements.txt

# Запуск бота
python src/bot/__init__.py

# Запуск вебхука (в другом терминале)
python src/web/__init__.py
```

---

## 🔁 Логика работы Webhook в Monobank API

1. Пользователь отправляет свой **Personal API Token** в бота.
2. Бот сохраняет токен и настраивает Webhook через метод `set_webhook`.

   ```text
   SET WEBHOOK
   │
   ▼
   Monobank sends POST /webhook/{secret}
   │
   ▼
   Python Flask Controller
   │
   ▼
   Save transaction
   Auto-classify by MCC
   Send Telegram Notification
   ```

---

## 📊 Основные функции

- Отображение балансов всех карт и банков.
- Автоматическая категоризация транзакций по MCC.
- Ручная смена категории или пометка транзакции как внутренняя.
- Формирование отчетов за периоды:
  - Сегодня
  - Текущая неделя
  - Текущий месяц

---

