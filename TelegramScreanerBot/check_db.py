import sqlite3
from datetime import datetime, timedelta

DB_FILE = "crypto_bot.db"

def delete_old_alerts():
    """ Видаляє алерти, яким більше 48 годин """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Теперішній час
    now = datetime.now()

    # Запит для видалення алертів, створених більше ніж 48 годин тому
    cursor.execute("""
        DELETE FROM alerts
        WHERE created_at < ?;
    """, (now - timedelta(hours=48),))

    conn.commit()  # Застосовуємо зміни до бази даних
    conn.close()  # Закриваємо підключення

    print("Старі алерти видалені успішно!")

def check_alerts_in_db():
    """ Перевірка наявності алертів в базі даних """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts")
    alerts = cursor.fetchall()

    if not alerts:
        print("❌ Алерти не знайдено в базі!")
    else:
        print("✅ Виявлені алерти в базі:")
        for alert in alerts:
            print(alert)

    conn.close()

if __name__ == "__main__":
    delete_old_alerts()  # Видаляємо старі алерти
    check_alerts_in_db()  # Перевіряємо наявність алертів в базі
