from sqlalchemy.orm import Session
from repositories import time_log_repo, task_repo

DAY_NAMES = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер",
             4: "П'ятниця", 5: "Субота", 6: "Неділя"}


def calculate_stats(db: Session, user_id: int, days: int = 30) -> dict:
    logs = time_log_repo.get_last_n_days(db, user_id, days)
    tasks = task_repo.get_all(db, user_id)

    if not logs:
        return {
            "total_sessions": 0, "total_hours": 0, "avg_session_min": 0,
            "morning_pct": 0, "afternoon_pct": 0, "evening_pct": 0,
            "best_day": "—", "completion_rate": 0, "overdue_pct": 0,
            "top_category": "—", "productivity_score": 0,
            "pomodoro_sessions": 0,
        }

    total_sessions = len(logs)
    total_seconds = sum(log.duration_seconds or 0 for log in logs)
    total_hours = round(total_seconds / 3600, 1)
    avg_session_min = round((total_seconds / total_sessions) / 60, 1) if total_sessions else 0

    # Розподіл активності за часом доби
    morning = sum(1 for l in logs if 6 <= l.started_at.hour < 12)
    afternoon = sum(1 for l in logs if 12 <= l.started_at.hour < 18)
    evening = sum(1 for l in logs if 18 <= l.started_at.hour < 24)

    morning_pct = round(morning / total_sessions * 100)
    afternoon_pct = round(afternoon / total_sessions * 100)
    evening_pct = round(evening / total_sessions * 100)

    # Найпродуктивніший день тижня
    day_counts: dict[int, int] = {}
    for log in logs:
        day = log.started_at.weekday()
        day_counts[day] = day_counts.get(day, 0) + 1
    best_day_num = max(day_counts, key=day_counts.get)
    best_day = DAY_NAMES[best_day_num]

    # Статистика задач
    completed = [t for t in tasks if t.status == "completed"]
    completion_rate = round(len(completed) / len(tasks) * 100) if tasks else 0

    overdue = [
        t for t in completed
        if t.deadline and t.completed_at and t.completed_at > t.deadline
    ]
    overdue_pct = round(len(overdue) / len(completed) * 100) if completed else 0

    # Топ-категорія за часом
    category_seconds: dict[str, int] = {}
    for log in logs:
        from repositories.task_repo import get_by_id
        task = get_by_id(db, log.task_id)
        if task:
            cat = task.category
            category_seconds[cat] = category_seconds.get(cat, 0) + (log.duration_seconds or 0)
    top_category = max(category_seconds, key=category_seconds.get) if category_seconds else "—"

    # Власна пропозиція: індекс продуктивності (0–100)
    # Формула: 40% completion_rate + 30% регулярності + 30% дедлайнів
    sessions_per_day = total_sessions / days
    regularity_score = min(sessions_per_day / 3 * 100, 100)  # 3 сесії/день = 100%
    deadline_score = 100 - overdue_pct
    productivity_score = round(
        0.4 * completion_rate + 0.3 * regularity_score + 0.3 * deadline_score
    )

    # Власна пропозиція: кількість Pomodoro-сесій
    pomodoro_sessions = sum(1 for l in logs if l.is_pomodoro)

    return {
        "total_sessions": total_sessions,
        "total_hours": total_hours,
        "avg_session_min": avg_session_min,
        "morning_pct": morning_pct,
        "afternoon_pct": afternoon_pct,
        "evening_pct": evening_pct,
        "best_day": best_day,
        "completion_rate": completion_rate,
        "overdue_pct": overdue_pct,
        "top_category": top_category,
        "productivity_score": productivity_score,
        "pomodoro_sessions": pomodoro_sessions,
    }
