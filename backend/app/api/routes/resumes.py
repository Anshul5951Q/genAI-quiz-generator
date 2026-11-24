"""
Resume upload, extraction, and analysis API routes.
"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_optional
from app.db.session import get_db
from app.models.resume import ResumeExtractionModel, ResumeModel, ResumeProjectModel, ResumeSkillModel
from app.services.llm_provider import LLMProviderError, get_llm_provider
from app.services.resume_extractor import ResumeExtractor
from app.services.resume_parser import ResumeParser, ResumeParserError

router = APIRouter(prefix="/resumes", tags=["Resume Intelligence"])


class ResumeResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    candidate_name: str | None
    email: str | None
    phone: str | None
    technical_skills: list[str]
    programming_languages: list[str]
    frameworks: list[str]
    databases: list[str]
    tools: list[str]
    projects: list[dict]
    experience: list[dict]
    education: list[dict]
    certifications: list[str]
    achievements: list[str]
    extraction_confidence: float


@router.post("/upload", status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Upload a PDF or DOCX resume and trigger AI extraction."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    file_bytes = await file.read()
    file_size = len(file_bytes)

    try:
        ext = ResumeParser.validate_resume_file(file.filename, file_size)
    except ResumeParserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    resume_id = str(uuid.uuid4())
    # Save file to disk
    try:
        file_path = ResumeParser.save_resume_file(file_bytes, file.filename, resume_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save resume file: {e}")

    # Create DB record
    resume = ResumeModel(
        id=resume_id,
        user_id=current_user.id if current_user else None,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_type=ext.lstrip("."),
        status="processing",
    )
    db.add(resume)
    db.commit()

    # Extract text
    try:
        resume_text = ResumeParser.parse_resume(file_bytes, file.filename)
    except ResumeParserError as e:
        resume.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=str(e))

    # Run AI extraction
    try:
        llm = get_llm_provider(task_type="resume_extraction")
        extractor = ResumeExtractor(llm)
        extracted = extractor.extract(resume_text)
        confidence = ResumeExtractor.compute_confidence(extracted)

        import json
        # Store extraction
        extraction = ResumeExtractionModel(
            resume_id=resume_id,
            candidate_name=extracted.get("candidate_name"),
            email=extracted.get("email"),
            phone=extracted.get("phone"),
            education_json=json.dumps(extracted.get("education", [])),
            experience_json=json.dumps(extracted.get("experience", [])),
            internships_json=json.dumps(extracted.get("internships", [])),
            certifications_json=json.dumps(extracted.get("certifications", [])),
            achievements_json=json.dumps(extracted.get("achievements", [])),
            programming_languages_json=json.dumps(extracted.get("programming_languages", [])),
            frameworks_json=json.dumps(extracted.get("frameworks", [])),
            databases_json=json.dumps(extracted.get("databases", [])),
            tools_json=json.dumps(extracted.get("tools", [])),
            raw_extraction_json=json.dumps(extracted),
            extraction_confidence=confidence,
        )
        db.add(extraction)

        # Store skills
        all_skills = set(extracted.get("technical_skills", []))
        for skill in all_skills:
            if skill and len(skill.strip()) > 0:
                cat = "programming" if skill in extracted.get("programming_languages", []) else \
                      "framework" if skill in extracted.get("frameworks", []) else \
                      "database" if skill in extracted.get("databases", []) else \
                      "tool" if skill in extracted.get("tools", []) else "technical"
                db.add(ResumeSkillModel(
                    resume_id=resume_id,
                    skill_name=skill.strip(),
                    skill_category=cat,
                ))

        # Store projects
        for idx, proj in enumerate(extracted.get("projects", [])):
            if isinstance(proj, dict) and proj.get("title"):
                db.add(ResumeProjectModel(
                    resume_id=resume_id,
                    title=proj.get("title", "")[:255],
                    description=proj.get("description"),
                    problem_statement=proj.get("problem_statement"),
                    technologies_json=json.dumps(proj.get("technologies", [])),
                    architecture=proj.get("architecture"),
                    candidate_contribution=proj.get("contribution"),
                    key_features_json=json.dumps(proj.get("key_features", [])),
                    achievements=proj.get("achievements"),
                    concepts_json=json.dumps(proj.get("concepts", [])),
                    order_index=idx,
                ))

        resume.status = "extracted"
        db.commit()

    except LLMProviderError as e:
        resume.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        resume.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)[:200]}")

    db.refresh(resume)
    return {
        "id": resume.id,
        "filename": resume.filename,
        "file_type": resume.file_type,
        "file_size": resume.file_size,
        "status": resume.status,
        "created_at": resume.created_at.isoformat(),
        "extraction_confidence": confidence,
        "candidate_name": extracted.get("candidate_name"),
    }


@router.get("", status_code=200)
def list_resumes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """List all uploaded resumes."""
    query = db.query(ResumeModel)
    if current_user:
        query = query.filter(ResumeModel.user_id == current_user.id)
    resumes = query.order_by(ResumeModel.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "file_type": r.file_type,
            "file_size": r.file_size,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in resumes
    ]


@router.get("/{resume_id}", status_code=200)
def get_resume(resume_id: str, db: Session = Depends(get_db)):
    """Get resume metadata."""
    resume = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return {
        "id": resume.id,
        "filename": resume.filename,
        "file_type": resume.file_type,
        "file_size": resume.file_size,
        "status": resume.status,
        "created_at": resume.created_at.isoformat(),
    }


@router.get("/{resume_id}/analysis", status_code=200)
def get_resume_analysis(resume_id: str, db: Session = Depends(get_db)):
    """Get the AI-extracted analysis for a resume."""
    import json
    resume = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    extraction = db.query(ResumeExtractionModel).filter(
        ResumeExtractionModel.resume_id == resume_id
    ).first()
    if not extraction:
        raise HTTPException(status_code=404, detail="Resume extraction not found. The resume may still be processing.")

    projects = db.query(ResumeProjectModel).filter(
        ResumeProjectModel.resume_id == resume_id
    ).order_by(ResumeProjectModel.order_index).all()

    skills = db.query(ResumeSkillModel).filter(
        ResumeSkillModel.resume_id == resume_id
    ).all()

    def safe_json(v):
        if not v:
            return []
        try:
            return json.loads(v)
        except Exception:
            return []

    return {
        "resume_id": resume_id,
        "filename": resume.filename,
        "status": resume.status,
        "candidate_name": extraction.candidate_name,
        "email": extraction.email,
        "phone": extraction.phone,
        "extraction_confidence": extraction.extraction_confidence,
        "technical_skills": [s.skill_name for s in skills if s.skill_category == "technical"],
        "programming_languages": safe_json(extraction.programming_languages_json),
        "frameworks": safe_json(extraction.frameworks_json),
        "databases": safe_json(extraction.databases_json),
        "tools": safe_json(extraction.tools_json),
        "all_skills": [{"name": s.skill_name, "category": s.skill_category} for s in skills],
        "education": safe_json(extraction.education_json),
        "experience": safe_json(extraction.experience_json),
        "internships": safe_json(extraction.internships_json),
        "certifications": safe_json(extraction.certifications_json),
        "achievements": safe_json(extraction.achievements_json),
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "problem_statement": p.problem_statement,
                "technologies": safe_json(p.technologies_json),
                "architecture": p.architecture,
                "contribution": p.candidate_contribution,
                "key_features": safe_json(p.key_features_json),
                "achievements": p.achievements,
                "concepts": safe_json(p.concepts_json),
            }
            for p in projects
        ],
    }


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    """Delete a resume and all associated data."""
    resume = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    # Delete file from disk
    if resume.file_path and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception:
            pass
    db.delete(resume)
    db.commit()
