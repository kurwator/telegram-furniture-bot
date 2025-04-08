from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import User, Subscription, SubscriptionStatus
from config import SUBSCRIPTION_PRICES

def get_subscription_price(subscription_type):
    """
    Возвращает стоимость подписки в зависимости от её типа.
    
    Args:
        subscription_type: Тип подписки (MONTH, YEAR, FOREVER)
        
    Returns:
        float: Стоимость подписки
    """
    return SUBSCRIPTION_PRICES.get(subscription_type, SUBSCRIPTION_PRICES["MONTH"])

def calculate_subscription_end_date(subscription_type):
    """
    Рассчитывает дату окончания подписки в зависимости от её типа.
    
    Args:
        subscription_type: Тип подписки (MONTH, YEAR, FOREVER)
        
    Returns:
        datetime: Дата окончания подписки
    """
    now = datetime.utcnow()
    
    if subscription_type == "MONTH":
        # Подписка на месяц
        return now + timedelta(days=30)
    elif subscription_type == "YEAR":
        # Подписка на год
        return now + timedelta(days=365)
    elif subscription_type == "FOREVER":
        # "Вечная" подписка (10 лет)
        return now + timedelta(days=3650)
    else:
        # По умолчанию - месяц
        return now + timedelta(days=30)

def create_subscription(db: Session, user_id, subscription_type, payment_id=None):
    """
    Создает новую подписку для пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        subscription_type: Тип подписки (MONTH, YEAR, FOREVER)
        payment_id: ID платежа (опционально)
        
    Returns:
        Subscription: Созданная подписка
    """
    # Получаем пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Рассчитываем дату окончания подписки
    end_date = calculate_subscription_end_date(subscription_type)
    
    # Получаем стоимость подписки
    price = get_subscription_price(subscription_type)
    
    # Создаем подписку
    subscription = Subscription(
        user_id=user_id,
        status=SubscriptionStatus.PAID,
        start_date=datetime.utcnow(),
        end_date=end_date,
        payment_id=payment_id,
        payment_amount=price,
        payment_date=datetime.utcnow()
    )
    
    # Обновляем статус подписки пользователя
    user.subscription_status = SubscriptionStatus.PAID
    user.subscription_expiry = end_date
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    db.refresh(user)
    
    return subscription

def get_user_subscription(db: Session, user_id):
    """
    Получает текущую подписку пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        Subscription: Текущая подписка пользователя или None
    """
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.end_date > datetime.utcnow()
    ).order_by(Subscription.end_date.desc()).first()

def extend_subscription(db: Session, user_id, subscription_type, payment_id=None):
    """
    Продлевает существующую подписку пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        subscription_type: Тип подписки (MONTH, YEAR, FOREVER)
        payment_id: ID платежа (опционально)
        
    Returns:
        Subscription: Обновленная подписка
    """
    # Получаем пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Получаем текущую подписку
    current_subscription = get_user_subscription(db, user_id)
    
    # Рассчитываем новую дату окончания подписки
    if current_subscription and current_subscription.end_date > datetime.utcnow():
        # Если есть активная подписка, продлеваем от даты её окончания
        if subscription_type == "MONTH":
            end_date = current_subscription.end_date + timedelta(days=30)
        elif subscription_type == "YEAR":
            end_date = current_subscription.end_date + timedelta(days=365)
        elif subscription_type == "FOREVER":
            end_date = current_subscription.end_date + timedelta(days=3650)
        else:
            end_date = current_subscription.end_date + timedelta(days=30)
    else:
        # Если нет активной подписки, создаем новую
        end_date = calculate_subscription_end_date(subscription_type)
    
    # Получаем стоимость подписки
    price = get_subscription_price(subscription_type)
    
    # Создаем новую запись о подписке
    subscription = Subscription(
        user_id=user_id,
        status=SubscriptionStatus.PAID,
        start_date=datetime.utcnow(),
        end_date=end_date,
        payment_id=payment_id,
        payment_amount=price,
        payment_date=datetime.utcnow()
    )
    
    # Обновляем статус подписки пользователя
    user.subscription_status = SubscriptionStatus.PAID
    user.subscription_expiry = end_date
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    db.refresh(user)
    
    return subscription

def cancel_subscription(db: Session, user_id):
    """
    Отменяет подписку пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        bool: True, если подписка успешно отменена, иначе False
    """
    # Получаем пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Получаем текущую подписку
    current_subscription = get_user_subscription(db, user_id)
    if not current_subscription:
        return False
    
    # Отменяем подписку
    current_subscription.status = SubscriptionStatus.EXPIRED
    current_subscription.end_date = datetime.utcnow()
    
    # Обновляем статус подписки пользователя
    user.subscription_status = SubscriptionStatus.EXPIRED
    user.subscription_expiry = datetime.utcnow()
    
    db.commit()
    db.refresh(current_subscription)
    db.refresh(user)
    
    return True

def get_subscription_info(db: Session, user_id):
    """
    Получает информацию о подписке пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        
    Returns:
        dict: Информация о подписке
    """
    # Получаем пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {
            "status": "not_found",
            "message": "Пользователь не найден"
        }
    
    # Получаем текущую подписку
    current_subscription = get_user_subscription(db, user_id)
    
    if not current_subscription:
        return {
            "status": "no_subscription",
            "message": "У вас нет активной подписки"
        }
    
    # Определяем тип подписки по длительности
    days_left = (current_subscription.end_date - datetime.utcnow()).days
    
    if days_left > 3000:
        subscription_type = "FOREVER"
    elif days_left > 300:
        subscription_type = "YEAR"
    else:
        subscription_type = "MONTH"
    
    return {
        "status": "active",
        "type": subscription_type,
        "start_date": current_subscription.start_date,
        "end_date": current_subscription.end_date,
        "days_left": days_left,
        "payment_amount": current_subscription.payment_amount,
        "payment_date": current_subscription.payment_date,
        "message": f"У вас активная подписка до {current_subscription.end_date.strftime('%d.%m.%Y')}"
    }
