from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.session import get_db
from app.schemas.question import QuestionReviewResponse, QuestionUpdate
from app.schemas.quiz import (
    QuizDetailResponse,
    QuizGenerateRequest,
    QuizSummaryResponse,
)
from app.services.llm_provider import LLMProviderError, get_llm_provider
from app.services.question_generator import QuestionGenerator
from app.services.quiz_service import QuizService, QuizServiceError

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/generate", response_model=QuizDetailResponse, status_code=201)
def generate_quiz(request: QuizGenerateRequest, db: Session = Depends(get_db)):
    """Generates MCQs using LLM with deterministic and semantic validation."""
    try:
        quiz, summary = QuizService.generate_quiz(db, request)
        detail = QuizService.get_quiz_detail(db, quiz.id)
        detail.validation_summary = summary
        return detail
    except QuizServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating quiz: {type(e).__name__} - {str(e)[:100]}")
        raise HTTPException(status_code=500, detail="Internal server error while generating quiz.")


@router.get("", response_model=list[QuizSummaryResponse])
def list_quizzes(db: Session = Depends(get_db)):
    """Lists saved quizzes, creation dates, question counts, and latest attempt scores."""
    return QuizService.list_quizzes(db)


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz(quiz_id: str, db: Session = Depends(get_db)):
    """Fetches full quiz details for review or editing."""
    try:
        return QuizService.get_quiz_detail(db, quiz_id)
    except QuizServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{quiz_id}/questions/{question_id}", response_model=QuestionReviewResponse)
def update_question(
    quiz_id: str,
    question_id: str,
    update_data: QuestionUpdate,
    db: Session = Depends(get_db),
):
    """Allows user to edit a question stem, options, correct answer, and explanation."""
    try:
        QuizService.update_question(db, quiz_id, question_id, update_data)
        detail = QuizService.get_quiz_detail(db, quiz_id)
        matching_q = next((q for q in detail.questions if q.id == question_id), None)
        if not matching_q:
            raise HTTPException(status_code=404, detail="Updated question not found.")
        return matching_q
    except QuizServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{quiz_id}/questions/{question_id}", status_code=204)
def delete_question(quiz_id: str, question_id: str, db: Session = Depends(get_db)):
    """Deletes an individual question from the quiz set."""
    try:
        QuizService.delete_question(db, quiz_id, question_id)
    except QuizServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{quiz_id}/questions/{question_id}/regenerate",
    response_model=QuestionReviewResponse,
)
def regenerate_question(
    quiz_id: str,
    question_id: str,
    feedback: str | None = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    """Regenerates a single question with targeted feedback."""
    try:
        quiz = QuizService.get_quiz_by_id(db, quiz_id)
        detail = QuizService.get_quiz_detail(db, quiz_id)
        current_q = next((q for q in detail.questions if q.id == question_id), None)
        if not current_q:
            raise HTTPException(status_code=404, detail="Question not found in quiz.")

        llm = get_llm_provider(force_demo=quiz.is_demo)
        generator = QuestionGenerator(llm)

        # Regenerate with feedback
        source_excerpt = current_q.evidence or quiz.title
        regenerated_data = generator.regenerate_single_question(
            current_question=current_q.model_dump(),
            source_text=source_excerpt,
            user_notes=feedback,
        )

        # Update in database
        update_schema = QuestionUpdate(
            question_text=regenerated_data["question_text"],
            explanation=regenerated_data["explanation"],
            evidence=regenerated_data["evidence"],
            source_page=regenerated_data.get("source_page"),
            topic=regenerated_data.get("topic"),
            difficulty=regenerated_data.get("difficulty"),
            distractor_rationale=regenerated_data.get("distractor_rationale"),
            validation_status=regenerated_data.get("validation_status", "review"),
        )
        QuizService.update_question(db, quiz_id, question_id, update_schema)

        updated_detail = QuizService.get_quiz_detail(db, quiz_id)
        updated_q = next((q for q in updated_detail.questions if q.id == question_id), None)
        return updated_q
    except QuizServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{quiz_id}/approve", response_model=QuizDetailResponse)
def approve_quiz(quiz_id: str, db: Session = Depends(get_db)):
    """Instructor approves a generated/reviewed quiz for publication."""
    try:
        QuizService.approve_quiz(db, quiz_id)
        return QuizService.get_quiz_detail(db, quiz_id)
    except QuizServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{quiz_id}/publish", response_model=QuizDetailResponse)
def publish_quiz(quiz_id: str, db: Session = Depends(get_db)):
    """Publishes a quiz, incrementing its version to seal its current state for attempts."""
    try:
        QuizService.publish_quiz(db, quiz_id)
        return QuizService.get_quiz_detail(db, quiz_id)
    except QuizServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{quiz_id}", status_code=204)
def delete_quiz(quiz_id: str, db: Session = Depends(get_db)):
    """Deletes an entire quiz with all its questions and attempt history."""
    try:
        QuizService.delete_quiz(db, quiz_id)
    except QuizServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
