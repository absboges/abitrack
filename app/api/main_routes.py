"""
Blueprint основных страниц приложения (dashboard, calculator, universities, …).
"""

from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.domain import University, Program, Deadline, Application
from app.services.services import UserService, ApplicationService, DeadlineService
from app.services.calculator import ScoreCalculator
from app.patterns.observer import emitter, get_notifications

main_bp = Blueprint("main", __name__)

EXAM_SUBJECTS = [
    "Русский язык", "Математика", "Физика", "Информатика",
    "Химия", "Биология", "История", "Обществознание",
    "Английский язык", "Литература",
]

calculator = ScoreCalculator()


@main_bp.route("/dashboard")
@login_required
def dashboard():
    exam_results = {r.subject: r.score for r in current_user.exam_results}
    applications = ApplicationService.get_user_applications(current_user.id)
    uni_ids = list({a.university_id for a in applications})
    upcoming = DeadlineService.get_upcoming(uni_ids or None, limit=6)

    # Паттерн Observer: проверяем дедлайны и формируем уведомления
    if uni_ids:
        emitter.check_deadlines(current_user.email, upcoming)
    notifications = get_notifications(current_user.email)

    return render_template(
        "main/dashboard.html",
        exam_results=exam_results,
        applications=applications,
        upcoming=upcoming,
        notifications=notifications,
        today=date.today(),
    )


@main_bp.route("/calculator", methods=["GET", "POST"])
@login_required
def calc():
    if request.method == "POST":
        scores = {}
        for subj in EXAM_SUBJECTS:
            val = request.form.get(f"score_{subj}", "").strip()
            if val.isdigit():
                scores[subj] = int(val)
        UserService.save_exam_results(current_user, scores)
        flash("Результаты ЕГЭ сохранены", "success")
        return redirect(url_for("main.calc"))

    exam_results = {r.subject: r.score for r in current_user.exam_results}
    programs = Program.query.all()
    individual = int(request.args.get("ind", 0))
    ranked = calculator.rank_programs(exam_results, programs, individual)

    return render_template(
        "main/calculator.html",
        subjects=EXAM_SUBJECTS,
        exam_results=exam_results,
        ranked=ranked,
        individual=individual,
        total=sum(exam_results.values()),
    )


@main_bp.route("/universities")
@login_required
def universities():
    q = request.args.get("q", "").strip()
    unis = University.query
    if q:
        unis = unis.filter(University.name.ilike(f"%{q}%"))
    unis = unis.all()
    user_app_program_ids = {a.program_id for a in current_user.applications}
    return render_template(
        "main/universities.html",
        universities=unis,
        query=q,
        user_app_program_ids=user_app_program_ids,
    )


@main_bp.route("/applications")
@login_required
def applications():
    apps = ApplicationService.get_user_applications(current_user.id)
    return render_template("main/applications.html", applications=apps, today=date.today())


@main_bp.route("/applications/add/<int:program_id>", methods=["POST"])
@login_required
def add_application(program_id):
    individual = int(request.form.get("individual", 0))
    try:
        ApplicationService.add(current_user, program_id, individual)
        flash("Направление добавлено в список заявлений", "success")
    except ValueError as e:
        flash(str(e), "info")
    return redirect(url_for("main.universities"))


@main_bp.route("/applications/status/<int:app_id>", methods=["POST"])
@login_required
def update_status(app_id):
    new_status = request.form.get("status", "draft")
    try:
        ApplicationService.update_status(app_id, current_user.id, new_status)
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.applications"))


@main_bp.route("/applications/delete/<int:app_id>", methods=["POST"])
@login_required
def delete_application(app_id):
    try:
        ApplicationService.delete(app_id, current_user.id)
        flash("Заявление удалено", "info")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.applications"))


@main_bp.route("/deadlines")
@login_required
def deadlines():
    all_dl = Deadline.query.order_by(Deadline.deadline_date).all()
    by_uni = {}
    for d in all_dl:
        key = d.university.short_name or d.university.name
        by_uni.setdefault(key, []).append(d)
    user_uni_ids = {a.university_id for a in current_user.applications}
    return render_template(
        "main/deadlines.html",
        by_uni=by_uni,
        user_uni_ids=user_uni_ids,
        today=date.today(),
    )


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        UserService.update_profile(
            current_user,
            full_name=request.form.get("full_name", "").strip(),
            phone=request.form.get("phone", "").strip(),
            new_password=request.form.get("new_password", "").strip() or None,
        )
        flash("Профиль обновлён", "success")
    return render_template("main/profile.html")
