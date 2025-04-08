from sqlalchemy.orm import Session
from models import Product, Category
from typing import List, Dict, Any, Optional

def search_by_price(db: Session, max_price: float = None):
    """Поиск товаров по максимальной цене."""
    query = db.query(Product)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Сортировка от дешевых к дорогим
    return query.order_by(Product.price).all()

def search_by_manufacturer(db: Session, manufacturer: str):
    """Поиск товаров по производителю."""
    return db.query(Product).filter(Product.manufacturer.ilike(f"%{manufacturer}%")).order_by(Product.price).all()

def search_by_city(db: Session, city: str):
    """Поиск товаров по городу."""
    return db.query(Product).filter(Product.city.ilike(f"%{city}%")).order_by(Product.price).all()

def search_by_name(db: Session, name: str):
    """Поиск товаров по названию."""
    return db.query(Product).filter(Product.name.ilike(f"%{name}%")).order_by(Product.price).all()

def search_by_code(db: Session, code: str):
    """Поиск товара по коду."""
    return db.query(Product).filter(Product.product_code.ilike(f"%{code}%")).order_by(Product.price).all()

def advanced_search(db: Session, **kwargs):
    """Расширенный поиск товаров по нескольким параметрам."""
    query = db.query(Product)
    
    if 'category_id' in kwargs and kwargs['category_id']:
        query = query.filter(Product.category_id == kwargs['category_id'])
    
    if 'max_price' in kwargs and kwargs['max_price']:
        query = query.filter(Product.price <= kwargs['max_price'])
    
    if 'manufacturer' in kwargs and kwargs['manufacturer']:
        query = query.filter(Product.manufacturer.ilike(f"%{kwargs['manufacturer']}%"))
    
    if 'city' in kwargs and kwargs['city']:
        query = query.filter(Product.city.ilike(f"%{kwargs['city']}%"))
    
    if 'name' in kwargs and kwargs['name']:
        query = query.filter(Product.name.ilike(f"%{kwargs['name']}%"))
    
    if 'code' in kwargs and kwargs['code']:
        query = query.filter(Product.product_code.ilike(f"%{kwargs['code']}%"))
    
    # Специфичные атрибуты для разных типов мебели
    if 'form' in kwargs and kwargs['form']:
        query = query.filter(Product.form.ilike(f"%{kwargs['form']}%"))
    
    if 'mechanism' in kwargs and kwargs['mechanism']:
        query = query.filter(Product.mechanism.ilike(f"%{kwargs['mechanism']}%"))
    
    if 'filling' in kwargs and kwargs['filling']:
        query = query.filter(Product.filling.ilike(f"%{kwargs['filling']}%"))
    
    if 'lifting_mechanism' in kwargs and kwargs['lifting_mechanism'] is not None:
        query = query.filter(Product.lifting_mechanism == kwargs['lifting_mechanism'])
    
    if 'has_box' in kwargs and kwargs['has_box'] is not None:
        query = query.filter(Product.has_box == kwargs['has_box'])
    
    # Сортировка от дешевых к дорогим
    return query.order_by(Product.price).all()

def get_all_manufacturers(db: Session):
    """Возвращает список всех производителей."""
    manufacturers = db.query(Product.manufacturer).distinct().all()
    return [m[0] for m in manufacturers if m[0]]

def get_all_cities(db: Session):
    """Возвращает список всех городов."""
    cities = db.query(Product.city).distinct().all()
    return [c[0] for c in cities if c[0]]

def get_forms():
    """Возвращает список доступных форм мебели."""
    return ['прямой', 'угловой', 'П-образный', 'с высокой спинкой', 'стандартный']

def get_mechanisms():
    """Возвращает список доступных механизмов раскладывания."""
    return ['еврокнижка', 'дельфин', 'книжка', 'аккордеон', 'клик-кляк', 'нет']

def get_fillings():
    """Возвращает список доступных наполнителей."""
    return ['пенополиуретан', 'латекс', 'пружинный блок', 'синтепон', 'холлофайбер']
