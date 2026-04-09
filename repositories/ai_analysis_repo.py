from sqlalchemy.orm import Session
from models.ai_analysis import AIAnalysis


def save(
    db: Session,
    user_id: int,
    stats_snapshot: str,
    recommendation: str,
) -> AIAnalysis:
    analysis = AIAnalysis(
        user_id=user_id,
        stats_snapshot=stats_snapshot,
        recommendation=recommendation,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_history(db: Session, user_id: int, limit: int = 10) -> list[AIAnalysis]:
    return (
        db.query(AIAnalysis)
        .filter(AIAnalysis.user_id == user_id)
        .order_by(AIAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )
