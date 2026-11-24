import json

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.attempt import QuizAttemptModel
from app.models.quiz import OptionModel, QuestionModel, QuizModel
from app.schemas.question import (
    OptionAttemptView,
    OptionReviewResponse,
    QuestionAttemptView,
    QuestionReviewResponse,
    QuestionUpdate,
)
from app.schemas.quiz import (
    QuizDetailResponse,
    QuizGenerateRequest,
    QuizSummaryResponse,
    QuizTakingResponse,
)
from app.schemas.validation import QuestionValidationSummary
from app.services.document_parser import DocumentParser
from app.services.llm_provider import get_llm_provider
from app.services.question_generator import QuestionGenerator
from app.services.text_chunker import TextChunker


class QuizServiceError(Exception):
    """User-safe exception for quiz business logic errors."""


class QuizService:
    @staticmethod
    def generate_quiz(db: Session, req: QuizGenerateRequest) -> tuple[QuizModel, QuestionValidationSummary]:
        # 1. Parse / Validate document text
        if req.source_type == "pasted":
            doc_result = DocumentParser.parse_pasted_text(req.source_text)
        elif req.source_type == "txt":
            doc_result = DocumentParser.parse_txt_bytes(
                req.source_text.encode("utf-8"), req.source_filename or "document.txt"
            )
        elif req.source_type in {"pptx", "ppt"}:
            doc_result = DocumentParser.parse_pasted_text(req.source_text)
        else:
            doc_result = DocumentParser.parse_pasted_text(req.source_text)

        # 2. Chunk document
        chunks = TextChunker.chunk_document(doc_result.pages)
        if not chunks:
            raise QuizServiceError("No readable content could be extracted from the document.")

        # 3. Select LLM provider - strictly separate demo mode from real document generation
        if req.use_demo_mode:
            llm = get_llm_provider(force_demo=True)
            quiz_origin = "demo"
            is_demo_used = True
        else:
            from app.core.config import settings

            if not settings.has_any_llm_key:
                raise QuizServiceError(
                    "No AI provider API key is configured. Please set GEMINI_API_KEY or GROQ_API_KEY in backend/.env to generate "
                    "quizzes from your uploaded documents, or use 'Try sample study set' for offline demo mode."
                )
            llm = get_llm_provider(force_demo=False)
            quiz_origin = "document_generated"
            is_demo_used = False

        # 4. Generate MCQs with bounded validation and deduplication loop
        generator = QuestionGenerator(llm)
        generated_questions, validation_summary = generator.generate_quiz_questions(
            chunks=chunks,
            num_questions=req.num_questions,
            target_difficulty=req.difficulty,
            topic_focus=req.topic_focus,
            difficulty_distribution=req.difficulty_distribution,
            included_topics=req.included_topics,
        )

        if not generated_questions:
            raise QuizServiceError(
                "Unable to generate valid, distinct multiple choice questions from the provided material. "
                "Please verify that the source document contains sufficient substantive text."
            )

        # 5. Persist QuizModel and Questions
        quiz = QuizModel(
            title=req.title.strip(),
            source_type=req.source_type,
            source_filename=req.source_filename,
            source_text_length=len(req.source_text),
            difficulty=req.difficulty,
            target_count=req.num_questions,
            topic_focus=req.topic_focus,
            status="draft",
            approval_status="draft",
            version=1,
            is_demo=is_demo_used,
            quiz_origin=quiz_origin,
            batch_id=req.batch_id,
            blueprint_config=json.dumps(req.blueprint_config) if req.blueprint_config else None,
        )
        db.add(quiz)
        db.flush()

        for idx, q_data in enumerate(generated_questions):
            question = QuestionModel(
                quiz_id=quiz.id,
                question_text=q_data["question_text"],
                explanation=q_data["explanation"],
                evidence=q_data["evidence"],
                source_page=q_data.get("source_page", 1),
                topic=q_data.get("topic", req.topic_focus or "General"),
                difficulty=q_data.get("difficulty", "medium"),
                question_style=q_data.get("question_style", "recall"),
                distractor_rationale=q_data.get("distractor_rationale"),
                validation_status=q_data.get("validation_status", "review"),
                validation_issues=json.dumps(q_data.get("validation_issues", [])),
                semantic_details=json.dumps(q_data.get("semantic_details", {})),
                order_index=idx + 1,
            )
            db.add(question)
            db.flush()

            for opt_data in q_data.get("options", []):
                opt = OptionModel(
                    question_id=question.id,
                    option_letter=opt_data["option_letter"],
                    option_text=opt_data["option_text"],
                    is_correct=opt_data["is_correct"],
                )
                db.add(opt)

        db.commit()
        db.refresh(quiz)
        return quiz, validation_summary

    @staticmethod
    def get_quiz_by_id(db: Session, quiz_id: str) -> QuizModel:
        quiz = db.query(QuizModel).filter(QuizModel.id == quiz_id).first()
        if not quiz:
            raise QuizServiceError(f"Quiz with ID '{quiz_id}' not found.")
        return quiz

    @staticmethod
    def get_quiz_taking_view(db: Session, quiz_id: str) -> QuizTakingResponse:
        """
        Returns a sanitized view of the quiz for test takers.
        Ensures correct options, explanations, and evidence are completely stripped.
        """
        quiz = QuizService.get_quiz_by_id(db, quiz_id)
        if not quiz.questions:
            raise QuizServiceError("This quiz has no questions.")

        attempt_questions = []
        for q in sorted(quiz.questions, key=lambda x: x.order_index):
            opts = [
                OptionAttemptView(id=o.id, option_letter=o.option_letter, option_text=o.option_text)
                for o in sorted(q.options, key=lambda x: x.option_letter)
            ]
            attempt_questions.append(
                QuestionAttemptView(
                    id=q.id,
                    question_text=q.question_text,
                    order_index=q.order_index,
                    options=opts,
                )
            )

        return QuizTakingResponse(
            id=quiz.id,
            title=quiz.title,
            version=quiz.version,
            total_questions=len(attempt_questions),
            questions=attempt_questions,
        )

    @staticmethod
    def get_quiz_detail(db: Session, quiz_id: str) -> QuizDetailResponse:
        quiz = QuizService.get_quiz_by_id(db, quiz_id)

        # Build review questions
        review_questions = []
        for q in sorted(quiz.questions, key=lambda x: x.order_index):
            opts = [
                OptionReviewResponse(
                    id=o.id,
                    option_letter=o.option_letter,
                    option_text=o.option_text,
                    is_correct=o.is_correct,
                )
                for o in sorted(q.options, key=lambda x: x.option_letter)
            ]
            try:
                issues = json.loads(q.validation_issues) if q.validation_issues else []
            except Exception:
                issues = []

            review_questions.append(
                QuestionReviewResponse(
                    id=q.id,
                    quiz_id=q.quiz_id,
                    question_text=q.question_text,
                    explanation=q.explanation,
                    evidence=q.evidence,
                    source_page=q.source_page,
                    topic=q.topic,
                    difficulty=q.difficulty,
                    question_style=getattr(q, "question_style", "recall"),
                    distractor_rationale=q.distractor_rationale,
                    validation_status=q.validation_status,
                    validation_issues=issues,
                    order_index=q.order_index,
                    options=opts,
                )
            )

        # Compute validation summary
        summary = QuestionValidationSummary(
            total_generated=len(quiz.questions),
            passed_count=sum(1 for q in quiz.questions if q.validation_status == "pass"),
            flagged_review_count=sum(1 for q in quiz.questions if q.validation_status == "review"),
            regenerated_count=0,
            rejected_count=sum(1 for q in quiz.questions if q.validation_status == "reject"),
        )

        return QuizDetailResponse(
            id=quiz.id,
            title=quiz.title,
            source_type=quiz.source_type,
            source_filename=quiz.source_filename,
            difficulty=quiz.difficulty,
            target_count=quiz.target_count,
            topic_focus=quiz.topic_focus,
            status=quiz.status,
            approval_status=getattr(quiz, "approval_status", "draft"),
            version=quiz.version,
            is_demo=quiz.is_demo,
            quiz_origin=getattr(quiz, "quiz_origin", "demo" if quiz.is_demo else "document_generated"),
            batch_id=quiz.batch_id,
            batch_name=quiz.batch.name if quiz.batch else None,
            blueprint_config=quiz.blueprint_config,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
            questions=review_questions,
            validation_summary=summary,
        )

    @staticmethod
    def update_question(db: Session, quiz_id: str, question_id: str, update_data: QuestionUpdate) -> QuestionModel:
        question = (
            db.query(QuestionModel).filter(QuestionModel.id == question_id, QuestionModel.quiz_id == quiz_id).first()
        )
        if not question:
            raise QuizServiceError(f"Question with ID '{question_id}' not found in this quiz.")

        if update_data.question_text is not None:
            question.question_text = update_data.question_text.strip()
        if update_data.explanation is not None:
            question.explanation = update_data.explanation.strip()
        if update_data.evidence is not None:
            question.evidence = update_data.evidence.strip()
        if update_data.source_page is not None:
            question.source_page = update_data.source_page
        if update_data.topic is not None:
            question.topic = update_data.topic.strip()
        if update_data.difficulty is not None:
            question.difficulty = update_data.difficulty.strip().lower()
        if update_data.distractor_rationale is not None:
            question.distractor_rationale = update_data.distractor_rationale.strip()

        # Update options if provided
        if update_data.options is not None:
            for opt_update in update_data.options:
                opt = next(
                    (
                        o
                        for o in question.options
                        if o.id == opt_update.id or o.option_letter == opt_update.option_letter
                    ),
                    None,
                )
                if opt:
                    opt.option_text = opt_update.option_text.strip()
                    opt.is_correct = opt_update.is_correct

        # Rerun deterministic checks upon edit to prevent stale PASS status
        from app.services.question_validator import QuestionValidator
        det_res = QuestionValidator.run_deterministic_checks(
            question={
                "question_text": question.question_text,
                "explanation": question.explanation,
                "evidence": question.evidence,
                "options": [
                    {"option_letter": o.option_letter, "option_text": o.option_text, "is_correct": o.is_correct}
                    for o in question.options
                ],
                "difficulty": question.difficulty,
            },
            source_text=question.evidence,
        )

        if not det_res.is_valid:
            question.validation_status = "review"
            question.validation_issues = json.dumps(det_res.issues)
        else:
            if update_data.validation_status is not None:
                question.validation_status = update_data.validation_status.strip().lower()
            elif question.validation_status == "reject":
                question.validation_status = "pass"
                question.validation_issues = json.dumps([])

        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def approve_quiz(db: Session, quiz_id: str) -> QuizModel:
        quiz = QuizService.get_quiz_by_id(db, quiz_id)
        if not quiz.questions:
            raise QuizServiceError("Cannot approve a quiz with no questions.")

        reject_count = sum(1 for q in quiz.questions if q.validation_status == "reject")
        if reject_count > 0:
            raise QuizServiceError(
                f"Cannot approve quiz with {reject_count} rejected question(s). "
                "Please regenerate or delete rejected questions before approving."
            )

        quiz.approval_status = "approved"
        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def delete_question(db: Session, quiz_id: str, question_id: str) -> None:
        question = (
            db.query(QuestionModel).filter(QuestionModel.id == question_id, QuestionModel.quiz_id == quiz_id).first()
        )
        if not question:
            raise QuizServiceError(f"Question with ID '{question_id}' not found.")

        db.delete(question)
        db.commit()

        # Re-index remaining questions
        remaining = (
            db.query(QuestionModel).filter(QuestionModel.quiz_id == quiz_id).order_by(QuestionModel.order_index).all()
        )
        for idx, q in enumerate(remaining, start=1):
            q.order_index = idx
        db.commit()

    @staticmethod
    def publish_quiz(db: Session, quiz_id: str) -> QuizModel:
        quiz = QuizService.get_quiz_by_id(db, quiz_id)
        if not quiz.questions:
            raise QuizServiceError("Cannot publish a quiz with no questions.")

        quiz.status = "published"
        quiz.approval_status = "published"
        quiz.version += 1
        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def list_quizzes(db: Session) -> list[QuizSummaryResponse]:
        quizzes = db.query(QuizModel).order_by(desc(QuizModel.created_at)).all()
        summaries = []

        for q in quizzes:
            # Find latest completed attempt if exists
            latest_attempt = (
                db.query(QuizAttemptModel)
                .filter(
                    QuizAttemptModel.quiz_id == q.id,
                    QuizAttemptModel.status == "completed",
                )
                .order_by(desc(QuizAttemptModel.completed_at))
                .first()
            )
            attempts_count = db.query(QuizAttemptModel).filter(QuizAttemptModel.quiz_id == q.id).count()

            summaries.append(
                QuizSummaryResponse(
                    id=q.id,
                    title=q.title,
                    source_type=q.source_type,
                    source_filename=q.source_filename,
                    question_count=len(q.questions),
                    difficulty=q.difficulty,
                    status=q.status,
                    approval_status=getattr(q, "approval_status", "draft"),
                    is_demo=q.is_demo,
                    quiz_origin=getattr(q, "quiz_origin", "demo" if q.is_demo else "document_generated"),
                    batch_id=q.batch_id,
                    batch_name=q.batch.name if q.batch else None,
                    created_at=q.created_at,
                    latest_score_percentage=latest_attempt.score_percentage if latest_attempt else None,
                    latest_attempt_id=latest_attempt.id if latest_attempt else None,
                    attempts_count=attempts_count,
                )
            )

        return summaries

    @staticmethod
    def delete_quiz(db: Session, quiz_id: str) -> None:
        quiz = QuizService.get_quiz_by_id(db, quiz_id)
        db.delete(quiz)
        db.commit()
