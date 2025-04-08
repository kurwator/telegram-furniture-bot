from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
from models import User, SubscriptionStatus
from config import SECRET_KEY, AUTH_CODE

def hash_password(password):
    """Хеширует пароль с использованием SHA-256."""
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    """Проверяет соответствие пароля хешу."""
    return hash_password(plain_password) == hashed_password

def register_user(db: Session, telegram_id, username=None, first_name=None, last_name=None, phone_number=None, email=None):
    """Регистрирует нового пользователя или обновляет существующего."""
    # Проверяем, существует ли пользователь
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        # Создаем нового пользователя
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            subscription_status=SubscriptionStatus.FREE,
            registration_date=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True  # Возвращаем пользователя и флаг, что это новый пользователь
    else:
        # Обновляем существующего пользователя
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if phone_number:
            user.phone_number = phone_number
        if email:
            user.email = email
        
        user.last_activity = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user, False  # Возвращаем пользователя и флаг, что это существующий пользователь

def get_user(db: Session, telegram_id):
    """Получает пользователя по telegram_id."""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def check_auth_code(code):
    """Проверяет код авторизации."""
    return code == AUTH_CODE

def use_auth_code(db: Session, telegram_id, code):
    """
    Использует код авторизации для активации подписки.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        code: Код авторизации
        
    Returns:
        tuple: (успех, сообщение)
    """
    if not check_auth_code(code):
        return False, "❌ Неверный код авторизации."
    
    user = get_user(db, telegram_id)
    if not user:
        return False, "❌ Пользователь не найден. Пожалуйста, начните с команды /start."
    
    # Активируем подписку на 1 месяц
    subscription_end_date = datetime.utcnow() + timedelta(days=30)
    user.subscription_status = SubscriptionStatus.PAID
    user.subscription_expiry = subscription_end_date
    
    # Создаем запись о подписке
    from models import Subscription
    subscription = Subscription(
        user_id=user.id,
        status=SubscriptionStatus.PAID,
        start_date=datetime.utcnow(),
        end_date=subscription_end_date,
        payment_amount=500.0,  # 500 рублей за месяц
        payment_date=datetime.utcnow()
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(user)
    
    return True, f"✅ Код активирован! Ваша подписка действительна до {subscription_end_date.strftime('%d.%m.%Y')}."

def check_subscription_status(db: Session, user_id):
    """Проверяет статус подписки пользователя и обновляет его, если срок истек."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return SubscriptionStatus.FREE
    
    # Если подписка платная или пробная, проверяем срок действия
    if user.subscription_status in [SubscriptionStatus.PAID, SubscriptionStatus.TRIAL]:
        if user.subscription_expiry and user.subscription_expiry < datetime.utcnow():
            # Срок подписки истек, обновляем статус
            user.subscription_status = SubscriptionStatus.EXPIRED
            db.commit()
            db.refresh(user)
    
    return user.subscription_status

def has_active_subscription(db: Session, telegram_id):
    """Проверяет, есть ли у пользователя активная подписка."""
    user = get_user(db, telegram_id)
    if not user:
        return False
    
    status = check_subscription_status(db, user.id)
    return status == SubscriptionStatus.PAID
