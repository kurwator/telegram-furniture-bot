import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Product, City, Admin, User, SubscriptionStatus
from config import DATABASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD
from auth import hash_password
import datetime

def init_database():
    """
    Инициализирует базу данных, создавая все таблицы и заполняя их начальными данными.
    """
    # Создаем директорию data, если она не существует
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Создаем движок SQLAlchemy
    engine = create_engine(DATABASE_URL)
    
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    
    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Проверяем, есть ли уже данные в таблицах
    if session.query(Category).count() == 0:
        # Добавляем категории
        categories = [
            Category(name="Диваны", description="Мягкие диваны различных форм и размеров"),
            Category(name="Кресла", description="Комфортные кресла для отдыха"),
            Category(name="Пуфы", description="Стильные пуфы для интерьера"),
            Category(name="Кровати", description="Удобные кровати для спальни"),
            Category(name="Аксессуары", description="Дополнительные аксессуары для мебели")
        ]
        session.add_all(categories)
        session.commit()
        print("Категории добавлены.")
    
    # Добавляем города, если их нет
    if session.query(City).count() == 0:
        cities = [
            City(name="Москва", region="Московская область"),
            City(name="Санкт-Петербург", region="Ленинградская область"),
            City(name="Казань", region="Республика Татарстан"),
            City(name="Новосибирск", region="Новосибирская область"),
            City(name="Екатеринбург", region="Свердловская область")
        ]
        session.add_all(cities)
        session.commit()
        print("Города добавлены.")
    
    # Добавляем администратора, если его нет
    if session.query(Admin).count() == 0:
        admin = Admin(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            is_active=True,
            last_login=datetime.datetime.utcnow()
        )
        session.add(admin)
        session.commit()
        print("Администратор добавлен.")
    
    # Добавляем примеры товаров, если их нет
    if session.query(Product).count() == 0:
        # Получаем ID категорий
        divanы_id = session.query(Category.id).filter(Category.name == "Диваны").scalar()
        kresla_id = session.query(Category.id).filter(Category.name == "Кресла").scalar()
        pufy_id = session.query(Category.id).filter(Category.name == "Пуфы").scalar()
        krovati_id = session.query(Category.id).filter(Category.name == "Кровати").scalar()
        
        # Добавляем примеры товаров
        products = [
            # Диваны
            Product(
                product_code="D001",
                category_id=divanы_id,
                name="Диван Комфорт",
                description="Удобный диван для гостиной",
                price=9900.0,
                manufacturer="МебельПлюс",
                size="200x90x80",
                city="Москва",
                form="Прямой",
                mechanism="Еврокнижка",
                filling="Пенополиуретан"
            ),
            Product(
                product_code="D002",
                category_id=divanы_id,
                name="Диван Престиж",
                description="Элегантный угловой диван",
                price=15000.0,
                manufacturer="ЛюксМебель",
                size="250x170x85",
                city="Санкт-Петербург",
                form="Угловой",
                mechanism="Дельфин",
                filling="Латекс"
            ),
            # Кресла
            Product(
                product_code="K001",
                category_id=kresla_id,
                name="Кресло Релакс",
                description="Комфортное кресло для отдыха",
                price=5500.0,
                manufacturer="МебельПлюс",
                size="80x90x100",
                city="Москва"
            ),
            # Пуфы
            Product(
                product_code="P001",
                category_id=pufy_id,
                name="Пуф Кубик",
                description="Компактный пуф для прихожей",
                price=2500.0,
                manufacturer="ДомМебель",
                size="40x40x40",
                city="Казань",
                has_box=True
            ),
            # Кровати
            Product(
                product_code="KR001",
                category_id=krovati_id,
                name="Кровать Сон",
                description="Удобная двуспальная кровать",
                price=12000.0,
                manufacturer="СонМебель",
                size="160x200",
                city="Новосибирск",
                lifting_mechanism=True
            )
        ]
        session.add_all(products)
        session.commit()
        print("Примеры товаров добавлены.")
    
    session.close()
    print("Инициализация базы данных завершена.")

if __name__ == "__main__":
    init_database()
