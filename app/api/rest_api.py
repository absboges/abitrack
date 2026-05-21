"""
REST API (JSON) — клиент-серверная часть приложения.

Предоставляет JSON-эндпоинты для взаимодействия фронтенда
с бэкендом без перезагрузки страницы. Используется JavaScript-клиентом
(fetch API) на страницах калькулятора и дашборда.

Endpoints:
    GET  /api/v1/programs          — список всех программ
    GET  /api/v1/programs/<id>     — одна программа
    GET  /api/v1/universities      — список вузов
    GET  /api/v1/deadlines         — предстоящие дедлайны
    POST /api/v1/calculate         — расчёт балла (без сохранения)
    GET  /api/v1/me                — данные текущего пользователя
    GET  /api/v1/me/applications   — заявления текущего пользователя
    GET  /api/v1/notifications     — уведомления текущего пользователя
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.models.domain import University, Program, Deadline
from app.services.calculator import ScoreCalculator
from app.services.services import DeadlineService, ApplicationService
from app.patterns.observer import get_notifications

api_bp = Blueprint("api", __name__)
calculator = ScoreCalculator()


def api_error(message: str, code: int = 400):
    return jsonify({"error": message}), code


def api_ok(data: dict, code: int = 200):
    return jsonify({"ok": True, "data": data}), code


# ─── UNIVERSITIES ─────────────────────────────────────────────────────────────


@api_bp.get("/universities")
@login_required
def api_universities():
    """Возвращает список всех вузов."""
    unis = University.query.all()
    return api_ok({"universities": [u.to_dict() for u in unis]})


# ─── PROGRAMS ─────────────────────────────────────────────────────────────────


@api_bp.get("/programs")
@login_required
def api_programs():
    """Возвращает список всех образовательных программ."""
    programs = Program.query.all()
    return api_ok({"programs": [p.to_dict() for p in programs]})


@api_bp.get("/programs/<int:program_id>")
@login_required
def api_program(program_id: int):
    """Возвращает данные одной программы по ID."""
    prog = Program.query.get(program_id)
    if not prog:
        return api_error("Программа не найдена", 404)
    return api_ok(prog.to_dict())


# ─── CALCULATE ────────────────────────────────────────────────────────────────


@api_bp.post("/calculate")
@login_required
def api_calculate():
    """
    Рассчитывает конкурсный балл для программы без сохранения.

    Request body (JSON):
        {
            "program_id": 1,
            "individual_score": 5
        }

    Response:
        {
            "ok": true,
            "data": {
                "exam_score": 253,
                "individual_score": 5,
                "total_score": 258,
                "can_apply": true,
                "score_gap": 38,
                "missing_subjects": []
            }
        }
    """
    body = request.get_json(silent=True) or {}
    program_id = body.get("program_id")
    individual = int(body.get("individual_score", 0))

    if not program_id:
        return api_error("Укажите program_id")

    prog = Program.query.get(program_id)
    if not prog:
        return api_error("Программа не найдена", 404)

    exam_results = {r.subject: r.score for r in current_user.exam_results}
    result = calculator.calculate_for_program(
        exam_results, prog.subject_list, individual, prog.min_score
    )
    return api_ok(result.to_dict())


# ─── DEADLINES ────────────────────────────────────────────────────────────────


@api_bp.get("/deadlines")
@login_required
def api_deadlines():
    """
    Возвращает предстоящие дедлайны.

    Query params:
        mine=1 — только дедлайны вузов из заявлений пользователя
        limit=N — количество (по умолчанию 10)
    """
    mine = request.args.get("mine") == "1"
    limit = min(int(request.args.get("limit", 10)), 50)

    uni_ids = None
    if mine:
        uni_ids = [a.university_id for a in current_user.applications]

    deadlines = DeadlineService.get_upcoming(uni_ids, limit)
    return api_ok({"deadlines": [d.to_dict() for d in deadlines]})


# ─── CURRENT USER ─────────────────────────────────────────────────────────────


@api_bp.get("/me")
@login_required
def api_me():
    """Возвращает данные текущего авторизованного пользователя."""
    return api_ok(current_user.to_dict())


@api_bp.get("/me/applications")
@login_required
def api_my_applications():
    """Возвращает заявления текущего пользователя."""
    apps = ApplicationService.get_user_applications(current_user.id)
    return api_ok({"applications": [a.to_dict() for a in apps]})


@api_bp.get("/notifications")
@login_required
def api_notifications():
    """Возвращает уведомления о приближающихся дедлайнах."""
    notifications = get_notifications(current_user.email)
    return api_ok({"notifications": notifications, "count": len(notifications)})
