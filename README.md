# Opoka Utilization

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0%2B-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](https://github.com/fedotrick/opoka-utilization)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Build Status](https://img.shields.io/github/actions/workflow/status/fedotrick/opoka-utilization/main.yml?branch=main)](https://github.com/fedotrick/opoka-utilization/actions)

## 📝 Описание
Система для отслеживания и анализа утилизации ресурсов Opoka. Этот инструмент помогает оптимизировать использование ресурсов и повысить эффективность работы.

## 🚀 Возможности
- Мониторинг использования ресурсов в реальном времени
- Детальная аналитика и отчетность
- Настраиваемые оповещения
- Визуализация данных
- Экспорт отчетов в различных форматах

## 🛠 Технологии
- Backend: [FastAPI, SQLAlchemy, Pydantic, Pandas, Plotly]
- Frontend: [PySide6, Qt]
- База данных: [JSON файлы]
- Другие инструменты: [pytest, black, flake8, uvicorn]

## ⚙️ Установка и запуск

### Предварительные требования
- Python 3.10+
- pip

### Установка
1. Клонируйте репозиторий:
git clone https://github.com/fedotrick/opoka-utilization.git

2. Создайте и активируйте виртуальное окружение:
python -m venv venv
source venv/bin/activate # Linux/MacOS

3. Установите зависимости:
pip install -r requirements.txt

4. Запустите приложение:
python main.py

## 📦 Структура проекта
project/
├── src/ # Исходный код
│ ├── api/ # API endpoints
│ ├── core/ # Основная бизнес-логика
│ ├── database/ # Модели и миграции БД
│ └── utils/ # Вспомогательные функции
├── tests/ # Тесты
│ ├── unit/ # Модульные тесты
│ └── integration/ # Интеграционные тесты
├── docs/ # Документация
├── config/ # Конфигурационные файлы
├── requirements.txt # Зависимости проекта
├── README.md # Документация проекта
└── main.py # Точка входа в приложение

### Конфигурация

config/
├── config.py # Основная конфигурация
├── logging.conf # Конфигурация логирования
└── settings.py # Настройки приложения

### Библиотеки
- FastAPI - современный веб-фреймворк для создания API
- SQLAlchemy - ORM для работы с базами данных
- Pydantic - валидация данных и сериализация
- Pandas - анализ и обработка данных
- Plotly - визуализация данных
- pytest - тестирование
- black - форматирование кода
- flake8 - линтер кода
- uvicorn - ASGI-сервер

## 📚 Документация

### Руководства
- [Руководство пользователя](docs/user-guide.md)
- [Руководство разработчика](docs/developer-guide.md)

## 🔒 Безопасность
- Пока отсутствует

## 🤝 Вклад в проект
1. Создайте форк проекта
2. Создайте ветку для новой функциональности
3. Отправьте пулл-реквест

## 📈 Статус проекта
- Версия: 1.0.0
- Статус: В активной разработке

## 📄 Лицензия
MIT License. Подробности в файле [LICENSE](LICENSE)

## 👥 Команда
- [Имя Фамилия](https://github.com/fedotrick) - Ведущий разработчик
- [Имя Фамилия](https://github.com/fedotrick) - DevOps инженер
- [Имя Фамилия](https://github.com/fedotrick) - Frontend разработчик

## 📞 Контакты
- Email: warriorpacis@yandex.ru
- Telegram: [@project_support](https://t.me/@Simp1i_City)




