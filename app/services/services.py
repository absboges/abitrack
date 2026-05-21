"""
Сервисный слой: UserService и ApplicationService.

Реализует паттерн «Репозиторий» (Repository) — сервисы инкапсулируют
всю логику работы с базой данных и скрывают детали ORM от маршрутов.
Маршруты (routes) взаимодействуют только с сервисами, не с db напрямую.

Это позволяет:
  - тестировать бизнес-логику без реальной БД (mock-репозиторий)
  - менять ORM без изменения маршрутов
  - централизовать валидацию
"""

from typing import Optional, List, Dict
from factory import db
from app.models.user import User
from app.models.domain import (
    University, Program, ExamResult, Application, Deadline
)
from app.services.calculator import ScoreCalculator


# ─── USER SERVICE ─────────────────────────────────────────────────────────────


class UserService:
    """
    Сервис управления пользователями.

    Инкапсулирует логику создания, аутентификации и обновления пользователей.
    Реализует паттерн «Сервисный слой» (Service Layer).
    """

    @staticmethod
    def create(email: str, password: str, full_name: str = "",
               role: str = "applicant") -> User:
        """
        Создаёт нового пользователя.

        Args:
            email: Email пользователя (уникальный).
            password: Открытый пароль.
            full_name: Полное имя.
            role: Роль ('applicant' или 'admin').

        Returns:
            Созданный объект User.

        Raises:
            ValueError: Если пользователь с таким email уже существует.
        """
        if User.query.filter_by(email=email).first():
            raise ValueError(f"Пользователь с email '{email}' уже существует")
        user = User(email=email, full_name=full_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[User]:
        """
        Аутентифицирует пользователя.

        Args:
            email: Email.
            password: Открытый пароль.

        Returns:
            User если аутентификация успешна, иначе None.
        """
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def update_profile(user: User, full_name: str = None,
                       phone: str = None, new_password: str = None) -> User:
        """
        Обновляет профиль пользователя.

        Args:
            user: Объект пользователя.
            full_name: Новое ФИО (None = не менять).
            phone: Новый телефон (None = не менять).
            new_password: Новый пароль (None = не менять).

        Returns:
            Обновлённый объект User.
        """
        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        if new_password:
            user.set_password(new_password)
        db.session.commit()
        return user

    @staticmethod
    def save_exam_results(user: User, scores: Dict[str, int]) -> List[ExamResult]:
        """
        Сохраняет результаты ЕГЭ пользователя (полная замена).

        Args:
            user: Пользователь.
            scores: Словарь {предмет: балл (0–100)}.

        Returns:
            Список сохранённых ExamResult.
        """
        ExamResult.query.filter_by(user_id=user.id).delete()
        results = []
        for subject, score in scores.items():
            score = max(0, min(100, int(score)))
            er = ExamResult(user_id=user.id, subject=subject, score=score)
            db.session.add(er)
            results.append(er)
        db.session.commit()
        return results


# ─── APPLICATION SERVICE ──────────────────────────────────────────────────────


class ApplicationService:
    """
    Сервис управления заявлениями абитуриента.

    Содержит бизнес-логику добавления, изменения статуса
    и удаления заявлений.
    """

    _calculator = ScoreCalculator()

    @classmethod
    def add(cls, user: User, program_id: int,
            individual_score: int = 0) -> Application:
        """
        Добавляет направление в список заявлений абитуриента.

        Args:
            user: Абитуриент.
            program_id: ID программы.
            individual_score: Баллы за ИД (0–10).

        Returns:
            Созданный объект Application.

        Raises:
            ValueError: Если направление уже добавлено.
            ValueError: Если программа не найдена.
        """
        if Application.query.filter_by(
            user_id=user.id, program_id=program_id
        ).first():
            raise ValueError("Это направление уже добавлено в список")

        program = Program.query.get(program_id)
        if not program:
            raise ValueError("Программа не найдена")

        exam_results = {r.subject: r.score for r in user.exam_results}
        result = cls._calculator.calculate_for_program(
            exam_results, program.subject_list,
            individual_score, program.min_score
        )

        count = Application.query.filter_by(user_id=user.id).count()
        app = Application(
            user_id=user.id,
            university_id=program.university_id,
            program_id=program_id,
            priority=count + 1,
            total_score=result.total_score,
            individual_score=individual_score,
            status="draft",
        )
        db.session.add(app)
        db.session.commit()
        return app

    @staticmethod
    def update_status(application_id: int, user_id: int,
                      new_status: str) -> Application:
        """
        Обновляет статус заявления.

        Args:
            application_id: ID заявления.
            user_id: ID пользователя (для проверки владельца).
            new_status: Новый статус ('draft'/'submitted'/'accepted'/'rejected').

        Returns:
            Обновлённый объект Application.

        Raises:
            ValueError: Если заявление не найдено или неверный статус.
        """
        valid = ("draft", "submitted", "accepted", "rejected")
        if new_status not in valid:
            raise ValueError(f"Недопустимый статус: {new_status}")

        app = Application.query.filter_by(
            id=application_id, user_id=user_id
        ).first()
        if not app:
            raise ValueError("Заявление не найдено")

        app.status = new_status
        db.session.commit()
        return app

    @staticmethod
    def delete(application_id: int, user_id: int) -> None:
        """
        Удаляет заявление.

        Args:
            application_id: ID заявления.
            user_id: ID пользователя.

        Raises:
            ValueError: Если заявление не найдено.
        """
        app = Application.query.filter_by(
            id=application_id, user_id=user_id
        ).first()
        if not app:
            raise ValueError("Заявление не найдено")
        db.session.delete(app)
        db.session.commit()

    @staticmethod
    def get_user_applications(user_id: int) -> List[Application]:
        """Возвращает все заявления пользователя по приоритету."""
        return Application.query.filter_by(user_id=user_id).order_by(
            Application.priority
        ).all()


# ─── DEADLINE SERVICE ─────────────────────────────────────────────────────────


class DeadlineService:
    """Сервис работы со сроками приёмной кампании."""

    @staticmethod
    def get_upcoming(university_ids: List[int] = None,
                     limit: int = 10) -> List[Deadline]:
        """
        Возвращает предстоящие дедлайны, отсортированные по дате.

        Args:
            university_ids: Фильтр по вузам (None = все вузы).
            limit: Максимальное количество результатов.

        Returns:
            Список объектов Deadline.
        """
        from datetime import date
        query = Deadline.query.filter(Deadline.deadline_date >= date.today())
        if university_ids:
            query = query.filter(Deadline.university_id.in_(university_ids))
        return query.order_by(Deadline.deadline_date).limit(limit).all()
