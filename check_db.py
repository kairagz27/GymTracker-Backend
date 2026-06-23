import sqlite3

# Подключаемся к нашему файлу базы данных
conn = sqlite3.connect("gym_tracker.db")
cursor = conn.cursor()

# Проверяем программы
print("=== ТВОИ ПРОГРАММЫ ===")
cursor.execute("SELECT id, name FROM programs")
print(cursor.fetchall())

# Проверяем упражнения
print("\n=== ТВОИ УПРАЖНЕНИЯ ===")
cursor.execute("SELECT id, name, day_id FROM exercises")
print(cursor.fetchall())

# Проверяем подходы
print("\n=== ПОДХОДЫ (Вес, Повторения) ===")
cursor.execute("SELECT weight, reps FROM exercise_sets")
print(cursor.fetchall())

conn.close()