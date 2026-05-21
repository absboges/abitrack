"""
Модели предметной области информационной системы абитуриента.

Содержит:
    - University: Вуз
    - Program: Образовательная программа
    - ExamResult: Результат ЕГЭ пользователя
    - Application: Заявление абитуриента
    - Deadline: Срок подачи документов
"""

from datetime import datetime, date
from factory import db


class University(db.Model):
    """
    Вуз (высшее учебное заведение).

    Attributes:
        id: Первичный ключ.
        name: Полное официальное название.
        short_name: Аббревиатура (МГУ, МФТИ и т.д.).
        city: Город расположения.
        description: Краткое описание.
        website: Официальный сайт.
    """

    __tablename__ = "universities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(400), nullable=False)
    short_name = db.Column(db.String(60), default="")
    city = db.Column(db.String(100), default="")
    description = db.Column(db.Text, default="")
    website = db.Column(db.String(200), default="")

    programs = db.relationship(
        "Program", backref="university", lazy=True, cascade="all, delete-orphan"
    )
    deadlines = db.relationship(
        "Deadline", backref="university", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Сериализует вуз в словарь для REST API."""
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "city": self.city,
            "description": self.description,
            "website": self.website,
            "programs_count": len(self.programs),
        }

    def __repr__(self) -> str:
        return f"<University {self.short_name or self.name[:30]}>"


class Program(db.Model):
    """
    Образовательная программа (направление подготовки).

    Attributes:
        id: Первичный ключ.
        university_id: Внешний ключ на University.
        name: Название программы.
        code: Код направления (09.03.01 и т.д.).
        field: Область знаний.
        budget_places: Количество бюджетных мест.
        paid_places: Количество платных мест.
        min_score: Минимальная сумма баллов ЕГЭ для подачи.
        subjects: Предметы ЕГЭ через запятую.
    """

    __tablename__ = "programs"

    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(
        db.Integer, db.ForeignKey("universities.id"), nullable=False
    )
    name = db.Column(db.String(300), nullable=False)
    code = db.Column(db.String(20), default="")
    field = db.Column(db.String(100), default="")
    budget_places = db.Column(db.Integer, default=0)
    paid_places = db.Column(db.Integer, default=0)
    min_score = db.Column(db.Integer, default=0)
    subjects = db.Column(db.String(300), default="")

    @property
    def subject_list(self) -> list:
        """Возвращает список предметов ЕГЭ."""
        return [s.strip() for s in self.subjects.split(",") if s.strip()]

    def to_dict(self) -> dict:
        """Сериализует программу в словарь для REST API."""
        return {
            "id": self.id,
            "university_id": self.university_id,
            "name": self.name,
            "code": self.code,
            "field": self.field,
            "budget_places": self.budget_places,
            "paid_places": self.paid_places,
            "min_score": self.min_score,
            "subjects": self.subject_list,
        }

    def __repr__(self) -> str:
        return f"<Program {self.code} {self.name[:30]}>"


class ExamResult(db.Model):
    """
    Результат ЕГЭ конкретного абитуриента по одному предмету.

    Attributes:
        id: Первичный ключ.
        user_id: Внешний ключ на User.
        subject: Название предмета ЕГЭ.
        score: Балл (0–100).
    """

    __tablename__ = "exam_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    def to_dict(self) -> dict:
        """Сериализует результат ЕГЭ в словарь."""
        return {"id": self.id, "subject": self.subject, "score": self.score}

    def __repr__(self) -> str:
        return f"<ExamResult {self.subject}={self.score}>"


# Статусы заявления
APPLICATION_STATUSES = ("draft", "submitted", "accepted", "rejected")


class Application(db.Model):
    """
    Заявление абитуриента на образовательную программу.

    Реализует таблицу applications из раздела 2.3 курсовой работы.

    Attributes:
        id: Первичный ключ.
        user_id: Ссылка на абитуриента.
        university_id: Ссылка на выбранный вуз.
        program_id: Ссылка на образовательную программу.
        priority: Приоритет направления в личном списке.
        total_score: Итоговый конкурсный балл (ЕГЭ + ИД).
        individual_score: Баллы за индивидуальные достижения.
        status: Статус заявления (draft/submitted/accepted/rejected).
        comment: Комментарий абитуриента.
        created_at: Дата создания.
        updated_at: Дата последнего изменения.
    """

    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    university_id = db.Column(
        db.Integer, db.ForeignKey("universities.id"), nullable=False
    )
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=1)
    total_score = db.Column(db.Integer, nullable=False, default=0)
    individual_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), nullable=False, default="draft")
    comment = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Отношения
    university = db.relationship("University", lazy=True)
    program = db.relationship("Program", lazy=True)

    def to_dict(self) -> dict:
        """Сериализует заявление в словарь для REST API."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "university_id": self.university_id,
            "program_id": self.program_id,
            "priority": self.priority,
            "total_score": self.total_score,
            "individual_score": self.individual_score,
            "status": self.status,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "university_name": self.university.short_name if self.university else "",
            "program_name": self.program.name if self.program else "",
        }

    def __repr__(self) -> str:
        return f"<Application user={self.user_id} program={self.program_id} status={self.status}>"


class Deadline(db.Model):
    """
    Срок подачи документов или другое важное событие приёмной кампании.

    Attributes:
        id: Первичный ключ.
        university_id: Ссылка на вуз.
        title: Название события.
        deadline_type: Тип ('documents', 'consent', 'exam').
        deadline_date: Дата дедлайна.
        description: Подробное описание.
    """

    __tablename__ = "deadlines"

    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(
        db.Integer, db.ForeignKey("universities.id"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    deadline_type = db.Column(db.String(50), default="documents")
    deadline_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, default="")

    @property
    def days_until(self) -> int:
        """Количество дней до дедлайна (отрицательное если прошёл)."""
        return (self.deadline_date - date.today()).days

    @property
    def urgency_class(self) -> str:
        """CSS-класс срочности для фронтенда."""
        d = self.days_until
        if d < 0:
            return "passed"
        if d <= 7:
            return "urgent"
        if d <= 21:
            return "soon"
        return "ok"

    def to_dict(self) -> dict:
        """Сериализует дедлайн в словарь для REST API."""
        return {
            "id": self.id,
            "university_id": self.university_id,
            "university_name": self.university.short_name if self.university else "",
            "title": self.title,
            "deadline_type": self.deadline_type,
            "deadline_date": self.deadline_date.isoformat(),
            "description": self.description,
            "days_until": self.days_until,
            "urgency_class": self.urgency_class,
        }

    def __repr__(self) -> str:
        return f"<Deadline {self.title} {self.deadline_date}>"
