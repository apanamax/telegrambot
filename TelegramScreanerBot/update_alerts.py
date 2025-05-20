import sqlite3  # Імпорт бібліотеки для роботи з SQLite базою даних

DB_FILE = "crypto_bot.db"  # Назва файлу бази даних

def update_alerts_created_at():
    """ Оновлює стовпець created_at для існуючих алертів """
    conn = sqlite3.connect(DB_FILE)  # Підключення до бази даних
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
    """)  # Оновлюємо записи, де created_at ще не заповнено
    conn.commit()  # Застосування змін до БД
    conn.close()  # Закриття з'єднання
    print("Існуючі алерти оновлено з поточним часом")

if __name__ == "__main__":
    update_alerts_created_at()  # Виклик функції для оновлення алертів
