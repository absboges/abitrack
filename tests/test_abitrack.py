"""Unit-тесты АбиТрек — 49 тестов."""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import date, timedelta, datetime

from factory import create_app, db as _db
from app.models.user import User
from app.models.domain import University, Program, ExamResult, Application, Deadline
from app.services.calculator import (
    ScoreCalculator, StandardScoreStrategy, OlympiadScoreStrategy, ScoreResult
)
from app.patterns.observer import (
    DeadlineEventEmitter, DeadlineEvent, LoggingObserver, InAppNotifyObserver
)
from app.services.services import UserService, ApplicationService

# ── фикстуры ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()

@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Очищаем данные после каждого теста
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()

@pytest.fixture
def client(app): return app.test_client()

def unique_email(): return f"u_{uuid.uuid4().hex[:8]}@test.com"

@pytest.fixture
def uni(db):
    u = University(name="Тест Университет", short_name="ТУ", city="Москва")
    db.session.add(u); db.session.flush(); return u

@pytest.fixture
def prog(db, uni):
    p = Program(university_id=uni.id, name="Тест Программа", code="00.00.00",
                budget_places=30, paid_places=10, min_score=220,
                subjects="Математика,Информатика,Русский язык")
    db.session.add(p); db.session.flush(); return p

@pytest.fixture
def user(db):
    u = User(email=unique_email(), full_name="Тест Тестов")
    u.set_password("pass123"); db.session.add(u); db.session.flush(); return u

@pytest.fixture
def auth_client(client, app, user, db):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id); sess["_fresh"] = True
    return client

# ── ScoreCalculator / Strategy ─────────────────────────────────────────────────

class TestStandardScoreStrategy:
    def setup_method(self): self.calc = ScoreCalculator()

    def test_perfect_scores(self):
        r = self.calc.calculate_for_program(
            {"Математика":100,"Русский язык":100,"Информатика":100},
            ["Математика","Русский язык","Информатика"], 10, 200)
        assert r.exam_score==300 and r.total_score==310 and r.can_apply is True

    def test_below_minimum(self):
        r = self.calc.calculate_for_program(
            {"Математика":60,"Русский язык":60,"Информатика":60},
            ["Математика","Русский язык","Информатика"], 0, 220)
        assert r.can_apply is False and r.score_gap==-40

    def test_missing_subject_blocks(self):
        r = self.calc.calculate_for_program(
            {"Математика":90,"Русский язык":90},
            ["Математика","Русский язык","Информатика"], 0, 100)
        assert r.can_apply is False and "Информатика" in r.missing_subjects

    def test_individual_score_added(self):
        r = self.calc.calculate_for_program(
            {"Математика":80,"Русский язык":80,"Информатика":80},
            ["Математика","Русский язык","Информатика"], 7, 220)
        assert r.total_score==247

    def test_exactly_at_minimum(self):
        r = self.calc.calculate_for_program(
            {"Математика":80,"Русский язык":70,"Информатика":70},
            ["Математика","Русский язык","Информатика"], 0, 220)
        assert r.can_apply is True and r.score_gap==0

    def test_score_result_to_dict(self):
        r = ScoreResult(250,5,255,[],True,30)
        d = r.to_dict()
        assert d["total_score"]==255 and d["can_apply"] is True

class TestOlympiadScoreStrategy:
    def test_boosts_to_100(self):
        calc = ScoreCalculator(OlympiadScoreStrategy("Математика"))
        r = calc.calculate_for_program(
            {"Математика":70,"Русский язык":80,"Информатика":75},
            ["Математика","Русский язык","Информатика"], 0, 230)
        assert r.exam_score==255 and r.can_apply is True

    def test_strategy_switch_at_runtime(self):
        calc = ScoreCalculator()
        assert isinstance(calc._strategy, StandardScoreStrategy)
        calc.set_strategy(OlympiadScoreStrategy("Физика"))
        assert isinstance(calc._strategy, OlympiadScoreStrategy)

class TestRankPrograms:
    def test_sorted_by_gap_desc(self):
        calc = ScoreCalculator()
        class FP:
            def __init__(self, subj, mn): self.subject_list=subj; self.min_score=mn
        programs = [FP(["Математика","Русский язык"],160), FP(["Математика","Русский язык"],180)]
        res = calc.rank_programs({"Математика":90,"Русский язык":85}, programs)
        assert res[0]["result"].score_gap >= res[1]["result"].score_gap

# ── Observer pattern ───────────────────────────────────────────────────────────

class TestObserverPattern:
    def setup_method(self):
        self.emitter = DeadlineEventEmitter()
        self.obs = InAppNotifyObserver()

    def test_subscribe_and_notify(self):
        self.emitter.subscribe(self.obs)
        self.emitter.notify(DeadlineEvent("ТУ","Подача",date.today()+timedelta(5),5,"a@b.com"))
        notes = self.obs.get_notifications("a@b.com")
        assert len(notes)==1 and "ТУ" in notes[0]["message"]

    def test_unsubscribe_stops(self):
        self.emitter.subscribe(self.obs)
        self.emitter.unsubscribe(self.obs)
        self.emitter.notify(DeadlineEvent("X","Y",date.today(),0,"x@x.com"))
        assert self.obs.get_notifications("x@x.com")==[]

    def test_multiple_observers(self):
        obs2 = InAppNotifyObserver()
        self.emitter.subscribe(self.obs); self.emitter.subscribe(obs2)
        self.emitter.notify(DeadlineEvent("У","Т",date.today()+timedelta(3),3,"u@u.com"))
        assert len(self.obs.get_notifications("u@u.com"))==1
        assert len(obs2.get_notifications("u@u.com"))==1

    def test_clear(self):
        self.emitter.subscribe(self.obs)
        self.emitter.notify(DeadlineEvent("В","Д",date.today(),0,"v@v.com"))
        self.obs.clear("v@v.com")
        assert self.obs.get_notifications("v@v.com")==[]

    def test_urgency_soon(self):
        self.emitter.subscribe(self.obs)
        self.emitter.notify(DeadlineEvent("А","Б",date.today()+timedelta(15),15,"a@a.com"))
        assert self.obs.get_notifications("a@a.com")[0]["urgency"]=="soon"

    def test_check_deadlines_far_future(self):
        self.emitter.subscribe(self.obs)
        class FU: short_name="ФУ"
        class FDL:
            university=FU(); title="Далёкий"; deadline_date=date.today()+timedelta(60); days_until=60
        self.emitter.check_deadlines("z@z.com", [FDL()])
        assert self.obs.get_notifications("z@z.com")==[]

# ── Модели ─────────────────────────────────────────────────────────────────────

class TestUserModel:
    def test_password_hashing(self, app):
        with app.app_context():
            u = User(email="h@h.com"); u.set_password("secret")
            assert u.check_password("secret") and not u.check_password("wrong")

    def test_hash_not_plaintext(self, app):
        with app.app_context():
            u = User(email="h2@h.com"); u.set_password("pw")
            assert "pw" not in u.password_hash

    def test_is_admin(self, app):
        with app.app_context():
            assert User(email="a@a.com",role="admin").is_admin is True
            assert User(email="u@u.com",role="applicant").is_admin is False

    def test_total_exam_score(self, db, user):
        db.session.add_all([
            ExamResult(user_id=user.id,subject="Математика",score=85),
            ExamResult(user_id=user.id,subject="Русский язык",score=90)
        ]); db.session.flush(); db.session.refresh(user)
        assert user.total_exam_score==175

    def test_to_dict_no_password(self, app):
        with app.app_context():
            u = User(email="t@t.com",full_name="Тест",role="applicant",
                     created_at=datetime.utcnow())
            u.set_password("pw")
            d = u.to_dict()
            assert "password_hash" not in d and d["email"]=="t@t.com"

class TestDeadlineModel:
    def test_days_until_future(self, db, uni):
        dl = Deadline(university_id=uni.id, title="T", deadline_type="documents",
                      deadline_date=date.today()+timedelta(10))
        assert dl.days_until==10

    def test_days_until_past(self, db, uni):
        dl = Deadline(university_id=uni.id, title="T", deadline_type="documents",
                      deadline_date=date.today()-timedelta(3))
        assert dl.days_until==-3

    def test_urgency_urgent(self, db, uni):
        dl = Deadline(university_id=uni.id, title="T", deadline_type="documents",
                      deadline_date=date.today()+timedelta(5))
        assert dl.urgency_class=="urgent"

    def test_urgency_soon(self, db, uni):
        dl = Deadline(university_id=uni.id, title="T", deadline_type="documents",
                      deadline_date=date.today()+timedelta(15))
        assert dl.urgency_class=="soon"

    def test_urgency_ok(self, db, uni):
        dl = Deadline(university_id=uni.id, title="T", deadline_type="documents",
                      deadline_date=date.today()+timedelta(30))
        assert dl.urgency_class=="ok"

class TestProgramModel:
    def test_subject_list(self, app):
        with app.app_context():
            p = Program(subjects="Математика, Физика, Русский язык")
            assert p.subject_list==["Математика","Физика","Русский язык"]

    def test_subject_list_empty(self, app):
        with app.app_context():
            assert Program(subjects="").subject_list==[]

# ── Сервисный слой ─────────────────────────────────────────────────────────────

class TestUserService:
    def test_create(self, db):
        u = UserService.create(unique_email(),"pw123","Новый")
        assert u.id and u.role=="applicant"

    def test_create_duplicate(self, db, user):
        with pytest.raises(ValueError, match="уже существует"):
            UserService.create(user.email,"pw")

    def test_authenticate_ok(self, db, user):
        u = UserService.authenticate(user.email,"pass123")
        assert u and u.id==user.id

    def test_authenticate_wrong_pw(self, db, user):
        assert UserService.authenticate(user.email,"bad") is None

    def test_authenticate_unknown(self, db):
        assert UserService.authenticate("nobody@x.com","pw") is None

    def test_update_profile(self, db, user):
        u = UserService.update_profile(user,full_name="Новое",phone="+7")
        assert u.full_name=="Новое" and u.phone=="+7"

    def test_save_results_replaces(self, db, user):
        UserService.save_exam_results(user,{"Математика":90})
        UserService.save_exam_results(user,{"Информатика":85,"Русский язык":75})
        r = {x.subject:x.score for x in user.exam_results}
        assert "Математика" not in r and r["Информатика"]==85

    def test_save_results_clamps(self, db, user):
        UserService.save_exam_results(user,{"Математика":150})
        r = ExamResult.query.filter_by(user_id=user.id,subject="Математика").first()
        assert r.score==100

class TestApplicationService:
    def _give_scores(self, db, user):
        UserService.save_exam_results(user,{"Математика":80,"Информатика":75,"Русский язык":70})
        db.session.refresh(user)

    def test_add(self, db, user, prog):
        self._give_scores(db,user)
        a = ApplicationService.add(user,prog.id,5)
        assert a.id and a.total_score==230

    def test_add_duplicate_raises(self, db, user, prog):
        self._give_scores(db,user)
        ApplicationService.add(user,prog.id)
        with pytest.raises(ValueError,match="уже добавлено"):
            ApplicationService.add(user,prog.id)

    def test_update_status(self, db, user, prog):
        self._give_scores(db,user)
        a = ApplicationService.add(user,prog.id)
        assert ApplicationService.update_status(a.id,user.id,"submitted").status=="submitted"

    def test_update_status_invalid(self, db, user, prog):
        self._give_scores(db,user)
        a = ApplicationService.add(user,prog.id)
        with pytest.raises(ValueError,match="Недопустимый"):
            ApplicationService.update_status(a.id,user.id,"unknown")

    def test_delete(self, db, user, prog):
        self._give_scores(db,user)
        a = ApplicationService.add(user,prog.id)
        aid = a.id; ApplicationService.delete(aid,user.id)
        assert Application.query.get(aid) is None

# ── REST API ───────────────────────────────────────────────────────────────────

class TestRestAPI:
    def test_universities(self, auth_client, db, uni):
        r = auth_client.get("/api/v1/universities")
        assert r.status_code==200 and r.get_json()["ok"] is True

    def test_programs(self, auth_client, db, prog):
        r = auth_client.get("/api/v1/programs")
        assert r.status_code==200

    def test_program_404(self, auth_client, db):
        r = auth_client.get("/api/v1/programs/99999")
        assert r.status_code==404

    def test_calculate(self, auth_client, db, user, prog):
        db.session.add_all([
            ExamResult(user_id=user.id,subject="Математика",score=80),
            ExamResult(user_id=user.id,subject="Информатика",score=75),
            ExamResult(user_id=user.id,subject="Русский язык",score=70),
        ]); db.session.flush()
        r = auth_client.post("/api/v1/calculate",
            json={"program_id":prog.id,"individual_score":5})
        assert r.status_code==200 and r.get_json()["data"]["total_score"]==230

    def test_calculate_no_program_id(self, auth_client, db):
        r = auth_client.post("/api/v1/calculate",json={})
        assert r.status_code==400

    def test_me(self, auth_client, db, user):
        r = auth_client.get("/api/v1/me")
        assert r.status_code==200 and r.get_json()["data"]["email"]==user.email

    def test_deadlines(self, auth_client, db, uni):
        db.session.add(Deadline(university_id=uni.id,title="T",deadline_type="documents",
                                deadline_date=date.today()+timedelta(30)))
        db.session.flush()
        r = auth_client.get("/api/v1/deadlines")
        assert r.status_code==200

    def test_unauthorized(self, client, db):
        r = client.get("/api/v1/me")
        assert r.status_code in (302,401)

    def test_notifications(self, auth_client, db):
        r = auth_client.get("/api/v1/notifications")
        assert r.status_code==200 and "notifications" in r.get_json()["data"]
