import random
import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attempt import QuizAttemptModel
from app.models.batch import BatchMembershipModel, BatchModel
from app.models.publication import PublicationModel
from app.models.quiz import QuizModel
from app.schemas.batch import (
    BatchCreate,
    BatchDetailResponse,
    BatchMemberCreate,
    BatchMemberResponse,
    BatchPublicationBrief,
    BatchSummaryResponse,
    BatchUpdate,
)


class BatchServiceError(Exception):
    """Business logic errors for Batch operations."""


class BatchService:
    @staticmethod
    def _generate_join_code(db: Session, prefix: str = "BCH") -> str:
        """Generates a clean, unambiguous uppercase alphanumeric join code (e.g. BCH-7482)."""
        chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Omits 0, 1, I, O to avoid confusion
        for _ in range(20):
            suffix = "".join(random.choices(chars, k=5))
            code = f"{prefix}-{suffix}"
            exists = db.query(BatchModel).filter(BatchModel.join_code == code).first()
            if not exists:
                return code
        # Fallback to UUID slice if collisions occur
        return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"

    @classmethod
    def create_batch(cls, db: Session, req: BatchCreate) -> BatchModel:
        name = req.name.strip()
        if not name:
            raise BatchServiceError("Batch name cannot be empty.")

        join_code = req.join_code.strip().upper() if req.join_code else cls._generate_join_code(db)

        # Ensure unique join_code
        existing = db.query(BatchModel).filter(BatchModel.join_code == join_code).first()
        if existing:
            raise BatchServiceError(f"A Batch with join code '{join_code}' already exists.")

        batch = BatchModel(
            name=name,
            description=req.description.strip() if req.description else None,
            join_code=join_code,
            is_archived=False,
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch

    @classmethod
    def list_batches(cls, db: Session, include_archived: bool = False) -> list[BatchSummaryResponse]:
        query = db.query(BatchModel)
        if not include_archived:
            query = query.filter(BatchModel.is_archived.is_(False))

        batches = query.order_by(BatchModel.created_at.desc()).all()
        summaries = []

        for b in batches:
            member_count = db.query(func.count(BatchMembershipModel.id)).filter(
                BatchMembershipModel.batch_id == b.id
            ).scalar() or 0

            active_pubs = db.query(func.count(PublicationModel.id)).filter(
                PublicationModel.batch_id == b.id,
                PublicationModel.status == "active",
            ).scalar() or 0

            summaries.append(
                BatchSummaryResponse(
                    id=b.id,
                    name=b.name,
                    description=b.description,
                    join_code=b.join_code,
                    is_archived=b.is_archived,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                    member_count=member_count,
                    active_publications_count=active_pubs,
                )
            )
        return summaries

    @classmethod
    def get_batch_detail(cls, db: Session, batch_id: str) -> BatchDetailResponse:
        batch = db.query(BatchModel).filter(BatchModel.id == batch_id).first()
        if not batch:
            raise BatchServiceError(f"Batch with ID '{batch_id}' not found.")

        members = (
            db.query(BatchMembershipModel)
            .filter(BatchMembershipModel.batch_id == batch_id)
            .order_by(BatchMembershipModel.joined_at.desc())
            .all()
        )

        member_dtos = [
            BatchMemberResponse(
                id=m.id,
                batch_id=m.batch_id,
                learner_name=m.learner_name,
                learner_email=m.learner_email,
                learner_id=m.learner_id,
                joined_at=m.joined_at,
            )
            for m in members
        ]

        publications = (
            db.query(PublicationModel, QuizModel)
            .join(QuizModel, PublicationModel.quiz_id == QuizModel.id)
            .filter(PublicationModel.batch_id == batch_id)
            .order_by(PublicationModel.created_at.desc())
            .all()
        )

        pub_dtos = []
        for pub, quiz in publications:
            sub_count = (
                db.query(func.count(QuizAttemptModel.id))
                .filter(
                    QuizAttemptModel.publication_id == pub.id,
                    QuizAttemptModel.status == "completed",
                )
                .scalar()
                or 0
            )

            avg_score = (
                db.query(func.avg(QuizAttemptModel.score_percentage))
                .filter(
                    QuizAttemptModel.publication_id == pub.id,
                    QuizAttemptModel.status == "completed",
                )
                .scalar()
            )

            pub_dtos.append(
                BatchPublicationBrief(
                    id=pub.id,
                    quiz_id=quiz.id,
                    quiz_title=quiz.title,
                    access_code=pub.access_code,
                    status=pub.status,
                    time_limit_minutes=pub.time_limit_minutes,
                    created_at=pub.created_at,
                    submissions_count=sub_count,
                    average_score_percentage=round(avg_score, 1) if avg_score is not None else None,
                )
            )

        return BatchDetailResponse(
            id=batch.id,
            name=batch.name,
            description=batch.description,
            join_code=batch.join_code,
            is_archived=batch.is_archived,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            member_count=len(member_dtos),
            members=member_dtos,
            publications=pub_dtos,
        )

    @classmethod
    def update_batch(cls, db: Session, batch_id: str, req: BatchUpdate) -> BatchModel:
        batch = db.query(BatchModel).filter(BatchModel.id == batch_id).first()
        if not batch:
            raise BatchServiceError(f"Batch with ID '{batch_id}' not found.")

        if req.name is not None:
            clean_name = req.name.strip()
            if not clean_name:
                raise BatchServiceError("Batch name cannot be blank.")
            batch.name = clean_name

        if req.description is not None:
            batch.description = req.description.strip() or None

        if req.is_archived is not None:
            batch.is_archived = req.is_archived

        batch.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(batch)
        return batch

    @classmethod
    def add_member(cls, db: Session, batch_id: str, req: BatchMemberCreate) -> BatchMembershipModel:
        batch = db.query(BatchModel).filter(BatchModel.id == batch_id).first()
        if not batch:
            raise BatchServiceError(f"Batch with ID '{batch_id}' not found.")
        if batch.is_archived:
            raise BatchServiceError("Cannot add members to an archived Batch.")

        email_clean = req.learner_email.strip().lower()
        existing = (
            db.query(BatchMembershipModel)
            .filter(
                BatchMembershipModel.batch_id == batch_id,
                func.lower(BatchMembershipModel.learner_email) == email_clean,
            )
            .first()
        )
        if existing:
            raise BatchServiceError(f"Learner with email '{email_clean}' is already enrolled in this Batch.")

        member = BatchMembershipModel(
            batch_id=batch_id,
            learner_name=req.learner_name.strip(),
            learner_email=email_clean,
            learner_id=req.learner_id.strip() if req.learner_id else None,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @classmethod
    def remove_member(cls, db: Session, batch_id: str, member_id: str) -> bool:
        member = (
            db.query(BatchMembershipModel)
            .filter(
                BatchMembershipModel.id == member_id,
                BatchMembershipModel.batch_id == batch_id,
            )
            .first()
        )
        if not member:
            raise BatchServiceError("Member not found in this Batch.")

        db.delete(member)
        db.commit()
        return True

    @classmethod
    def join_batch_by_code(cls, db: Session, join_code: str, name: str, email: str, learner_id: str | None = None) -> BatchMembershipModel:
        clean_code = join_code.strip().upper()
        batch = db.query(BatchModel).filter(BatchModel.join_code == clean_code).first()
        if not batch:
            raise BatchServiceError(f"No Batch found with join code '{clean_code}'.")
        if batch.is_archived:
            raise BatchServiceError("This Batch is archived and is no longer accepting new learners.")

        clean_email = email.strip().lower()
        existing = (
            db.query(BatchMembershipModel)
            .filter(
                BatchMembershipModel.batch_id == batch.id,
                func.lower(BatchMembershipModel.learner_email) == clean_email,
            )
            .first()
        )
        if existing:
            # Idempotent re-join: update name/ID if needed and return existing membership
            existing.learner_name = name.strip()
            if learner_id:
                existing.learner_id = learner_id.strip()
            db.commit()
            db.refresh(existing)
            return existing

        member = BatchMembershipModel(
            batch_id=batch.id,
            learner_name=name.strip(),
            learner_email=clean_email,
            learner_id=learner_id.strip() if learner_id else None,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member
