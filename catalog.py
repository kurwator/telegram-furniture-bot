from sqlalchemy.orm import Session
from models import Product, Category, City
from typing import List, Dict, Any, Optional

def get_all_categories(db: Session) -> List[Category]:
    """Получает список всех категорий."""
    return db.query(Category).all()

def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """Получает категорию по ID."""
    return db.query(Category).filter(Category.id == category_id).first()

def get_products_by_category(db: Session, category_id: int) -> List[Product]:
    """Получает список товаров в указанной категории."""
    return db.query(Product).filter(Product.category_id == category_id).all()

def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Получает товар по ID."""
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_code(db: Session, product_code: str) -> Optional[Product]:
    """Получает товар по коду."""
    return db.query(Product).filter(Product.product_code == product_code).first()

def get_all_cities(db: Session) -> List[City]:
    """Получает список всех городов."""
    return db.query(City).all()

def get_city_by_id(db: Session, city_id: int) -> Optional[City]:
    """Получает город по ID."""
    return db.query(City).filter(City.id == city_id).first()

def get_products_by_city(db: Session, city: str) -> List[Product]:
    """Получает список товаров, производимых в указанном городе."""
    return db.query(Product).filter(Product.city.ilike(f"%{city}%")).all()

def get_products_by_manufacturer(db: Session, manufacturer: str) -> List[Product]:
    """Получает список товаров указанного производителя."""
    return db.query(Product).filter(Product.manufacturer.ilike(f"%{manufacturer}%")).all()

def get_all_manufacturers(db: Session) -> List[str]:
    """Получает список всех производителей."""
    products = db.query(Product.manufacturer).distinct().all()
    return [p[0] for p in products if p[0]]

def get_all_cities_from_products(db: Session) -> List[str]:
    """Получает список всех городов из товаров."""
    products = db.query(Product.city).distinct().all()
    return [p[0] for p in products if p[0]]

def format_product_name_with_price(product: Product) -> str:
    """Форматирует название товара с ценой."""
    return f"{product.name} {int(product.price)}р."

def get_product_details(product: Product) -> Dict[str, Any]:
    """Получает детальную информацию о товаре."""
    details = {
        "id": product.id,
        "code": product.product_code,
        "name": product.name,
        "price": product.price,
        "manufacturer": product.manufacturer,
        "size": product.size,
        "city": product.city,
        "description": product.description,
        "image_path": product.image_path,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else None,
    }
    
    # Добавляем специфичные атрибуты в зависимости от категории
    category_name = product.category.name.lower() if product.category else ""
    
    if "диван" in category_name:
        details.update({
            "form": product.form,
            "mechanism": product.mechanism,
            "filling": product.filling
        })
    elif "кровать" in category_name:
        details.update({
            "lifting_mechanism": "Есть" if product.lifting_mechanism else "Нет"
        })
    elif "пуф" in category_name:
        details.update({
            "has_box": "Есть" if product.has_box else "Нет"
        })
    
    return details

def get_product_display_text(product: Product) -> str:
    """Формирует текст для отображения информации о товаре."""
    category_name = product.category.name if product.category else "Неизвестная категория"
    
    text = (
        f"🛋️ *{format_product_name_with_price(product)}*\n\n"
        f"Код товара: {product.product_code}\n"
        f"Категория: {category_name}\n"
        f"Производитель: {product.manufacturer or 'Не указан'}\n"
        f"Размер: {product.size or 'Не указан'}\n"
        f"Город: {product.city or 'Не указан'}\n\n"
    )
    
    # Добавляем специфичные атрибуты в зависимости от категории
    category_name = category_name.lower()
    
    if "диван" in category_name:
        text += (
            f"Форма: {product.form or 'Не указана'}\n"
            f"Механизм разложения: {product.mechanism or 'Не указан'}\n"
            f"Наполнение: {product.filling or 'Не указано'}\n\n"
        )
    elif "кровать" in category_name:
        text += f"Подъемный механизм: {'Есть' if product.lifting_mechanism else 'Нет'}\n\n"
    elif "пуф" in category_name:
        text += f"Ящик: {'Есть' if product.has_box else 'Нет'}\n\n"
    
    text += f"Описание: {product.description or 'Отсутствует'}"
    
    return text
