"""
Модель пользователя системы.

Реализует интерфейс UserMixin Flask-Login.
Поддерживает роли: 'applicant' (абитуриент) и 'admin' (администратор).
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from factory import db


class User(UserMixin, db.Model):
    """
    Пользователь информационной системы.

    Attributes:
        id: Первичный ключ.
        email: Уникальный email пользователя.
        password_hash: Хэш пароля (bcrypt через werkzeug).
        full_name: Полное имя.
        phone: Телефон.
        role: Роль ('applicant' или 'admin').
        created_at: Дата регистрации.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(200), default="")
    phone = db.Column(db.String(30), default="")
    role = db.Column(db.String(20), nullable=False, default="applicant")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Отношения
    exam_results = db.relationship(
        "ExamResult", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    applications = db.relationship(
        "Application", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """
        Устанавливает хэшированный пароль.

        Args:
            password: Открытый пароль пользователя.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Проверяет пароль.

        Args:
            password: Открытый пароль для проверки.

        Returns:
            True если пароль верен, иначе False.
        """
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """Возвращает True если пользователь — администратор."""
        return self.role == "admin"

    @property
    def total_exam_score(self) -> int:
        """Возвращает сумму всех баллов ЕГЭ пользователя."""
        return sum(r.score for r in self.exam_results)

    def to_dict(self) -> dict:
        """
        Сериализует пользователя в словарь (для REST API).

        Returns:
            Словарь с данными пользователя (без пароля).
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "total_exam_score": self.total_exam_score,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
