"""
Job description upload, extraction, and resume-JD matching routes.
"""
import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_optional
from app.db.session import get_db
from app.models.job_description import JDRequirementModel, JobDescriptionModel, ResumeJDMatchModel
from app.services.jd_extractor import JDExtractor, MatchingService
from app.services.llm_provider import LLMProviderError, get_llm_provider
from app.services.resume_parser import ResumeParser, ResumeParserError

router = APIRouter(prefix="/job-descriptions", tags=["Job Description Intelligence"])


class JDCreateRequest(BaseModel):
    title: str = "Job Description"
    company: str | None = None
    content_text: str


@router.post("", status_code=201)
def create_jd_from_text(
    req: JDCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Create a job description from pasted text and trigger AI extraction."""
    if len(req.content_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description text is too short.")

    jd_id = str(uuid.uuid4())
    jd = JobDescriptionModel(
        id=jd_id,
        user_id=current_user.id if current_user else None,
        title=req.title,
        company=req.company,
        content_text=req.content_text,
        status="processing",
    )
    db.add(jd)
    db.commit()

    # Run AI extraction
    try:
        llm = get_llm_provider(task_type="jd_extraction")
        extractor = JDExtractor(llm)
        extracted = extractor.extract(req.content_text)

        jd.title = extracted.get("job_title") or req.title
        jd.company = extracted.get("company") or req.company
        jd.experience_min_years = extracted.get("experience_min_years")
        jd.experience_max_years = extracted.get("experience_max_years")
        jd.education_requirement = extracted.get("education_requirement")
        jd.required_skills_json = json.dumps(extracted.get("required_skills", []))
        jd.preferred_skills_json = json.dumps(extracted.get("preferred_skills", []))
        jd.responsibilities_json = json.dumps(extracted.get("responsibilities", []))
        jd.domain_knowledge_json = json.dumps(extracted.get("domain_knowledge", []))
        jd.soft_skills_json = json.dumps(extracted.get("soft_skills", []))
        jd.status = "extracted"

        # Store individual requirements
        for req_item in extracted.get("requirements_list", [])[:50]:
            if isinstance(req_item, dict) and req_item.get("text"):
                db.add(JDRequirementModel(
                    jd_id=jd_id,
                    requirement_text=req_item["text"][:500],
                    category=req_item.get("category", "technical"),
                    is_required=bool(req_item.get("is_required", True)),
                ))

        db.commit()

    except LLMProviderError as e:
        jd.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        jd.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"JD extraction failed: {str(e)[:200]}")

    db.refresh(jd)
    return _jd_response(jd, db)


@router.get("", status_code=200)
def list_jds(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """List all job descriptions."""
    query = db.query(JobDescriptionModel)
    if current_user:
        query = query.filter(JobDescriptionModel.user_id == current_user.id)
    jds = query.order_by(JobDescriptionModel.created_at.desc()).all()
    return [_jd_summary(j) for j in jds]


@router.get("/{jd_id}", status_code=200)
def get_jd(jd_id: str, db: Session = Depends(get_db)):
    """Get job description details."""
    jd = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found.")
    return _jd_response(jd, db)


@router.get("/{jd_id}/analysis", status_code=200)
def get_jd_analysis(jd_id: str, db: Session = Depends(get_db)):
    """Get extracted requirements for a JD."""
    jd = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found.")

    requirements = db.query(JDRequirementModel).filter(
        JDRequirementModel.jd_id == jd_id
    ).all()

    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    return {
        "jd_id": jd_id,
        "title": jd.title,
        "company": jd.company,
        "status": jd.status,
        "experience_range": f"{jd.experience_min_years or 0}-{jd.experience_max_years or 'any'} years",
        "education_requirement": jd.education_requirement,
        "required_skills": safe_json(jd.required_skills_json),
        "preferred_skills": safe_json(jd.preferred_skills_json),
        "responsibilities": safe_json(jd.responsibilities_json),
        "domain_knowledge": safe_json(jd.domain_knowledge_json),
        "soft_skills": safe_json(jd.soft_skills_json),
        "requirements": [
            {
                "text": r.requirement_text,
                "category": r.category,
                "is_required": r.is_required,
            }
            for r in requirements
        ],
    }


def _jd_summary(jd: JobDescriptionModel) -> dict:
    return {
        "id": jd.id,
        "title": jd.title,
        "company": jd.company,
        "status": jd.status,
        "created_at": jd.created_at.isoformat(),
    }


def _jd_response(jd: JobDescriptionModel, db: Session) -> dict:
    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    return {
        "id": jd.id,
        "title": jd.title,
        "company": jd.company,
        "status": jd.status,
        "content_preview": jd.content_text[:500] + "..." if len(jd.content_text) > 500 else jd.content_text,
        "experience_min_years": jd.experience_min_years,
        "experience_max_years": jd.experience_max_years,
        "education_requirement": jd.education_requirement,
        "required_skills": safe_json(jd.required_skills_json),
        "preferred_skills": safe_json(jd.preferred_skills_json),
        "responsibilities": safe_json(jd.responsibilities_json),
        "created_at": jd.created_at.isoformat(),
    }
