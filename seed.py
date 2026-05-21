"""
Скрипт первичного заполнения базы данных тестовыми данными.

Вызывается при первом запуске приложения.
Добавляет вузы, программы, дедлайны и тестовых пользователей.
"""

from datetime import date
from factory import db
from app.models.user import User
from app.models.domain import University, Program, Deadline


def seed_all() -> None:
    """Заполняет БД начальными данными. Безопасно при повторном вызове."""
    if University.query.count() > 0:
        return  # Уже заполнено

    # ─── Вузы ─────────────────────────────────────────────────────────────────
    unis = [
        University(name="Московский политехнический университет",
                   short_name="Мосполитех", city="Москва",
                   website="https://mospolytech.ru",
                   description="Ведущий технический вуз Москвы"),
        University(name="Московский государственный университет им. М.В. Ломоносова",
                   short_name="МГУ", city="Москва",
                   website="https://msu.ru",
                   description="Старейший университет России"),
        University(name="НИУ «Высшая школа экономики»",
                   short_name="НИУ ВШЭ", city="Москва",
                   website="https://hse.ru",
                   description="Ведущий исследовательский университет"),
        University(name="МГТУ им. Н.Э. Баумана",
                   short_name="МГТУ Бауман", city="Москва",
                   website="https://bmstu.ru",
                   description="Ведущий технический университет России"),
        University(name="Санкт-Петербургский государственный университет",
                   short_name="СПбГУ", city="Санкт-Петербург",
                   website="https://spbu.ru",
                   description="Старейший университет Санкт-Петербурга"),
    ]
    db.session.add_all(unis)
    db.session.flush()

    # ─── Программы ────────────────────────────────────────────────────────────
    programs = [
        Program(university_id=unis[0].id, name="Информатика и вычислительная техника",
                code="09.03.01", field="IT", budget_places=50, paid_places=30,
                min_score=180, subjects="Математика,Информатика,Русский язык"),
        Program(university_id=unis[0].id, name="Программная инженерия",
                code="09.03.04", field="IT", budget_places=40, paid_places=25,
                min_score=190, subjects="Математика,Информатика,Русский язык"),
        Program(university_id=unis[1].id, name="Прикладная математика и информатика",
                code="01.03.02", field="Math", budget_places=60, paid_places=20,
                min_score=260, subjects="Математика,Физика,Русский язык"),
        Program(university_id=unis[2].id, name="Программная инженерия",
                code="09.03.04", field="IT", budget_places=45, paid_places=40,
                min_score=230, subjects="Математика,Информатика,Русский язык"),
        Program(university_id=unis[3].id, name="Информатика и системы управления",
                code="09.03.01", field="IT", budget_places=80, paid_places=20,
                min_score=200, subjects="Математика,Физика,Русский язык"),
        Program(university_id=unis[4].id, name="Математика и компьютерные науки",
                code="02.03.01", field="Math", budget_places=35, paid_places=15,
                min_score=240, subjects="Математика,Информатика,Русский язык"),
    ]
    db.session.add_all(programs)

    # ─── Дедлайны ─────────────────────────────────────────────────────────────
    deadlines = [
        Deadline(university_id=unis[0].id, title="Подача документов (бюджет)",
                 deadline_type="documents", deadline_date=date(2026, 7, 25),
                 description="Последний день подачи документов на бюджетные места"),
        Deadline(university_id=unis[0].id, title="Согласие на зачисление (1 волна)",
                 deadline_type="consent", deadline_date=date(2026, 8, 5),
                 description="Срок подачи согласия на зачисление"),
        Deadline(university_id=unis[1].id, title="Подача документов",
                 deadline_type="documents", deadline_date=date(2026, 7, 20),
                 description="Документы в МГУ"),
        Deadline(university_id=unis[1].id, title="Доп. вступительные испытания",
                 deadline_type="exam", deadline_date=date(2026, 7, 10),
                 description="ДВИ по профильному предмету"),
        Deadline(university_id=unis[2].id, title="Подача документов",
                 deadline_type="documents", deadline_date=date(2026, 7, 22),
                 description="Документы в ВШЭ"),
        Deadline(university_id=unis[3].id, title="Подача документов",
                 deadline_type="documents", deadline_date=date(2026, 7, 25),
                 description="Документы в Бауманку"),
        Deadline(university_id=unis[4].id, title="Подача документов",
                 deadline_type="documents", deadline_date=date(2026, 7, 20),
                 description="Документы в СПбГУ"),
    ]
    db.session.add_all(deadlines)

    # ─── Тестовые пользователи ────────────────────────────────────────────────
    admin = User(email="admin@mospolytech.ru", full_name="Администратор системы",
                 role="admin")
    admin.set_password("admin123")

    applicant = User(email="test@student.ru", full_name="Иванов Иван Иванович",
                     role="applicant")
    applicant.set_password("test123")

    db.session.add_all([admin, applicant])
    db.session.commit()
    print("[seed] База данных заполнена тестовыми данными")
