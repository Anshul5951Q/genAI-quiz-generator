"""
Interview configuration, generation, and management routes.
"""
import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_optional
from app.db.session import get_db
from app.models.interview import InterviewModel, InterviewQuestionModel, InterviewRoundModel
from app.models.job_description import JobDescriptionModel
from app.models.resume import ResumeExtractionModel, ResumeModel, ResumeProjectModel, ResumeSkillModel
from app.services.interview_question_generator import InterviewQuestionGenerator
from app.services.jd_extractor import JDExtractor
from app.services.llm_provider import LLMProviderError, get_llm_provider

router = APIRouter(prefix="/interviews", tags=["Interview Management"])

VALID_CATEGORIES = {
    "technical", "hr", "managerial", "behavioural", "coding",
    "aptitude", "project-based", "mixed"
}
VALID_EXPERIENCE_LEVELS = {"fresher", "0-2", "2-5", "5+"}
VALID_DIFFICULTIES = {"easy", "medium", "hard", "adaptive"}


class InterviewCreateRequest(BaseModel):
    name: str
    job_role: str = "Software Engineer"
    experience_level: str = "fresher"
    categories: list[str] = ["technical"]
    difficulty: str = "medium"
    num_questions: int = 10
    duration_minutes: int | None = None
    num_rounds: int = 1
    difficulty_distribution: dict | None = None  # {"easy": 30, "medium": 40, "hard": 30}
    resume_id: str | None = None
    jd_id: str | None = None
    custom_instructions: str | None = None

    @field_validator("num_questions")
    @classmethod
    def validate_num_questions(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError("Number of questions must be between 1 and 50.")
        return v

    @field_validator("difficulty_distribution")
    @classmethod
    def validate_distribution(cls, v: dict | None) -> dict | None:
        if v is None:
            return v
        total = sum(v.values())
        if abs(total - 100) > 1:
            raise ValueError(f"Difficulty distribution must total 100%. Got {total}%.")
        return v


def _run_question_generation(interview_id: str, database_url: str) -> None:
    """
    Background task: generate interview questions.
    Runs outside the request lifecycle.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
        if not interview:
            return

        interview.status = "generating"
        interview.generation_progress = 5
        db.commit()

        # Load resume data
        candidate_highlights = {}
        if interview.resume_id:
            extraction = db.query(ResumeExtractionModel).filter(
                ResumeExtractionModel.resume_id == interview.resume_id
            ).first()
            if extraction:
                def safe_json(v):
                    if not v:
                        return []
                    try:
                        return json.loads(v)
                    except Exception:
                        return []

                projects = db.query(ResumeProjectModel).filter(
                    ResumeProjectModel.resume_id == interview.resume_id
                ).all()

                candidate_highlights = {
                    "technical_skills": safe_json(extraction.programming_languages_json) + safe_json(extraction.frameworks_json),
                    "programming_languages": safe_json(extraction.programming_languages_json),
                    "frameworks": safe_json(extraction.frameworks_json),
                    "databases": safe_json(extraction.databases_json),
                    "tools": safe_json(extraction.tools_json),
                    "experience": safe_json(extraction.experience_json),
                    "projects": [
                        {
                            "title": p.title,
                            "technologies": safe_json(p.technologies_json),
                            "description": p.description,
                            "concepts": safe_json(p.concepts_json),
                        }
                        for p in projects
                    ],
                }

        # Load JD data
        job_requirements = {}
        if interview.jd_id:
            jd = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == interview.jd_id).first()
            if jd:
                def safe_json(v):
                    if not v:
                        return []
                    try:
                        return json.loads(v)
                    except Exception:
                        return []
                job_requirements = {
                    "required_skills": safe_json(jd.required_skills_json),
                    "preferred_skills": safe_json(jd.preferred_skills_json),
                    "technical_requirements": [],
                    "domain_knowledge": safe_json(jd.domain_knowledge_json),
                }

        categories = json.loads(interview.categories_json) if interview.categories_json else ["technical"]
        difficulty_dist = json.loads(interview.difficulty_distribution_json) if interview.difficulty_distribution_json else None

        # Build rounds
        rounds = db.query(InterviewRoundModel).filter(
            InterviewRoundModel.interview_id == interview_id
        ).order_by(InterviewRoundModel.round_number).all()

        llm = get_llm_provider(task_type="question_generation")
        generator = InterviewQuestionGenerator(llm)

        total_target = interview.num_questions
        cat_count = len(categories)
        all_generated_questions = []
        total_progress_per_category = 85 // max(1, cat_count)

        for cat_idx, category in enumerate(categories):
            # Allocate target count for this specific category
            cat_quota = (total_target // cat_count) + (1 if cat_idx < (total_target % cat_count) else 0)
            if cat_quota <= 0:
                continue

            # Determine difficulty distribution for this category
            if difficulty_dist:
                easy_count = round(cat_quota * difficulty_dist.get("easy", 33) / 100)
                medium_count = round(cat_quota * difficulty_dist.get("medium", 34) / 100)
                hard_count = cat_quota - easy_count - medium_count
                difficulties = (["easy"] * easy_count + ["medium"] * medium_count + ["hard"] * hard_count)
            elif interview.difficulty == "adaptive":
                # Adaptive difficulty starts foundational and scales to hard
                easy_count = cat_quota // 3
                hard_count = cat_quota // 3
                medium_count = cat_quota - easy_count - hard_count
                difficulties = (["easy"] * easy_count + ["medium"] * medium_count + ["hard"] * hard_count)
            else:
                difficulties = [interview.difficulty] * cat_quota

            cat_questions = []
            diff_counts = {}
            for d in difficulties:
                diff_counts[d] = diff_counts.get(d, 0) + 1

            for diff, count in diff_counts.items():
                if count <= 0:
                    continue
                try:
                    batch = generator.generate_questions_for_round(
                        job_role=interview.job_role or "Software Engineer",
                        experience_level=interview.experience_level,
                        category=category,
                        difficulty=diff,
                        num_questions=count,
                        candidate_highlights=candidate_highlights,
                        job_requirements=job_requirements,
                        existing_questions=all_generated_questions + cat_questions,
                        batch_size=5,
                    )
                    cat_questions.extend(batch)
                except Exception as e:
                    import logging
                    logging.getLogger("studyset").error(f"Question generation failed for {category}/{diff}: {e}")

            all_generated_questions.extend(cat_questions)
            interview.generation_progress = 10 + (cat_idx + 1) * total_progress_per_category
            db.commit()

        # Guarantee exact total question target
        if len(all_generated_questions) < total_target:
            shortfall = total_target - len(all_generated_questions)
            extra = generator.generate_questions_for_round(
                job_role=interview.job_role or "Software Engineer",
                experience_level=interview.experience_level,
                category=categories[0] if categories else "technical",
                difficulty="medium",
                num_questions=shortfall,
                candidate_highlights=candidate_highlights,
                job_requirements=job_requirements,
                existing_questions=all_generated_questions,
                batch_size=5,
            )
            all_generated_questions.extend(extra)

        # Save questions to DB
        round_id = rounds[0].id if rounds else None
        for idx, q in enumerate(all_generated_questions):
            if isinstance(q, dict) and q.get("question_text"):
                db.add(InterviewQuestionModel(
                    id=q.get("id", str(uuid.uuid4())),
                    interview_id=interview_id,
                    round_id=round_id,
                    question_text=q["question_text"],
                    category=q.get("category", "technical"),
                    difficulty=q.get("difficulty", "medium"),
                    related_skill=q.get("related_skill"),
                    source_type=q.get("source_type", "general_technical"),
                    source_evidence=q.get("source_evidence"),
                    expected_concepts_json=json.dumps(q.get("expected_concepts", [])),
                    rubric_json=json.dumps(q.get("rubric", {})),
                    max_score=q.get("max_score", 10),
                    suggested_time_seconds=q.get("suggested_time_seconds", 120),
                    is_follow_up_eligible=1,
                    order_index=idx,
                ))

        interview.status = "ready"
        interview.generation_progress = 100
        db.commit()

    except Exception as e:
        import logging
        logging.getLogger("studyset").error(f"Background question generation failed: {e}")
        interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
        if interview:
            interview.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("", status_code=201)
def create_interview(
    req: InterviewCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Create an interview configuration and start question generation."""
    interview_id = str(uuid.uuid4())

    interview = InterviewModel(
        id=interview_id,
        user_id=current_user.id if current_user else None,
        resume_id=req.resume_id,
        jd_id=req.jd_id,
        name=req.name,
        job_role=req.job_role,
        experience_level=req.experience_level,
        categories_json=json.dumps(req.categories),
        difficulty=req.difficulty,
        num_questions=req.num_questions,
        duration_minutes=req.duration_minutes,
        num_rounds=req.num_rounds,
        difficulty_distribution_json=json.dumps(req.difficulty_distribution) if req.difficulty_distribution else None,
        custom_instructions=req.custom_instructions,
        status="draft",
        generation_progress=0,
    )
    db.add(interview)

    # Create rounds
    round_names = {
        1: "Fundamentals", 2: "Technical Deep Dive", 3: "Coding",
        4: "Project Discussion", 5: "HR & Behavioural"
    }
    for i in range(1, req.num_rounds + 1):
        db.add(InterviewRoundModel(
            interview_id=interview_id,
            round_number=i,
            round_name=round_names.get(i, f"Round {i}"),
            round_type="technical" if i <= 3 else "hr",
        ))

    db.commit()

    # Trigger background question generation
    from app.core.config import settings
    background_tasks.add_task(_run_question_generation, interview_id, settings.DATABASE_URL)

    db.refresh(interview)
    return _interview_summary(interview)


@router.get("", status_code=200)
def list_interviews(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """List all interviews for the current user."""
    query = db.query(InterviewModel)
    if current_user:
        query = query.filter(InterviewModel.user_id == current_user.id)
    interviews = query.order_by(InterviewModel.created_at.desc()).all()
    return [_interview_summary(i) for i in interviews]


@router.get("/{interview_id}", status_code=200)
def get_interview(interview_id: str, db: Session = Depends(get_db)):
    """Get interview details including generation status."""
    interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return _interview_detail(interview, db)


@router.post("/{interview_id}/generate", status_code=200)
def trigger_generation(
    interview_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger question generation (e.g., after a failure)."""
    interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    if interview.status == "generating":
        raise HTTPException(status_code=400, detail="Question generation is already in progress.")

    interview.status = "draft"
    interview.generation_progress = 0
    db.commit()

    from app.core.config import settings
    background_tasks.add_task(_run_question_generation, interview_id, settings.DATABASE_URL)
    return {"message": "Question generation started.", "interview_id": interview_id}


@router.get("/{interview_id}/questions", status_code=200)
def get_interview_questions(interview_id: str, db: Session = Depends(get_db)):
    """Get all questions for an interview."""
    interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    questions = db.query(InterviewQuestionModel).filter(
        InterviewQuestionModel.interview_id == interview_id
    ).order_by(InterviewQuestionModel.order_index).all()

    return {
        "interview_id": interview_id,
        "interview_name": interview.name,
        "status": interview.status,
        "generation_progress": interview.generation_progress,
        "total_questions": len(questions),
        "questions": [_question_response(q) for q in questions],
    }


@router.delete("/{interview_id}", status_code=204)
def delete_interview(interview_id: str, db: Session = Depends(get_db)):
    """Delete an interview and all associated questions."""
    interview = db.query(InterviewModel).filter(InterviewModel.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    db.delete(interview)
    db.commit()


def _interview_summary(interview: InterviewModel) -> dict:
    return {
        "id": interview.id,
        "name": interview.name,
        "job_role": interview.job_role,
        "experience_level": interview.experience_level,
        "difficulty": interview.difficulty,
        "num_questions": interview.num_questions,
        "num_rounds": interview.num_rounds,
        "status": interview.status,
        "generation_progress": interview.generation_progress,
        "created_at": interview.created_at.isoformat(),
    }


def _interview_detail(interview: InterviewModel, db: Session) -> dict:
    questions = db.query(InterviewQuestionModel).filter(
        InterviewQuestionModel.interview_id == interview.id
    ).count()

    rounds = db.query(InterviewRoundModel).filter(
        InterviewRoundModel.interview_id == interview.id
    ).order_by(InterviewRoundModel.round_number).all()

    summary = _interview_summary(interview)
    summary.update({
        "resume_id": interview.resume_id,
        "jd_id": interview.jd_id,
        "categories": json.loads(interview.categories_json) if interview.categories_json else [],
        "duration_minutes": interview.duration_minutes,
        "custom_instructions": interview.custom_instructions,
        "questions_generated": questions,
        "rounds": [
            {"id": r.id, "number": r.round_number, "name": r.round_name, "type": r.round_type}
            for r in rounds
        ],
    })
    return summary


def _question_response(q: InterviewQuestionModel) -> dict:
    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    def safe_dict_json(v):
        if not v:
            return {}
        try:
            return json.loads(v)
        except Exception:
            return {}

    return {
        "id": q.id,
        "question_text": q.question_text,
        "category": q.category,
        "difficulty": q.difficulty,
        "related_skill": q.related_skill,
        "source_type": q.source_type,
        "source_evidence": q.source_evidence,
        "expected_concepts": safe_json(q.expected_concepts_json),
        "rubric": safe_dict_json(q.rubric_json),
        "max_score": q.max_score,
        "suggested_time_seconds": q.suggested_time_seconds,
        "order_index": q.order_index,
    }
