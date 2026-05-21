"""
Точка входа приложения АбиТрек.

Запуск:
    python run.py

Переменные окружения:
    FLASK_ENV   - окружение (development/testing/production), по умолчанию development
    SECRET_KEY  - секретный ключ (для production обязательно)
    DATABASE_URL - URL базы данных
"""

import os
from factory import create_app, db
from seed import seed_all



with app.app_context():
    db.create_all()
    seed_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=(env == "development"))
