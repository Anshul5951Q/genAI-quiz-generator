"""
Resume-JD matching API route.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job_description import JobDescriptionModel, ResumeJDMatchModel
from app.models.resume import ResumeExtractionModel, ResumeModel
from app.services.jd_extractor import MatchingService
from app.services.llm_provider import LLMProviderError, get_llm_provider

router = APIRouter(prefix="/matching", tags=["Resume-JD Matching"])


class MatchRequest(BaseModel):
    resume_id: str
    jd_id: str


@router.post("/analyze", status_code=201)
def analyze_match(req: MatchRequest, db: Session = Depends(get_db)):
    """Generate or retrieve a resume-JD compatibility analysis."""
    # Check if match already exists (use cached result)
    existing = db.query(ResumeJDMatchModel).filter(
        ResumeJDMatchModel.resume_id == req.resume_id,
        ResumeJDMatchModel.jd_id == req.jd_id,
    ).first()

    if existing:
        return _match_response(existing)

    # Load resume extraction
    resume = db.query(ResumeModel).filter(ResumeModel.id == req.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    extraction = db.query(ResumeExtractionModel).filter(
        ResumeExtractionModel.resume_id == req.resume_id
    ).first()
    if not extraction:
        raise HTTPException(status_code=404, detail="Resume extraction not found. Upload and process the resume first.")

    # Load JD
    jd = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == req.jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found.")

    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    resume_data = {
        "candidate_name": extraction.candidate_name,
        "technical_skills": safe_json(extraction.programming_languages_json) + safe_json(extraction.frameworks_json),
        "programming_languages": safe_json(extraction.programming_languages_json),
        "frameworks": safe_json(extraction.frameworks_json),
        "databases": safe_json(extraction.databases_json),
        "tools": safe_json(extraction.tools_json),
        "experience": safe_json(extraction.experience_json),
        "projects": [],  # Will load from projects table if needed
    }

    jd_data = {
        "required_skills": safe_json(jd.required_skills_json),
        "preferred_skills": safe_json(jd.preferred_skills_json),
        "technical_requirements": [],
        "domain_knowledge": safe_json(jd.domain_knowledge_json),
        "experience_min_years": jd.experience_min_years,
        "experience_max_years": jd.experience_max_years,
    }

    try:
        llm = get_llm_provider(task_type="matching")
        matcher = MatchingService(llm)
        result = matcher.analyze(resume_data, jd_data)
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Store result
    match = ResumeJDMatchModel(
        resume_id=req.resume_id,
        jd_id=req.jd_id,
        compatibility_score=result.get("compatibility_score", 0.0),
        matching_skills_json=json.dumps(result.get("matching_skills", [])),
        missing_skills_json=json.dumps(result.get("missing_skills", [])),
        weak_areas_json=json.dumps(result.get("weak_areas", [])),
        recommendations_json=json.dumps(result.get("recommendations", [])),
        interview_focus_json=json.dumps(result.get("interview_focus", [])),
        full_analysis_json=json.dumps(result),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return _match_response(match)


@router.get("/{match_id}", status_code=200)
def get_match(match_id: str, db: Session = Depends(get_db)):
    """Get a specific match result."""
    match = db.query(ResumeJDMatchModel).filter(ResumeJDMatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match result not found.")
    return _match_response(match)


def _match_response(match: ResumeJDMatchModel) -> dict:
    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    full = safe_json(match.full_analysis_json) if match.full_analysis_json else {}

    return {
        "id": match.id,
        "resume_id": match.resume_id,
        "jd_id": match.jd_id,
        "compatibility_score": match.compatibility_score,
        "matching_skills": safe_json(match.matching_skills_json),
        "missing_skills": safe_json(match.missing_skills_json),
        "weak_areas": safe_json(match.weak_areas_json),
        "recommendations": safe_json(match.recommendations_json),
        "interview_focus": safe_json(match.interview_focus_json),
        "strengths": full.get("strengths", []) if isinstance(full, dict) else [],
        "partial_matches": full.get("partial_matches", []) if isinstance(full, dict) else [],
        "created_at": match.created_at.isoformat(),
    }
