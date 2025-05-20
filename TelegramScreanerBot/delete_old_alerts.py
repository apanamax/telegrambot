import sqlite3  # Імпорт бібліотеки для роботи з SQLite базою даних

DB_FILE = "crypto_bot.db"  # Назва файлу бази даних

def delete_old_alerts():
    """ Видаляє алерти, що не спрацювали протягом 48 годин """
    conn = sqlite3.connect(DB_FILE)  # Підключення до бази даних
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM alerts
        WHERE created_at < datetime('now', '-48 hours')
    """)  # Видалення алертів, що старші за 48 годин
    conn.commit()  # Застосування змін до БД
    conn.close()  # Закриття з'єднання
    print("Старі алерти видалено успішно")

if __name__ == "__main__":
    delete_old_alerts()  # Виклик функції для видалення старих алертів
