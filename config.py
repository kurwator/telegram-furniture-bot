import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен бота Telegram
BOT_TOKEN = os.getenv("7467352806:AAHNd_kgcvuSDo5UkEFn53kNpJcRCke9DZo")

# Путь к базе данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/catalog.db")

# Секретный ключ для хеширования
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

# Код авторизации (не более 5 символов)
AUTH_CODE = os.getenv("AUTH_CODE", "M1234")

# Настройки подписки
SUBSCRIPTION_PRICES = {
    "MONTH": 500.0,
    "YEAR": 5000.0,
    "FOREVER": 0.0  # Бесплатно для друзей
}

# Настройки администратора
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
