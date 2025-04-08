import os
from dotenv import load_dotenv
import sqlite3
from pathlib import Path

def create_env_file():
    """
    Создает файл .env с необходимыми переменными окружения.
    """
    # Создаем директорию data, если она не существует
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Проверяем, существует ли уже файл .env
    if os.path.exists(".env"):
        print("Файл .env уже существует. Хотите перезаписать его? (y/n)")
        choice = input().lower()
        if choice != 'y':
            print("Операция отменена.")
            return
    
    # Запрашиваем токен бота
    print("Введите токен вашего Telegram бота:")
    bot_token = input()
    
    # Генерируем секретный ключ
    import secrets
    secret_key = secrets.token_hex(16)
    
    # Код авторизации
    auth_code = "M1234"  # Используем фиксированный код, как было запрошено
    
    # Создаем содержимое файла .env
    env_content = f"""BOT_TOKEN={bot_token}
DATABASE_URL=sqlite:///data/catalog.db
SECRET_KEY={secret_key}
AUTH_CODE={auth_code}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
"""
    
    # Записываем файл .env
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("Файл .env успешно создан.")

if __name__ == "__main__":
    create_env_file()
