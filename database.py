from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from config import DATABASE_URL

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Генератор для получения сессии базы данных.
    Автоматически закрывает сессию после использования.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Инициализирует базу данных, создавая все таблицы.
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    
def check_db_exists():
    """
    Проверяет, существует ли файл базы данных.
    """
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        return os.path.exists(db_path)
    return True
