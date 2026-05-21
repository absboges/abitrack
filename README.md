# АбиТрек — Информационная система абитуриента

Веб-приложение на Flask для расчёта конкурсного балла ЕГЭ и отслеживания сроков подачи документов в вузы.

> Курсовой проект по дисциплине «Разработка веб-приложений»  
> Московский политехнический университет, 2026  
> Выполнил: Сергиенко Павел Андреевич, группа 241-3211

---

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Бэкенд | Python 3.12 + Flask 3.0 |
| База данных | SQLite (dev) / PostgreSQL (prod) |
| ORM | Flask-SQLAlchemy |
| Авторизация | Flask-Login + Werkzeug (bcrypt) |
| REST API | Flask Blueprints + Flask-CORS |
| Тестирование | pytest + pytest-flask |
| Контейнеризация | Docker + docker-compose |
| Документация кода | Doxygen |
| Контроль версий | Git |

## Архитектурные решения и паттерны

### 1. Паттерн «Фабричный метод» (Application Factory)
Функция `create_app()` в `factory.py` создаёт и конфигурирует экземпляр Flask.
Это позволяет создавать несколько экземпляров приложения (development, testing, production)
без конфликтов глобального состояния.

### 2. Паттерн «Стратегия» (Strategy) — `app/services/calculator.py`
Алгоритм расчёта конкурсного балла вынесен в иерархию классов:
- `ScoreStrategy` — абстрактный интерфейс
- `StandardScoreStrategy` — стандартный расчёт по формуле Stotal = Σ Ei + Bind
- `OlympiadScoreStrategy` — расчёт для победителей олимпиад
- `ScoreCalculator` — контекст, использующий стратегию

### 3. Паттерн «Наблюдатель» (Observer) — `app/patterns/observer.py`
Система уведомлений о приближающихся дедлайнах:
- `DeadlineEventEmitter` — издатель событий
- `LoggingObserver` — логирование в консоль
- `InAppNotifyObserver` — уведомления в интерфейсе

### 4. Паттерн «Сервисный слой» (Service Layer / Repository)
Классы `UserService`, `ApplicationService`, `DeadlineService` инкапсулируют
всю бизнес-логику. Маршруты не обращаются к БД напрямую.

## Структура проекта

```
abitrack/
├── app/
│   ├── models/
│   │   ├── user.py          # Модель User
│   │   └── domain.py        # University, Program, ExamResult, Application, Deadline
│   ├── services/
│   │   ├── calculator.py    # Паттерн Стратегия (расчёт баллов)
│   │   └── services.py      # UserService, ApplicationService, DeadlineService
│   ├── patterns/
│   │   └── observer.py      # Паттерн Наблюдатель (уведомления)
│   ├── api/
│   │   ├── auth_routes.py   # Blueprint: /login, /register, /logout
│   │   ├── main_routes.py   # Blueprint: страницы приложения
│   │   ├── rest_api.py      # Blueprint: /api/v1/* (JSON REST API)
│   │   └── admin_routes.py  # Blueprint: /admin/*
│   └── templates/           # Jinja2-шаблоны
│       ├── base.html
│       ├── auth/
│       ├── main/
│       └── admin/
├── tests/
│   └── test_abitrack.py     # 49 unit-тестов
├── docs/
│   ├── Doxyfile             # Конфигурация Doxygen
│   └── uml/
│       └── diagrams.puml    # UML: классы, БД, use case, sequence
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config.py                # Конфигурации (dev/test/prod)
├── factory.py               # Application Factory
├── run.py                   # Точка входа
├── seed.py                  # Тестовые данные
└── requirements.txt
```

## REST API

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/me` | Данные текущего пользователя |
| GET | `/api/v1/me/applications` | Заявления пользователя |
| GET | `/api/v1/universities` | Список вузов |
| GET | `/api/v1/programs` | Список программ |
| GET | `/api/v1/programs/<id>` | Одна программа |
| POST | `/api/v1/calculate` | Расчёт балла (JSON) |
| GET | `/api/v1/deadlines` | Предстоящие дедлайны |
| GET | `/api/v1/notifications` | Уведомления пользователя |

### Пример запроса к API
```bash
curl -X POST http://localhost:5000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"program_id": 1, "individual_score": 5}'
```

## Быстрый старт

### Локально
```bash
pip install -r requirements.txt
python run.py
# Открыть http://localhost:5000
```

### Docker
```bash
cd docker
docker-compose up --build
```

### Тестовые аккаунты
| Email | Пароль | Роль |
|-------|--------|------|
| admin@mospolytech.ru | admin123 | Администратор |
| test@student.ru | test123 | Абитуриент |

## Тесты

```bash
# Запуск всех тестов
pytest tests/ -v

# С отчётом о покрытии
pytest tests/ -v --cov=app --cov-report=html
```

**49 тестов** покрывают:
- Паттерн Стратегия (ScoreCalculator, 9 тестов)
- Паттерн Наблюдатель (6 тестов)
- Модели User, Deadline, Program (12 тестов)
- Сервисный слой UserService, ApplicationService (13 тестов)
- REST API эндпоинты (9 тестов)

## Документация кода (Doxygen)

```bash
doxygen docs/Doxyfile
# Открыть docs/generated/html/index.html
```

## UML-диаграммы

Диаграммы в формате PlantUML: `docs/uml/diagrams.puml`

Содержит:
1. **Диаграмма классов** — все модели, сервисы, паттерны
2. **ER-диаграмма** — схема базы данных
3. **Use Case диаграмма** — варианты использования
4. **Sequence-диаграмма** — расчёт балла через REST API

Онлайн-рендеринг: https://www.plantuml.com/plantuml/uml/

## Git

```bash
git init
git add .
git commit -m "feat: initial commit — АбиТрек информационная система абитуриента"
git remote add origin https://github.com/YOUR_USER/abitrack.git
git push -u origin main
```
