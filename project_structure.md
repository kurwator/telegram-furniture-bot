# Структура проекта нового Telegram-бота для каталога мебели

```
/new_bot/
├── main.py                 # Основной файл запуска бота
├── config.py               # Конфигурационные параметры
├── database.py             # Настройка и подключение к базе данных
├── models.py               # Модели данных SQLAlchemy
├── auth.py                 # Система авторизации по кодам
├── subscription.py         # Управление подписками
├── catalog.py              # Функции для работы с каталогом
├── search.py               # Функции поиска
├── handlers/
│   ├── __init__.py
│   ├── auth_handlers.py    # Обработчики авторизации
│   ├── catalog_handlers.py # Обработчики каталога
│   ├── search_handlers.py  # Обработчики поиска
│   ├── admin_handlers.py   # Обработчики админ-панели
│   └── subscription_handlers.py # Обработчики подписок
├── utils/
│   ├── __init__.py
│   ├── keyboards.py        # Клавиатуры и кнопки
│   └── helpers.py          # Вспомогательные функции
├── data/
│   └── catalog.db          # База данных SQLite
├── init_db.py              # Скрипт инициализации базы данных
├── create_env.py           # Скрипт создания .env файла
├── requirements.txt        # Зависимости проекта
├── amvera.yml              # Конфигурация для Amvera
└── README.md               # Документация проекта
```
