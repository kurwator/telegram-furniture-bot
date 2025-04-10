from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
import logging
import os
from dotenv import load_dotenv
from database import init_db, check_db_exists
from config import BOT_TOKEN
from handlers.auth_handlers import (
    start, auth_code_handler, show_main_menu, profile
)
from handlers.catalog_handlers import (
    show_catalog, show_category_action, show_category_products, 
    show_product_details as catalog_product_details
)
from handlers.search_handlers import (
    show_search_menu, quick_search_price, quick_search_manufacturer,
    quick_search_city, quick_search_name, quick_search_code,
    process_search_value, process_search_callback, show_product_details,
    back_to_results
)
from handlers.subscription_handlers import (
    show_subscription_menu, select_subscription_period, process_payment,
    confirm_payment, cancel_subscription_handler, confirm_cancel_subscription
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
AUTH_CODE = 1
MAIN_MENU = 2
CATEGORY_SELECTION = 3
PRODUCT_SELECTION = 4
PRODUCT_DETAIL = 5
SEARCH_TYPE = 6
QUICK_SEARCH = 7
QUICK_SEARCH_VALUE = 8
SEARCH_RESULTS = 9
SUBSCRIPTION_MENU = 10
SUBSCRIPTION_PERIOD = 11
SUBSCRIPTION_PAYMENT = 12
SUBSCRIPTION_CONFIRMATION = 13
CATEGORY_ACTION = 14

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о боте."""
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message
    
    about_text = (
        "ℹ️ *О боте*\n\n"
        "Этот бот предоставляет доступ к каталогу мебели.\n\n"
        "*Основные функции:*\n"
        "• Просмотр каталога мебели по категориям\n"
        "• Поиск товаров по различным параметрам\n"
        "• Просмотр детальной информации о товарах\n"
        "• Управление подпиской\n\n"
        "*Команды:*\n"
        "/start - Начать работу с ботом\n"
        "/catalog - Открыть каталог мебели\n"
        "/search - Поиск товаров\n"
        "/subscription - Управление подпиской\n"
        "/profile - Просмотр профиля\n"
        "/about - Информация о боте\n\n"
        "Для доступа к полному каталогу необходима активная подписка."
    )
    
    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await message.edit_text(about_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await message.reply_text(about_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_menu":
        await show_main_menu(update, context)
        return MAIN_MENU
    elif query.data == "catalog":
        await show_catalog(update, context)
        return CATEGORY_SELECTION
    elif query.data == "search":
        await show_search_menu(update, context)
        return SEARCH_TYPE
    elif query.data == "about":
        await about(update, context)
        return MAIN_MENU
    elif query.data == "profile":
        await profile(update, context)
        return MAIN_MENU
    elif query.data == "subscription":
        await show_subscription_menu(update, context)
        return SUBSCRIPTION_MENU
    elif query.data == "cancel_subscription":
        await cancel_subscription_handler(update, context)
        return SUBSCRIPTION_MENU
    elif query.data == "confirm_cancel":
        await confirm_cancel_subscription(update, context)
        return MAIN_MENU
    elif query.data == "back_to_results":
        await show_search_menu(update, context)
        return SEARCH_TYPE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущую операцию и возвращает в главное меню."""
    if update.message:
        await update.message.reply_text(
            "Операция отменена. Возвращаемся в главное меню."
        )
    
    await show_main_menu(update, context)
    return ConversationHandler.END

def main():
    """Запускает бота."""
    # Проверяем наличие базы данных и инициализируем её при необходимости
    if not check_db_exists():
        logger.info("База данных не найдена. Инициализация...")
        init_db()
        logger.info("База данных инициализирована.")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создание ConversationHandler для основного меню
    main_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTH_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, auth_code_handler)
            ],
            MAIN_MENU: [
                CallbackQueryHandler(show_catalog, pattern="^catalog$"),
                CallbackQueryHandler(show_search_menu, pattern="^search$"),
                CallbackQueryHandler(about, pattern="^about$"),
                CallbackQueryHandler(profile, pattern="^profile$"),
                CallbackQueryHandler(show_subscription_menu, pattern="^subscription$"),
                CallbackQueryHandler(button)
            ],
            CATEGORY_SELECTION: [
                CallbackQueryHandler(show_category_action, pattern=r"^category_\d+$"),
                CallbackQueryHandler(button)
            ],
            CATEGORY_ACTION: [
                CallbackQueryHandler(show_category_products, pattern=r"^show_all_\d+$"),
                CallbackQueryHandler(button)
            ],
            PRODUCT_SELECTION: [
                CallbackQueryHandler(catalog_product_details, pattern=r"^product_\d+$"),
                CallbackQueryHandler(button)
            ],
            PRODUCT_DETAIL: [
                CallbackQueryHandler(button)
            ],
            SEARCH_TYPE: [
                CallbackQueryHandler(quick_search_price, pattern="^quick_search_price$"),
                CallbackQueryHandler(quick_search_manufacturer, pattern="^quick_search_manufacturer$"),
                CallbackQueryHandler(quick_search_city, pattern="^quick_search_city$"),
                CallbackQueryHandler(quick_search_name, pattern="^quick_search_name$"),
                CallbackQueryHandler(quick_search_code, pattern="^quick_search_code$"),
                CallbackQueryHandler(button)
            ],
            QUICK_SEARCH: [
                CallbackQueryHandler(process_search_callback, pattern=r"^price_\d+$"),
                CallbackQueryHandler(process_search_callback, pattern="^price_any$"),
                CallbackQueryHandler(process_search_callback, pattern=r"^manufacturer_"),
                CallbackQueryHandler(process_search_callback, pattern=r"^city_"),
                CallbackQueryHandler(button)
            ],
            QUICK_SEARCH_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_value)
            ],
            SEARCH_RESULTS: [
                CallbackQueryHandler(show_product_details, pattern=r"^product_\d+$"),
                CallbackQueryHandler(button)
            ],
            SUBSCRIPTION_MENU: [
                CallbackQueryHandler(select_subscription_period, pattern=r"^subscribe_\w+$"),
                CallbackQueryHandler(cancel_subscription_handler, pattern="^cancel_subscription$"),
                CallbackQueryHandler(button)
            ],
            SUBSCRIPTION_PERIOD: [
                CallbackQueryHandler(process_payment, pattern=r"^payment_\w+$"),
                CallbackQueryHandler(button)
            ],
            SUBSCRIPTION_PAYMENT: [
                CallbackQueryHandler(confirm_payment, pattern="^payment_confirmed$"),
                CallbackQueryHandler(button)
            ],
            SUBSCRIPTION_CONFIRMATION: [
                CallbackQueryHandler(button)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # Добавляем обработчики команд
    # Добавляем обработчики команд 2

    application.add_handler(main_conv_handler)
    application.add_handler(CommandHandler("catalog", show_catalog))
    application.add_handler(CommandHandler("search", show_search_menu))
    application.add_handler(CommandHandler("subscription", show_subscription_menu))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("about", about))
    
    # Добавление обработчика для callback_query, которые не обрабатываются ConversationHandler
    application.add_handler(CallbackQueryHandler(button))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling()

if __name__ == "__main__":
    main()
