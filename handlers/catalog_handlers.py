from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user, has_active_subscription, check_auth
from catalog import (
    get_all_categories, get_category_by_id, get_products_by_category,
    get_product_by_id, format_product_name_with_price, get_product_display_text
)
from models import Product

# Состояния для ConversationHandler
CATEGORY_SELECTION = 1
PRODUCT_SELECTION = 2
PRODUCT_DETAIL = 3
CATEGORY_ACTION = 4

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает каталог категорий мебели."""
    # Проверяем авторизацию
    if not await check_auth(update, context):
        return ConversationHandler.END
    
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message
    
    # Получаем список категорий из базы данных
    db = next(get_db())
    categories = get_all_categories(db)
    
    catalog_message = (
        "🛋️ *Каталог мебели*\n\n"
        "Выберите категорию:"
    )
    
    # Создаем кнопки для каждой категории
    keyboard = []
    for category in categories:
        emoji = get_category_emoji(category.name)
        keyboard.append([InlineKeyboardButton(f"{emoji} {category.name}", callback_data=f"category_{category.id}")])
    
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await message.edit_text(catalog_message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await message.reply_text(catalog_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return CATEGORY_SELECTION

async def show_category_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает действия для выбранной категории: просмотр всех товаров или поиск."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[1])
    context.user_data["selected_category_id"] = category_id
    
    # Получаем информацию о категории
    db = next(get_db())
    category = get_category_by_id(db, category_id)
    
    if not category:
        await query.message.edit_text(
            "❌ Категория не найдена.\n\n"
            "Пожалуйста, выберите другую категорию или вернитесь в главное меню.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад к категориям", callback_data="catalog")]])
        )
        return CATEGORY_SELECTION
    
    emoji = get_category_emoji(category.name)
    action_message = (
        f"{emoji} *{category.name}*\n\n"
        f"{category.description or 'Выберите действие:'}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Показать все товары", callback_data=f"show_all_{category_id}")],
        [InlineKeyboardButton("🔍 Поиск в этой категории", callback_data=f"search_in_{category_id}")],
        [InlineKeyboardButton("⬅️ Назад к категориям", callback_data="catalog")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(action_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return CATEGORY_ACTION

async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает товары в выбранной категории."""
    query = update.callback_query
    await query.answer()
    
    action, category_id = query.data.split("_")[0], int(query.data.split("_")[2])
    
    # Получаем информацию о категории и товарах
    db = next(get_db())
    category = get_category_by_id(db, category_id)
    
    if not category:
        await query.message.edit_text(
            "❌ Категория не найдена.\n\n"
            "Пожалуйста, выберите другую категорию или вернитесь в главное меню.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад к категориям", callback_data="catalog")]])
        )
        return CATEGORY_SELECTION
    
    # Получаем товары в этой категории
    products = get_products_by_category(db, category_id)
    
    emoji = get_category_emoji(category.name)
    products_message = (
        f"{emoji} *{category.name}*\n\n"
        f"Найдено товаров: {len(products)}\n\n"
        f"Выберите товар для просмотра подробной информации:"
    )
    
    # Создаем кнопки для каждого товара, сортируем по цене
    keyboard = []
    for product in sorted(products, key=lambda p: p.price):
        keyboard.append([InlineKeyboardButton(
            format_product_name_with_price(product), 
            callback_data=f"product_{product.id}"
        )])
    
    # Добавляем кнопки навигации
    keyboard.append([InlineKeyboardButton("⬅️ Назад к категории", callback_data=f"category_{category_id}")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(products_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return PRODUCT_SELECTION

async def show_product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает подробную информацию о выбранном товаре."""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split("_")[1])
    
    # Получаем информацию о товаре
    db = next(get_db())
    product = get_product_by_id(db, product_id)
    
    if not product:
        await query.message.edit_text(
            "❌ Товар не найден.\n\n"
            "Пожалуйста, выберите другой товар или вернитесь в каталог.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад к каталогу", callback_data="catalog")]])
        )
        return PRODUCT_SELECTION
    
    # Формируем текст с информацией о товаре
    product_text = get_product_display_text(product)
    
    # Создаем кнопки навигации
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад к товарам", callback_data=f"show_all_{product.category_id}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Если есть изображение, отправляем его
    if product.image_path:
        try:
            with open(product.image_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=product_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            await query.message.delete()
        except Exception as e:
            # Если не удалось отправить изображение, отправляем только текст
            await query.message.edit_text(
                product_text + "\n\n(Изображение недоступно)",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        # Если изображения нет, отправляем только текст
        await query.message.edit_text(
            product_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return PRODUCT_DETAIL

def get_category_emoji(category_name):
    """Возвращает эмодзи для категории."""
    category_emojis = {
        "Диваны": "🛋️",
        "Кресла": "💺",
        "Пуфы": "🪑",
        "Кровати": "🛏️",
        "Аксессуары": "🧸"
    }
    return category_emojis.get(category_name, "📦")
