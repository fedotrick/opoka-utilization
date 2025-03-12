import sqlite3

def init_database():
    conn = sqlite3.connect('opoka_usage.db')
    cursor = conn.cursor()
    
    # Таблица для хранения информации об опоках
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS opokas (
        id INTEGER PRIMARY KEY,
        current_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        repair_count INTEGER DEFAULT 0,
        last_use_date TEXT,
        last_repair_date TEXT,
        in_repair BOOLEAN DEFAULT FALSE
    )
    ''')
    
    # Таблица для хранения использований опок
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opoka_id INTEGER,
        use_date TEXT,
        sector TEXT,
        FOREIGN KEY (opoka_id) REFERENCES opokas (id)
    )
    ''')
    
    # Таблица для хранения истории ремонтов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repair_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opoka_id INTEGER,
        repair_date TEXT,
        repair_end_date TEXT,
        uses_before_repair INTEGER,
        FOREIGN KEY (opoka_id) REFERENCES opokas (id)
    )
    ''')
    
    # Инициализация опок (если таблица пустая)
    cursor.execute('SELECT COUNT(*) FROM opokas')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 12):
            cursor.execute('INSERT INTO opokas (id) VALUES (?)', (i,))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database() 