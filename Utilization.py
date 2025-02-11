import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QPushButton, QComboBox, 
                              QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QDate
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
        
        # Инициализация менеджеров данных
        self.opoka_data_manager = OpokaDataManager()
        self.data_cache = DataCache()
        self.current_date = datetime.now()
        
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Создание верхней панели
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        # Добавление даты
        date_label = QLabel(f"Дата: {self.current_date.strftime('%d.%m.%Y')}")
        date_label.setStyleSheet("font-size: 12px;")
        
        # Кнопка пересчета
        self.recalc_button = QPushButton("Пересчитать историю")
        self.recalc_button.clicked.connect(self.recalculate_history)
        
        # Выпадающий список с месяцами
        self.month_dropdown = QComboBox()
        self.setup_month_dropdown()
        self.month_dropdown.currentIndexChanged.connect(self.on_month_changed)
        
        header_layout.addWidget(date_label)
        header_layout.addWidget(self.recalc_button)
        header_layout.addWidget(self.month_dropdown)
        header_layout.addStretch()
        
        # Создание основного контейнера
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Создание таблицы
        self.table = QTableWidget()
        self.setup_table()
        
        # Создание панели статистики
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.setup_stats_panel()
        
        content_layout.addWidget(self.table, stretch=4)
        content_layout.addWidget(self.stats_widget, stretch=1)
        
        main_layout.addWidget(header_widget)
        main_layout.addWidget(content_widget)
        
        # Инициализация данных
        self.update_repair_dates()
        self.update_table(self.current_date)

    def setup_month_dropdown(self):
        months = []
        for year in range(self.current_date.year - 1, self.current_date.year + 1):
            for month in range(1, 13):
                if year == self.current_date.year and month > self.current_date.month:
                    continue
                month_str = f"{calendar.month_name[month]} {year}"
                self.month_dropdown.addItem(month_str, f"{year}-{month:02d}")
        
        current_month_idx = self.month_dropdown.findData(
            f"{self.current_date.year}-{self.current_date.month:02d}"
        )
        self.month_dropdown.setCurrentIndex(current_month_idx)

    def setup_table(self):
        self.table.setColumnCount(32)  # 1 колонка для номера опоки + 31 день
        self.table.setRowCount(11)     # 11 опок
        
        # Настройка заголовков
        self.table.setHorizontalHeaderItem(0, QTableWidgetItem("Опока"))
        for i in range(1, 32):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(str(i)))
        
        # Настройка размеров
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 45)
        for i in range(1, 32):
            self.table.setColumnWidth(i, 28)
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)

    def setup_stats_panel(self):
        # Заголовок статистики
        stats_header = QLabel("Статистика использования:")
        stats_header.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.stats_layout.addWidget(stats_header)
        
        # Создание заголовков колонок
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setSpacing(2)
        
        headers = ["№", "Тек.", "Всего", "Рем.", "Статус"]
        widths = [25, 35, 40, 35, 50]
        
        for header, width in zip(headers, widths):
            label = QLabel(header)
            label.setFixedWidth(width)
            label.setStyleSheet("font-size: 11px;")
            header_layout.addWidget(label)
        
        self.stats_layout.addWidget(header_widget)

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

    def update_repair_dates(self):
        usage_history = self.opoka_data_manager.load_history()
        
        # 28.01.2025 - опоки 2 и 5
        for opoka in ['2', '5']:
            usage_history[opoka].update({
                "last_repair_date": "2025-01-28",
                "count": 0,
                "in_repair": False,
                "auto_reset": False
            })
        
        self.opoka_data_manager.save_history(usage_history)

    def update_table(self, selected_date):
        try:
            # Очищаем существующие виджеты статистики
            while self.stats_layout.count():
                item = self.stats_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            df = pd.read_excel(self.opoka_data_manager.excel_file)
            df['Плавка_дата'] = pd.to_datetime(df['Плавка_дата'], format='%d.%m.%Y')
            
            usage_history = self.check_unused_opoks()
            if usage_history is None:
                usage_history = self.opoka_data_manager.load_history()
            
            # Обновляем основную таблицу
            for opoka_num in range(1, 12):
                row_idx = opoka_num - 1
                
                # Номер опоки
                opoka_item = QTableWidgetItem(f"№{opoka_num}")
                opoka_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 0, opoka_item)
                
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
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    if count > 0:
                        item.setBackground(QColor(200, 255, 200))  # Светло-зеленый
                    
                    self.table.setItem(row_idx, day, item)

            # Обновляем статистику
            self.setup_stats_panel()  # Пересоздаем заголовки

            for opoka_num in range(1, 12):
                opoka_data = usage_history[str(opoka_num)]
                
                # Создаем строку статистики
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(5, 2, 5, 2)
                row_layout.setSpacing(5)

                # Добавляем данные
                labels = [
                    (str(opoka_num), 25),
                    (str(opoka_data["count"]), 35),
                    (str(opoka_data["total_count"]), 40),
                    (str(opoka_data["repair_count"]), 35)
                ]

                for text, width in labels:
                    label = QLabel(text)
                    label.setFixedWidth(width)
                    label.setStyleSheet("font-size: 11px;")
                    row_layout.addWidget(label)

                # Статус
                status_text = self.get_status_text(opoka_data)
                status_label = QLabel(status_text)
                status_label.setFixedWidth(50)
                status_label.setStyleSheet("font-size: 11px;")

                if opoka_data["in_repair"]:
                    row_widget.setStyleSheet("background-color: #E0E0E0;")  # Серый
                elif opoka_data.get("auto_reset"):
                    row_widget.setStyleSheet("background-color: #E3F2FD;")  # Светло-голубой
                    row_widget.setToolTip(f"Не использовалась {opoka_data.get('unused_days', 0)} дней")
                elif opoka_data["count"] >= 100:
                    row_widget.setStyleSheet("background-color: #FFEBEE;")  # Светло-красный

                row_layout.addWidget(status_label)

                # Кнопка ремонта
                repair_button = QPushButton(
                    "Вернуть" if opoka_data["in_repair"] else "В ремонт",
                    clicked=lambda checked, num=opoka_num: 
                        self.return_from_repair(num) if opoka_data["in_repair"] 
                        else self.send_to_repair(num)
                )
                repair_button.setFixedWidth(70)
                repair_button.setStyleSheet("font-size: 11px;")
                row_layout.addWidget(repair_button)

                self.stats_layout.addWidget(row_widget)

            self.stats_layout.addStretch()
            
        except Exception as e:
            print(f"Ошибка при обновлении таблицы: {str(e)}")
            error_label = QLabel(f"Ошибка: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.stats_layout.addWidget(error_label)

        self.update()

    def get_status_text(self, opoka_data):
        status_text = ""  # Инициализируем переменную
        
        if opoka_data.get("in_repair"):
            status_text = "В ремонте"
        elif opoka_data.get("auto_reset"):
            status_text = f"Простой ({opoka_data.get('unused_days', 0)} дней)"
        else:
            status_text = "Готова"
        
        return status_text

    def check_unused_opoks(self):
        try:
            df = pd.read_excel(self.opoka_data_manager.excel_file)
            df['Плавка_дата'] = pd.to_datetime(df['Плавка_дата'], format='%d.%m.%Y')
            usage_history = self.opoka_data_manager.load_history()
            current_time = datetime.now()
            current_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            print(f"Текущее время: {current_time}")

            for opoka_num in range(1, 12):
                last_use_data = df[
                    (df['Плавка_дата'].dt.normalize() <= current_time) &
                    ((df['Сектор_A_опоки'] == opoka_num) |
                     (df['Сектор_B_опоки'] == opoka_num) |
                     (df['Сектор_C_опоки'] == opoka_num) |
                     (df['Сектор_D_опоки'] == opoka_num))
                ].sort_values('Плавка_дата', ascending=False)

                if not last_use_data.empty:
                    last_use_date = last_use_data.iloc[0]['Плавка_дата'].normalize()
                    days_unused = (current_time - last_use_date).days
                    
                    print(f"Опока {opoka_num}:")
                    print(f"  Последнее использование: {last_use_date}")
                    print(f"  Дней без использования: {days_unused}")

                    if days_unused > 4:
                        print(f"  Установка статуса простоя")
                        # Только добавляем статус простоя и количество дней
                        usage_history[str(opoka_num)].update({
                            "auto_reset": True,
                            "unused_days": days_unused
                        })
                    else:
                        print(f"  Снятие статуса простоя")
                        if "auto_reset" in usage_history[str(opoka_num)]:
                            usage_history[str(opoka_num)].pop("auto_reset", None)
                            usage_history[str(opoka_num)].pop("unused_days", None)

                self.opoka_data_manager.save_history(usage_history)

            return usage_history

        except Exception as e:
            print(f"Ошибка при проверке неиспользуемых опок: {str(e)}")
            return None

    def send_to_repair(self, opoka_num):
        usage_history = self.opoka_data_manager.load_history()
        usage_history[str(opoka_num)]["repair_count"] += 1
        usage_history[str(opoka_num)]["count"] = 0  # Сбрасываем текущий счетчик
        usage_history[str(opoka_num)]["in_repair"] = True
        usage_history[str(opoka_num)]["last_use"] = None
        usage_history[str(opoka_num)]["last_repair_date"] = datetime.now().strftime('%Y-%m-%d')
        self.opoka_data_manager.save_history(usage_history)
        self.update_table(datetime.strptime(self.month_dropdown.currentText(), '%Y-%m'))

    def return_from_repair(self, opoka_num):
        usage_history = self.opoka_data_manager.load_history()
        usage_history[str(opoka_num)]["in_repair"] = False
        usage_history[str(opoka_num)]["count"] = 0  # Сбрасываем счетчик после ремонта
        self.opoka_data_manager.save_history(usage_history)
        self.update_table(datetime.strptime(self.month_dropdown.currentText(), '%Y-%m'))

    def on_month_changed(self, index):
        selected_date = datetime.strptime(
            self.month_dropdown.itemData(index),
            '%Y-%m'
        )
        self.update_table(selected_date)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль приложения
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 