# Dockerfile — образ для АбиТрек
# Многоэтапная сборка: зависимости → приложение

FROM python:3.12-slim AS base

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python-зависимости отдельным слоем
# (кэшируется Docker, пока requirements.txt не изменится)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаём директорию для базы данных
RUN mkdir -p /app/instance

# Переменные окружения по умолчанию
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

# Точка входа
CMD ["python", "run.py"]
