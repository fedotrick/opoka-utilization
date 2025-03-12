import sqlite3

def init_repair_dates():
    conn = sqlite3.connect('opoka_usage.db')
    cursor = conn.cursor()
    
    # Очищаем таблицу repair_history
    cursor.execute('DELETE FROM repair_history')
    
    # Вставляем правильные даты последнего ремонта
    repair_dates = {
        # opoka_id: (repair_date, repair_end_date)
        1: ("2025-02-24", "2025-02-24"),  # не в ремонте
        2: ("2025-03-01", "2025-03-01"),  # не в ремонте
        3: ("2025-03-05", None),          # в ремонте
        4: ("2025-02-12", "2025-02-12"),  # не в ремонте
        5: ("2025-03-01", "2025-03-01"),  # не в ремонте
        6: ("2025-03-10", None),          # в ремонте
        7: ("2025-02-14", "2025-02-14"),  # не в ремонте
        8: ("2025-03-11", None),          # в ремонте
        9: ("2025-03-10", None),          # в ремонте
        10: ("2024-07-06", None),         # в ремонте
        11: ("2025-02-12", "2025-02-12")  # не в ремонте
    }
    
    for opoka_id, (repair_date, repair_end_date) in repair_dates.items():
        cursor.execute('''
        INSERT INTO repair_history (opoka_id, repair_date, repair_end_date)
        VALUES (?, ?, ?)
        ''', (opoka_id, repair_date, repair_end_date))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_repair_dates() 