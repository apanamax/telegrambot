import sqlite3  # Імпорт бібліотеки для роботи з SQLite базою даних

def create_connection():
    """ Функція для створення підключення до бази даних """
    conn = sqlite3.connect('crypto_bot.db')  # Підключення до бази даних
    return conn

def get_alerts():
    """ Отримання всіх алертів з бази даних """
    conn = create_connection()  # Підключення до бази даних
    cursor = conn.cursor()  # Створення курсора для виконання запитів
    cursor.execute("SELECT * FROM alerts;")  # Запит для отримання всіх алертів
    alerts = cursor.fetchall()  # Отримання всіх результатів запиту
    conn.close()  # Закриття підключення до бази даних
    return alerts  # Повертаємо отримані алерти

def check_specific_alert(symbol, price):
    """ Перевірка наявності конкретного алерта для заданого символу та ціни """
    conn = create_connection()  # Підключення до бази даних
    cursor = conn.cursor()  # Створення курсора для виконання запитів
    
    # Запит для перевірки конкретного алерта
    cursor.execute("SELECT symbol, price FROM alerts WHERE symbol = ? AND price = ?", (symbol, price))
    alert = cursor.fetchone()  # Отримуємо перший знайдений алерт (якщо є)
    
    conn.close()  # Закриття підключення до бази даних
    
    return alert  # Повертаємо знайдений алерт або None

def check_alert_command(update, context):
    """ Обробка команди /checkalert для перевірки наявності алерта """
    if len(context.args) != 2:  # Перевірка, чи правильно вказано аргументи
        update.message.reply_text("Правильний формат: /checkalert <символ> <ціна>")
        return
    
    symbol = context.args[0].upper()  # Символ монети (наприклад, "ETHUSDT")
    price = float(context.args[1])  # Ціна як float
    
    alert = check_specific_alert(symbol, price)  # Викликаємо функцію для перевірки алерта
    
    if alert:  # Якщо алерт знайдено
        update.message.reply_text(f"Алерт для {alert[0]} встановлений на ціну {alert[1]}$.")
    else:  # Якщо алерт не знайдено
        update.message.reply_text(f"Не знайдено алерта для {symbol} на ціну {price}$.")

def add_alert(symbol, price, chat_id):
    """ Додає новий алерт до бази даних """
    conn = create_connection()  # Створення підключення до бази даних
    cursor = conn.cursor()  # Створення курсора для виконання SQL-запиту
    cursor.execute("INSERT INTO alerts (symbol, price, chat_id) VALUES (?, ?, ?)", (symbol, price, chat_id))  # Вставка нового алерта
    conn.commit()  # Збереження змін у базі даних
    conn.close()  # Закриття підключення до бази даних

def create_tables():
    """ Створення таблиць у базі даних (якщо ще не існують) """
    try:
        conn = sqlite3.connect('crypto_bot.db')  # Підключення до бази даних
        cursor = conn.cursor()  # Створення курсора для виконання запитів

        # Створення таблиці chat_ids (для зберігання chat_id користувачів)
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS chat_ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE
        );
        ''')
        conn.commit()  # Збереження змін у базі даних

        # Створення таблиці alerts (для зберігання алертів користувачів)
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            chat_id INTEGER,
            FOREIGN KEY(chat_id) REFERENCES chat_ids(id)
        );
        ''')
        conn.commit()  # Збереження змін у базі даних

        # Перевірка наявності стовпця created_at у таблиці alerts
        cursor.execute("PRAGMA table_info(alerts);")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]  # Отримуємо імена стовпців

        if 'created_at' not in column_names:
            # Додаємо стовпець created_at (якщо його ще немає)
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("ALTER TABLE alerts ADD COLUMN created_at TIMESTAMP;")
            cursor.execute("PRAGMA foreign_keys = ON;")
            conn.commit()  # Збереження змін у базі даних

            # Оновлюємо існуючі записи в alerts, додаючи поточний timestamp у створений стовпець
            cursor.execute("""
                UPDATE alerts
                SET created_at = CURRENT_TIMESTAMP
                WHERE created_at IS NULL;
            """)
            conn.commit()  # Збереження змін у базі даних

        # Створення таблиці price_history (для зберігання історії цін монет)
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS price_history (
            symbol TEXT PRIMARY KEY,
            open_price REAL,
            last_checked DATETIME
        );
        ''')
        conn.commit()  # Збереження змін у базі даних

        print("Таблиці створено успішно!")

    except sqlite3.Error as e:
        print(f"Помилка: {e}")  # Виведення помилки при підключенні до бази даних або виконанні запиту
    finally:
        conn.close()  # Закриття підключення до бази даних

if __name__ == "__main__":  # Якщо цей файл є головним скриптом
    create_tables()  # Викликаємо функцію для створення таблиць у базі даних