#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Программа для управления каталогом мебели
Совместима с Telegram-ботом для каталога мебели
Автор: Manus
Дата: 08.04.2025
"""

import os
import sys
import sqlite3
import datetime
import shutil
from pathlib import Path

# Константы
DB_PATH = "catalog.db"
BACKUP_DIR = "backups"
SCRIPT_DIR = Path(__file__).parent.absolute()

# Категории мебели
CATEGORIES = {}

def connect_to_database():
    """Подключение к базе данных"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        create_new_db = input("Хотите создать новую базу данных? (да/нет): ").lower()
        if create_new_db == "да":
            create_database()
        else:
            print(f"Поместите файл catalog.db в директорию {SCRIPT_DIR}")
            sys.exit(1)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        sys.exit(1)

def close_connection(conn):
    """Закрытие соединения с базой данных"""
    if conn:
        conn.close()

def create_database():
    """Создание новой базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Создание таблицы категорий
        cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            description TEXT
        )
        """)
        
        # Создание таблицы городов
        cursor.execute("""
        CREATE TABLE cities (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            region VARCHAR
        )
        """)
        
        # Создание таблицы товаров
        cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            product_code VARCHAR NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            price FLOAT NOT NULL,
            manufacturer VARCHAR,
            size VARCHAR,
            city VARCHAR,
            form VARCHAR,
            mechanism VARCHAR,
            filling VARCHAR,
            lifting_mechanism BOOLEAN,
            has_box BOOLEAN,
            image_path VARCHAR,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)
        
        # Создание таблицы пользователей
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            telegram_id VARCHAR NOT NULL UNIQUE,
            username VARCHAR,
            first_name VARCHAR,
            last_name VARCHAR,
            phone_number VARCHAR,
            email VARCHAR,
            registration_date DATETIME,
            last_activity DATETIME,
            subscription_status VARCHAR(7),
            subscription_expiry DATETIME,
            is_active BOOLEAN
        )
        """)
        
        # Создание таблицы администраторов
        cursor.execute("""
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY,
            username VARCHAR NOT NULL UNIQUE,
            password_hash VARCHAR NOT NULL,
            is_active BOOLEAN,
            last_login DATETIME
        )
        """)
        
        # Создание таблицы подписок
        cursor.execute("""
        CREATE TABLE subscriptions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status VARCHAR(7),
            start_date DATETIME,
            end_date DATETIME,
            payment_id VARCHAR,
            payment_amount FLOAT,
            payment_date DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Добавление стандартных категорий
        categories = [
            (1, "Диваны", "Мягкие диваны различных форм и размеров"),
            (2, "Кресла", "Комфортные кресла для отдыха"),
            (3, "Столы", "Обеденные, журнальные и письменные столы"),
            (4, "Кровати", "Односпальные и двуспальные кровати"),
            (5, "Шкафы", "Шкафы для одежды и книг")
        ]
        
        cursor.executemany("INSERT INTO categories (id, name, description) VALUES (?, ?, ?)", categories)
        
        # Добавление стандартных городов
        cities = [
            (1, "Москва", "Московская область"),
            (2, "Санкт-Петербург", "Ленинградская область"),
            (3, "Екатеринбург", "Свердловская область"),
            (4, "Новосибирск", "Новосибирская область"),
            (5, "Казань", "Республика Татарстан")
        ]
        
        cursor.executemany("INSERT INTO cities (id, name, region) VALUES (?, ?, ?)", cities)
        
        # Добавление администратора по умолчанию
        import hashlib
        password_hash = hashlib.sha256("admin".encode()).hexdigest()
        cursor.execute("""
        INSERT INTO admins (username, password_hash, is_active, last_login)
        VALUES (?, ?, ?, ?)
        """, ("admin", password_hash, True, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        print("База данных успешно создана.")
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
        sys.exit(1)

def load_categories(conn):
    """Загрузка категорий из базы данных"""
    global CATEGORIES
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    CATEGORIES = {row['id']: row['name'] for row in cursor.fetchall()}

def display_menu():
    """Отображение главного меню"""
    print("\n" + "="*50)
    print("УПРАВЛЕНИЕ КАТАЛОГОМ МЕБЕЛИ".center(50))
    print("="*50)
    print("1. Просмотр каталога")
    print("2. Добавление нового товара")
    print("3. Редактирование товара")
    print("4. Удаление товара")
    print("5. Управление категориями")
    print("6. Поиск товаров")
    print("7. Статистика")
    print("8. Экспорт/Импорт данных")
    print("0. Выход")
    print("="*50)
    
    choice = input("Выберите действие (0-8): ")
    return choice

def view_catalog_menu():
    """Меню просмотра каталога"""
    print("\n" + "="*50)
    print("ПРОСМОТР КАТАЛОГА".center(50))
    print("="*50)
    print("1. Просмотр всех товаров")
    print("2. Просмотр товаров по категориям")
    print("3. Просмотр товаров по ценовому диапазону")
    print("4. Просмотр товаров по городу")
    print("5. Просмотр товаров по производителю")
    print("0. Назад")
    print("="*50)
    
    choice = input("Выберите действие (0-5): ")
    return choice

def view_all_products(conn):
    """Просмотр всех товаров"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.category_id, p.name
    """)
    products = cursor.fetchall()
    
    if not products:
        print("\nКаталог пуст.")
        return
    
    print("\n" + "="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def view_products_by_category(conn):
    """Просмотр товаров по категориям"""
    print("\n" + "="*50)
    print("КАТЕГОРИИ ТОВАРОВ".center(50))
    print("="*50)
    
    for cat_id, cat_name in CATEGORIES.items():
        print(f"{cat_id}. {cat_name}")
    
    print("0. Назад")
    print("="*50)
    
    category_id = input("Выберите категорию: ")
    if category_id == "0":
        return
    
    try:
        category_id = int(category_id)
        if category_id not in CATEGORIES:
            print("Неверный выбор категории.")
            return
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_code, p.name, p.price, p.manufacturer, p.city, p.size
        FROM products p
        WHERE p.category_id = ?
        ORDER BY p.name
    """, (category_id,))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nВ категории '{CATEGORIES[category_id]}' нет товаров.")
        return
    
    print("\n" + "="*100)
    print(f"ТОВАРЫ В КАТЕГОРИИ '{CATEGORIES[category_id]}'".center(100))
    print("="*100)
    print(f"{'ID':<5}{'Код':<10}{'Название':<30}{'Цена':<10}{'Производитель':<20}{'Город':<15}{'Размер':<10}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['name']:<30}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}{product.get('size', ''):<10}")
    
    print("="*100)
    print(f"Всего товаров в категории: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def view_products_by_price_range(conn):
    """Просмотр товаров по ценовому диапазону"""
    print("\n" + "="*50)
    print("ПОИСК ПО ЦЕНОВОМУ ДИАПАЗОНУ".center(50))
    print("="*50)
    
    min_price = input("Введите минимальную цену (или Enter для любой): ")
    max_price = input("Введите максимальную цену (или Enter для любой): ")
    
    query = """
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if min_price:
        try:
            min_price = float(min_price)
            query += " AND p.price >= ?"
            params.append(min_price)
        except ValueError:
            print("Неверный формат минимальной цены. Используется значение по умолчанию.")
    
    if max_price:
        try:
            max_price = float(max_price)
            query += " AND p.price <= ?"
            params.append(max_price)
        except ValueError:
            print("Неверный формат максимальной цены. Используется значение по умолчанию.")
    
    query += " ORDER BY p.price"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    if not products:
        print("\nТовары в указанном ценовом диапазоне не найдены.")
        return
    
    print("\n" + "="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего найдено товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def view_products_by_city(conn):
    """Просмотр товаров по городу"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM products WHERE city IS NOT NULL AND city != '' ORDER BY city")
    cities = [row['city'] for row in cursor.fetchall()]
    
    if not cities:
        print("\nНет товаров с указанным городом.")
        return
    
    print("\n" + "="*50)
    print("ГОРОДА".center(50))
    print("="*50)
    
    for i, city in enumerate(cities, 1):
        print(f"{i}. {city}")
    
    print("0. Назад")
    print("="*50)
    
    choice = input("Выберите город: ")
    if choice == "0":
        return
    
    try:
        choice = int(choice)
        if choice < 1 or choice > len(cities):
            print("Неверный выбор города.")
            return
        selected_city = cities[choice - 1]
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.city = ?
        ORDER BY p.category_id, p.name
    """, (selected_city,))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nВ городе '{selected_city}' нет товаров.")
        return
    
    print("\n" + "="*90)
    print(f"ТОВАРЫ В ГОРОДЕ '{selected_city}'".center(90))
    print("="*90)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<30}{'Цена':<10}{'Производитель':<20}")
    print("="*90)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<30}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}")
    
    print("="*90)
    print(f"Всего товаров в городе '{selected_city}': {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def view_products_by_manufacturer(conn):
    """Просмотр товаров по производителю"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT manufacturer FROM products WHERE manufacturer IS NOT NULL AND manufacturer != '' ORDER BY manufacturer")
    manufacturers = [row['manufacturer'] for row in cursor.fetchall()]
    
    if not manufacturers:
        print("\nНет товаров с указанным производителем.")
        return
    
    print("\n" + "="*50)
    print("ПРОИЗВОДИТЕЛИ".center(50))
    print("="*50)
    
    for i, manufacturer in enumerate(manufacturers, 1):
        print(f"{i}. {manufacturer}")
    
    print("0. Назад")
    print("="*50)
    
    choice = input("Выберите производителя: ")
    if choice == "0":
        return
    
    try:
        choice = int(choice)
        if choice < 1 or choice > len(manufacturers):
            print("Неверный выбор производителя.")
            return
        selected_manufacturer = manufacturers[choice - 1]
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.manufacturer = ?
        ORDER BY p.category_id, p.name
    """, (selected_manufacturer,))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nНет товаров производителя '{selected_manufacturer}'.")
        return
    
    print("\n" + "="*90)
    print(f"ТОВАРЫ ПРОИЗВОДИТЕЛЯ '{selected_manufacturer}'".center(90))
    print("="*90)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<30}{'Цена':<10}{'Город':<20}")
    print("="*90)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<30}{product['price']:<10.2f}{product.get('city', ''):<20}")
    
    print("="*90)
    print(f"Всего товаров производителя '{selected_manufacturer}': {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def view_product_details(conn, product_id):
    """Просмотр подробной информации о товаре"""
    try:
        product_id = int(product_id)
    except ValueError:
        print("Неверный формат ID товара.")
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,))
    product = cursor.fetchone()
    
    if not product:
        print(f"Товар с ID {product_id} не найден.")
        return
    
    print("\n" + "="*70)
    print(f"ИНФОРМАЦИЯ О ТОВАРЕ".center(70))
    print("="*70)
    print(f"ID: {product['id']}")
    print(f"Код товара: {product['product_code']}")
    print(f"Категория: {product['category_name']}")
    print(f"Название: {product['name']}")
    print(f"Описание: {product['description']}")
    print(f"Цена: {product['price']:.2f} руб.")
    print(f"Производитель: {product.get('manufacturer', 'Не указан')}")
    print(f"Размер: {product.get('size', 'Не указан')}")
    print(f"Город: {product.get('city', 'Не указан')}")
    
    if product['category_id'] in [1, 2]:  # Диваны или кресла
        print(f"Форма: {product.get('form', 'Не указана')}")
        print(f"Механизм: {product.get('mechanism', 'Не указан')}")
        print(f"Наполнение: {product.get('filling', 'Не указано')}")
    
    if product['category_id'] == 4:  # Кровати
        print(f"Подъемный механизм: {'Да' if product.get('lifting_mechanism') else 'Нет'}")
    
    print(f"Путь к изображению: {product.get('image_path', 'Не указан')}")
    print(f"Дата создания: {product['created_at']}")
    print(f"Дата обновления: {product['updated_at']}")
    print("="*70)
    
    input("\nНажмите Enter для возврата...")

def add_new_product(conn):
    """Добавление нового товара"""
    print("\n" + "="*50)
    print("ДОБАВЛЕНИЕ НОВОГО ТОВАРА".center(50))
    print("="*50)
    
    # Выбор категории
    print("Выберите категорию товара:")
    for cat_id, cat_name in CATEGORIES.items():
        print(f"{cat_id}. {cat_name}")
    
    try:
        category_id = int(input("Категория: "))
        if category_id not in CATEGORIES:
            print("Неверная категория.")
            return
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    # Генерация нового кода товара
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(SUBSTR(product_code, 2) AS INTEGER)) FROM products")
    max_code = cursor.fetchone()[0]
    new_code = f"#{max_code + 1:03d}" if max_code else "#001"
    
    # Ввод основной информации
    product_code = input(f"Код товара [{new_code}]: ") or new_code
    name = input("Название товара: ")
    if not name:
        print("Название товара обязательно для заполнения.")
        return
    
    description = input("Описание товара: ")
    
    try:
        price = float(input("Цена (руб.): "))
    except ValueError:
        print("Неверный формат цены.")
        return
    
    manufacturer = input("Производитель: ")
    size = input("Размер (например, 200x100 см): ")
    city = input("Город: ")
    image_path = input("Путь к изображению (например, /images/product.jpg): ")
    
    # Дополнительные поля в зависимости от категории
    form = ""
    mechanism = ""
    filling = ""
    lifting_mechanism = False
    has_box = False
    
    if category_id == 1:  # Диваны
        form = input("Форма дивана (прямой, угловой и т.д.): ")
        mechanism = input("Механизм трансформации (еврокнижка, дельфин и т.д.): ")
        filling = input("Наполнение (пенополиуретан, латекс и т.д.): ")
    elif category_id == 2:  # Кресла
        form = input("Тип кресла (стандартное, с высокой спинкой и т.д.): ")
        mechanism = input("Механизм (качание, реклайнер и т.д.): ")
        filling = input("Наполнение (пенополиуретан, латекс и т.д.): ")
    elif category_id == 4:  # Кровати
        form = input("Форма кровати (прямоугольная, круглая и т.д.): ")
        lifting_mechanism_input = input("Наличие подъемного механизма (да/нет): ").lower()
        lifting_mechanism = lifting_mechanism_input == "да"
        filling = input("Тип матраса (ортопедический, пружинный и т.д.): ")
    elif category_id == 5:  # Шкафы
        form = input("Тип шкафа (платяной, книжный и т.д.): ")
        has_box_input = input("Наличие ящиков (да/нет): ").lower()
        has_box = has_box_input == "да"
    
    # Текущая дата и время
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Добавление товара в базу данных
    try:
        cursor.execute("""
            INSERT INTO products (
                product_code, category_id, name, description, price, 
                manufacturer, size, city, form, mechanism, filling, 
                lifting_mechanism, has_box, image_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_code, category_id, name, description, price,
            manufacturer, size, city, form, mechanism, filling,
            lifting_mechanism, has_box, image_path, now, now
        ))
        conn.commit()
        print(f"\nТовар '{name}' успешно добавлен в каталог.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка при добавлении товара: {e}")

def edit_product(conn):
    """Редактирование товара"""
    print("\n" + "="*50)
    print("РЕДАКТИРОВАНИЕ ТОВАРА".center(50))
    print("="*50)
    
    product_id = input("Введите ID или код товара для редактирования: ")
    
    cursor = conn.cursor()
    
    # Поиск товара по ID или коду
    if product_id.isdigit():
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    else:
        cursor.execute("SELECT * FROM products WHERE product_code = ?", (product_id,))
    
    product = cursor.fetchone()
    
    if not product:
        print("Товар не найден.")
        return
    
    print(f"\nРедактирование товара: {product['name']} (ID: {product['id']}, Код: {product['product_code']})")
    print("\nОставьте поле пустым, если не хотите его менять.")
    
    # Ввод новых значений
    name = input(f"Название [{product['name']}]: ") or product['name']
    description = input(f"Описание [{product['description']}]: ") or product['description']
    
    price_str = input(f"Цена [{product['price']}]: ")
    price = float(price_str) if price_str else product['price']
    
    manufacturer = input(f"Производитель [{product.get('manufacturer', '')}]: ") or product.get('manufacturer', '')
    size = input(f"Размер [{product.get('size', '')}]: ") or product.get('size', '')
    city = input(f"Город [{product.get('city', '')}]: ") or product.get('city', '')
    image_path = input(f"Путь к изображению [{product.get('image_path', '')}]: ") or product.get('image_path', '')
    
    # Дополнительные поля в зависимости от категории
    form = product.get('form', '')
    mechanism = product.get('mechanism', '')
    filling = product.get('filling', '')
    lifting_mechanism = product.get('lifting_mechanism', False)
    has_box = product.get('has_box', False)
    
    if product['category_id'] == 1:  # Диваны
        form = input(f"Форма [{form}]: ") or form
        mechanism = input(f"Механизм [{mechanism}]: ") or mechanism
        filling = input(f"Наполнение [{filling}]: ") or filling
    elif product['category_id'] == 2:  # Кресла
        form = input(f"Тип кресла [{form}]: ") or form
        mechanism = input(f"Механизм [{mechanism}]: ") or mechanism
        filling = input(f"Наполнение [{filling}]: ") or filling
    elif product['category_id'] == 4:  # Кровати
        form = input(f"Форма кровати [{form}]: ") or form
        lifting_mechanism_input = input(f"Наличие подъемного механизма ({'да' if lifting_mechanism else 'нет'}): ").lower()
        if lifting_mechanism_input in ["да", "нет"]:
            lifting_mechanism = lifting_mechanism_input == "да"
        filling = input(f"Тип матраса [{filling}]: ") or filling
    elif product['category_id'] == 5:  # Шкафы
        form = input(f"Тип шкафа [{form}]: ") or form
        has_box_input = input(f"Наличие ящиков ({'да' if has_box else 'нет'}): ").lower()
        if has_box_input in ["да", "нет"]:
            has_box = has_box_input == "да"
    
    # Текущая дата и время для обновления
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Обновление товара в базе данных
    try:
        cursor.execute("""
            UPDATE products SET
                name = ?, description = ?, price = ?, 
                manufacturer = ?, size = ?, city = ?, form = ?, 
                mechanism = ?, filling = ?, lifting_mechanism = ?, 
                has_box = ?, image_path = ?, updated_at = ?
            WHERE id = ?
        """, (
            name, description, price, 
            manufacturer, size, city, form, 
            mechanism, filling, lifting_mechanism, 
            has_box, image_path, now, product['id']
        ))
        conn.commit()
        print(f"\nТовар '{name}' успешно обновлен.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка при обновлении товара: {e}")

def delete_product(conn):
    """Удаление товара"""
    print("\n" + "="*50)
    print("УДАЛЕНИЕ ТОВАРА".center(50))
    print("="*50)
    
    product_id = input("Введите ID или код товара для удаления: ")
    
    cursor = conn.cursor()
    
    # Поиск товара по ID или коду
    if product_id.isdigit():
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    else:
        cursor.execute("SELECT * FROM products WHERE product_code = ?", (product_id,))
    
    product = cursor.fetchone()
    
    if not product:
        print("Товар не найден.")
        return
    
    print(f"\nВы собираетесь удалить товар: {product['name']} (ID: {product['id']}, Код: {product['product_code']})")
    confirm = input("Вы уверены? (да/нет): ").lower()
    
    if confirm != "да":
        print("Удаление отменено.")
        return
    
    try:
        # Удаление товара
        cursor.execute("DELETE FROM products WHERE id = ?", (product['id'],))
        
        conn.commit()
        print(f"\nТовар '{product['name']}' успешно удален.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка при удалении товара: {e}")

def manage_categories(conn):
    """Управление категориями"""
    print("\n" + "="*50)
    print("УПРАВЛЕНИЕ КАТЕГОРИЯМИ".center(50))
    print("="*50)
    print("1. Просмотр всех категорий")
    print("2. Добавление новой категории")
    print("3. Редактирование категории")
    print("4. Удаление категории")
    print("0. Назад")
    print("="*50)
    
    choice = input("Выберите действие (0-4): ")
    
    if choice == "1":
        view_all_categories(conn)
    elif choice == "2":
        add_new_category(conn)
    elif choice == "3":
        edit_category(conn)
    elif choice == "4":
        delete_category(conn)

def view_all_categories(conn):
    """Просмотр всех категорий"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.description, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY c.id
    """)
    categories = cursor.fetchall()
    
    print("\n" + "="*70)
    print(f"{'ID':<5}{'Название':<20}{'Описание':<30}{'Кол-во товаров':<15}")
    print("="*70)
    
    for category in categories:
        print(f"{category['id']:<5}{category['name']:<20}{category['description']:<30}{category['product_count']:<15}")
    
    print("="*70)
    print(f"Всего категорий: {len(categories)}")
    
    input("\nНажмите Enter для возврата...")

def add_new_category(conn):
    """Добавление новой категории"""
    print("\n" + "="*50)
    print("ДОБАВЛЕНИЕ НОВОЙ КАТЕГОРИИ".center(50))
    print("="*50)
    
    name = input("Название категории: ")
    if not name:
        print("Название категории обязательно для заполнения.")
        return
    
    description = input("Описание категории: ")
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO categories (name, description)
            VALUES (?, ?)
        """, (name, description))
        conn.commit()
        print(f"\nКатегория '{name}' успешно добавлена.")
        
        # Обновление глобального словаря категорий
        load_categories(conn)
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка при добавлении категории: {e}")

def edit_category(conn):
    """Редактирование категории"""
    print("\n" + "="*50)
    print("РЕДАКТИРОВАНИЕ КАТЕГОРИИ".center(50))
    print("="*50)
    
    for cat_id, cat_name in CATEGORIES.items():
        print(f"{cat_id}. {cat_name}")
    
    category_id = input("\nВведите ID категории для редактирования: ")
    
    try:
        category_id = int(category_id)
        if category_id not in CATEGORIES:
            print("Категория не найдена.")
            return
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    category = cursor.fetchone()
    
    print(f"\nРедактирование категории: {category['name']} (ID: {category['id']})")
    print("\nОставьте поле пустым, если не хотите его менять.")
    
    name = input(f"Название [{category['name']}]: ") or category['name']
    description = input(f"Описание [{category['description']}]: ") or category['description']
    
    try:
        cursor.execute("""
            UPDATE categories SET
                name = ?, description = ?
            WHERE id = ?
        """, (name, description, category_id))
        conn.commit()
        print(f"\nКатегория '{name}' успешно обновлена.")
        
        # Обновление глобального словаря категорий
        load_categories(conn)
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка при обновлении категории: {e}")

def delete_category(conn):
    """Удаление категории"""
    print("\n" + "="*50)
    print("УДАЛЕНИЕ КАТЕГОРИИ".center(50))
    print("="*50)
    
    for cat_id, cat_name in CATEGORIES.items():
        print(f"{cat_id}. {cat_name}")
    
    category_id = input("\nВведите ID категории для удаления: ")
    
    try:
        category_id = int(category_id)
        if category_id not in CATEGORIES:
            print("Категория не найдена.")
            return
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    cursor = conn.cursor()
    
    # Проверка наличия товаров в категории
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE category_id = ?", (category_id,))
    product_count = cursor.fetchone()['count']
    
    if product_count > 0:
        print(f"\nКатегория '{CATEGORIES[category_id]}' содержит {product_count} товаров.")
        print("Удаление невозможно. Сначала удалите или переместите товары из этой категории.")
        return
    
    print(f"\nВы собираетесь удалить категорию: {CATEGORIES[category_id]} (ID: {category_id})")
    confirm = input("Вы уверены? (да/нет): ").lower()
    
    if confirm != "да":
        print("Удаление отменено.")
        return
    
    try:
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        print(f"\nКатегория '{CATEGORIES[category_id]}' успешно удалена.")
        
        # Обновление глобального словаря категорий
        load_categories(conn)
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка при удалении категории: {e}")

def search_products(conn):
    """Поиск товаров"""
    print("\n" + "="*50)
    print("ПОИСК ТОВАРОВ".center(50))
    print("="*50)
    print("1. Поиск по названию")
    print("2. Поиск по описанию")
    print("3. Поиск по производителю")
    print("4. Поиск по городу")
    print("5. Расширенный поиск")
    print("0. Назад")
    print("="*50)
    
    choice = input("Выберите действие (0-5): ")
    
    if choice == "1":
        search_by_name(conn)
    elif choice == "2":
        search_by_description(conn)
    elif choice == "3":
        search_by_manufacturer(conn)
    elif choice == "4":
        search_by_city(conn)
    elif choice == "5":
        advanced_search(conn)

def search_by_name(conn):
    """Поиск товаров по названию"""
    print("\n" + "="*50)
    print("ПОИСК ПО НАЗВАНИЮ".center(50))
    print("="*50)
    
    search_term = input("Введите часть названия товара: ")
    if not search_term:
        print("Поисковый запрос не может быть пустым.")
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.name LIKE ?
        ORDER BY p.name
    """, (f"%{search_term}%",))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nТовары с названием, содержащим '{search_term}', не найдены.")
        return
    
    print("\n" + "="*100)
    print(f"РЕЗУЛЬТАТЫ ПОИСКА ПО НАЗВАНИЮ: '{search_term}'".center(100))
    print("="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего найдено товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def search_by_description(conn):
    """Поиск товаров по описанию"""
    print("\n" + "="*50)
    print("ПОИСК ПО ОПИСАНИЮ".center(50))
    print("="*50)
    
    search_term = input("Введите часть описания товара: ")
    if not search_term:
        print("Поисковый запрос не может быть пустым.")
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.description LIKE ?
        ORDER BY p.name
    """, (f"%{search_term}%",))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nТовары с описанием, содержащим '{search_term}', не найдены.")
        return
    
    print("\n" + "="*100)
    print(f"РЕЗУЛЬТАТЫ ПОИСКА ПО ОПИСАНИЮ: '{search_term}'".center(100))
    print("="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего найдено товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def search_by_manufacturer(conn):
    """Поиск товаров по производителю"""
    print("\n" + "="*50)
    print("ПОИСК ПО ПРОИЗВОДИТЕЛЮ".center(50))
    print("="*50)
    
    search_term = input("Введите название производителя: ")
    if not search_term:
        print("Поисковый запрос не может быть пустым.")
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.manufacturer LIKE ?
        ORDER BY p.name
    """, (f"%{search_term}%",))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nТовары производителя, содержащего '{search_term}', не найдены.")
        return
    
    print("\n" + "="*100)
    print(f"РЕЗУЛЬТАТЫ ПОИСКА ПО ПРОИЗВОДИТЕЛЮ: '{search_term}'".center(100))
    print("="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего найдено товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def search_by_city(conn):
    """Поиск товаров по городу"""
    print("\n" + "="*50)
    print("ПОИСК ПО ГОРОДУ".center(50))
    print("="*50)
    
    search_term = input("Введите название города: ")
    if not search_term:
        print("Поисковый запрос не может быть пустым.")
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.city LIKE ?
        ORDER BY p.name
    """, (f"%{search_term}%",))
    products = cursor.fetchall()
    
    if not products:
        print(f"\nТовары в городе, содержащем '{search_term}', не найдены.")
        return
    
    print("\n" + "="*100)
    print(f"РЕЗУЛЬТАТЫ ПОИСКА ПО ГОРОДУ: '{search_term}'".center(100))
    print("="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего найдено товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def advanced_search(conn):
    """Расширенный поиск товаров"""
    print("\n" + "="*50)
    print("РАСШИРЕННЫЙ ПОИСК".center(50))
    print("="*50)
    
    # Выбор категории (необязательно)
    print("Выберите категорию товара (0 - любая):")
    for cat_id, cat_name in CATEGORIES.items():
        print(f"{cat_id}. {cat_name}")
    
    try:
        category_id = int(input("Категория (0-5): "))
        if category_id != 0 and category_id not in CATEGORIES:
            print("Неверная категория.")
            return
    except ValueError:
        print("Неверный ввод. Введите число.")
        return
    
    # Ввод параметров поиска
    name = input("Название товара (или часть): ")
    manufacturer = input("Производитель (или часть): ")
    city = input("Город (или часть): ")
    
    min_price = input("Минимальная цена (или Enter для любой): ")
    max_price = input("Максимальная цена (или Enter для любой): ")
    
    # Формирование запроса
    query = """
        SELECT p.id, p.product_code, c.name as category, p.name, p.price, p.manufacturer, p.city
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if category_id != 0:
        query += " AND p.category_id = ?"
        params.append(category_id)
    
    if name:
        query += " AND p.name LIKE ?"
        params.append(f"%{name}%")
    
    if manufacturer:
        query += " AND p.manufacturer LIKE ?"
        params.append(f"%{manufacturer}%")
    
    if city:
        query += " AND p.city LIKE ?"
        params.append(f"%{city}%")
    
    if min_price:
        try:
            min_price = float(min_price)
            query += " AND p.price >= ?"
            params.append(min_price)
        except ValueError:
            print("Неверный формат минимальной цены. Используется значение по умолчанию.")
    
    if max_price:
        try:
            max_price = float(max_price)
            query += " AND p.price <= ?"
            params.append(max_price)
        except ValueError:
            print("Неверный формат максимальной цены. Используется значение по умолчанию.")
    
    query += " ORDER BY p.category_id, p.name"
    
    # Выполнение запроса
    cursor = conn.cursor()
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    if not products:
        print("\nТовары, соответствующие заданным критериям, не найдены.")
        return
    
    print("\n" + "="*100)
    print("РЕЗУЛЬТАТЫ РАСШИРЕННОГО ПОИСКА".center(100))
    print("="*100)
    print(f"{'ID':<5}{'Код':<10}{'Категория':<15}{'Название':<25}{'Цена':<10}{'Производитель':<20}{'Город':<15}")
    print("="*100)
    
    for product in products:
        print(f"{product['id']:<5}{product['product_code']:<10}{product['category']:<15}{product['name']:<25}{product['price']:<10.2f}{product.get('manufacturer', ''):<20}{product.get('city', ''):<15}")
    
    print("="*100)
    print(f"Всего найдено товаров: {len(products)}")
    
    product_id = input("\nВведите ID товара для просмотра подробной информации (или 0 для возврата): ")
    if product_id != "0":
        view_product_details(conn, product_id)

def show_statistics(conn):
    """Отображение статистики"""
    print("\n" + "="*50)
    print("СТАТИСТИКА КАТАЛОГА".center(50))
    print("="*50)
    
    cursor = conn.cursor()
    
    # Общее количество товаров
    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()['count']
    
    # Количество товаров по категориям
    cursor.execute("""
        SELECT c.name, COUNT(p.id) as count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY count DESC
    """)
    category_stats = cursor.fetchall()
    
    # Средняя цена товаров
    cursor.execute("SELECT AVG(price) as avg_price FROM products")
    avg_price = cursor.fetchone()['avg_price'] or 0
    
    # Минимальная и максимальная цена
    cursor.execute("SELECT MIN(price) as min_price, MAX(price) as max_price FROM products")
    price_range = cursor.fetchone()
    min_price = price_range['min_price'] or 0
    max_price = price_range['max_price'] or 0
    
    # Количество товаров по городам
    cursor.execute("""
        SELECT city, COUNT(*) as count
        FROM products
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city
        ORDER BY count DESC
        LIMIT 5
    """)
    city_stats = cursor.fetchall()
    
    # Количество товаров по производителям
    cursor.execute("""
        SELECT manufacturer, COUNT(*) as count
        FROM products
        WHERE manufacturer IS NOT NULL AND manufacturer != ''
        GROUP BY manufacturer
        ORDER BY count DESC
        LIMIT 5
    """)
    manufacturer_stats = cursor.fetchall()
    
    # Вывод статистики
    print(f"Общее количество товаров: {total_products}")
    print(f"Средняя цена товара: {avg_price:.2f} руб.")
    print(f"Ценовой диапазон: от {min_price:.2f} до {max_price:.2f} руб.")
    
    print("\nРаспределение товаров по категориям:")
    print("-"*50)
    for category in category_stats:
        print(f"{category['name']}: {category['count']} товаров")
    
    if city_stats:
        print("\nТоп-5 городов по количеству товаров:")
        print("-"*50)
        for city in city_stats:
            print(f"{city['city']}: {city['count']} товаров")
    
    if manufacturer_stats:
        print("\nТоп-5 производителей по количеству товаров:")
        print("-"*50)
        for manufacturer in manufacturer_stats:
            print(f"{manufacturer['manufacturer']}: {manufacturer['count']} товаров")
    
    print("="*50)
    input("\nНажмите Enter для возврата...")

def export_import_data(conn):
    """Экспорт/импорт данных"""
    print("\n" + "="*50)
    print("ЭКСПОРТ/ИМПОРТ ДАННЫХ".center(50))
    print("="*50)
    print("1. Экспортировать базу данных")
    print("2. Импортировать базу данных")
    print("3. Создать резервную копию")
    print("4. Восстановить из резервной копии")
    print("0. Назад")
    print("="*50)
    
    choice = input("Выберите действие (0-4): ")
    
    if choice == "1":
        export_database(conn)
    elif choice == "2":
        import_database(conn)
    elif choice == "3":
        create_backup(conn)
    elif choice == "4":
        restore_from_backup(conn)

def export_database(conn):
    """Экспорт базы данных"""
    print("\n" + "="*50)
    print("ЭКСПОРТ БАЗЫ ДАННЫХ".center(50))
    print("="*50)
    
    export_path = input("Введите путь для сохранения файла базы данных (или Enter для сохранения в текущей директории): ")
    
    if not export_path:
        export_path = os.path.join(SCRIPT_DIR, "export_catalog.db")
    
    try:
        # Закрытие соединения перед копированием
        close_connection(conn)
        
        # Копирование файла базы данных
        shutil.copy2(DB_PATH, export_path)
        
        print(f"\nБаза данных успешно экспортирована в файл: {export_path}")
        
        # Повторное подключение к базе данных
        conn = connect_to_database()
        load_categories(conn)
        return conn
    except Exception as e:
        print(f"Ошибка при экспорте базы данных: {e}")
        
        # Повторное подключение к базе данных в случае ошибки
        conn = connect_to_database()
        load_categories(conn)
        return conn

def import_database(conn):
    """Импорт базы данных"""
    print("\n" + "="*50)
    print("ИМПОРТ БАЗЫ ДАННЫХ".center(50))
    print("="*50)
    
    import_path = input("Введите путь к файлу базы данных для импорта: ")
    
    if not import_path or not os.path.exists(import_path):
        print("Файл не найден.")
        return conn
    
    try:
        # Закрытие соединения перед заменой
        close_connection(conn)
        
        # Создание резервной копии текущей базы данных
        backup_path = os.path.join(SCRIPT_DIR, f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(DB_PATH, backup_path)
        
        # Замена файла базы данных
        shutil.copy2(import_path, DB_PATH)
        
        print(f"\nБаза данных успешно импортирована из файла: {import_path}")
        print(f"Резервная копия сохранена в файле: {backup_path}")
        
        # Повторное подключение к базе данных
        conn = connect_to_database()
        load_categories(conn)
        return conn
    except Exception as e:
        print(f"Ошибка при импорте базы данных: {e}")
        print("Восстановление из резервной копии...")
        
        try:
            # Восстановление из резервной копии
            shutil.copy2(backup_path, DB_PATH)
            print(f"База данных восстановлена из резервной копии: {backup_path}")
        except Exception as restore_error:
            print(f"Ошибка при восстановлении из резервной копии: {restore_error}")
        
        # Повторное подключение к базе данных
        conn = connect_to_database()
        load_categories(conn)
        return conn

def create_backup(conn):
    """Создание резервной копии базы данных"""
    print("\n" + "="*50)
    print("СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ".center(50))
    print("="*50)
    
    # Создание директории для резервных копий, если она не существует
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Генерация имени файла резервной копии
    backup_filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(SCRIPT_DIR, BACKUP_DIR, backup_filename)
    
    try:
        # Закрытие соединения перед копированием
        close_connection(conn)
        
        # Копирование файла базы данных
        shutil.copy2(DB_PATH, backup_path)
        
        print(f"\nРезервная копия успешно создана: {backup_path}")
        
        # Повторное подключение к базе данных
        conn = connect_to_database()
        load_categories(conn)
        return conn
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        
        # Повторное подключение к базе данных в случае ошибки
        conn = connect_to_database()
        load_categories(conn)
        return conn

def restore_from_backup(conn):
    """Восстановление из резервной копии"""
    print("\n" + "="*50)
    print("ВОССТАНОВЛЕНИЕ ИЗ РЕЗЕРВНОЙ КОПИИ".center(50))
    print("="*50)
    
    # Проверка наличия директории с резервными копиями
    if not os.path.exists(BACKUP_DIR):
        print("Директория с резервными копиями не найдена.")
        return conn
    
    # Получение списка резервных копий
    backup_files = [f for f in os.listdir(os.path.join(SCRIPT_DIR, BACKUP_DIR)) if f.startswith("backup_") and f.endswith(".db")]
    
    if not backup_files:
        print("Резервные копии не найдены.")
        return conn
    
    # Сортировка резервных копий по дате создания (от новых к старым)
    backup_files.sort(reverse=True)
    
    print("Доступные резервные копии:")
    for i, backup_file in enumerate(backup_files, 1):
        # Извлечение даты и времени из имени файла
        date_time_str = backup_file[7:-3]  # Удаление "backup_" и ".db"
        try:
            date_time = datetime.datetime.strptime(date_time_str, '%Y%m%d_%H%M%S')
            date_time_formatted = date_time.strftime('%d.%m.%Y %H:%M:%S')
        except ValueError:
            date_time_formatted = date_time_str
        
        print(f"{i}. {backup_file} (создана {date_time_formatted})")
    
    print("0. Отмена")
    
    choice = input("\nВыберите резервную копию для восстановления: ")
    
    if choice == "0":
        return conn
    
    try:
        choice = int(choice)
        if choice < 1 or choice > len(backup_files):
            print("Неверный выбор.")
            return conn
        
        selected_backup = backup_files[choice - 1]
        backup_path = os.path.join(SCRIPT_DIR, BACKUP_DIR, selected_backup)
        
        # Закрытие соединения перед заменой
        close_connection(conn)
        
        # Создание резервной копии текущей базы данных
        current_backup_path = os.path.join(SCRIPT_DIR, BACKUP_DIR, f"pre_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(DB_PATH, current_backup_path)
        
        # Замена файла базы данных
        shutil.copy2(backup_path, DB_PATH)
        
        print(f"\nБаза данных успешно восстановлена из резервной копии: {selected_backup}")
        print(f"Текущее состояние сохранено в файле: {os.path.basename(current_backup_path)}")
        
        # Повторное подключение к базе данных
        conn = connect_to_database()
        load_categories(conn)
        return conn
    except ValueError:
        print("Неверный ввод. Введите число.")
        return conn
    except Exception as e:
        print(f"Ошибка при восстановлении из резервной копии: {e}")
        
        # Повторное подключение к базе данных в случае ошибки
        conn = connect_to_database()
        load_categories(conn)
        return conn

def main():
    """Основная функция"""
    print("Программа для управления каталогом мебели")
    print("Версия 1.0 (08.04.2025)")
    print("Совместима с Telegram-ботом для каталога мебели")
    
    # Подключение к базе данных
    conn = connect_to_database()
    
    # Загрузка категорий
    load_categories(conn)
    
    while True:
        choice = display_menu()
        
        if choice == "1":
            catalog_choice = view_catalog_menu()
            if catalog_choice == "1":
                view_all_products(conn)
            elif catalog_choice == "2":
                view_products_by_category(conn)
            elif catalog_choice == "3":
                view_products_by_price_range(conn)
            elif catalog_choice == "4":
                view_products_by_city(conn)
            elif catalog_choice == "5":
                view_products_by_manufacturer(conn)
        elif choice == "2":
            add_new_product(conn)
        elif choice == "3":
            edit_product(conn)
        elif choice == "4":
            delete_product(conn)
        elif choice == "5":
            manage_categories(conn)
        elif choice == "6":
            search_products(conn)
        elif choice == "7":
            show_statistics(conn)
        elif choice == "8":
            conn = export_import_data(conn)
        elif choice == "0":
            break
        else:
            print("Неверный выбор. Пожалуйста, выберите действие из меню.")
    
    # Закрытие соединения с базой данных
    close_connection(conn)
    print("Программа завершена.")

if __name__ == "__main__":
    main()
