from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attempt import QuizAttemptModel
from app.models.quiz import QuestionModel, QuizModel
from app.schemas.attempt import (
    AttemptCreateResponse,
    AttemptResultResponse,
    AttemptSubmissionRequest,
    ScoreBreakdownItem,
)
from app.schemas.question import OptionReviewResponse, QuestionResultResponse
from app.schemas.quiz import QuizTakingResponse
from app.services.quiz_service import QuizService, QuizServiceError
from app.services.scoring_service import ScoringService, ScoringServiceError

router = APIRouter(tags=["Attempts"])


@router.post("/quizzes/{quiz_id}/attempts", response_model=AttemptCreateResponse, status_code=201)
def start_quiz_attempt(quiz_id: str, db: Session = Depends(get_db)):
    """
    Initializes a new quiz attempt.
    Creates an attempt record tied to the current quiz version.
    """
    quiz = db.query(QuizModel).filter(QuizModel.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    if not quiz.questions:
        raise HTTPException(status_code=400, detail="Cannot attempt an empty quiz.")

    attempt = QuizAttemptModel(
        quiz_id=quiz.id,
        quiz_version=quiz.version,
        status="in_progress",
        total_questions=len(quiz.questions),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return AttemptCreateResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        quiz_version=quiz.version,
        total_questions=len(quiz.questions),
        started_at=attempt.started_at,
    )


@router.get("/quizzes/{quiz_id}/take", response_model=QuizTakingResponse)
def get_quiz_for_taking(quiz_id: str, db: Session = Depends(get_db)):
    """
    Fetches questions strictly sanitized for test-takers.
    NO correct answer keys or explanations are exposed.
    """
    try:
        return QuizService.get_quiz_taking_view(db, quiz_id)
    except QuizServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptResultResponse)
def submit_quiz_attempt(attempt_id: str, submission: AttemptSubmissionRequest, db: Session = Depends(get_db)):
    """
    Submits user answers for scoring.
    Score is calculated deterministically on the backend.
    Only after submission are correct answers and explanations revealed.
    """
    attempt = db.query(QuizAttemptModel).filter(QuizAttemptModel.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found.")

    try:
        return ScoringService.calculate_attempt_results(db, attempt, submission)
    except ScoringServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attempts/{attempt_id}/results", response_model=AttemptResultResponse)
def get_attempt_results(attempt_id: str, db: Session = Depends(get_db)):
    """Fetches previously scored results for a completed attempt."""
    attempt = db.query(QuizAttemptModel).filter(QuizAttemptModel.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found.")
    if attempt.status != "completed":
        raise HTTPException(status_code=400, detail="This attempt has not been submitted yet.")

    quiz = attempt.quiz
    questions = (
        db.query(QuestionModel).filter(QuestionModel.quiz_id == quiz.id).order_by(QuestionModel.order_index).all()
    )

    answers_map = {ans.question_id: ans for ans in attempt.answers}
    detailed_questions: list[QuestionResultResponse] = []
    diff_stats = {}
    topic_stats = {}

    for q in questions:
        ans = answers_map.get(q.id)
        selected_option_id = ans.selected_option_id if ans else None
        is_correct = ans.is_correct if ans else False

        correct_opt = next((o for o in q.options if o.is_correct), None)
        correct_option_id = correct_opt.id if correct_opt else ""

        opt_responses = [
            OptionReviewResponse(
                id=o.id,
                option_letter=o.option_letter,
                option_text=o.option_text,
                is_correct=o.is_correct,
            )
            for o in sorted(q.options, key=lambda x: x.option_letter)
        ]

        detailed_questions.append(
            QuestionResultResponse(
                id=q.id,
                question_text=q.question_text,
                order_index=q.order_index,
                topic=q.topic,
                difficulty=q.difficulty,
                explanation=q.explanation,
                evidence=q.evidence,
                source_page=q.source_page,
                options=opt_responses,
                selected_option_id=selected_option_id,
                correct_option_id=correct_option_id,
                is_correct=is_correct,
            )
        )

        dif = q.difficulty or "medium"
        if dif not in diff_stats:
            diff_stats[dif] = {"total": 0, "correct": 0}
        diff_stats[dif]["total"] += 1
        if is_correct:
            diff_stats[dif]["correct"] += 1

        top = q.topic or "General"
        if top not in topic_stats:
            topic_stats[top] = {"total": 0, "correct": 0}
        topic_stats[top]["total"] += 1
        if is_correct:
            topic_stats[top]["correct"] += 1

    diff_breakdown = [
        ScoreBreakdownItem(
            category=k.capitalize(),
            total=v["total"],
            correct=v["correct"],
            percentage=round((v["correct"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0,
        )
        for k, v in diff_stats.items()
    ]

    topic_breakdown = [
        ScoreBreakdownItem(
            category=k,
            total=v["total"],
            correct=v["correct"],
            percentage=round((v["correct"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0,
        )
        for k, v in topic_stats.items()
    ]

    return AttemptResultResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        score=attempt.score,
        total_questions=attempt.total_questions,
        unanswered_count=attempt.unanswered_count,
        score_percentage=attempt.score_percentage,
        difficulty_breakdown=diff_breakdown,
        topic_breakdown=topic_breakdown,
        questions=detailed_questions,
    )
