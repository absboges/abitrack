"""
Конфигурация приложения АбиТрек.

Содержит три конфигурации: Development, Testing, Production.
Используется паттерн «Фабричный метод» через factory function create_app().
"""

import os


class BaseConfig:
    """Базовая конфигурация."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "abitrack-dev-secret-2026")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False


class DevelopmentConfig(BaseConfig):
    """Конфигурация для разработки."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///abitrack_dev.db"
    )


class TestingConfig(BaseConfig):
    """Конфигурация для тестирования."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """Конфигурация для production."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///abitrack_prod.db"
    )


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
