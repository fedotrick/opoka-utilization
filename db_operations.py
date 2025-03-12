import sqlite3
from datetime import datetime
import pandas as pd
import json

class OpokaDB:
    def __init__(self):
        self.db_path = 'opoka_usage.db'
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def send_to_repair(self, opoka_id):
        """Отправляет опоку в ремонт"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Получаем текущее количество использований
            cursor.execute('''
            SELECT current_count FROM opokas WHERE id = ?
            ''', (opoka_id,))
            current_count = cursor.fetchone()[0]
            
            # Добавляем запись в историю ремонтов
            cursor.execute('''
            INSERT INTO repair_history (opoka_id, repair_date, uses_before_repair)
            VALUES (?, ?, ?)
            ''', (opoka_id, current_date, current_count))
            
            # Обновляем статус опоки
            cursor.execute('''
            UPDATE opokas 
            SET in_repair = TRUE,
                repair_count = repair_count + 1,
                current_count = 0,
                last_repair_date = ?
            WHERE id = ?
            ''', (current_date, opoka_id))
            
            conn.commit()
        finally:
            conn.close()
    
    def return_from_repair(self, opoka_id):
        """Возвращает опоку из ремонта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Обновляем дату окончания ремонта
            cursor.execute('''
            UPDATE repair_history 
            SET repair_end_date = ?
            WHERE opoka_id = ? AND repair_end_date IS NULL
            ''', (current_date, opoka_id))
            
            # Обновляем статус опоки
            cursor.execute('''
            UPDATE opokas 
            SET in_repair = FALSE,
                current_count = 0
            WHERE id = ?
            ''', (opoka_id,))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_repair_history(self, opoka_id):
        """Получает историю ремонтов опоки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            repair_date,
            COALESCE(repair_end_date, 
                (SELECT MIN(use_date) 
                 FROM usage_records 
                 WHERE opoka_id = repair_history.opoka_id 
                 AND use_date > repair_date)
            ) as end_date,
            uses_before_repair
        FROM repair_history
        WHERE opoka_id = ?
        ORDER BY repair_date DESC
        ''', (opoka_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        return history
    
    def import_repair_history_from_json(self, json_file='opoka_usage_history.json'):
        """Импортирует историю ремонтов из JSON файла"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Очищаем таблицу repair_history
            cursor.execute('DELETE FROM repair_history')
            
            with open(json_file, 'r') as f:
                history = json.load(f)
                
            for opoka_id, data in history.items():
                if data.get('last_repair_date'):
                    cursor.execute('''
                    INSERT INTO repair_history (opoka_id, repair_date)
                    VALUES (?, ?)
                    ''', (int(opoka_id), data['last_repair_date']))
            
            conn.commit()
        finally:
            conn.close()
    
    def update_from_excel(self, excel_file):
        """Обновляет данные из Excel файла"""
        df = pd.read_excel(excel_file)
        df['Плавка_дата'] = pd.to_datetime(df['Плавка_дата'], format='%d.%m.%Y')
        df = df.sort_values('Плавка_дата')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Очищаем таблицу usage_records
            cursor.execute('DELETE FROM usage_records')
            
            # Словарь для подсчета общего количества использований
            total_counts = {i: 0 for i in range(1, 12)}
            
            # Обрабатываем каждую строку из Excel
            for _, row in df.iterrows():
                date = row['Плавка_дата'].strftime('%Y-%m-%d')
                sectors = {
                    'A': row['Сектор_A_опоки'],
                    'B': row['Сектор_B_опоки'],
                    'C': row['Сектор_C_опоки'],
                    'D': row['Сектор_D_опоки']
                }
                
                for sector, opoka_num in sectors.items():
                    if pd.notna(opoka_num):
                        opoka_num = int(opoka_num)
                        
                        # Добавляем запись использования
                        cursor.execute('''
                        INSERT INTO usage_records (opoka_id, use_date, sector)
                        VALUES (?, ?, ?)
                        ''', (opoka_num, date, sector))
                        
                        # Увеличиваем общее количество использований
                        total_counts[opoka_num] = total_counts.get(opoka_num, 0) + 1
            
            # Обновляем статистику для каждой опоки
            for opoka_id in range(1, 12):
                # Получаем последний ремонт
                cursor.execute('''
                SELECT repair_date 
                FROM repair_history 
                WHERE opoka_id = ? 
                ORDER BY repair_date DESC 
                LIMIT 1
                ''', (opoka_id,))
                last_repair = cursor.fetchone()
                
                # Считаем текущие использования (после последнего ремонта)
                if last_repair:
                    cursor.execute('''
                    SELECT COUNT(*) 
                    FROM usage_records 
                    WHERE opoka_id = ? 
                    AND date(use_date) >= date(?)
                    ''', (opoka_id, last_repair[0]))
                    current_count = cursor.fetchone()[0]
                else:
                    current_count = total_counts[opoka_id]
                
                # Обновляем статистику опоки
                cursor.execute('''
                UPDATE opokas 
                SET current_count = ?,
                    total_count = ?,
                    repair_count = (SELECT COUNT(*) FROM repair_history WHERE opoka_id = ?),
                    last_repair_date = ?,
                    in_repair = (
                        SELECT COUNT(*) > 0 
                        FROM repair_history 
                        WHERE opoka_id = ? 
                        AND repair_end_date IS NULL
                        AND repair_date = (
                            SELECT MAX(repair_date) 
                            FROM repair_history 
                            WHERE opoka_id = ?
                        )
                    )
                WHERE id = ?
                ''', (
                    current_count,
                    total_counts[opoka_id],
                    opoka_id,
                    last_repair[0] if last_repair else None,
                    opoka_id,
                    opoka_id,
                    opoka_id
                ))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_opoka_stats(self, opoka_id):
        """Получает статистику для конкретной опоки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM opokas WHERE id = ?
        ''', (opoka_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'current_count': result[1],
                'total_count': result[2],
                'repair_count': result[3],
                'last_use_date': result[4],
                'last_repair_date': result[5],
                'in_repair': bool(result[6])
            }
        return None
    
    def get_all_stats(self):
        """Получает статистику для всех опок"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT 
                o.id,
                o.current_count,
                o.total_count,
                o.repair_count,
                o.last_use_date,
                o.last_repair_date,
                (SELECT COUNT(*) FROM repair_history 
                 WHERE opoka_id = o.id 
                 AND repair_end_date IS NULL 
                 AND repair_date = (
                     SELECT MAX(repair_date) 
                     FROM repair_history 
                     WHERE opoka_id = o.id
                 )
                ) as is_in_repair
            FROM opokas o
            ''')
            results = cursor.fetchall()
            
            return {str(row[0]): {
                'count': row[1],
                'total_count': row[2],
                'repair_count': row[3],
                'last_use': row[4],
                'last_repair_date': row[5],
                'in_repair': bool(row[6])
            } for row in results}
        finally:
            conn.close()
    
    def get_monthly_stats(self, year, month):
        """Получает статистику за конкретный месяц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        start_date = f'{year}-{month:02d}-01'
        end_date = f'{year}-{month:02d}-31'
        
        cursor.execute('''
        SELECT COUNT(*) as uses,
               (SELECT COUNT(*) FROM opokas 
                WHERE last_repair_date BETWEEN ? AND ?) as repairs
        FROM usage_records 
        WHERE use_date BETWEEN ? AND ?
        ''', (start_date, end_date, start_date, end_date))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_uses': result[0],
            'repairs_count': result[1]
        }

    def manual_set_repair_end_date(self, opoka_id, end_date):
        """Ручная установка даты окончания ремонта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE repair_history 
            SET repair_end_date = ?
            WHERE opoka_id = ? AND repair_end_date IS NULL
            ''', (end_date, opoka_id))
            
            cursor.execute('''
            UPDATE opokas 
            SET in_repair = FALSE,
                current_count = 0
            WHERE id = ?
            ''', (opoka_id,))
            
            conn.commit()
        finally:
            conn.close() 