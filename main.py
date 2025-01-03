import sqlite3
import time
from telebot import TeleBot, types
from os import getenv
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = getenv('API_TOKEN')
bot = TeleBot(API_TOKEN)

# функція для ініціалізації бази даних
def init_db():
    with sqlite3.connect('database.db') as db: # 1 підключення
        cursor = db.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                phone TEXT,
                full_name TEXT,
                is_registered INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                category TEXT,
                name TEXT,
                photo TEXT,
                description TEXT,
                price REAL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product_id INTEGER,
                delivery_option TEXT,
                payment_method TEXT,
                order_status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        ''')
        add_sample_products()  # зразкові товари
        db.commit() # збереження бд

def add_sample_products():
    with sqlite3.connect('database.db') as db: # 2 підключення
        cursor = db.cursor()
        cursor.executescript('''
        delete from products; 
            INSERT INTO products (category, name, photo, description, price) VALUES
                ('ВЕРХ', 'Enfants Riches Deprimes Hoodie (Black)', 'https://imgur.com/a/PncjvBO', 'Найкраща якість 1 до 1, ідеально виконані всі бирки, має архівний вигляд. \nУ наявності розміри M, L.', 6800),
                ('ВЕРХ', 'Enfants Riches Deprimes Hoodie (Red)', 'https://imgur.com/a/GXOUq8J', 'Найкраща якість 1 до 1, ідеально виконані всі бирки, має архівний вигляд. \nУ наявності розміри S, M.', 7000),
                ('ВЕРХ', 'MM6 Archive Logo T-Shirt', 'https://imgur.com/a/wnixDKt', 'Найкраща якість, є всі бирки, якісні матеріали та пошиття, щільний принт. Дуже гарно виглядає, легко поєднувати. \nУ наявності розміри S, M.', 3500),
                ('НИЗ', 'Yori Sport Wide Grey Sweatpant', 'https://imgur.com/a/BJJignK', 'Широкий крій, цікавий дизайн, дуже гарно виглядає на тілі. \nУ наявності розмір S, L.', 4000),
                ('НИЗ', 'Rick Owens belas grinch drkshdw Jeans', 'https://imgur.com/a/G8d6eEN', 'У наявності розміри S, M.', 5500),
                ('ВЗУТТЯ', 'Balenciaga 3XL Extreme Lace (Grey)', 'https://imgur.com/a/utDGiYB', 'У наявності 41-43 розмір.', 5000),
                ('ВЗУТТЯ', 'Balenciaga 3XL Extreme Lace (Red)', 'https://imgur.com/a/6stRip8', 'У наявності 40-42 розмір.', 5200),
                ('АКСЕСУАРИ', 'Comme Des Garçons bag', 'https://imgur.com/a/rNMiUAe', 'Щільні матеріали, багато місця в сумці, можна носити через плече, є всі бирки.', 4000),
                ('АКСЕСУАРИ', 'Maison Margiela Braclet', 'https://imgur.com/a/Z46kuy0', 'Виконано зі срібла. Розмір регулюється.', 6000);
        ''')
        db.commit()

# перша команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    with sqlite3.connect('database.db') as db: # 3 підключення
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()

        if user and user[3]:  # перевірка реєстрації
            bot.reply_to(message, "_Ви вже зареєстровані. Перегляньте асортимент._", parse_mode='Markdown')
            show_main_menu(message)
        else:
            bot.reply_to(message, "_Будь ласка, введіть ваш номер телефону для реєстрації. Обов'язково у форматі +380._", parse_mode='Markdown')

# обробка тел
@bot.message_handler(func=lambda message: message.text.startswith("+"))
def handle_phone(message):
    user_id = message.from_user.id
    phone = message.text
    
    bot.reply_to(message, "_Будь ласка, введіть ваше ПІБ._", parse_mode='Markdown')
    bot.register_next_step_handler(message, handle_full_name, phone)

# обробка піб
def handle_full_name(message, phone):
    full_name = message.text
    user_id = message.from_user.id

    # збереження інфо в базі даних про користувача
    with sqlite3.connect('database.db') as db: # 4 підключення
        cursor = db.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (id, phone, full_name, is_registered) VALUES (?, ?, ?, ?)", 
                       (user_id, phone, full_name, 1))
        db.commit()

    bot.reply_to(message, "_Реєстрація успішна! Перегляньте асортимент._", parse_mode='Markdown')
    show_main_menu(message)

# основне меню
def show_main_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Асортимент"), types.KeyboardButton("Розмірна сітка"), types.KeyboardButton("Розмірна сітка для взуття"), types.KeyboardButton("Умови доставки"))
    bot.send_message(message.chat.id, "_Оберіть опцію:_", reply_markup=keyboard, parse_mode='Markdown')

# вибір асортимент
@bot.message_handler(func=lambda message: message.text == "Асортимент")
def show_catalog_options(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("ВЕРХ"), types.KeyboardButton("НИЗ"), types.KeyboardButton("ВЗУТТЯ"), types.KeyboardButton("АКСЕСУАРИ"))
    bot.send_message(message.chat.id, "_Оберіть категорію асортименту:_", reply_markup=keyboard, parse_mode='Markdown')

# вибір розмірної сітки
@bot.message_handler(func=lambda message: message.text == "Розмірна сітка")
def show_size_chart(message):
    size_chart = (
        "*Розмірна сітка для загального одягу:*\n"
        "\n"
        "_XS: 32-34 (EU)_\n"
        "_S: 36-38 (EU)_\n"
        "_M: 40-42 (EU)_\n"
        "_L: 44-46 (EU)_\n"
        "_XL: 48-50 (EU)_\n"
        "_XXL: 52-54 (EU)_\n"
        "\n"
        "*Вимірювання можуть варіюватися залежно від моделі.*"
    )
    bot.reply_to(message, size_chart, parse_mode='Markdown')

# вибір розмірної сітки для взуття
@bot.message_handler(func=lambda message: message.text == "Розмірна сітка для взуття")
def show_shoe_size_chart(message):
    shoe_size_chart = (
        "*Розмірна сітка для взуття:*\n"
        "\n"
        "_36: 22.5 см_\n"
        "_37: 23.5 см_\n"
        "_38: 24.0 см_\n"
        "_39: 25.0 см_\n"
        "_40: 25.5 см_\n"
        "_41: 26.5 см_\n"
        "_42: 27.0 см_\n"
        "_43: 28.0 см_\n"
        "_44: 29.0 см_\n"
        "_45: 29.5 см_\n"
        "_46: 30.5 см_\n"
        "\n"
        "*Вимірювання можуть варіюватися залежно від моделі.*"
    )
    bot.reply_to(message, shoe_size_chart, parse_mode='Markdown')

# вибір умова доставки
@bot.message_handler(func=lambda message: message.text == "Умови доставки")
def show_delivery_terms(message):
    delivery_terms = (
        "*Умови доставки:*\n"
        "\n"
        "*1. Укрпошта:* стандартна доставка (_3-7 днів_).\n"
        "*2. Нова Пошта:* швидка доставка (_1-2 дні_).\n"
        "*3. Міст Пошта:* доставка до відділення (_2-5 днів_).\n"
        "\n"
        "_Вартість доставки залежить від компанії та місця призначення._"
    )
    bot.reply_to(message, delivery_terms, parse_mode='Markdown')

# вибір категорії
@bot.message_handler(func=lambda message: message.text in ["ВЕРХ", "НИЗ", "ВЗУТТЯ", "АКСЕСУАРИ"])
def show_products(message):
    category = message.text
    with sqlite3.connect('database.db') as db: # останнє підключення
        cursor = db.cursor()
        cursor.execute("SELECT * FROM products WHERE category=?", (category,))
        products = cursor.fetchall()
        
        if products:
            for product in products:
                # інлайн кнопка замовлення під товаром
                keyboard = types.InlineKeyboardMarkup()
                order_button = types.InlineKeyboardButton("🛒 ЗАМОВИТИ", callback_data=f"order_{product[0]}")  # product[0] - айді товару
                keyboard.add(order_button)
                
                # відправка фото з описом товару
                bot.send_photo(message.chat.id, product[3], caption=f"{product[2]}\n{product[4]}\nЦіна: {product[5]}", reply_markup=keyboard)
                time.sleep(0.5)
        else:
            bot.reply_to(message, "")

    # кнопка повернення назад до меню
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("🔙 Повернутись назад до меню"))
    bot.send_message(message.chat.id, "_Натисніть кнопку нижче, щоб повернутись._", reply_markup=keyboard, parse_mode='Markdown')

# опрацювання кнопки повернення назад до меню
@bot.message_handler(func=lambda message: message.text == "🔙 Повернутись назад до меню")
def back_to_main_menu(message):
    show_main_menu(message)

# опрацювання замовлення
@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def handle_order(call):
    product_id = call.data.split("_")[1]  # отримання айді товару
    user_id = call.from_user.id

    bot.answer_callback_query(call.id, "Товар додано!")
    bot.send_message(call.from_user.id, f"Ви замовили товар з ID: {product_id}. Очікуйте на зворотній зв'язок від менеджера. Дякуємо.")

# запуск блок
if __name__ == '__main__':
    init_db() # ініціалізація бд
    bot.polling() # запуск бота
