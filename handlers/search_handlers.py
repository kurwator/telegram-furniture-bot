from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user, has_active_subscription, check_auth
from search import (
    search_by_price, search_by_manufacturer, search_by_city,
    search_by_name, search_by_code, advanced_search,
    get_all_manufacturers, get_all_cities
)
from catalog import get_product_by_id, format_product_name_with_price, get_product_display_text
from models import Product

# Состояния для ConversationHandler
SEARCH_TYPE = 1
QUICK_SEARCH = 2
QUICK_SEARCH_VALUE = 3
SEARCH_RESULTS = 4
PRODUCT_DETAIL = 5

async def show_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню поиска."""
    # Проверяем авторизацию
    if not await check_auth(update, context):
        return ConversationHandler.END
    
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message
    
    search_message = (
        "🔍 *Поиск мебели*\n\n"
        "Выберите тип поиска:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 По цене", callback_data="quick_search_price")],
        [InlineKeyboardButton("🏭 По производителю", callback_data="quick_search_manufacturer")],
        [InlineKeyboardButton("🏙️ По городу", callback_data="quick_search_city")],
        [InlineKeyboardButton("📝 По названию", callback_data="quick_search_name")],
        [InlineKeyboardButton("🔢 По коду товара", callback_data="quick_search_code")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await message.edit_text(search_message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await message.reply_text(search_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return SEARCH_TYPE

async def quick_search_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашивает максимальную цену для быстрого поиска по цене."""
    query = update.callback_query
    await query.answer()
    
    context.user_data["search_type"] = "price"
    
    price_message = (
        "💰 *Поиск по цене*\n\n"
        "Выберите максимальную цену:"
    )
    
    # Создаем кнопки с различными ценовыми диапазонами
    keyboard = [
        [InlineKeyboardButton("До 5 000₽", callback_data="price_5000")],
        [InlineKeyboardButton("До 10 000₽", callback_data="price_10000")],
        [InlineKeyboardButton("До 20 000₽", callback_data="price_20000")],
        [InlineKeyboardButton("До 30 000₽", callback_data="price_30000")],
        [InlineKeyboardButton("До 50 000₽", callback_data="price_50000")],
        [InlineKeyboardButton("Любая цена", callback_data="price_any")],
        [InlineKeyboardButton("⬅️ Назад к поиску", callback_data="search")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(price_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return QUICK_SEARCH

async def quick_search_manufacturer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список производителей для быстрого поиска."""
    query = update.callback_query
    await query.answer()
    
    context.user_data["search_type"] = "manufacturer"
    
    # Получаем список производителей
    db = next(get_db())
    manufacturers = get_all_manufacturers(db)
    
    manufacturer_message = (
        "🏭 *Поиск по производителю*\n\n"
        "Выберите производителя:"
    )
    
    # Создаем кнопки для каждого производителя
    keyboard = []
    for manufacturer in manufacturers:
        keyboard.append([InlineKeyboardButton(manufacturer, callback_data=f"manufacturer_{manufacturer}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад к поиску", callback_data="search")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(manufacturer_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return QUICK_SEARCH

async def quick_search_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список городов для быстрого поиска."""
    query = update.callback_query
    await query.answer()
    
    context.user_data["search_type"] = "city"
    
    # Получаем список городов
    db = next(get_db())
    cities = get_all_cities(db)
    
    city_message = (
        "🏙️ *Поиск по городу*\n\n"
        "Выберите город:"
    )
    
    # Создаем кнопки для каждого города
    keyboard = []
    for city in cities:
        keyboard.append([InlineKeyboardButton(city, callback_data=f"city_{city}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад к поиску", callback_data="search")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(city_message, reply_markup=reply_markup, parse_mode="Markdown")
    
    return QUICK_SEARCH

async def quick_search_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашивает название для поиска."""
    query = update.callback_query
    await query.answer()
    
    context.user_data["search_type"] = "name"
    
    name_message = (
        "📝 *Поиск по названию*\n\n"
        "Введите название или часть названия товара:"
    )
    
    await query.message.edit_text(
        name_message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад к поиску", callback_data="search")]]),
        parse_mode="Markdown"
    )
    
    return QUICK_SEARCH_VALUE

async def quick_search_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашивает код товара для поиска."""
    query = update.callback_query
    await query.answer()
    
    context.user_data["search_type"] = "code"
    
    code_message = (
        "🔢 *Поиск по коду товара*\n\n"
        "Введите код товара или его часть:"
    )
    
    await query.message.edit_text(
        code_message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад к поиску", callback_data="search")]]),
        parse_mode="Markdown"
    )
    
    return QUICK_SEARCH_VALUE

async def process_search_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает введенное значение для поиска."""
    search_type = context.user_data.get("search_type")
    search_value = update.message.text.strip()
    
    # Сохраняем значение поиска
    context.user_data["search_value"] = search_value
    
    # Выполняем поиск
    db = next(get_db())
    
    if search_type == "name":
        products = search_by_name(db, search_value)
    elif search_type == "code":
        products = search_by_code(db, search_value)
    else:
        await update.message.reply_text(
            "❌ Ошибка: неизвестный тип поиска.\n\nПожалуйста, вернитесь в меню поиска.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Поиск", callback_data="search")]])
        )
        return SEARCH_TYPE
    
    # Отображаем результаты поиска
    await show_search_results(update, context, products)
    
    return SEARCH_RESULTS

async def process_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор значения для быстрого поиска из кнопок."""
    query = update.callback_query
    await query.answer()
    
    search_type = context.user_data.get("search_type")
    callback_data = query.data
    
    # Выполняем поиск
    db = next(get_db())
    
    if search_type == "price":
        if callback_data == "price_any":
            max_price = None
        else:
            max_price = float(callback_data.split("_")[1])
        products = search_by_price(db, max_price)
    elif search_type == "manufacturer":
        manufacturer = callback_data.split("_", 1)[1]
        products = search_by_manufacturer(db, manufacturer)
    elif search_type == "city":
        city = callback_data.split("_", 1)[1]
        products = search_by_city(db, city)
    else:
        await query.message.edit_text(
            "❌ Ошибка: неизвестный тип поиска.\n\nПожалуйста, вернитесь в меню поиска.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Поиск", callback_data="search")]])
        )
        return SEARCH_TYPE
    
    # Отображаем результаты поиска
    await show_search_results_callback(update, context, products)
    
    return SEARCH_RESULTS

async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, products):
    """Показывает результаты поиска."""
    search_type = context.user_data.get("search_type")
    search_value = context.user_data.get("search_value", "")
    
    # Формируем сообщение с результатами поиска
    if search_type == "name":
        search_message = f"🔍 *Результаты поиска по названию:* {search_value}\n\n"
    elif search_type == "code":
        search_message = f"🔍 *Результаты поиска по коду:* {search_value}\n\n"
    else:
        search_message = "🔍 *Результаты поиска*\n\n"
    
    search_message += f"Найдено товаров: {len(products)}\n\n"
    
    if not products:
        search_message += "К сожалению, ничего не найдено. Попробуйте изменить параметры поиска."
    else:
        search_message += "Выберите товар для просмотра подробной информации:"
    
    # Создаем кнопки для каждого товара, сортируем по цене
    keyboard = []
    for product in sorted(products, key=lambda p: p.price):
        keyboard.append([InlineKeyboardButton(
            format_product_name_with_price(product), 
            callback_data=f"product_{product.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(search_message, reply_markup=reply_markup, parse_mode="Markdown")

async def show_search_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, products):
    """Показывает результаты поиска через callback."""
    query = update.callback_query
    search_type = context.user_data.get("search_type")
    
    # Формируем сообщение с результатами поиска
    if search_type == "price":
        if query.data == "price_any":
            search_message = "🔍 *Результаты поиска по цене:* любая\n\n"
        else:
            max_price = query.data.split("_")[1]
            search_message = f"🔍 *Результаты поиска по цене:* до {max_price}₽\n\n"
    elif search_type == "manufacturer":
        manufacturer = query.data.split("_", 1)[1]
        search_message = f"🔍 *Результаты поиска по производителю:* {manufacturer}\n\n"
    elif search_type == "city":
        city = query.data.split("_", 1)[1]
        search_message = f"🔍 *Результаты поиска по городу:* {city}\n\n"
    else:
        search_message = "🔍 *Результаты поиска*\n\n"
    
    search_message += f"Найдено товаров: {len(products)}\n\n"
    
    if not products:
        search_message += "К сожалению, ничего не найдено. Попробуйте изменить параметры поиска."
    else:
        search_message += "Выберите товар для просмотра подробной информации:"
    
    # Создаем кнопки для каждого товара, сортируем по цене
    keyboard = []
    for product in sorted(products, key=lambda p: p.price):
        keyboard.append([InlineKeyboardButton(
            format_product_name_with_price(product), 
            callback_data=f"product_{product.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(search_message, reply_markup=reply_markup, parse_mode="Markdown")

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
            "Пожалуйста, выберите другой товар или вернитесь к поиску.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Поиск", callback_data="search")]])
        )
        return SEARCH_RESULTS
    
    # Формируем текст с информацией о товаре
    product_text = get_product_display_text(product)
    
    # Создаем кнопки навигации
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад к результатам", callback_data="back_to_results")],
        [InlineKeyboardButton("🔍 Новый поиск", callback_data="search")],
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

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает к результатам поиска."""
    query = update.callback_query
    await query.answer()
    
    # Возвращаемся к поиску, так как результаты могли быть потеряны
    await show_search_menu(update, context)
    
    return SEARCH_TYPE
