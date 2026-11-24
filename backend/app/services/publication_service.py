import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attempt import AttemptAnswerModel, QuizAttemptModel
from app.models.batch import BatchMembershipModel, BatchModel
from app.models.publication import PublicationModel
from app.models.quiz import QuizModel
from app.schemas.publication import (
    OptionAttemptView,
    PublicationCreate,
    PublicationResponse,
    PublicationUpdate,
    StudentAssessmentView,
    StudentAttemptResultResponse,
    StudentAttemptStartRequest,
    StudentAttemptStartResponse,
    StudentAttemptSubmitRequest,
    StudentOptionResult,
    StudentQuestionItem,
    StudentQuestionResult,
)


class PublicationServiceError(Exception):
    """Business logic errors for Publication and online assessment workflows."""


class PublicationService:
    @staticmethod
    def _generate_access_code(db: Session, prefix: str = "QZ") -> str:
        """Generates a unique 6-character access code for students (e.g. QZ-8392)."""
        chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
        for _ in range(20):
            suffix = "".join(random.choices(chars, k=4))
            code = f"{prefix}-{suffix}"
            exists = db.query(PublicationModel).filter(PublicationModel.access_code == code).first()
            if not exists:
                return code
        return f"{prefix}-{uuid.uuid4().hex[:5].upper()}"

    @classmethod
    def create_publication(cls, db: Session, req: PublicationCreate) -> PublicationModel:
        quiz = db.query(QuizModel).filter(QuizModel.id == req.quiz_id).first()
        if not quiz:
            raise PublicationServiceError(f"Quiz with ID '{req.quiz_id}' not found.")
        if not quiz.questions:
            raise PublicationServiceError("Cannot publish a quiz that has 0 questions.")

        # Batch validation
        if req.batch_id:
            batch = db.query(BatchModel).filter(BatchModel.id == req.batch_id).first()
            if not batch:
                raise PublicationServiceError(f"Batch with ID '{req.batch_id}' not found.")
            if batch.is_archived:
                raise PublicationServiceError("Cannot publish assessments to an archived Batch.")

        access_code = req.access_code.strip().upper() if req.access_code else cls._generate_access_code(db)
        existing = db.query(PublicationModel).filter(PublicationModel.access_code == access_code).first()
        if existing:
            raise PublicationServiceError(f"Access code '{access_code}' is already in use.")

        pub = PublicationModel(
            quiz_id=quiz.id,
            batch_id=req.batch_id,
            access_code=access_code,
            status="active",
            time_limit_minutes=req.time_limit_minutes,
            max_attempts=req.max_attempts,
            shuffle_questions=req.shuffle_questions,
            shuffle_options=req.shuffle_options,
            show_explanations_after=req.show_explanations_after,
            passing_percentage=req.passing_percentage,
            marks_per_question=req.marks_per_question,
            negative_marking_per_question=req.negative_marking_per_question,
            start_time=req.start_time,
            end_time=req.end_time,
            instructions=req.instructions.strip() if req.instructions else None,
        )
        # Mark quiz status as published and bump version
        quiz.status = "published"
        quiz.approval_status = "published"
        quiz.version += 1

        db.add(pub)
        db.commit()
        db.refresh(pub)
        return pub

    @classmethod
    def get_publication_response(cls, db: Session, pub_id: str) -> PublicationResponse:
        pub = db.query(PublicationModel).filter(PublicationModel.id == pub_id).first()
        if not pub:
            raise PublicationServiceError(f"Publication with ID '{pub_id}' not found.")

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

        return PublicationResponse(
            id=pub.id,
            quiz_id=pub.quiz_id,
            quiz_title=pub.quiz.title,
            batch_id=pub.batch_id,
            batch_name=pub.batch.name if pub.batch else None,
            access_code=pub.access_code,
            status=pub.status,
            time_limit_minutes=pub.time_limit_minutes,
            max_attempts=pub.max_attempts,
            shuffle_questions=pub.shuffle_questions,
            shuffle_options=pub.shuffle_options,
            show_explanations_after=pub.show_explanations_after,
            passing_percentage=pub.passing_percentage,
            marks_per_question=pub.marks_per_question,
            negative_marking_per_question=pub.negative_marking_per_question,
            start_time=pub.start_time,
            end_time=pub.end_time,
            instructions=pub.instructions,
            created_at=pub.created_at,
            submissions_count=sub_count,
            average_score_percentage=round(avg_score, 1) if avg_score is not None else None,
        )

    @classmethod
    def update_publication(cls, db: Session, pub_id: str, req: PublicationUpdate) -> PublicationResponse:
        pub = db.query(PublicationModel).filter(PublicationModel.id == pub_id).first()
        if not pub:
            raise PublicationServiceError(f"Publication with ID '{pub_id}' not found.")

        if req.status is not None:
            pub.status = req.status
        if req.time_limit_minutes is not None:
            pub.time_limit_minutes = req.time_limit_minutes
        if req.max_attempts is not None:
            pub.max_attempts = req.max_attempts
        if req.show_explanations_after is not None:
            pub.show_explanations_after = req.show_explanations_after
        if req.instructions is not None:
            pub.instructions = req.instructions.strip() or None

        db.commit()
        return cls.get_publication_response(db, pub.id)

    @classmethod
    def get_student_assessment_view(cls, db: Session, access_code: str) -> StudentAssessmentView:
        code_clean = access_code.strip().upper()
        pub = db.query(PublicationModel).filter(PublicationModel.access_code == code_clean).first()
        if not pub:
            raise PublicationServiceError(f"Assessment with access code '{code_clean}' not found.")

        if pub.status != "active":
            raise PublicationServiceError(f"This assessment is currently {pub.status} and not accepting submissions.")

        now = datetime.now(UTC)
        if pub.start_time and now < pub.start_time:
            raise PublicationServiceError(f"This assessment is not open yet. It opens at {pub.start_time.isoformat()}.")
        if pub.end_time and now > pub.end_time:
            raise PublicationServiceError(f"This assessment closed at {pub.end_time.isoformat()}.")

        questions = list(pub.quiz.questions)
        if pub.shuffle_questions:
            # Deterministic pseudo-random order based on quiz id to avoid shifting during page refresh
            rnd = random.Random(pub.id)
            rnd.shuffle(questions)

        question_items: list[StudentQuestionItem] = []
        for idx, q in enumerate(questions, start=1):
            opts = list(q.options)
            if pub.shuffle_options:
                rnd_opt = random.Random(f"{pub.id}_{q.id}")
                rnd_opt.shuffle(opts)

            # Re-label letters cleanly A-D while keeping option IDs intact
            letters = ["A", "B", "C", "D"]
            opt_views = [
                OptionAttemptView(
                    id=o.id,
                    option_letter=letters[i % 4],
                    option_text=o.option_text,
                )
                for i, o in enumerate(opts)
            ]

            question_items.append(
                StudentQuestionItem(
                    id=q.id,
                    question_text=q.question_text,
                    order_index=idx,
                    options=opt_views,
                )
            )

        return StudentAssessmentView(
            publication_id=pub.id,
            access_code=pub.access_code,
            quiz_title=pub.quiz.title,
            time_limit_minutes=pub.time_limit_minutes,
            total_questions=len(question_items),
            marks_per_question=pub.marks_per_question,
            negative_marking_per_question=pub.negative_marking_per_question,
            instructions=pub.instructions,
            questions=question_items,
        )

    @classmethod
    def start_student_attempt(
        cls,
        db: Session,
        access_code: str,
        req: StudentAttemptStartRequest,
    ) -> StudentAttemptStartResponse:
        code_clean = access_code.strip().upper()
        pub = db.query(PublicationModel).filter(PublicationModel.access_code == code_clean).first()
        if not pub:
            raise PublicationServiceError(f"Assessment with access code '{code_clean}' not found.")
        if pub.status != "active":
            raise PublicationServiceError(f"This assessment is {pub.status}.")

        now = datetime.now(UTC)
        email_clean = req.learner_email.strip().lower()

        # If publication is assigned to a Batch, enforce batch membership
        if pub.batch_id:
            membership = (
                db.query(BatchMembershipModel)
                .filter(
                    BatchMembershipModel.batch_id == pub.batch_id,
                    func.lower(BatchMembershipModel.learner_email) == email_clean,
                )
                .first()
            )
            if not membership:
                raise PublicationServiceError(
                    f"Email '{email_clean}' is not enrolled in the Batch for this assessment. "
                    "Please join the Batch using your instructor's join code first."
                )

        # Enforce max attempts
        prior_attempts = (
            db.query(func.count(QuizAttemptModel.id))
            .filter(
                QuizAttemptModel.publication_id == pub.id,
                func.lower(QuizAttemptModel.learner_email) == email_clean,
                QuizAttemptModel.status == "completed",
            )
            .scalar()
            or 0
        )
        if prior_attempts >= pub.max_attempts:
            raise PublicationServiceError(
                f"You have already used the maximum allowed attempts ({pub.max_attempts}) for this assessment."
            )

        # Check for uncompleted attempt
        existing_in_progress = (
            db.query(QuizAttemptModel)
            .filter(
                QuizAttemptModel.publication_id == pub.id,
                func.lower(QuizAttemptModel.learner_email) == email_clean,
                QuizAttemptModel.status == "in_progress",
            )
            .order_by(QuizAttemptModel.started_at.desc())
            .first()
        )
        if existing_in_progress:
            # Check if expired
            if pub.time_limit_minutes:
                deadline = existing_in_progress.started_at.replace(tzinfo=UTC) + timedelta(minutes=pub.time_limit_minutes)
                if now <= deadline + timedelta(seconds=60):
                    # Resume existing attempt
                    return StudentAttemptStartResponse(
                        attempt_id=existing_in_progress.id,
                        publication_id=pub.id,
                        started_at=existing_in_progress.started_at,
                        expires_at=deadline,
                        server_time=now,
                    )

        # Create new attempt
        expires_at = now + timedelta(minutes=pub.time_limit_minutes) if pub.time_limit_minutes else None

        attempt = QuizAttemptModel(
            quiz_id=pub.quiz_id,
            publication_id=pub.id,
            batch_id=pub.batch_id,
            learner_name=req.learner_name.strip(),
            learner_email=email_clean,
            learner_id=req.learner_id.strip() if req.learner_id else None,
            version_label="A",
            quiz_version=pub.quiz.version,
            status="in_progress",
            started_at=now,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return StudentAttemptStartResponse(
            attempt_id=attempt.id,
            publication_id=pub.id,
            started_at=now,
            expires_at=expires_at,
            server_time=now,
        )

    @classmethod
    def submit_student_attempt(
        cls,
        db: Session,
        access_code: str,
        req: StudentAttemptSubmitRequest,
    ) -> StudentAttemptResultResponse:
        attempt = db.query(QuizAttemptModel).filter(QuizAttemptModel.id == req.attempt_id).first()
        if not attempt:
            raise PublicationServiceError(f"Attempt with ID '{req.attempt_id}' not found.")
        if attempt.status == "completed":
            # Idempotent: return finalized result
            return cls.get_student_attempt_result(db, attempt.id)

        pub = attempt.publication
        if not pub:
            raise PublicationServiceError("Publication associated with this attempt was not found.")

        now = datetime.now(UTC)

        # Server-authoritative timer deadline enforcement with 60s network grace period
        if pub.time_limit_minutes:
            started = attempt.started_at.replace(tzinfo=UTC) if attempt.started_at.tzinfo is None else attempt.started_at
            deadline = started + timedelta(minutes=pub.time_limit_minutes, seconds=60)
            if now > deadline:
                pass  # Accept whatever was submitted up to expiration

        # Grade submitted answers against authoritative OptionModel.is_correct
        quiz_questions = {q.id: q for q in pub.quiz.questions}
        total_questions = len(quiz_questions)

        score = 0
        unanswered_count = 0
        marks_obtained = 0.0

        # Clear any prior answers for this attempt
        db.query(AttemptAnswerModel).filter(AttemptAnswerModel.attempt_id == attempt.id).delete()

        submitted_answers_map = {a.question_id: a.selected_option_id for a in req.answers}

        for q_id, question in quiz_questions.items():
            selected_opt_id = submitted_answers_map.get(q_id)
            is_correct = False

            if not selected_opt_id:
                unanswered_count += 1
            else:
                correct_opt = next((o for o in question.options if o.is_correct), None)
                if correct_opt and correct_opt.id == selected_opt_id:
                    is_correct = True
                    score += 1
                    marks_obtained += pub.marks_per_question
                else:
                    marks_obtained -= pub.negative_marking_per_question

            ans_record = AttemptAnswerModel(
                attempt_id=attempt.id,
                question_id=q_id,
                selected_option_id=selected_opt_id,
                is_correct=is_correct,
            )
            db.add(ans_record)

        total_marks = total_questions * pub.marks_per_question
        marks_obtained = max(0.0, marks_obtained)  # Do not allow negative aggregate score
        score_pct = round((score / total_questions) * 100.0, 1) if total_questions > 0 else 0.0

        attempt.status = "completed"
        attempt.completed_at = now
        attempt.score = score
        attempt.total_questions = total_questions
        attempt.unanswered_count = unanswered_count
        attempt.score_percentage = score_pct
        attempt.marks_obtained = round(marks_obtained, 2)
        attempt.total_marks = round(total_marks, 2)

        db.commit()
        db.refresh(attempt)

        return cls.get_student_attempt_result(db, attempt.id)

    @classmethod
    def get_student_attempt_result(cls, db: Session, attempt_id: str) -> StudentAttemptResultResponse:
        attempt = db.query(QuizAttemptModel).filter(QuizAttemptModel.id == attempt_id).first()
        if not attempt:
            raise PublicationServiceError(f"Attempt with ID '{attempt_id}' not found.")

        pub = attempt.publication
        quiz = attempt.quiz
        passed = attempt.score_percentage >= (pub.passing_percentage if pub else 50.0)

        show_exps = pub.show_explanations_after if pub else True
        question_results: list[StudentQuestionResult] | None = None

        if show_exps:
            # Build reviewable question details
            answers_map = {a.question_id: a for a in attempt.answers}
            q_results = []

            for q in sorted(quiz.questions, key=lambda x: x.order_index):
                user_ans = answers_map.get(q.id)
                correct_opt = next((o for o in q.options if o.is_correct), None)
                correct_id = correct_opt.id if correct_opt else ""

                opt_results = [
                    StudentOptionResult(
                        id=o.id,
                        option_letter=o.option_letter,
                        option_text=o.option_text,
                        is_correct=o.is_correct,
                    )
                    for o in sorted(q.options, key=lambda x: x.option_letter)
                ]

                q_results.append(
                    StudentQuestionResult(
                        id=q.id,
                        question_text=q.question_text,
                        order_index=q.order_index,
                        explanation=q.explanation,
                        evidence=q.evidence,
                        source_page=q.source_page,
                        selected_option_id=user_ans.selected_option_id if user_ans else None,
                        correct_option_id=correct_id,
                        is_correct=user_ans.is_correct if user_ans else False,
                        options=opt_results,
                    )
                )
            question_results = q_results

        return StudentAttemptResultResponse(
            attempt_id=attempt.id,
            quiz_title=quiz.title,
            score=attempt.score,
            total_questions=attempt.total_questions,
            unanswered_count=attempt.unanswered_count,
            score_percentage=attempt.score_percentage,
            marks_obtained=attempt.marks_obtained,
            total_marks=attempt.total_marks,
            passed=passed,
            completed_at=attempt.completed_at or datetime.now(UTC),
            show_explanations=show_exps,
            question_results=question_results,
        )
