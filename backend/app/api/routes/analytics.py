
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import FullBatchAnalyticsResponse
from app.services.analytics_service import AnalyticsService, AnalyticsServiceError
from app.services.question_bank_service import QuestionBankService
from app.services.version_service import VersionService, VersionServiceError

router = APIRouter(tags=["Analytics, Question Bank & Versions"])


class QuestionReuseCheckRequest(BaseModel):
    candidate_stems: list[str]
    window_days: int = 180


@router.get("/publications/{publication_id}/analytics", response_model=FullBatchAnalyticsResponse)
def get_publication_analytics(publication_id: str, db: Session = Depends(get_db)):
    """Retrieves full assessment performance analytics, score distribution, and question statistics."""
    try:
        return AnalyticsService.get_publication_analytics(db, publication_id)
    except AnalyticsServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quizzes/{quiz_id}/versions")
def generate_parallel_versions(
    quiz_id: str,
    db: Session = Depends(get_db),
):
    """
    Generates parallel exam versions (A, B, C) with randomized question and option orders
    while strictly preserving answer-key and scoring equivalence.
    """
    try:
        return VersionService.generate_parallel_versions(db, quiz_id, ["A", "B", "C"])
    except VersionServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/reuse-check")
def check_question_reuse(
    batch_id: str,
    req: QuestionReuseCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Checks whether candidate questions have already been assigned to this Batch in recent assessments,
    preventing unintended question repetition.
    """
    return QuestionBankService.check_reuse_for_batch(
        db=db,
        batch_id=batch_id,
        candidate_stems=req.candidate_stems,
        window_days=req.window_days,
    )


@router.get("/question-bank")
def search_question_bank(
    topic: str | None = Query(None),
    difficulty: str | None = Query(None),
    keyword: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Searches vetted, reusable questions from past approved quizzes."""
    return QuestionBankService.search_question_bank(
        db=db,
        topic=topic,
        difficulty=difficulty,
        keyword=keyword,
        limit=limit,
    )


@router.post("/quizzes/{quiz_id}/sync-question-bank")
def sync_quiz_to_question_bank(quiz_id: str, db: Session = Depends(get_db)):
    """Syncs approved quiz questions to the global Question Bank."""
    count = QuestionBankService.sync_quiz_to_question_bank(db, quiz_id)
    return {"synced_count": count, "message": f"Successfully indexed {count} questions to Question Bank."}
