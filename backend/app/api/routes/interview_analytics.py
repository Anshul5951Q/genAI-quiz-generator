"""
Interview analytics, performance tracking, and learning roadmap routes.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_optional
from app.db.session import get_db
from app.models.interview import InterviewModel, InterviewQuestionModel
from app.models.interview_session import AnswerEvaluationModel, InterviewResponseModel, InterviewSessionModel
from app.models.learning import LearningRecommendationModel, SkillProfileModel

router = APIRouter(prefix="/interview-analytics", tags=["Interview Analytics"])


@router.get("/dashboard", status_code=200)
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Get overall interview performance analytics dashboard."""
    query = db.query(InterviewSessionModel)
    if current_user:
        query = query.filter(InterviewSessionModel.user_id == current_user.id)

    all_sessions = query.all()
    completed_sessions = [s for s in all_sessions if s.status == "completed"]

    if not completed_sessions:
        return {
            "total_interviews": len(all_sessions),
            "completed_interviews": 0,
            "average_score_percentage": 0.0,
            "best_score_percentage": 0.0,
            "total_questions_answered": 0,
            "category_performance": [],
            "difficulty_performance": [],
            "recent_sessions": [],
        }

    avg_score = sum(s.score_percentage for s in completed_sessions) / len(completed_sessions)
    best_score = max(s.score_percentage for s in completed_sessions)

    # Aggregate category performance
    cat_stats: dict = {}
    diff_stats: dict = {}
    total_answered = 0

    for session in completed_sessions:
        responses = db.query(InterviewResponseModel).filter(
            InterviewResponseModel.session_id == session.id,
            InterviewResponseModel.is_skipped == False,
        ).all()
        total_answered += len(responses)

        for resp in responses:
            question = db.query(InterviewQuestionModel).filter(
                InterviewQuestionModel.id == resp.question_id
            ).first()
            evaluation = db.query(AnswerEvaluationModel).filter(
                AnswerEvaluationModel.response_id == resp.id
            ).first()

            if not question or not evaluation:
                continue

            cat = question.category
            diff = question.difficulty

            if cat not in cat_stats:
                cat_stats[cat] = {"total_score": 0, "max_score": 0, "count": 0}
            cat_stats[cat]["total_score"] += evaluation.final_score
            cat_stats[cat]["max_score"] += evaluation.max_score
            cat_stats[cat]["count"] += 1

            if diff not in diff_stats:
                diff_stats[diff] = {"total_score": 0, "max_score": 0, "count": 0}
            diff_stats[diff]["total_score"] += evaluation.final_score
            diff_stats[diff]["max_score"] += evaluation.max_score
            diff_stats[diff]["count"] += 1

    category_performance = [
        {
            "category": cat,
            "questions": stats["count"],
            "score_earned": round(stats["total_score"], 2),
            "max_score": stats["max_score"],
            "percentage": round((stats["total_score"] / stats["max_score"] * 100) if stats["max_score"] > 0 else 0, 1),
        }
        for cat, stats in sorted(cat_stats.items())
    ]

    difficulty_performance = [
        {
            "difficulty": diff,
            "questions": stats["count"],
            "percentage": round((stats["total_score"] / stats["max_score"] * 100) if stats["max_score"] > 0 else 0, 1),
        }
        for diff, stats in sorted(diff_stats.items())
    ]

    recent_sessions = []
    for session in sorted(completed_sessions, key=lambda s: s.started_at, reverse=True)[:5]:
        interview = db.query(InterviewModel).filter(InterviewModel.id == session.interview_id).first()
        recent_sessions.append({
            "session_id": session.id,
            "interview_name": interview.name if interview else "Unknown",
            "score_percentage": session.score_percentage,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        })

    return {
        "total_interviews": len(all_sessions),
        "completed_interviews": len(completed_sessions),
        "average_score_percentage": round(avg_score, 1),
        "best_score_percentage": round(best_score, 1),
        "total_questions_answered": total_answered,
        "category_performance": category_performance,
        "difficulty_performance": difficulty_performance,
        "recent_sessions": recent_sessions,
    }


@router.get("/skills", status_code=200)
def get_skill_analysis(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Get skill-level performance analysis."""
    if not current_user:
        return {"skills": [], "message": "Login to see your personalized skill analysis."}

    profiles = db.query(SkillProfileModel).filter(
        SkillProfileModel.user_id == current_user.id
    ).order_by(SkillProfileModel.proficiency_score.desc()).all()

    return {
        "skills": [
            {
                "skill": p.skill_name,
                "category": p.skill_category,
                "proficiency_score": p.proficiency_score,
                "attempts": p.attempts_count,
                "last_updated": p.last_updated.isoformat(),
            }
            for p in profiles
        ]
    }


@router.get("/history", status_code=200)
def get_interview_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Get detailed interview history."""
    query = db.query(InterviewSessionModel).filter(
        InterviewSessionModel.status == "completed"
    )
    if current_user:
        query = query.filter(InterviewSessionModel.user_id == current_user.id)

    sessions = query.order_by(InterviewSessionModel.started_at.desc()).all()

    history = []
    for session in sessions:
        interview = db.query(InterviewModel).filter(InterviewModel.id == session.interview_id).first()
        total_responses = db.query(InterviewResponseModel).filter(
            InterviewResponseModel.session_id == session.id
        ).count()
        history.append({
            "session_id": session.id,
            "interview_name": interview.name if interview else "Unknown",
            "job_role": interview.job_role if interview else None,
            "score_percentage": session.score_percentage,
            "total_score": session.total_score,
            "max_score": session.max_possible_score,
            "questions_answered": total_responses,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        })

    return {"sessions": history, "total": len(history)}


@router.get("/learning-roadmap", status_code=200)
def get_learning_roadmap(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Get personalized learning recommendations."""
    if not current_user:
        return {"recommendations": [], "message": "Login to see your personalized learning roadmap."}

    recommendations = db.query(LearningRecommendationModel).filter(
        LearningRecommendationModel.user_id == current_user.id
    ).order_by(
        LearningRecommendationModel.priority,
        LearningRecommendationModel.created_at.desc()
    ).all()

    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    return {
        "recommendations": [
            {
                "id": r.id,
                "topic": r.topic,
                "description": r.description,
                "priority": r.priority,
                "resources": safe_json(r.resources_json),
                "is_completed": r.is_completed,
                "created_at": r.created_at.isoformat(),
            }
            for r in recommendations
        ],
        "total": len(recommendations),
        "pending": sum(1 for r in recommendations if not r.is_completed),
    }


@router.patch("/learning-roadmap/{recommendation_id}/complete", status_code=200)
def mark_recommendation_complete(
    recommendation_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Mark a learning recommendation as completed."""
    rec = db.query(LearningRecommendationModel).filter(
        LearningRecommendationModel.id == recommendation_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    rec.is_completed = True
    db.commit()
    return {"id": recommendation_id, "is_completed": True}
