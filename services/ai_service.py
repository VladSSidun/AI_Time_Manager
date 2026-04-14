import json
import anthropic
from sqlalchemy.orm import Session
from services.stats_service import calculate_stats
from repositories import ai_analysis_repo
from core.config import settings
from models.ai_analysis import AIAnalysis


def get_recommendations(db: Session, user_id: int) -> AIAnalysis:
    stats = calculate_stats(db, user_id)

    prompt = f"""Ти — персональний коуч з тайм-менеджменту.
Ось статистика користувача за останні 30 днів:

- Всього робочих сесій: {stats['total_sessions']}
- Загальний час роботи: {stats['total_hours']} год
- Середня тривалість сесії: {stats['avg_session_min']} хв
- Активність вранці (6-12): {stats['morning_pct']}%
- Активність вдень (12-18): {stats['afternoon_pct']}%
- Активність ввечері (18-24): {stats['evening_pct']}%
- Найпродуктивніший день тижня: {stats['best_day']}
- Відсоток виконаних задач: {stats['completion_rate']}%
- Відсоток прострочених задач: {stats['overdue_pct']}%
- Найактивніша категорія: {stats['top_category']}
- Індекс продуктивності: {stats['productivity_score']}/100
- Pomodoro-сесій: {stats['pomodoro_sessions']}

Проаналізуй дані та відповідай ЛИШЕ валідним JSON (без markdown, без ```):
{{
  "summary": "короткий підсумок продуктивності (2-3 речення, українською)",
  "productivity_score": число від 1 до 10,
  "recommendations": ["порада 1", "порада 2", "порада 3", "порада 4"],
  "patterns": ["патерн 1", "патерн 2", "патерн 3"]
}}

Дай 4-5 конкретних, персоналізованих порад. Визнач 2-4 патерни поведінки.
Говори лаконічно, по ділу, українською мовою."""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = message.content[0].text

    recommendation_text = _parse_ai_response(raw_text)

    return ai_analysis_repo.save(
        db,
        user_id=user_id,
        stats_snapshot=json.dumps(stats, ensure_ascii=False),
        recommendation=recommendation_text,
    )


def _parse_ai_response(raw: str) -> str:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "summary" in parsed:
            return json.dumps(parsed, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass

    return json.dumps({
        "summary": raw[:300],
        "productivity_score": 5,
        "recommendations": [line.strip() for line in raw.split('\n') if line.strip() and len(line.strip()) > 10][:5],
        "patterns": [],
    }, ensure_ascii=False)


def get_history(db: Session, user_id: int) -> list[AIAnalysis]:
    return ai_analysis_repo.get_history(db, user_id)
