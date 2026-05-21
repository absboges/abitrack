"""
Сервис расчёта конкурсного балла.

Реализует паттерн «Стратегия» (Strategy): алгоритм расчёта балла
вынесен в отдельную иерархию классов и может быть заменён без изменения
клиентского кода. Это позволяет поддерживать разные правила подсчёта
(стандартный ЕГЭ, ДВИ, олимпиады) через единый интерфейс.

Паттерн Observer используется для уведомления об изменении балла.

Диаграмма классов (UML):
    ScoreStrategy (abstract)
        ├── StandardScoreStrategy
        └── OlympiadScoreStrategy

    ScoreCalculator
        - strategy: ScoreStrategy
        + calculate(exam_results, program) -> ScoreResult
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScoreResult:
    """
    Результат расчёта конкурсного балла.

    Attributes:
        exam_score: Сумма баллов по требуемым предметам ЕГЭ.
        individual_score: Баллы за индивидуальные достижения.
        total_score: Итоговый конкурсный балл (exam + individual).
        missing_subjects: Предметы, результаты по которым не введены.
        can_apply: True если балл >= минимального порога программы.
        score_gap: Разница между total_score и min_score программы.
    """

    exam_score: int
    individual_score: int
    total_score: int
    missing_subjects: List[str]
    can_apply: bool
    score_gap: int

    def to_dict(self) -> dict:
        return {
            "exam_score": self.exam_score,
            "individual_score": self.individual_score,
            "total_score": self.total_score,
            "missing_subjects": self.missing_subjects,
            "can_apply": self.can_apply,
            "score_gap": self.score_gap,
        }


# ─── ПАТТЕРН СТРАТЕГИЯ ────────────────────────────────────────────────────────


class ScoreStrategy(ABC):
    """
    Абстрактная стратегия расчёта конкурсного балла.

    Определяет интерфейс, который должны реализовать все конкретные
    стратегии расчёта. Используется в паттерне «Стратегия».
    """

    @abstractmethod
    def calculate(
        self,
        exam_results: Dict[str, int],
        required_subjects: List[str],
        individual_score: int,
        min_score: int,
    ) -> ScoreResult:
        """
        Вычисляет конкурсный балл.

        Args:
            exam_results: Словарь {предмет: балл}.
            required_subjects: Список необходимых предметов ЕГЭ.
            individual_score: Баллы за индивидуальные достижения (0–10).
            min_score: Минимальный порог программы.

        Returns:
            ScoreResult с итоговым баллом и метаданными.
        """


class StandardScoreStrategy(ScoreStrategy):
    """
    Стандартная стратегия расчёта по формуле из курсовой работы.

    Формула: Stotal = Σ Ei + Bind
    где Ei — балл по i-му предмету ЕГЭ, Bind — баллы за ИД.
    """

    def calculate(
        self,
        exam_results: Dict[str, int],
        required_subjects: List[str],
        individual_score: int,
        min_score: int,
    ) -> ScoreResult:
        missing = [s for s in required_subjects if s not in exam_results]
        exam_score = sum(exam_results.get(s, 0) for s in required_subjects)
        total = exam_score + individual_score
        gap = total - min_score
        return ScoreResult(
            exam_score=exam_score,
            individual_score=individual_score,
            total_score=total,
            missing_subjects=missing,
            can_apply=(not missing and total >= min_score),
            score_gap=gap,
        )


class OlympiadScoreStrategy(ScoreStrategy):
    """
    Стратегия расчёта для олимпиадников.

    Если абитуриент — победитель олимпиады, по профильному предмету
    засчитывается максимальный балл (100).
    """

    def __init__(self, olympiad_subject: str):
        """
        Args:
            olympiad_subject: Предмет, по которому есть олимпиада.
        """
        self._olympiad_subject = olympiad_subject

    def calculate(
        self,
        exam_results: Dict[str, int],
        required_subjects: List[str],
        individual_score: int,
        min_score: int,
    ) -> ScoreResult:
        boosted = dict(exam_results)
        if self._olympiad_subject in required_subjects:
            boosted[self._olympiad_subject] = 100

        missing = [s for s in required_subjects if s not in boosted]
        exam_score = sum(boosted.get(s, 0) for s in required_subjects)
        total = exam_score + individual_score
        gap = total - min_score
        return ScoreResult(
            exam_score=exam_score,
            individual_score=individual_score,
            total_score=total,
            missing_subjects=missing,
            can_apply=(not missing and total >= min_score),
            score_gap=gap,
        )


# ─── КОНТЕКСТ СТРАТЕГИИ ───────────────────────────────────────────────────────


class ScoreCalculator:
    """
    Контекст паттерна «Стратегия».

    Использует ScoreStrategy для расчёта конкурсного балла.
    Стратегию можно заменить во время выполнения через set_strategy().

    Example:
        >>> calc = ScoreCalculator()
        >>> results = {'Математика': 85, 'Русский язык': 78, 'Информатика': 90}
        >>> from app.models.domain import Program
        >>> # Упрощённый пример без ORM
        >>> calc.set_strategy(StandardScoreStrategy())
    """

    def __init__(self, strategy: ScoreStrategy = None):
        self._strategy = strategy or StandardScoreStrategy()

    def set_strategy(self, strategy: ScoreStrategy) -> None:
        """
        Заменяет текущую стратегию расчёта.

        Args:
            strategy: Новая стратегия расчёта.
        """
        self._strategy = strategy

    def calculate_for_program(
        self,
        exam_results: Dict[str, int],
        required_subjects: List[str],
        individual_score: int,
        min_score: int,
    ) -> ScoreResult:
        """
        Вычисляет конкурсный балл для конкретной программы.

        Args:
            exam_results: Словарь {предмет: балл} абитуриента.
            required_subjects: Необходимые предметы ЕГЭ для программы.
            individual_score: Баллы за индивидуальные достижения.
            min_score: Минимальный порог программы.

        Returns:
            ScoreResult с результатом расчёта.

        Example:
            >>> calc = ScoreCalculator()
            >>> r = calc.calculate_for_program(
            ...     {'Математика': 85, 'Русский язык': 78, 'Информатика': 90},
            ...     ['Математика', 'Русский язык', 'Информатика'],
            ...     5, 220
            ... )
            >>> r.total_score
            258
            >>> r.can_apply
            True
        """
        return self._strategy.calculate(
            exam_results, required_subjects, individual_score, min_score
        )

    def rank_programs(
        self,
        exam_results: Dict[str, int],
        programs: list,
        individual_score: int = 0,
    ) -> List[dict]:
        """
        Оценивает и ранжирует список программ по конкурсному баллу.

        Args:
            exam_results: Словарь {предмет: балл} абитуриента.
            programs: Список объектов Program (ORM).
            individual_score: Баллы за индивидуальные достижения.

        Returns:
            Список словарей {program, result} отсортированный по score_gap убыванию.
        """
        ranked = []
        for prog in programs:
            result = self.calculate_for_program(
                exam_results,
                prog.subject_list,
                individual_score,
                prog.min_score,
            )
            ranked.append({"program": prog, "result": result})
        ranked.sort(key=lambda x: x["result"].score_gap, reverse=True)
        return ranked
