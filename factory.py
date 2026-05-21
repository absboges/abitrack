"""
Фабрика приложения Flask (паттерн «Application Factory»).

Использует паттерн «Фабричный метод» — create_app() создаёт и конфигурирует
экземпляр Flask в зависимости от переданной конфигурации. Это позволяет
создавать несколько экземпляров приложения (например, для тестирования)
без конфликтов глобального состояния.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS

from config import config_map

# Глобальные расширения (инициализируются без app — паттерн init_app)
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name: str = "default") -> Flask:
    """
    Создаёт и настраивает экземпляр Flask-приложения.

    Args:
        config_name: Имя конфигурации из config_map.
                     Допустимые значения: 'development', 'testing', 'production'.

    Returns:
        Настроенный экземпляр Flask.

    Example:
        >>> app = create_app('testing')
        >>> app.config['TESTING']
        True
    """
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
    app.config.from_object(config_map[config_name])

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Войдите, чтобы получить доступ"
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Регистрация blueprints
    from app.api.auth_routes import auth_bp
    from app.api.main_routes import main_bp
    from app.api.rest_api import api_bp
    from app.api.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Загрузчик пользователя для Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    return app
