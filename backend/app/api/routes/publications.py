from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.publication import (
    PublicationCreate,
    PublicationResponse,
    PublicationUpdate,
    StudentAssessmentView,
    StudentAttemptResultResponse,
    StudentAttemptStartRequest,
    StudentAttemptStartResponse,
    StudentAttemptSubmitRequest,
)
from app.services.publication_service import PublicationService, PublicationServiceError

router = APIRouter(tags=["Quiz Publishing & Assessments"])


# --- Instructor Publishing Endpoints ---


@router.post("/publications", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED)
def create_publication(req: PublicationCreate, db: Session = Depends(get_db)):
    """Publishes an approved quiz to an instructional Batch or as a standalone shareable link."""
    try:
        pub = PublicationService.create_publication(db, req)
        return PublicationService.get_publication_response(db, pub.id)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/publications/{publication_id}", response_model=PublicationResponse)
def get_publication(publication_id: str, db: Session = Depends(get_db)):
    """Instructor view of publication details, submission metrics, and access link."""
    try:
        return PublicationService.get_publication_response(db, publication_id)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/publications/{publication_id}", response_model=PublicationResponse)
def update_publication(publication_id: str, req: PublicationUpdate, db: Session = Depends(get_db)):
    """Updates publication settings such as status (active/closed), time limit, or instructions."""
    try:
        return PublicationService.update_publication(db, publication_id, req)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Secure Student Assessment Endpoints (Zero Answer Leakage) ---


@router.get("/public/assessment/{access_code}", response_model=StudentAssessmentView)
def get_student_assessment(access_code: str, db: Session = Depends(get_db)):
    """
    Returns the student view of a published quiz.
    Answer keys, evidence, and explanations are strictly excluded.
    """
    try:
        return PublicationService.get_student_assessment_view(db, access_code)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/public/assessment/{access_code}/start", response_model=StudentAttemptStartResponse)
def start_assessment_attempt(
    access_code: str,
    req: StudentAttemptStartRequest,
    db: Session = Depends(get_db),
):
    """
    Enrolls a learner into an attempt and initializes server-authoritative timer tracking.
    Validates batch membership if the assessment is published to a Batch.
    """
    try:
        return PublicationService.start_student_attempt(db, access_code, req)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/public/assessment/{access_code}/submit", response_model=StudentAttemptResultResponse)
def submit_assessment_attempt(
    access_code: str,
    req: StudentAttemptSubmitRequest,
    db: Session = Depends(get_db),
):
    """
    Grades submitted answers server-side against authoritative answer keys.
    Enforces server-authoritative timer deadlines and prevents score fabrication.
    """
    try:
        return PublicationService.submit_student_attempt(db, access_code, req)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/public/assessment/results/{attempt_id}", response_model=StudentAttemptResultResponse)
def get_assessment_result(attempt_id: str, db: Session = Depends(get_db)):
    """Retrieves finalized score and explanations for a completed learner attempt."""
    try:
        return PublicationService.get_student_attempt_result(db, attempt_id)
    except PublicationServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
