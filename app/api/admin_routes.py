"""
Blueprint административной панели.
Доступен только пользователям с ролью 'admin'.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from factory import db
from app.models.user import User
from app.models.domain import University, Program, Deadline
from datetime import date

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    """Декоратор: требует роль 'admin'."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash("Доступ запрещён", "error")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@admin_required
def panel():
    unis = University.query.all()
    users = User.query.all()
    deadlines = Deadline.query.order_by(Deadline.deadline_date).all()
    return render_template("admin/panel.html", universities=unis,
                           users=users, deadlines=deadlines)


@admin_bp.route("/university/add", methods=["POST"])
@admin_required
def add_university():
    uni = University(
        name=request.form["name"],
        short_name=request.form.get("short_name", ""),
        city=request.form.get("city", ""),
        website=request.form.get("website", ""),
        description=request.form.get("description", ""),
    )
    db.session.add(uni)
    db.session.commit()
    flash(f"Вуз «{uni.short_name}» добавлен", "success")
    return redirect(url_for("admin.panel"))


@admin_bp.route("/program/add", methods=["POST"])
@admin_required
def add_program():
    prog = Program(
        university_id=int(request.form["university_id"]),
        name=request.form["name"],
        code=request.form.get("code", ""),
        budget_places=int(request.form.get("budget_places", 0)),
        paid_places=int(request.form.get("paid_places", 0)),
        min_score=int(request.form.get("min_score", 0)),
        subjects=request.form.get("subjects", ""),
    )
    db.session.add(prog)
    db.session.commit()
    flash(f"Программа «{prog.name}» добавлена", "success")
    return redirect(url_for("admin.panel"))


@admin_bp.route("/deadline/add", methods=["POST"])
@admin_required
def add_deadline():
    dl = Deadline(
        university_id=int(request.form["university_id"]),
        title=request.form["title"],
        deadline_type=request.form.get("deadline_type", "documents"),
        deadline_date=date.fromisoformat(request.form["deadline_date"]),
        description=request.form.get("description", ""),
    )
    db.session.add(dl)
    db.session.commit()
    flash("Срок добавлен", "success")
    return redirect(url_for("admin.panel"))
