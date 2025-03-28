import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, 
                              QComboBox, QPushButton, QHeaderView, QFrame, QMessageBox, 
                              QLineEdit, QGraphicsDropShadowEffect, QFileDialog, QDialog, QCheckBox)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPalette
import pandas as pd
from datetime import datetime, timedelta
import calendar
from db_operations import OpokaDB
from db_init import init_database

# В начале файла, после импортов
EXCEL_PATH = None  # Изначально путь не определен

# Добавляем словарь с переводами месяцев
MONTHS_RU = {
    'January': 'Январь',
    'February': 'Февраль',
    'March': 'Март',
    'April': 'Апрель',
    'May': 'Май',
    'June': 'Июнь',
    'July': 'Июль',
    'August': 'Август',
    'September': 'Сентябрь',
    'October': 'Октябрь',
    'November': 'Ноябрь',
    'December': 'Декабрь'
}

class DataCache:
    def __init__(self):
        self.df = None
        self.last_update = None
        
    def get_dataframe(self):
        try:
            current_time = datetime.now()
            if self.df is None or (current_time - self.last_update).seconds > 300:  # Обновляем каждые 5 минут
                self.df = pd.read_excel(EXCEL_PATH)
                self.last_update = current_time
            return self.df
        except Exception as e:
            QMessageBox.critical(
                None,
                'Ошибка',
                f'Не удалось прочитать файл по пути {EXCEL_PATH}.\n'
                f'Убедитесь, что у вас есть доступ к сетевой папке.\n\n'
                f'Ошибка: {str(e)}'
            )
            return pd.DataFrame()  # Возвращаем пустой DataFrame в случае ошибки

class FileSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор файла данных")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Добавляем описание
        label = QLabel("Укажите расположение файла plavka.xlsx")
        layout.addWidget(label)
        
        # Кнопка выбора файла
        self.select_button = QPushButton("Выбрать файл...")
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)
        
        # Путь к файлу
        self.path_label = QLabel("")
        layout.addWidget(self.path_label)
        
        # Чекбокс "Запомнить выбор"
        self.remember_cb = QCheckBox("Запомнить выбор")
        layout.addWidget(self.remember_cb)
        
        # Кнопки OK и Cancel
        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)
        
        self.selected_path = None
        
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл plavka.xlsx",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            try:
                # Проверяем, можем ли мы прочитать файл
                pd.read_excel(file_path)
                self.selected_path = file_path
                self.path_label.setText(file_path)
                self.ok_button.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Ошибка',
                    f'Не удалось открыть файл:\n{str(e)}'
                )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Показываем диалог выбора файла
        if not self.get_excel_path():
            sys.exit(1)
            
        self.setWindowTitle("Учет использования опок")
        self.setFixedSize(1400, 900)
        
        # Инициализируем базу данных при первом запуске
        init_database()
        
        self.current_date = datetime.now()
        self.data_cache = DataCache()
        self.db = OpokaDB()
        
        # Создаем основные виджеты
        self.table = QTableWidget()
        self.stats_widget = QFrame()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.month_dropdown = QComboBox()
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Обновляем данные
        self.update_table(self.current_date)
        self.update_repair_dates()

    def setup_ui(self):
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
        
        change_file_button = QPushButton("Изменить файл")
        change_file_button.clicked.connect(self.show_file_dialog)
        
        # Обновленный стиль кнопок с иконками и анимацией
        button_style = """
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2196F3, stop: 1 #1976D2
                );
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1E88E5, stop: 1 #1565C0
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1565C0, stop: 1 #0D47A1
                );
                padding: 6px 9px 4px 11px;
            }
        """
        
        self.recalc_button.setStyleSheet(button_style)
        export_button.setStyleSheet(button_style)
        change_file_button.setStyleSheet(button_style)
        
        # Добавляем иконки к кнопкам
        self.recalc_button.setIcon(QIcon("icons/refresh.png"))  # Нужно добавить иконки
        self.recalc_button.setIconSize(QSize(16, 16))
        export_button.setIcon(QIcon("icons/export.png"))
        export_button.setIconSize(QSize(16, 16))
        change_file_button.setIcon(QIcon("icons/file.png"))
        change_file_button.setIconSize(QSize(16, 16))
        
        # Добавляем разделители
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
            QFrame {
                border: none;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #E0E0E0, stop: 0.5 #9E9E9E, stop: 1 #E0E0E0
                );
                height: 1px;
            }
        """)
        
        # Добавляем разделитель после верхней панели
        header_layout.addWidget(line)
        
        top_layout.addWidget(date_label)
        top_layout.addWidget(self.recalc_button)
        top_layout.addWidget(export_button)
        top_layout.addWidget(change_file_button)
        top_layout.addStretch()
        
        # Вторая строка верхней панели
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем выбор месяца и поиск
        month_label = QLabel("Месяц:")
        month_label.setStyleSheet("font-size: 12px;")
        
        self.month_dropdown.setFixedWidth(200)
        
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
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Добавляем верхнюю панель
        main_layout.addWidget(header_widget)
        
        # Создаем контейнер для таблицы и правой панели
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
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
        right_layout.setContentsMargins(10, 10, 10, 10)
        
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
        
        # Обновляем стиль статистики с градиентом
        stats_style = """
            QFrame {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFFFFF, stop: 1 #F5F5F5
                );
                border: 1px solid #BDBDBD;
                border-radius: 8px;
            }
            QLabel {
                font-size: 11px;
                background: transparent;
            }
            QLabel[header="true"] {
                font-weight: bold;
                color: #1976D2;
            }
        """
        
        self.stats_widget.setStyleSheet(stats_style)
        
        # Добавляем тени
        self.add_shadow(self.stats_widget)
        self.add_shadow(self.table)
        
        # Инициализируем выпадающий список месяцев
        self.setup_month_dropdown()

    def setup_month_dropdown(self):
        # Получаем список месяцев, за которые есть данные
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT DISTINCT strftime('%Y-%m', use_date) as month
        FROM usage_records
        ORDER BY month DESC
        ''')
        available_months = cursor.fetchall()
        print(f"Доступные месяцы: {available_months}")  # Отладочный вывод
        conn.close()

        # Добавляем месяцы в выпадающий список
        for month_data in available_months:
            month_str = month_data[0]  # формат 'YYYY-MM'
            year, month = map(int, month_str.split('-'))
            month_name = calendar.month_name[month]  # получаем название месяца
            month_ru = MONTHS_RU[month_name]  # переводим на русский
            self.month_dropdown.addItem(f"{month_ru} {year}", month_str)

        # Устанавливаем первый месяц как текущий, если есть месяцы
        if self.month_dropdown.count() > 0:
            self.month_dropdown.setCurrentIndex(0)

        self.month_dropdown.currentIndexChanged.connect(self.on_month_changed)

    def on_month_changed(self):
        selected_date = datetime.strptime(
            self.month_dropdown.currentData(), 
            '%Y-%m'
        )
        self.update_table(selected_date)

    def update_table(self, selected_date):
        try:
            # Обновляем данные из Excel
            self.db.update_from_excel(EXCEL_PATH)
            
            # Получаем статистику
            usage_history = self.db.get_all_stats()
            
            # Обновляем таблицу
            self.table.clear()
            
            # Настраиваем таблицу
            self.table.setRowCount(11)
            self.table.setColumnCount(32)
            
            # Устанавливаем заголовки
            headers = ['Опока'] + [str(i) for i in range(1, 32)]
            self.table.setHorizontalHeaderLabels(headers)
            
            # Настраиваем ширину колонок
            self.table.horizontalHeader().setDefaultSectionSize(28)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(0, 45)
            
            # Заполняем данные
            df = self.data_cache.get_dataframe()
            df['Плавка_дата'] = pd.to_datetime(df['Плавка_дата'], format='%d.%m.%Y')
            
            for opoka_num in range(1, 12):
                # Номер опоки
                self.table.setItem(opoka_num-1, 0, QTableWidgetItem(f"№{opoka_num}"))
                
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
                    if count > 3:
                        item.setBackground(QColor("#FFE0B2"))
                    elif count > 0:
                        item.setBackground(QColor("#C8E6C9"))
                    self.table.setItem(opoka_num-1, day, item)
            
            # Обновляем статистику
            self.update_statistics()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                'Ошибка', 
                f'Ошибка обновления данных:\n{str(e)}\n\n'
                f'Проверьте доступ к файлу {EXCEL_PATH}'
            )

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
        
        # Получаем статистику из базы данных
        usage_history = self.db.get_all_stats()
        
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
            
            # Добавляем анимацию при наведении на строку статистики
            self.add_hover_animation(row_widget)
            
            # Обновляем стиль кнопки ремонта
            repair_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #F5F5F5, stop: 1 #E0E0E0
                    );
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #E0E0E0, stop: 1 #BDBDBD
                    );
                }
                QPushButton:pressed {
                    padding: 2px -2px -2px 2px;
                }
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
        usage_history = self.db.get_all_stats()
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
            self.db.send_to_repair(opoka_num)
            self.update_table(datetime.strptime(self.month_dropdown.currentData(), '%Y-%m'))

    def return_from_repair(self, opoka_num):
        self.db.return_from_repair(opoka_num)
        self.update_table(datetime.strptime(self.month_dropdown.currentData(), '%Y-%m'))

    def recalculate_and_update(self):
        self.recalculate_history()
        self.update_table(self.current_date)

    def update_repair_dates(self):
        # Устанавливаем даты ремонта для опок 2 и 5
        repair_date = "2025-01-28"
        for opoka_id in [2, 5]:
            self.db.manual_set_repair_end_date(opoka_id, repair_date)

    def recalculate_history(self):
        try:
            # Обновляем данные из Excel
            self.db.update_from_excel(EXCEL_PATH)
            # Обновляем отображение
            self.update_table(self.current_date)
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка при пересчете истории:\n{str(e)}\n\n'
                f'Проверьте доступ к файлу {EXCEL_PATH}'
            )

    def export_statistics(self):
        try:
            usage_history = self.db.get_all_stats()
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
        
        # Стиль для комбобокса и поля поиска
        input_style = """
            QComboBox, QLineEdit {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 3px;
                background-color: white;
                font-size: 11px;
            }
            QComboBox:hover, QLineEdit:hover {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 5px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """
        
        self.month_dropdown.setStyleSheet(input_style)
        self.search_input.setStyleSheet(input_style)
        
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
        
        header = QLabel("Месячная статистика")
        header.setStyleSheet("""
            font-weight: bold;
            font-size: 11px;
            color: #1976D2;
            padding-bottom: 5px;
        """)
        layout.addWidget(header)
        
        # Проверяем, есть ли выбранный месяц
        current_month = self.month_dropdown.currentData()
        if current_month:
            year, month = map(int, current_month.split('-'))
            
            # Получаем статистику за месяц
            monthly_data = self.db.get_monthly_stats(year, month)
            
            # Переводим название месяца
            month_ru = MONTHS_RU[calendar.month_name[month].capitalize()]
            
            stats_text = (
                f"Статистика за {month_ru} {year}:\n"
                f"Всего использований: {monthly_data['total_uses']}\n"
                f"Всего ремонтов: {monthly_data['repairs_count']}"
            )
        else:
            # Если месяц не выбран, показываем сообщение по умолчанию
            stats_text = "Нет данных для отображения"
        
        label = QLabel(stats_text)
        layout.addWidget(label)
        
        label.setStyleSheet("""
            background-color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 11px;
            line-height: 1.4;
        """)
        
        return monthly_stats

    def setup_table_style(self):
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDBDBD;
                border-radius: 8px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFFFFF, stop: 1 #F5F5F5
                );
            }
            QTableWidget::item {
                padding: 2px;
                font-size: 11px;
            }
            QTableWidget::item:hover {
                background: rgba(33, 150, 243, 0.1);
            }
            QHeaderView::section {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #F5F5F5, stop: 1 #E0E0E0
                );
                padding: 2px;
                font-size: 11px;
                border: 1px solid #BDBDBD;
            }
        """)

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        widget.setGraphicsEffect(shadow)

    def add_hover_animation(self, widget):
        """Добавляет анимацию при наведении"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(100)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        def on_hover_enter():
            geometry = widget.geometry()
            animation.setStartValue(geometry)
            animation.setEndValue(geometry.adjusted(-2, -2, 2, 2))
            animation.start()
        
        def on_hover_leave():
            geometry = widget.geometry()
            animation.setStartValue(geometry)
            animation.setEndValue(geometry.adjusted(2, 2, -2, -2))
            animation.start()
        
        widget.enterEvent = lambda e: on_hover_enter()
        widget.leaveEvent = lambda e: on_hover_leave()

    def get_excel_path(self):
        """Показывает диалог выбора файла Excel и сохраняет путь"""
        global EXCEL_PATH
        
        # Проверяем сохраненный путь
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                line = f.readline().strip()
                if line.startswith('EXCEL_PATH='):
                    saved_path = line[11:]
                    if os.path.exists(saved_path):
                        try:
                            pd.read_excel(saved_path)
                            EXCEL_PATH = saved_path
                            return True
                        except:
                            pass
        
        # Показываем диалог выбора файла
        dialog = FileSelectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            EXCEL_PATH = dialog.selected_path
            
            # Если выбрана опция "Запомнить", сохраняем путь
            if dialog.remember_cb.isChecked():
                with open(config_path, 'w') as f:
                    f.write(f'EXCEL_PATH={EXCEL_PATH}')
            
            return True
        return False

    def show_file_dialog(self):
        """Показывает диалог выбора файла по запросу пользователя"""
        if self.get_excel_path():
            self.update_table(self.current_date)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Ошибка при запуске приложения: {str(e)}") 