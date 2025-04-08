from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Enum, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import enum

Base = declarative_base()

class SubscriptionStatus(enum.Enum):
    FREE = "free"
    PAID = "paid"
    TRIAL = "trial"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    email = Column(String)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.FREE)
    subscription_expiry = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id='{self.telegram_id}', subscription_status={self.subscription_status})>"

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Отношение к товарам
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_code = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    manufacturer = Column(String)  # Производитель
    size = Column(String)  # Размер
    city = Column(String)  # Город
    # Специфичные атрибуты для разных типов мебели
    form = Column(String)  # Форма (для диванов)
    mechanism = Column(String)  # Механизм разложения (для диванов)
    filling = Column(String)  # Наполнение (для диванов)
    lifting_mechanism = Column(Boolean)  # Наличие подъемного механизма (для кроватей)
    has_box = Column(Boolean)  # Наличие ящика (для пуфов)
    image_path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Отношения
    category = relationship("Category", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, code='{self.product_code}', name='{self.name}')>"

class City(Base):
    __tablename__ = 'cities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    region = Column(String)
    
    def __repr__(self):
        return f"<City(id={self.id}, name='{self.name}')>"

class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<Admin(id={self.id}, username='{self.username}')>"

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.FREE)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime)
    payment_id = Column(String)
    payment_amount = Column(Float)
    payment_date = Column(DateTime)
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status})>"

# Функция для создания таблиц в базе данных
def create_tables(db_url):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine
