from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from database import get_db
from auth import register_user, get_user, use_auth_code, has_active_subscription
from models import SubscriptionStatus

# Состояния для ConversationHandler
AUTH_CODE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом и регистрация пользователя."""
    user = update.effective_user
    db = next(get_db())
    
    # Регистрируем пользователя или обновляем информацию
    db_user, is_new = register_user(
        db=db,
        telegram_id=str(user.id),
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Проверяем, есть ли у пользователя активная подписка
    if has_active_subscription(db, str(user.id)):
        # Если есть активная подписка, переходим в главное меню
        await show_main_menu(update, context)
        return ConversationHandler.END
    else:
        # Если нет активной подписки, запрашиваем код авторизации
        greeting = (
            f"👋 Здравствуйте, {user.first_name}!\n\n"
            "Для доступа к каталогу мебели необходимо ввести код авторизации.\n"
            "Пожалуйста, введите ваш код:"
        )
        
        await update.message.reply_text(greeting)
        return AUTH_CODE

async def auth_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенного кода авторизации."""
    user = update.effective_user
    code = update.message.text.strip()
    
    db = next(get_db())
    success, message = use_auth_code(db, str(user.id), code)
    
    if success:
        # Код верный, активирована подписка
        await update.message.reply_text(message)
        # Переходим в главное меню
        await show_main_menu(update, context)
        return ConversationHandler.END
    else:
        # Код неверный, просим ввести снова
        await update.message.reply_text(
            f"{message}\n\nПожалуйста, попробуйте еще раз или обратитесь к администратору."
        )
        return AUTH_CODE

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню бота."""
    keyboard = [
        [InlineKeyboardButton("🛋️ Каталог мебели", callback_data="catalog")],
        [InlineKeyboardButton("🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "🏠 Главное меню\n\nВыберите раздел:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🏠 Главное меню\n\nВыберите раздел:",
            reply_markup=reply_markup
        )
    
    return ConversationHandler.END

async def check_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет авторизацию пользователя перед выполнением защищенных действий.
    Возвращает True, если пользователь авторизован, иначе False.
    """
    user = update.effective_user
    db = next(get_db())
    
    if has_active_subscription(db, str(user.id)):
        return True
    
    # Если пользователь не авторизован, отправляем сообщение
    message = (
        "⚠️ У вас нет активной подписки.\n\n"
        "Для доступа к каталогу мебели необходимо ввести код авторизации.\n"
        "Пожалуйста, используйте команду /start для авторизации."
    )
    
    if update.callback_query:
        await update.callback_query.answer("Требуется авторизация")
        await update.callback_query.message.reply_text(message)
    else:
        await update.message.reply_text(message)
    
    return False

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль пользователя и информацию о подписке."""
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message
    
    user = update.effective_user
    db = next(get_db())
    db_user = get_user(db, str(user.id))
    
    if not db_user:
        await message.reply_text("❌ Ошибка: пользователь не найден в базе данных.")
        return
    
    # Формируем информацию о статусе подписки
    subscription_status = "Активна" if db_user.subscription_status == SubscriptionStatus.PAID else "Не активна"
    expiry_date = db_user.subscription_expiry.strftime("%d.%m.%Y") if db_user.subscription_expiry else "Нет"
    
    profile_text = (
        f"👤 *Профиль пользователя*\n\n"
        f"*Имя:* {db_user.first_name or 'Не указано'}\n"
        f"*Фамилия:* {db_user.last_name or 'Не указана'}\n"
        f"*Username:* @{db_user.username or 'Не указан'}\n\n"
        f"*Статус подписки:* {subscription_status}\n"
        f"*Действует до:* {expiry_date}\n\n"
        f"*Дата регистрации:* {db_user.registration_date.strftime('%d.%m.%Y')}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await message.edit_text(profile_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await message.reply_text(profile_text, reply_markup=reply_markup, parse_mode="Markdown")
