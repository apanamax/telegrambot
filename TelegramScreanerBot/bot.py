import json
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Application, CommandHandler
import time
import threading
from threading import Thread
import asyncio
import requests
import sqlite3
import logging

# Налаштування логування для відстеження інформації та помилок
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHECK_INTERVAL = 10  # Інтервал перевірки цін у секундах

print(f"333")  # Виведення для тесту

async def main():
    """ Головна асинхронна функція для перевірки цін """
    logging.info("Запуск головної функції")  # Логування запуску функції
    print(f"222")  # Виведення для тесту
    while True:
        new_prices = await get_current_prices()  # Отримання нових цін
        if new_prices:
            await check_price_changes(new_prices)  # Перевірка зміни цін
        await asyncio.sleep(CHECK_INTERVAL)  # Очікування перед наступною перевіркою

def get_current_price(symbol):
    """ Отримання поточної ціни для заданого символу """
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol.upper()}'
    logging.info(f"Отримання ціни для {symbol} за URL: {url}")  # Логування запиту до Binance
    
    try:
        response = requests.get(url)  # Виконання HTTP запиту до API Binance
        response.raise_for_status()  # Перевірка на помилки HTTP
        data = response.json()  # Парсинг відповіді JSON
        
        if 'price' in data:  # Якщо ціна присутня в даних
            price = float(data['price'])  # Конвертація ціни в число з плаваючою точкою
            logging.info(f"Поточна ціна {symbol}: {price}")  # Логування поточної ціни
            return price
        else:
            logging.warning(f"Не знайдено ціну у відповіді Binance для {symbol}")  # Попередження, якщо ціна не знайдена
            return None 
    except requests.RequestException as e:
        logging.error(f"Помилка запиту до Binance: {e}")  # Логування помилок запиту
        return None

def create_connection():
    """ Створення підключення до бази даних """
    try:
        conn = sqlite3.connect('crypto_bot.db')  # Підключення до бази даних SQLite
        logging.info("Підключено до бази даних crypto_bot.db")  # Логування успішного підключення
        return conn
    except sqlite3.Error as e:
        logging.error(f"Помилка підключення до БД: {e}")  # Логування помилок підключення
        return None

def check_alerts():
    """ Перевірка спрацьовування алертів """
    logging.info("Перевірка активних алертів")  # Логування початку перевірки алертів
    conn = create_connection()  # Створення підключення до БД
    if conn is None:
        logging.error("Не вдалося підключитися до бази даних")  # Логування помилки підключення
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts")  # Отримання всіх алертів з БД
    alerts = cursor.fetchall()  # Завантаження алертів
    
    for alert in alerts:
        alert_id = alert[0]  # ID алерта
        symbol = alert[1].lstrip('/')  # Символ монети (без слешу)
        alert_price = alert[2]  # Встановлена ціна алерта
        chat_id = alert[3]  # ID чату Telegram для сповіщення
        
        logging.info(f"Перевірка алерта {alert_id} для {symbol} на {alert_price}$")  # Логування перевірки конкретного алерта
        current_price = get_current_price(symbol)  # Отримання поточної ціни
        
        if current_price is not None and round(current_price, 4) == round(alert_price, 4):  # Перевірка чи досягнута ціна
            message = f"🚨 {symbol} досяг {alert_price}$! Поточна ціна: {current_price}$."  # Формування повідомлення
            logging.info(f"Алерт спрацював: {message}")  # Логування спрацьовування алерта
            send_telegram_message(chat_id, message)  # Надсилання повідомлення в Telegram
            
            delete_alert(alert_id)  # Видалення алерта після спрацювання
    
    conn.close()  # Закриття з'єднання з БД

def delete_alert(alert_id):
    """ Видалення алерта з бази даних після його спрацювання """
    logging.info(f"Видалення алерта {alert_id}")  # Логування видалення алерта
    conn = create_connection()  # Створення підключення до БД
    if conn is None:
        logging.error("Не вдалося підключитися до бази даних для видалення алерта")  # Логування помилки підключення
        return
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))  # Видалення алерта з БД
    conn.commit()  # Застосування змін до бази даних
    conn.close()  # Закриття з'єднання з БД
    logging.info(f"Алерт {alert_id} успішно видалено")  # Логування успішного видалення


def send_telegram_message(chat_id, message):
    """ Надсилає повідомлення у Telegram """
    bot_token = 'YOUR_BOT_TOKEN'  # Токен бота для доступу до Telegram API
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'  # URL для надсилання повідомлення
    payload = {
        'chat_id': chat_id,  # ID чату, куди надсилати повідомлення
        'text': message  # Текст повідомлення
    }
    logging.info(f"Надсилання повідомлення у Telegram: {message}")  # Логування повідомлення
    try:
        requests.post(url, data=payload)  # Надсилання POST запиту для повідомлення
    except requests.RequestException as e:
        logging.error(f"Помилка надсилання повідомлення у Telegram: {e}")  # Логування помилок запиту

def check_alerts_periodically():
    """ Запускає перевірку алертів у фоновому потоці """
    while True:
        logging.info("Перевірка алертів у фоновому режимі")  # Логування початку перевірки
        check_alerts()  # Перевірка алертів
        time.sleep(3)  # Затримка між перевірками

alert_thread = threading.Thread(target=check_alerts_periodically)  # Створення потоку для фонової перевірки
alert_thread.daemon = True  # Потік буде завершено при завершенні основної програми
alert_thread.start()  # Запуск фонової перевірки

def add_alert(symbol, price, chat_id):
    """ Додає новий алерт у базу даних """
    conn = create_connection()  # Створення підключення до БД
    cursor = conn.cursor()
    cursor.execute("INSERT INTO alerts (symbol, price, chat_id) VALUES (?, ?, ?)", (symbol, price, chat_id))  # Додавання алерта
    conn.commit()  # Застосування змін до БД
    conn.close()  # Закриття з'єднання
    logging.info(f"Алерт додано: {symbol} - {price}$ для чату {chat_id}")  # Логування успішного додавання

def check_alert(symbol, price):
    """ Перевіряє, чи існує заданий алерт """
    conn = create_connection()  # Підключення до БД
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE symbol = ? AND price = ?", (symbol, price))  # Пошук алерта в БД
    alert = cursor.fetchone()  # Отримання першого знайденого алерта
    conn.close()  # Закриття з'єднання
    return alert  # Повернення алерта, якщо знайдений

def is_valid_symbol(symbol):
    """ Перевіряє, чи існує символ на Binance """
    symbol = symbol.lstrip('/')  # Видалення слешу на початку, якщо він є
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol.upper()}'  # URL для перевірки символу
    logging.info(f"Перевірка валідності символу: {symbol}")  # Логування перевірки
    try:
        response = requests.get(url)  # HTTP запит для перевірки символу
        data = response.json()  # Парсинг відповіді
        return 'price' in data  # Якщо є поле 'price', то символ валідний
    except requests.RequestException as e:
        logging.error(f"Помилка перевірки символу {symbol}: {e}")  # Логування помилки
        return False

async def add_alert_command(update, context):
    """ Команда для додавання алерта через Telegram """
    if len(context.args) != 2:  # Перевірка правильності формату команди
        await update.message.reply_text("Правильний формат: /addalert <символ> <ціна>")
        return

    symbol = context.args[0].upper()  # Символ монети, переведений до верхнього регістру
    price = float(context.args[1])  # Ціна, на яку встановлюється алерт
    chat_id = update.message.chat_id  # ID чату користувача в Telegram

    if not is_valid_symbol(symbol):  # Перевірка валідності символу
        await update.message.reply_text(f"Символ {symbol} не знайдений на Binance. Введіть правильний символ.")
        return

    add_alert(symbol, price, chat_id)  # Додавання алерта в БД
    await update.message.reply_text(f"Алерт для {symbol} встановлений на ціну {price}$.")  # Сповіщення користувача

async def check_alert_command(update, context):
    """ Команда для перевірки наявності алерта через Telegram """
    if len(context.args) != 2:  # Перевірка правильності формату команди
        await update.message.reply_text("Правильний формат: /checkalert <символ> <ціна>")
        return
    
    symbol = context.args[0].upper()  # Символ монети
    price = float(context.args[1])  # Ціна для перевірки
    
    conn = create_connection()  # Підключення до БД
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM alerts WHERE symbol = ? AND price = ?", (symbol, price))  # Перевірка наявності алерта
    alert = cursor.fetchone()  # Отримання першого знайденого алерта
    
    conn.close()  # Закриття з'єднання

    if alert:
        await update.message.reply_text(f"Алерт для {symbol} встановлений на ціну {price}$.")  # Повідомлення про наявність алерта
    else:
        await update.message.reply_text(f"Не знайдено алерта для {symbol} на ціну {price}$.")  # Повідомлення про відсутність алерта

TOKEN = "7567505791:AAE5Yqbd7gG9ydsx2_inJJmnS1Ln6rmh2Ts"  # Токен бота Telegram

application = Application.builder().token(TOKEN).build()  # Створення об'єкта додатку для Telegram бота

application.add_handler(CommandHandler("addalert", add_alert_command))  # Обробник команди для додавання алерта
application.add_handler(CommandHandler("checkalert", check_alert_command))  # Обробник команди для перевірки алерта

def tg_start_pool():
    """ Запускає Telegram бот на постійному polling для отримання повідомлень від користувачів """
    application.run_polling()  # Запуск polling бота для отримання оновлень

tg_pool_thread = None  # Змінна для зберігання потоку, що обробляє polling

CHAT_ID_FILE = "chat_ids.json"  # Файл для збереження ID чатів
try:
    with open(CHAT_ID_FILE, "r") as file:
        config = json.load(file)  # Читання конфігурації з JSON файлу
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"Помилка завантаження JSON: {e}")  # Обробка помилок при читанні JSON
    config = {"TOKEN": "", "CHAT_ID": []}  # Створення порожньої конфігурації
    with open(CHAT_ID_FILE, "w") as file:
        json.dump(config, file)  # Запис порожньої конфігурації до файлу

TOKEN = config.get("TOKEN", "")  # Отримання токену з конфігурації
CHAT_IDS = config.get("CHAT_ID", [])  # Отримання чат ID з конфігурації

if not TOKEN:
    raise ValueError("Токен не знайдено або він порожній!")  # Перевірка на наявність токену

BASE_URL = "https://fapi.binance.com"  # Основний URL для API Binance
ENDPOINT = "/fapi/v1/ticker/price"  # API ендпоінт для отримання цін
THRESHOLDS = [0.01, 0.04, 0.09, 0.20]  # Пороги для змін ціни, які будуть відстежуватись
CHECK_INTERVAL = 1.5  # Інтервал перевірки цін у секундах

bot = Bot(token=TOKEN)  # Ініціалізація Telegram бота за допомогою токену

price_history = {}  # Зберігання історії цін для кожного символу

async def get_current_prices():
    """ Отримує поточні ціни для всіх монет на Binance """
    try:
        response = requests.get(BASE_URL + ENDPOINT, timeout=5)  # Запит до API Binance
        print(f"Запит до API Binance, статус-код: {response.status_code}")
        if response.status_code == 200:
            prices = response.json()  # Парсинг відповіді
            return {item['symbol']: float(item['price']) for item in prices}  # Формування словника цін
        else:
            print(f"Помилка {response.status_code}: {response.text}")  # Логування помилки
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Помилка при запиті до API: {e}")  # Логування помилки запиту
        return {}

async def check_price_changes(new_prices):
    """ Перевіряє зміни цін і надсилає сповіщення, якщо зміни перевищують задані пороги """
    now = datetime.now()  # Поточний час
    messages = []  # Список для повідомлень

    for symbol, new_price in new_prices.items():  # Для кожної монети
        data = price_history.get(symbol)  # Отримання історії цін для символу
        
        if data is None:
            price_history[symbol] = {'open_price': new_price, 'last_checked': now}  # Ініціалізація історії
            continue

        open_price = data['open_price']  # Початкова ціна монети
        last_checked = data['last_checked']  # Час останньої перевірки

        if now - last_checked >= timedelta(minutes=5):  # Якщо з часу останньої перевірки пройшло більше 5 хвилин
            price_history[symbol] = {'open_price': new_price, 'last_checked': now}  # Оновлюємо історію
            continue

        change = (new_price - open_price) / open_price  # Обчислення зміни ціни
        abs_change = abs(change)  # Абсолютна зміна ціни

        for threshold in THRESHOLDS:  # Для кожного порогу
            if abs_change >= threshold and not data.get(f'notified_{threshold}', False):  # Якщо зміна перевищує поріг
                direction = "🟢" if change > 0 else "🔴"  # Визначаємо напрямок зміни
                change_percent = abs_change * 100  # Переведення зміни в проценти
                message = f"{direction} {symbol} BINANCE 5m {change_percent:.1f}%"  # Формування повідомлення
                messages.append(message)  # Додавання повідомлення
                price_history[symbol][f'notified_{threshold}'] = True  # Оновлення статусу повідомлення
                logging.info(f"Зміна ціни {symbol}: {change_percent:.1f}% (поріг {threshold})")  # Логування зміни ціни
                break
        else:
            price_history[symbol]['last_checked'] = now  # Оновлення часу перевірки

    await send_notifications(messages)  # Надсилання повідомлень

async def send_notifications(messages):
    """ Надсилає повідомлення в Telegram для кожного чату """
    if messages:
        full_message = "\n".join(messages)  # Об'єднання всіх повідомлень
        for chat_id in CHAT_IDS:  # Для кожного ID чату
            try:
                await bot.send_message(chat_id=chat_id, text=full_message)  # Надсилання повідомлення
                logging.info(f"Сповіщення відправлено до {chat_id}: {full_message}")  # Логування успіху
            except Exception as e:
                logging.error(f"Помилка надсилання до {chat_id}: {e}")  # Логування помилки

if __name__ == "__main__":
    logging.info("Запуск основного потоку")  # Логування запуску програми
    import nest_asyncio
    nest_asyncio.apply()  # Використання nest_asyncio для підтримки асинхронних функцій в середовищі, яке не підтримує їх нативно

    tg_pool_thread = threading.Thread(target=tg_start_pool)  # Створення потоку для запуску Telegram бота
    tg_pool_thread.daemon = True  # Встановлення потоку як daemon, щоб він завершувався разом з основним процесом
    tg_pool_thread.start()  # Запуск потоку

    asyncio.run(main())  # Запуск головної асинхронної функції
    logging.info("Основний процес завершений")  # Логування завершення процесу
