import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, 
                              QComboBox, QPushButton, QHeaderView, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
import pandas as pd
from datetime import datetime, timedelta
import calendar
import json

class OpokaDataManager:
    def __init__(self):
        self.filename = 'opoka_usage_history.json'
        self.excel_file = 'plavka.xlsx'
        
    def load_history(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                # Добавляем дополнительные поля, если их нет
                for key in data:
                    if isinstance(data[key], (int, float)):
                        data[key] = {
                            "count": data[key],
                            "total_count": data[key],
                            "repair_count": 0,
                            "last_use": None,
                            "last_repair_date": None,  # Дата последнего ремонта
                            "in_repair": False
                        }
                    elif "total_count" not in data[key]:
                        data[key].update({
                            "total_count": data[key]["count"],
                            "repair_count": 0
                        })
                    elif "last_repair_date" not in data[key]:
                        data[key].update({
                            "last_repair_date": None
                        })
                return data
        except FileNotFoundError:
            return {str(i): {
                "count": 0,
                "total_count": 0,
                "repair_count": 0,
                "last_use": None,
                "last_repair_date": None,
                "in_repair": False
            } for i in range(1, 12)}

    def save_history(self, history):
        with open(self.filename, 'w') as f:
            json.dump(history, f, indent=4)

class DataCache:
    def __init__(self):
        self.df = None
        self.last_update = None
        
    def get_dataframe(self):
        current_time = datetime.now()
        if self.df is None or (current_time - self.last_update).seconds > 300:  # Обновляем каждые 5 минут
            self.df = pd.read_excel('plavka.xlsx')
            self.last_update = current_time
        return self.df

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Учет использования опок")
        self.setFixedSize(1255, 800)
        
        self.current_date = datetime.now()
        self.opoka_data_manager = OpokaDataManager()
        self.data_cache = DataCache()
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Создаем верхнюю панель
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        # Добавляем дату
        date_label = QLabel(f"Дата: {self.current_date.strftime('%d.%m.%Y')}")
        date_label.setStyleSheet("font-size: 12px;")
        
        # Кнопка пересчета
        self.recalc_button = QPushButton("Пересчитать историю")
        self.recalc_button.clicked.connect(self.recalculate_and_update)
        
        # Выпадающий список с месяцами
        self.month_dropdown = QComboBox()
        self.setup_month_dropdown()
        
        header_layout.addWidget(date_label)
        header_layout.addWidget(self.recalc_button)
        header_layout.addWidget(self.month_dropdown)
        header_layout.addStretch()
        
        # Добавляем статус
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 12px;")
        
        # Создаем основной контейнер для таблицы и статистики
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Создаем таблицу
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDBDBD;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 2px;
                font-size: 11px;
            }
        """)
        
        # Создаем виджет статистики
        self.stats_widget = QFrame()
        self.stats_widget.setFixedWidth(250)
        self.stats_widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.stats_layout = QVBoxLayout(self.stats_widget)
        
        content_layout.addWidget(self.table, stretch=4)
        content_layout.addWidget(self.stats_widget)
        
        # Добавляем все в главный layout
        main_layout.addWidget(header_widget)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(content_widget)
        
        # Инициализируем таблицу
        self.update_table(self.current_date)
        self.update_repair_dates()

    def setup_month_dropdown(self):
        months = []
        for year in range(self.current_date.year - 1, self.current_date.year + 1):
            for month in range(1, 13):
                if year == self.current_date.year and month > self.current_date.month:
                    continue
                month_str = f"{year}-{month:02d}"
                month_name = f"{calendar.month_name[month]} {year}"
                self.month_dropdown.addItem(month_name, month_str)
        
        current_month_idx = self.month_dropdown.findData(
            f"{self.current_date.year}-{self.current_date.month:02d}"
        )
        self.month_dropdown.setCurrentIndex(current_month_idx)
        self.month_dropdown.currentIndexChanged.connect(self.on_month_changed)

    def on_month_changed(self):
        selected_date = datetime.strptime(
            self.month_dropdown.currentData(), 
            '%Y-%m'
        )
        self.update_table(selected_date)

    def update_table(self, selected_date):
        try:
            df = pd.read_excel(self.opoka_data_manager.excel_file)
            df['Плавка_дата'] = pd.to_datetime(df['Плавка_дата'], format='%d.%m.%Y')
            usage_history = self.opoka_data_manager.load_history()
            
            # Обновляем счетчики использований после ремонта
            for opoka_num in range(1, 12):
                last_repair_date = usage_history[str(opoka_num)]["last_repair_date"]
                if last_repair_date:
                    last_repair_date = datetime.strptime(last_repair_date, '%Y-%m-%d')
                    
                    # Считаем использования после последнего ремонта
                    current_uses = 0
                    filtered_df = df[df['Плавка_дата'] > last_repair_date]
                    
                    for _, row in filtered_df.iterrows():
                        day_uses = sum(1 for col in ['Сектор_A_опоки', 'Сектор_B_опоки', 
                                                   'Сектор_C_опоки', 'Сектор_D_опоки']
                                     if pd.notna(row[col]) and int(row[col]) == opoka_num)
                        current_uses += day_uses
                    
                    usage_history[str(opoka_num)]["count"] = current_uses
                    
                    # Если достигнут лимит использований, отправляем в ремонт
                    if current_uses >= 100:
                        self.send_to_repair(opoka_num)
            
            self.opoka_data_manager.save_history(usage_history)
            
            # Обновляем таблицу
            self.table.clear()
            
            # Настраиваем таблицу
            self.table.setRowCount(11)  # для опок 1-11
            self.table.setColumnCount(32)  # номер опоки + 31 день
            
            # Устанавливаем заголовки
            headers = ['Опока'] + [str(i) for i in range(1, 32)]
            self.table.setHorizontalHeaderLabels(headers)
            
            # Настраиваем ширину колонок
            self.table.horizontalHeader().setDefaultSectionSize(28)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(0, 45)
            
            # Заполняем данные
            for opoka_num in range(1, 12):
                # Номер опоки
                self.table.setItem(opoka_num-1, 0, 
                                 QTableWidgetItem(f"№{opoka_num}"))
                
                # Данные по дням
                for day in range(1, 32):
                    day_data = df[
                        (df['Плавка_дата'].dt.day == day) &
                        (df['Плавка_дата'].dt.month == selected_date.month) &
                        (df['Плавка_дата'].dt.year == selected_date.year)
                    ]
                    
                    count = 0
                    for col in ['Сектор_A_опоки', 'Сектор_B_опоки', 
                               'Сектор_C_опоки', 'Сектор_D_опоки']:
                        count += len(day_data[day_data[col] == opoka_num])
                    
                    item = QTableWidgetItem(str(count) if count > 0 else "")
                    if count > 0:
                        item.setBackground(QColor("#C8E6C9"))  # Зеленый цвет
                    self.table.setItem(opoka_num-1, day, item)
            
            # Обновляем статистику
            self.update_statistics()
            
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def get_row_color(self, opoka_data):
        """Определяет цвет фона строки на основе текущего количества использований"""
        count = int(opoka_data["count"])
        
        if opoka_data.get("in_repair"):
            return "#BDBDBD"  # Серый для ремонта
        elif opoka_data.get("auto_reset"):
            return "#E3F2FD"  # Голубой для простоя
        elif count >= 91:
            return "#FFCDD2"  # Красный для 91-100
        elif count >= 80:
            return "#FFF9C4"  # Желтый для 80-90
        return "#FFFFFF"  # Белый для остальных случаев

    def update_statistics(self):
        # Очищаем текущую статистику
        for i in reversed(range(self.stats_layout.count())): 
            self.stats_layout.itemAt(i).widget().deleteLater()
        
        # Добавляем заголовок
        header = QLabel("Статистика использования:")
        header.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.stats_layout.addWidget(header)
        
        # Создаем заголовок таблицы статистики
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setSpacing(2)
        
        headers = ["№", "Тек.", "Всего", "Рем.", "Статус"]
        widths = [25, 35, 40, 35, 50]
        
        for header_text, width in zip(headers, widths):
            label = QLabel(header_text)
            label.setFixedWidth(width)
            label.setStyleSheet("font-size: 11px;")
            header_layout.addWidget(label)
        
        header_widget.setStyleSheet("background-color: #CFD8DC; border-radius: 3px;")
        self.stats_layout.addWidget(header_widget)
        
        # Добавляем данные статистики
        usage_history = self.opoka_data_manager.load_history()
        
        for i in range(1, 12):
            opoka_data = usage_history[str(i)]
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(2)
            
            # Добавляем данные
            data = [
                str(i),
                str(opoka_data["count"]),
                str(opoka_data["total_count"]),
                str(opoka_data["repair_count"]),
                self.get_status_text(opoka_data)
            ]
            
            # Определяем цвет текста для значения count
            count_color = "red" if int(opoka_data["count"]) >= 91 else "black"
            
            for idx, (text, width) in enumerate(zip(data, widths)):
                label = QLabel(text)
                label.setFixedWidth(width)
                # Применяем красный цвет только к полю "Тек." если count >= 91
                if idx == 1 and count_color == "red":
                    label.setStyleSheet("font-size: 11px; color: red; font-weight: bold;")
                else:
                    label.setStyleSheet("font-size: 11px;")
                row_layout.addWidget(label)
            
            # Добавляем кнопку ремонта
            repair_button = QPushButton()
            repair_button.setFixedSize(QSize(30, 30))
            repair_button.clicked.connect(
                lambda checked, num=i: self.toggle_repair(num)
            )
            repair_button.setText("🔧" if not opoka_data["in_repair"] else "↩")
            row_layout.addWidget(repair_button)
            
            # Устанавливаем цвет фона строки
            bg_color = self.get_row_color(opoka_data)
            row_widget.setStyleSheet(f"""
                background-color: {bg_color}; 
                border-radius: 3px;
                margin: 1px;
                padding: 2px;
            """)
            
            self.stats_layout.addWidget(row_widget)

    def get_status_text(self, opoka_data):
        if opoka_data.get("in_repair"):
            return "В ремонте"
        elif opoka_data.get("auto_reset"):
            return f"Простой ({opoka_data.get('unused_days', 0)} дней)"
        return "Готова"

    def get_status_color(self, opoka_data):
        if opoka_data.get("in_repair"):
            return "#BDBDBD"  # Серый
        elif opoka_data.get("auto_reset"):
            return "#E3F2FD"  # Голубой
        elif opoka_data["count"] >= 100:
            return "#FFCDD2"  # Красный
        return "#C8E6C9"  # Зеленый

    def toggle_repair(self, opoka_num):
        usage_history = self.opoka_data_manager.load_history()
        if usage_history[str(opoka_num)]["in_repair"]:
            self.return_from_repair(opoka_num)
        else:
            self.send_to_repair(opoka_num)

    def send_to_repair(self, opoka_num):
        usage_history = self.opoka_data_manager.load_history()
        usage_history[str(opoka_num)]["repair_count"] += 1
        usage_history[str(opoka_num)]["count"] = 0  # Сбрасываем текущий счетчик
        usage_history[str(opoka_num)]["in_repair"] = True
        usage_history[str(opoka_num)]["last_use"] = None
        usage_history[str(opoka_num)]["last_repair_date"] = datetime.now().strftime('%Y-%m-%d')
        self.opoka_data_manager.save_history(usage_history)
        self.update_table(datetime.strptime(self.month_dropdown.currentData(), '%Y-%m'))

    def return_from_repair(self, opoka_num):
        usage_history = self.opoka_data_manager.load_history()
        usage_history[str(opoka_num)]["in_repair"] = False
        usage_history[str(opoka_num)]["count"] = 0  # Сбрасываем счетчик после ремонта
        self.opoka_data_manager.save_history(usage_history)
        self.update_table(datetime.strptime(self.month_dropdown.currentData(), '%Y-%m'))

    def recalculate_and_update(self):
        self.recalculate_history()
        self.update_table(self.current_date)

    def update_repair_dates(self):
        usage_history = self.opoka_data_manager.load_history()
        
        # 28.01.2025 - опоки 2 и 5
        for opoka in ['2', '5']:
            usage_history[opoka].update({
                "last_repair_date": "2025-01-28",
                "in_repair": False,
                "auto_reset": False
            })
        
        self.opoka_data_manager.save_history(usage_history)

    def recalculate_history(self):
        try:
            df = pd.read_excel(self.opoka_data_manager.excel_file)
            df['Плавка_дата'] = pd.to_datetime(df['Плавка_дата'], format='%d.%m.%Y')
            df = df.sort_values('Плавка_дата')
            
            history = {str(i): {
                "count": 0,
                "total_count": 0,
                "repair_count": 0,
                "last_use": None,
                "last_repair_date": None,
                "in_repair": False
            } for i in range(1, 12)}
            
            # Для каждой опоки
            for opoka_num in range(1, 12):
                total_uses = 0
                current_count = 0
                repair_dates = []
                last_use_date = None
                
                # Проходим по всем записям
                for _, row in df.iterrows():
                    date = row['Плавка_дата']
                    if date > pd.Timestamp('2025-02-01'):
                        continue
                    
                    # Считаем использования в этот день
                    day_uses = sum(1 for col in ['Сектор_A_опоки', 'Сектор_B_опоки', 
                                               'Сектор_C_опоки', 'Сектор_D_опоки']
                                 if pd.notna(row[col]) and int(row[col]) == opoka_num)
                    
                    if day_uses > 0:
                        total_uses += day_uses
                        current_count += day_uses
                        last_use_date = date
                        
                        # Проверяем необходимость ремонта
                        if current_count >= 100:
                            repair_dates.append(date.strftime('%Y-%m-%d'))
                            current_count = 0
                
                # Устанавливаем значения
                history[str(opoka_num)].update({
                    "total_count": total_uses,
                    "repair_count": len(repair_dates),
                    "count": current_count,
                    "last_use": last_use_date.strftime('%Y-%m-%d') if last_use_date else None,
                    "last_repair_date": repair_dates[-1] if repair_dates else None
                })
            
            return history
            
        except Exception as e:
            print(f"Ошибка при пересчете истории: {str(e)}")
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 