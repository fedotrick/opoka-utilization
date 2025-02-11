import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, 
                              QComboBox, QPushButton, QHeaderView, QFrame, QMessageBox, QLineEdit)
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
        
        # Создаем верхнюю панель с двумя строками
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(5)
        
        # Первая строка верхней панели
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем дату и кнопки
        date_label = QLabel(f"Дата: {self.current_date.strftime('%d.%m.%Y')}")
        date_label.setStyleSheet("font-size: 12px;")
        
        self.recalc_button = QPushButton("Пересчитать историю")
        self.recalc_button.clicked.connect(self.recalculate_and_update)
        
        export_button = QPushButton("Экспорт статистики")
        export_button.clicked.connect(self.export_statistics)
        
        top_layout.addWidget(date_label)
        top_layout.addWidget(self.recalc_button)
        top_layout.addWidget(export_button)
        top_layout.addStretch()
        
        # Вторая строка верхней панели
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем выбор месяца и поиск
        month_label = QLabel("Месяц:")
        month_label.setStyleSheet("font-size: 12px;")
        
        self.month_dropdown = QComboBox()
        self.month_dropdown.setFixedWidth(200)
        self.setup_month_dropdown()
        
        # Добавляем поиск
        search_widget = self.add_search_widget()
        
        bottom_layout.addWidget(month_label)
        bottom_layout.addWidget(self.month_dropdown)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(search_widget)
        bottom_layout.addStretch()
        
        # Добавляем строки в верхнюю панель
        header_layout.addWidget(top_row)
        header_layout.addWidget(bottom_row)
        
        # Создаем основной контейнер
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(10)
        
        # Добавляем верхнюю панель
        main_layout.addWidget(header_widget)
        
        # Создаем контейнер для таблицы и правой панели
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setSpacing(10)
        
        # Добавляем таблицу
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.setup_table_style()
        table_layout.addWidget(self.table)
        
        # Создаем правую панель
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        
        # Добавляем статистику использования
        self.stats_widget = QFrame()
        self.stats_widget.setFixedWidth(250)
        self.stats_widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.stats_layout = QVBoxLayout(self.stats_widget)
        
        # Добавляем месячную статистику
        monthly_stats = self.add_monthly_stats()
        monthly_stats.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel {
                font-size: 11px;
            }
        """)
        
        right_layout.addWidget(self.stats_widget)
        right_layout.addWidget(monthly_stats)
        
        # Добавляем компоненты в content_layout
        content_layout.addWidget(table_container, stretch=4)
        content_layout.addWidget(right_panel)
        
        # Добавляем все в главный layout
        main_layout.addWidget(content_container)
        
        # Устанавливаем главный контейнер
        self.setCentralWidget(main_container)
        
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
                    if count > 3:  # Высокая нагрузка в день
                        item.setBackground(QColor("#FFE0B2"))  # Оранжевый
                    elif count > 0:
                        item.setBackground(QColor("#C8E6C9"))  # Зеленый
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
            
            # Создаем детальную подсказку
            tooltip_text = (
                f"Опока №{i}\n"
                f"Текущих использований: {opoka_data['count']}\n"
                f"Всего использований: {opoka_data['total_count']}\n"
                f"Количество ремонтов: {opoka_data['repair_count']}\n"
                f"Последний ремонт: {opoka_data['last_repair_date'] or 'Не было'}\n"
                f"Последнее использование: {opoka_data['last_use'] or 'Не использовалась'}"
            )
            
            row_widget.setToolTip(tooltip_text)
            
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
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            f'Отправить опоку №{opoka_num} в ремонт?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
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

    def export_statistics(self):
        try:
            usage_history = self.opoka_data_manager.load_history()
            export_data = []
            
            for i in range(1, 12):
                opoka_data = usage_history[str(i)]
                export_data.append({
                    'Номер опоки': i,
                    'Текущие использования': opoka_data['count'],
                    'Всего использований': opoka_data['total_count'],
                    'Количество ремонтов': opoka_data['repair_count'],
                    'Последний ремонт': opoka_data['last_repair_date'],
                    'Последнее использование': opoka_data['last_use'],
                    'Статус': self.get_status_text(opoka_data)
                })
            
            df = pd.DataFrame(export_data)
            df.to_excel('статистика_опок.xlsx', index=False)
            
            QMessageBox.information(
                self,
                'Успех',
                'Статистика успешно экспортирована в файл "статистика_опок.xlsx"'
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Не удалось экспортировать статистику: {str(e)}'
            )

    def add_search_widget(self):
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_label = QLabel("Поиск опоки:")
        search_label.setStyleSheet("font-size: 12px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите номер опоки...")
        self.search_input.setFixedWidth(150)
        self.search_input.textChanged.connect(self.filter_table)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        return search_widget

    def filter_table(self, text):
        if not text:
            # Показать все строки
            for row in range(self.table.rowCount()):
                self.table.showRow(row)
        else:
            # Скрыть строки, которые не соответствуют поиску
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item and text in item.text():
                    self.table.showRow(row)
                else:
                    self.table.hideRow(row)

    def add_monthly_stats(self):
        monthly_stats = QWidget()
        layout = QVBoxLayout(monthly_stats)
        
        current_month = self.month_dropdown.currentData()
        usage_history = self.opoka_data_manager.load_history()
        
        total_uses = sum(int(data["count"]) for data in usage_history.values())
        repairs_this_month = sum(
            1 for data in usage_history.values() 
            if data["last_repair_date"] 
            and data["last_repair_date"].startswith(current_month)
        )
        
        stats_text = (
            f"Статистика за {self.month_dropdown.currentText()}:\n"
            f"Всего использований: {total_uses}\n"
            f"Ремонтов за месяц: {repairs_this_month}"
        )
        
        label = QLabel(stats_text)
        layout.addWidget(label)
        
        return monthly_stats

    def setup_table_style(self):
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDBDBD;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 2px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 2px;
                font-size: 11px;
                border: 1px solid #BDBDBD;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 