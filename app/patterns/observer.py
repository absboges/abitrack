"""
Паттерн «Наблюдатель» (Observer) для системы уведомлений.

Используется для оповещения об истечении сроков подачи документов.
Позволяет добавлять новые типы уведомлений (email, SMS, push)
без изменения кода, который генерирует события.

UML-диаграмма:
    DeadlineEventEmitter (Subject / Observable)
        - _observers: List[DeadlineObserver]
        + subscribe(observer)
        + unsubscribe(observer)
        + notify(event)

    DeadlineObserver (abstract)
        + on_deadline_event(event)
            ├── LoggingObserver       → пишет в лог
            └── InAppNotifyObserver  → сохраняет уведомление в БД
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeadlineEvent:
    """
    Событие приближающегося дедлайна.

    Attributes:
        university_name: Название вуза.
        deadline_title: Название срока.
        deadline_date: Дата дедлайна.
        days_until: Дней до дедлайна.
        user_email: Email абитуриента.
    """

    university_name: str
    deadline_title: str
    deadline_date: date
    days_until: int
    user_email: str


# ─── ИНТЕРФЕЙС НАБЛЮДАТЕЛЯ ────────────────────────────────────────────────────


class DeadlineObserver(ABC):
    """Абстрактный наблюдатель за событиями дедлайнов."""

    @abstractmethod
    def on_deadline_event(self, event: DeadlineEvent) -> None:
        """
        Обрабатывает событие дедлайна.

        Args:
            event: Данные о приближающемся дедлайне.
        """


# ─── КОНКРЕТНЫЕ НАБЛЮДАТЕЛИ ───────────────────────────────────────────────────


class LoggingObserver(DeadlineObserver):
    """Наблюдатель, который логирует события в консоль/файл."""

    def on_deadline_event(self, event: DeadlineEvent) -> None:
        logger.warning(
            "[DEADLINE] %s: '%s' через %d дн. (пользователь: %s)",
            event.university_name,
            event.deadline_title,
            event.days_until,
            event.user_email,
        )


class InAppNotifyObserver(DeadlineObserver):
    """
    Наблюдатель, который сохраняет уведомления в памяти приложения.

    В production можно заменить на запись в БД или отправку email.
    """

    def __init__(self):
        self._notifications: List[dict] = []

    def on_deadline_event(self, event: DeadlineEvent) -> None:
        self._notifications.append(
            {
                "user_email": event.user_email,
                "message": (
                    f"Осталось {event.days_until} дней: "
                    f"{event.university_name} — {event.deadline_title} "
                    f"({event.deadline_date.strftime('%d.%m.%Y')})"
                ),
                "urgency": "urgent" if event.days_until <= 7 else "soon",
            }
        )

    def get_notifications(self, user_email: str) -> List[dict]:
        """Возвращает уведомления для конкретного пользователя."""
        return [n for n in self._notifications if n["user_email"] == user_email]

    def clear(self, user_email: str) -> None:
        """Очищает уведомления пользователя."""
        self._notifications = [
            n for n in self._notifications if n["user_email"] != user_email
        ]


# ─── СУБЪЕКТ (ИЗДАТЕЛЬ) ───────────────────────────────────────────────────────


class DeadlineEventEmitter:
    """
    Издатель событий дедлайнов (Subject в паттерне Observer).

    Хранит список наблюдателей и рассылает им уведомления
    при появлении новых событий.
    """

    def __init__(self):
        self._observers: List[DeadlineObserver] = []

    def subscribe(self, observer: DeadlineObserver) -> None:
        """Подписывает наблюдателя на события."""
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: DeadlineObserver) -> None:
        """Отписывает наблюдателя."""
        self._observers.remove(observer)

    def notify(self, event: DeadlineEvent) -> None:
        """Рассылает событие всем подписчикам."""
        for observer in self._observers:
            observer.on_deadline_event(event)

    def check_deadlines(self, user_email: str, deadlines: list) -> None:
        """
        Проверяет список дедлайнов и рассылает события для срочных.

        Args:
            user_email: Email пользователя.
            deadlines: Список объектов Deadline.
        """
        for dl in deadlines:
            days = dl.days_until
            if 0 <= days <= 14:
                self.notify(
                    DeadlineEvent(
                        university_name=dl.university.short_name,
                        deadline_title=dl.title,
                        deadline_date=dl.deadline_date,
                        days_until=days,
                        user_email=user_email,
                    )
                )


# Глобальный экземпляр — Singleton через модуль
_notify_observer = InAppNotifyObserver()
_logging_observer = LoggingObserver()

emitter = DeadlineEventEmitter()
emitter.subscribe(_logging_observer)
emitter.subscribe(_notify_observer)


def get_notifications(user_email: str) -> List[dict]:
    """Удобная функция получения уведомлений для пользователя."""
    return _notify_observer.get_notifications(user_email)
