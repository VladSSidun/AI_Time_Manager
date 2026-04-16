import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from schemas.ai_analysis import AIAnalysisOut
from services import ai_service, stats_service
from core.dependencies import get_db, get_current_user
from models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/stats")
def get_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return stats_service.calculate_stats(db, current_user.id, days=days)


@router.post("/ai-analysis", response_model=AIAnalysisOut)
def run_ai_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Виклик лише за явним запитом користувача (дорогий зовнішній API)
    return ai_service.get_recommendations(db, current_user.id)


@router.get("/ai-analysis", response_model=list[AIAnalysisOut])
def get_ai_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ai_service.get_history(db, current_user.id)


@router.get("/export")
def export_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Власна пропозиція: експорт статистики у JSON для зовнішнього аналізу
    stats = stats_service.calculate_stats(db, current_user.id, days=days)
    formatted = json.dumps(stats, ensure_ascii=False, indent=2)
    return Response(
        content=formatted,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=stats_export.json"},
    )
