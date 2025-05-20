import sqlite3  # Імпорт бібліотеки для роботи з SQLite базою даних

DB_FILE = "crypto_bot.db"  # Назва файлу бази даних

def add_created_at_column():
    """ Додає стовпець created_at до таблиці alerts, якщо він ще не існує """
    conn = sqlite3.connect(DB_FILE)  # Підключення до бази даних
    cursor = conn.cursor()

    # Перевірка, чи є вже стовпець created_at в таблиці alerts
    cursor.execute("PRAGMA table_info(alerts);")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    if 'created_at' not in column_names:
        try:
            cursor.execute("""
                ALTER TABLE alerts ADD COLUMN created_at TIMESTAMP
            """)  # Додаємо стовпець без значення за замовчуванням
            conn.commit()  # Застосування змін до БД
            print("Стовпець created_at успішно додано в таблицю alerts.")
        except sqlite3.OperationalError as e:
            print(f"Помилка: {e}")
    else:
        print("Стовпець 'created_at' вже існує в таблиці alerts.")
    
    conn.close()  # Закриття з'єднання

if __name__ == "__main__":
    add_created_at_column()  # Викликаємо функцію для додавання стовпця
