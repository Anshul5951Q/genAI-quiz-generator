"""
Interview session lifecycle: start, answer, evaluate, complete.
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_optional
from app.db.session import get_db
from app.models.interview import InterviewModel, InterviewQuestionModel
from app.models.interview_session import AnswerEvaluationModel, InterviewResponseModel, InterviewSessionModel
from app.services.evaluation_service import AnswerEvaluationService
from app.services.interview_question_generator import InterviewQuestionGenerator
from app.services.llm_provider import LLMProviderError, get_llm_provider

router = APIRouter(prefix="/interview-sessions", tags=["Interview Sessions"])


class StartSessionRequest(BaseModel):
    interview_id: str


class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer_text: str | None = None
    code_answer: str | None = None
    time_taken_seconds: int = 0
    is_skipped: bool = False


class SubmitSessionRequest(BaseModel):
    pass  # All answers submitted individually; this finalizes the session


@router.post("", status_code=201)
def start_session(
    req: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Start a new interview session."""
    interview = db.query(InterviewModel).filter(InterviewModel.id == req.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    if interview.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Interview is not ready. Current status: {interview.status}. "
                   "Please wait for question generation to complete."
        )

    # Count total questions
    questions = db.query(InterviewQuestionModel).filter(
        InterviewQuestionModel.interview_id == req.interview_id
    ).order_by(InterviewQuestionModel.order_index).all()

    if not questions:
        raise HTTPException(status_code=400, detail="No questions available for this interview.")

    max_score = sum(q.max_score for q in questions)

    session = InterviewSessionModel(
        interview_id=req.interview_id,
        user_id=current_user.id if current_user else None,
        status="in_progress",
        current_question_index=0,
        max_possible_score=float(max_score),
        adaptive_state_json=json.dumps({"consecutive_strong": 0, "consecutive_weak": 0}),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "interview_id": req.interview_id,
        "interview_name": interview.name,
        "total_questions": len(questions),
        "max_possible_score": max_score,
        "duration_minutes": interview.duration_minutes,
        "started_at": session.started_at.isoformat(),
        "first_question": _question_for_taking(questions[0]) if questions else None,
    }


@router.get("/{session_id}", status_code=200)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get current session state and next question."""
    session = db.query(InterviewSessionModel).filter(InterviewSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    questions = db.query(InterviewQuestionModel).filter(
        InterviewQuestionModel.interview_id == session.interview_id
    ).order_by(InterviewQuestionModel.order_index).all()

    answered_ids = {r.question_id for r in db.query(InterviewResponseModel).filter(
        InterviewResponseModel.session_id == session_id
    ).all()}

    next_question = None
    for q in questions:
        if q.id not in answered_ids:
            next_question = _question_for_taking(q)
            break

    return {
        "session_id": session_id,
        "status": session.status,
        "current_question_index": session.current_question_index,
        "total_questions": len(questions),
        "answered_count": len(answered_ids),
        "total_score": session.total_score,
        "max_possible_score": session.max_possible_score,
        "score_percentage": session.score_percentage,
        "next_question": next_question,
        "is_complete": session.status == "completed",
    }


@router.post("/{session_id}/responses", status_code=201)
def submit_answer(
    session_id: str,
    req: SubmitAnswerRequest,
    db: Session = Depends(get_db),
):
    """Submit an answer for a question. Triggers AI evaluation asynchronously."""
    session = db.query(InterviewSessionModel).filter(InterviewSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not active.")

    # Check for duplicate answer
    existing = db.query(InterviewResponseModel).filter(
        InterviewResponseModel.session_id == session_id,
        InterviewResponseModel.question_id == req.question_id,
        InterviewResponseModel.is_follow_up == False,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Answer already submitted for this question.")

    # Get question for rubric
    question = db.query(InterviewQuestionModel).filter(
        InterviewQuestionModel.id == req.question_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # Save response
    response = InterviewResponseModel(
        session_id=session_id,
        question_id=req.question_id,
        answer_text=req.answer_text,
        code_answer=req.code_answer,
        time_taken_seconds=req.time_taken_seconds,
        is_skipped=req.is_skipped,
    )
    db.add(response)
    session.current_question_index += 1
    db.commit()
    db.refresh(response)

    # Run AI evaluation immediately (synchronous for now)
    evaluation_result = None
    if not req.is_skipped and (req.answer_text or req.code_answer):
        try:
            llm = get_llm_provider(task_type="answer_evaluation")
            from app.core.config import settings
            evaluator = AnswerEvaluationService(llm)

            def safe_json(v):
                if not v:
                    return []
                try:
                    return json.loads(v)
                except Exception:
                    return []

            eval_data = evaluator.evaluate(
                question_text=question.question_text,
                expected_concepts=safe_json(question.expected_concepts_json),
                rubric=safe_json(question.rubric_json) if question.rubric_json else {},
                candidate_answer=req.answer_text or req.code_answer or "",
                provider_name=settings.LLM_PRIMARY_PROVIDER,
            )

            evaluation = AnswerEvaluationModel(
                response_id=response.id,
                session_id=session_id,
                technical_accuracy_score=eval_data.get("technical_accuracy_score", 0),
                conceptual_understanding_score=eval_data.get("conceptual_understanding_score", 0),
                completeness_score=eval_data.get("completeness_score", 0),
                clarity_score=eval_data.get("clarity_score", 0),
                practical_examples_score=eval_data.get("practical_examples_score", 0),
                final_score=eval_data.get("final_score", 0),
                max_score=eval_data.get("max_score", 10),
                correct_concepts_json=json.dumps(eval_data.get("correct_concepts", [])),
                missing_concepts_json=json.dumps(eval_data.get("missing_concepts", [])),
                incorrect_statements_json=json.dumps(eval_data.get("incorrect_statements", [])),
                strengths_json=json.dumps(eval_data.get("strengths", [])),
                weaknesses_json=json.dumps(eval_data.get("weaknesses", [])),
                suggested_improvement=eval_data.get("suggested_improvement"),
                model_confidence=eval_data.get("model_confidence", 0.7),
                evaluation_provider=eval_data.get("evaluation_provider"),
            )
            db.add(evaluation)

            # Update session total score
            session.total_score += eval_data.get("final_score", 0)
            if session.max_possible_score > 0:
                session.score_percentage = round(
                    (session.total_score / session.max_possible_score) * 100, 1
                )

            db.commit()
            evaluation_result = eval_data

        except LLMProviderError as e:
            # Don't fail the submission if evaluation errors
            import logging
            logging.getLogger("studyset").warning(f"Evaluation failed: {e}")

    # Determine adaptive signal for next question
    adaptive_signal = "partial"
    if evaluation_result:
        adaptive_signal = evaluation_result.get("adaptive_signal", "partial")

    return {
        "response_id": response.id,
        "question_id": req.question_id,
        "is_skipped": req.is_skipped,
        "evaluation": evaluation_result,
        "adaptive_signal": adaptive_signal,
        "session_progress": {
            "answered": session.current_question_index,
            "total_score": session.total_score,
            "score_percentage": session.score_percentage,
        },
    }


@router.post("/{session_id}/submit", status_code=200)
def submit_session(session_id: str, db: Session = Depends(get_db)):
    """Finalize and complete the interview session."""
    from datetime import UTC, datetime
    session = db.query(InterviewSessionModel).filter(InterviewSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status == "completed":
        return {"message": "Session already completed.", "session_id": session_id}

    session.status = "completed"
    session.completed_at = datetime.now(UTC)
    db.commit()

    return {
        "message": "Interview completed successfully.",
        "session_id": session_id,
        "total_score": session.total_score,
        "max_possible_score": session.max_possible_score,
        "score_percentage": session.score_percentage,
    }


@router.get("/{session_id}/report", status_code=200)
def get_session_report(session_id: str, db: Session = Depends(get_db)):
    """Get the full evaluation report for a completed session."""
    session = db.query(InterviewSessionModel).filter(InterviewSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    interview = db.query(InterviewModel).filter(InterviewModel.id == session.interview_id).first()
    responses = db.query(InterviewResponseModel).filter(
        InterviewResponseModel.session_id == session_id
    ).all()

    response_data = []
    for resp in responses:
        question = db.query(InterviewQuestionModel).filter(
            InterviewQuestionModel.id == resp.question_id
        ).first()
        evaluation = db.query(AnswerEvaluationModel).filter(
            AnswerEvaluationModel.response_id == resp.id
        ).first()

        def safe_json(v):
            if not v:
                return []
            try:
                return json.loads(v)
            except Exception:
                return []

        response_data.append({
            "question_id": resp.question_id,
            "question_text": question.question_text if question else "Unknown",
            "category": question.category if question else "unknown",
            "difficulty": question.difficulty if question else "medium",
            "answer_text": resp.answer_text,
            "is_skipped": resp.is_skipped,
            "time_taken_seconds": resp.time_taken_seconds,
            "evaluation": {
                "final_score": evaluation.final_score if evaluation else 0,
                "max_score": evaluation.max_score if evaluation else 10,
                "technical_accuracy": evaluation.technical_accuracy_score if evaluation else 0,
                "conceptual_understanding": evaluation.conceptual_understanding_score if evaluation else 0,
                "completeness": evaluation.completeness_score if evaluation else 0,
                "clarity": evaluation.clarity_score if evaluation else 0,
                "practical_examples": evaluation.practical_examples_score if evaluation else 0,
                "strengths": safe_json(evaluation.strengths_json) if evaluation else [],
                "weaknesses": safe_json(evaluation.weaknesses_json) if evaluation else [],
                "missing_concepts": safe_json(evaluation.missing_concepts_json) if evaluation else [],
                "suggested_improvement": evaluation.suggested_improvement if evaluation else None,
            } if evaluation else None,
        })

    # Build category breakdown
    cat_stats = {}
    for item in response_data:
        cat = item["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "earned": 0, "count": 0}
        if item["evaluation"]:
            cat_stats[cat]["total"] += item["evaluation"]["max_score"]
            cat_stats[cat]["earned"] += item["evaluation"]["final_score"]
            cat_stats[cat]["count"] += 1

    return {
        "session_id": session_id,
        "interview_name": interview.name if interview else "Unknown",
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "total_score": session.total_score,
        "max_possible_score": session.max_possible_score,
        "score_percentage": session.score_percentage,
        "total_questions": len(responses),
        "answered_count": sum(1 for r in responses if not r.is_skipped),
        "skipped_count": sum(1 for r in responses if r.is_skipped),
        "responses": response_data,
        "category_breakdown": [
            {
                "category": cat,
                "questions_answered": stats["count"],
                "score_earned": round(stats["earned"], 2),
                "max_score": stats["total"],
                "percentage": round((stats["earned"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1),
            }
            for cat, stats in cat_stats.items()
        ],
    }


def _question_for_taking(q: InterviewQuestionModel) -> dict:
    """Return question data safe for display during interview (no rubric/answers)."""
    return {
        "id": q.id,
        "question_text": q.question_text,
        "category": q.category,
        "difficulty": q.difficulty,
        "related_skill": q.related_skill,
        "suggested_time_seconds": q.suggested_time_seconds,
        "order_index": q.order_index,
        # NOTE: expected_concepts, rubric, source_evidence NOT exposed during session
    }
