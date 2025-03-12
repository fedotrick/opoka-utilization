import sqlite3

def init_repair_dates():
    conn = sqlite3.connect('opoka_usage.db')
    cursor = conn.cursor()
    
    # Очищаем таблицу repair_history
    cursor.execute('DELETE FROM repair_history')
    
    # История ремонтов для каждой опоки
    repair_history = {
        1: [
            ("2024-05-15", "2024-05-20"),
            ("2024-09-10", "2024-09-15"),
            ("2025-02-24", "2025-02-24")
        ],
        2: [
            ("2024-06-01", "2024-06-05"),
            ("2024-11-15", "2024-11-20"),
            ("2025-03-01", "2025-03-01")
        ],
        3: [
            ("2024-07-10", "2024-07-15"),
            ("2024-12-20", "2024-12-25"),
            ("2025-03-05", None)  # текущий ремонт
        ],
        4: [
            ("2025-02-12", "2025-02-12")
        ],
        5: [
            ("2025-03-01", "2025-03-01")
        ],
        6: [
            ("2025-03-10", None)
        ],
        7: [
            ("2025-02-14", "2025-02-14")
        ],
        8: [
            ("2025-03-11", None)
        ],
        9: [
            ("2025-03-10", None)
        ],
        10: [
            ("2024-07-06", None)
        ],
        11: [
            ("2025-02-12", "2025-02-12")
        ]
    }
    
    # Вставляем все записи о ремонтах
    for opoka_id, repairs in repair_history.items():
        for repair_date, repair_end_date in repairs:
            cursor.execute('''
            INSERT INTO repair_history (opoka_id, repair_date, repair_end_date)
            VALUES (?, ?, ?)
            ''', (opoka_id, repair_date, repair_end_date))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_repair_dates() 