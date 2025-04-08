from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user, has_active_subscription
from subscription import get_subscription_info, extend_subscription, cancel_subscription
from models import SubscriptionStatus

# Состояния для ConversationHandler
SUBSCRIPTION_MENU = 1
SUBSCRIPTION_PERIOD = 2
SUBSCRIPTION_PAYMENT = 3
SUBSCRIPTION_CONFIRMATION = 4

async def show_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню управления подпиской."""
    user = update.effective_user
    db = next(get_db())
    
    # Получаем информацию о подписке
    subscription_info = get_subscription_info(db, get_user(db, str(user.id)).id)
    
    if subscription_info["status"] == "active":
        # У пользователя есть активная подписка
        subscription_text = (
            f"👑 *Ваша подписка*\n\n"
            f"Статус: Активна\n"
            f"Действует до: {subscription_info['end_date'].strftime('%d.%m.%Y')}\n"
            f"Осталось дней: {subscription_info['days_left']}\n\n"
            f"Хотите продлить подписку?"
        )
        
        keyboard = [
            [InlineKeyboardButton("📅 Продлить на месяц", callback_data="subscribe_MONTH")],
            [InlineKeyboardButton("📆 Продлить на год", callback_data="subscribe_YEAR")],
            [InlineKeyboardButton("❌ Отменить подписку", callback_data="cancel_subscription")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
        ]
    else:
        # У пользователя нет активной подписки
        subscription_text = (
            "🔒 *Подписка*\n\n"
            "У вас нет активной подписки.\n\n"
            "Выберите тип подписки:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📅 Подписка на месяц - 500₽", callback_data="subscribe_MONTH")],
            [InlineKeyboardButton("📆 Подписка на год - 5000₽", callback_data="subscribe_YEAR")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            subscription_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            subscription_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return SUBSCRIPTION_MENU

async def select_subscription_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор периода подписки."""
    query = update.callback_query
    await query.answer()
    
    subscription_type = query.data.split("_")[1]
    context.user_data["subscription_type"] = subscription_type
    
    # Определяем стоимость и период
    if subscription_type == "MONTH":
        price = 500
        period = "1 месяц"
    elif subscription_type == "YEAR":
        price = 5000
        period = "1 год"
    else:
        # Этот случай не должен произойти, но на всякий случай
        await query.message.edit_text(
            "❌ Ошибка: неизвестный тип подписки.\n\nПожалуйста, вернитесь в меню подписки.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="subscription")]])
        )
        return SUBSCRIPTION_MENU
    
    payment_text = (
        f"💳 *Оплата подписки*\n\n"
        f"Тип подписки: {period}\n"
        f"Стоимость: {price}₽\n\n"
        f"Для оплаты выберите способ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Банковская карта", callback_data="payment_card")],
        [InlineKeyboardButton("🏦 СБП", callback_data="payment_sbp")],
        [InlineKeyboardButton("🔙 Назад", callback_data="subscription")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        payment_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SUBSCRIPTION_PERIOD

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор способа оплаты."""
    query = update.callback_query
    await query.answer()
    
    payment_method = query.data.split("_")[1]
    context.user_data["payment_method"] = payment_method
    
    # В реальном боте здесь была бы интеграция с платежной системой
    # Для демонстрации просто показываем сообщение об успешной оплате
    
    payment_text = (
        f"✅ *Оплата успешно выполнена!*\n\n"
        f"Для активации подписки нажмите кнопку ниже:"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить активацию", callback_data="payment_confirmed")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        payment_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SUBSCRIPTION_PAYMENT

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает оплату и активирует подписку."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db = next(get_db())
    db_user = get_user(db, str(user.id))
    
    if not db_user:
        await query.message.edit_text(
            "❌ Ошибка: пользователь не найден в базе данных.\n\nПожалуйста, начните с команды /start."
        )
        return ConversationHandler.END
    
    subscription_type = context.user_data.get("subscription_type", "MONTH")
    
    # Активируем или продлеваем подписку
    subscription = extend_subscription(db, db_user.id, subscription_type, payment_id="manual_payment")
    
    if subscription:
        confirmation_text = (
            f"🎉 *Подписка успешно активирована!*\n\n"
            f"Тип подписки: {'1 месяц' if subscription_type == 'MONTH' else '1 год'}\n"
            f"Действует до: {subscription.end_date.strftime('%d.%m.%Y')}\n\n"
            f"Теперь вам доступен полный каталог мебели. Приятного использования!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛋️ Перейти в каталог", callback_data="catalog")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            confirmation_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(
            "❌ Ошибка при активации подписки.\n\nПожалуйста, попробуйте еще раз или обратитесь к администратору.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]])
        )
    
    return SUBSCRIPTION_CONFIRMATION

async def cancel_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет подписку пользователя."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db = next(get_db())
    db_user = get_user(db, str(user.id))
    
    if not db_user:
        await query.message.edit_text(
            "❌ Ошибка: пользователь не найден в базе данных.\n\nПожалуйста, начните с команды /start."
        )
        return ConversationHandler.END
    
    # Запрашиваем подтверждение отмены
    confirmation_text = (
        "⚠️ *Отмена подписки*\n\n"
        "Вы уверены, что хотите отменить подписку?\n"
        "После отмены вы потеряете доступ к каталогу мебели."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, отменить", callback_data="confirm_cancel")],
        [InlineKeyboardButton("❌ Нет, вернуться", callback_data="subscription")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        confirmation_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SUBSCRIPTION_MENU

async def confirm_cancel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает отмену подписки."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db = next(get_db())
    db_user = get_user(db, str(user.id))
    
    if not db_user:
        await query.message.edit_text(
            "❌ Ошибка: пользователь не найден в базе данных.\n\nПожалуйста, начните с команды /start."
        )
        return ConversationHandler.END
    
    # Отменяем подписку
    success = cancel_subscription(db, db_user.id)
    
    if success:
        await query.message.edit_text(
            "✅ Ваша подписка успешно отменена.\n\n"
            "Вы можете оформить новую подписку в любое время через меню подписки.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]])
        )
    else:
        await query.message.edit_text(
            "❌ Ошибка при отмене подписки.\n\n"
            "Возможно, у вас нет активной подписки или произошла ошибка базы данных.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]])
        )
    
    return ConversationHandler.END
