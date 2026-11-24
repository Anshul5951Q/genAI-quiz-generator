from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.batch import (
    BatchCreate,
    BatchDetailResponse,
    BatchJoinRequest,
    BatchMemberCreate,
    BatchMemberResponse,
    BatchSummaryResponse,
    BatchUpdate,
)
from app.services.batch_service import BatchService, BatchServiceError

router = APIRouter(prefix="/batches", tags=["Batch Management"])


@router.post("", response_model=BatchDetailResponse, status_code=status.HTTP_201_CREATED)
def create_batch(req: BatchCreate, db: Session = Depends(get_db)):
    """Creates a new instructional Batch with a unique join code."""
    try:
        batch = BatchService.create_batch(db, req)
        return BatchService.get_batch_detail(db, batch.id)
    except BatchServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[BatchSummaryResponse])
def list_batches(
    include_archived: bool = Query(False, description="Include archived batches in results"),
    db: Session = Depends(get_db),
):
    """Lists all Batches with member counts and active assessments."""
    return BatchService.list_batches(db, include_archived=include_archived)


@router.get("/{batch_id}", response_model=BatchDetailResponse)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    """Retrieves full Batch details including enrolled learners and assigned publications."""
    try:
        return BatchService.get_batch_detail(db, batch_id)
    except BatchServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{batch_id}", response_model=BatchDetailResponse)
def update_batch(batch_id: str, req: BatchUpdate, db: Session = Depends(get_db)):
    """Updates Batch name, description, or archives/restores the Batch."""
    try:
        BatchService.update_batch(db, batch_id, req)
        return BatchService.get_batch_detail(db, batch_id)
    except BatchServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{batch_id}/members", response_model=BatchMemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(batch_id: str, req: BatchMemberCreate, db: Session = Depends(get_db)):
    """Adds a learner to a Batch."""
    try:
        member = BatchService.add_member(db, batch_id, req)
        return BatchMemberResponse.model_validate(member)
    except BatchServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{batch_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(batch_id: str, member_id: str, db: Session = Depends(get_db)):
    """Removes a learner from a Batch."""
    try:
        BatchService.remove_member(db, batch_id, member_id)
        return None
    except BatchServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/join", response_model=BatchMemberResponse)
def join_batch(req: BatchJoinRequest, db: Session = Depends(get_db)):
    """Learner self-enrolls into a Batch using an alphanumeric join code."""
    try:
        member = BatchService.join_batch_by_code(
            db=db,
            join_code=req.join_code,
            name=req.learner_name,
            email=req.learner_email,
            learner_id=req.learner_id,
        )
        return BatchMemberResponse.model_validate(member)
    except BatchServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
