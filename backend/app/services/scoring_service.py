from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.attempt import AttemptAnswerModel, QuizAttemptModel
from app.models.quiz import QuestionModel, QuizModel
from app.schemas.attempt import (
    AttemptResultResponse,
    AttemptSubmissionRequest,
    ScoreBreakdownItem,
)
from app.schemas.question import OptionReviewResponse, QuestionResultResponse


class ScoringServiceError(Exception):
    """User-safe exception for scoring and attempt submission errors."""


class ScoringService:
    @staticmethod
    def calculate_attempt_results(
        db: Session, attempt: QuizAttemptModel, submission: AttemptSubmissionRequest
    ) -> AttemptResultResponse:
        if attempt.status == "completed":
            raise ScoringServiceError("This quiz attempt has already been submitted and scored.")

        quiz = db.query(QuizModel).filter(QuizModel.id == attempt.quiz_id).first()
        if not quiz:
            raise ScoringServiceError("Quiz associated with this attempt was not found.")

        # Load questions for this quiz
        questions = (
            db.query(QuestionModel).filter(QuestionModel.quiz_id == quiz.id).order_by(QuestionModel.order_index).all()
        )

        if not questions:
            raise ScoringServiceError("No questions found for this quiz.")

        # Map user submitted answers by question_id, validating against duplicate submissions
        submitted_answers_map: dict[str, str | None] = {}
        for ans in submission.answers:
            if ans.question_id in submitted_answers_map:
                logger.warning(f"Duplicate answer entry submitted for question {ans.question_id}")
            submitted_answers_map[ans.question_id] = ans.selected_option_id

        total_questions = len(questions)
        correct_count = 0
        unanswered_count = 0

        # Topic and difficulty tracking
        topic_stats: dict[str, dict[str, int]] = {}
        diff_stats: dict[str, dict[str, int]] = {}

        detailed_question_results: list[QuestionResultResponse] = []

        for q in questions:
            selected_option_id = submitted_answers_map.get(q.id)

            # Find the correct option from the database
            correct_opt = next((opt for opt in q.options if opt.is_correct), None)
            correct_option_id = correct_opt.id if correct_opt else ""

            is_correct = False
            if selected_option_id is None:
                unanswered_count += 1
            else:
                # Verify that selected_option_id actually belongs to this question
                valid_option_ids = {opt.id for opt in q.options}
                if selected_option_id not in valid_option_ids:
                    raise ScoringServiceError(
                        f"Selected option ID '{selected_option_id}' is invalid for question '{q.id}'."
                    )
                if selected_option_id == correct_option_id:
                    is_correct = True
                    correct_count += 1

            # Record answer in database
            answer_record = AttemptAnswerModel(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option_id=selected_option_id,
                is_correct=is_correct,
            )
            db.add(answer_record)

            # Topic tracking
            top = q.topic or "General"
            if top not in topic_stats:
                topic_stats[top] = {"total": 0, "correct": 0}
            topic_stats[top]["total"] += 1
            if is_correct:
                topic_stats[top]["correct"] += 1

            # Difficulty tracking
            dif = q.difficulty or "medium"
            if dif not in diff_stats:
                diff_stats[dif] = {"total": 0, "correct": 0}
            diff_stats[dif]["total"] += 1
            if is_correct:
                diff_stats[dif]["correct"] += 1

            # Build detailed question result for response
            opt_responses = [
                OptionReviewResponse(
                    id=opt.id,
                    option_letter=opt.option_letter,
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                )
                for opt in sorted(q.options, key=lambda x: x.option_letter)
            ]

            detailed_question_results.append(
                QuestionResultResponse(
                    id=q.id,
                    question_text=q.question_text,
                    order_index=q.order_index,
                    topic=q.topic,
                    difficulty=q.difficulty,
                    explanation=q.explanation,
                    evidence=q.evidence,
                    source_page=q.source_page,
                    options=opt_responses,
                    selected_option_id=selected_option_id,
                    correct_option_id=correct_option_id,
                    is_correct=is_correct,
                )
            )

        # Calculate final percentage
        score_pct = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0

        # Update attempt record
        attempt.status = "completed"
        attempt.completed_at = datetime.now(UTC)
        attempt.score = correct_count
        attempt.total_questions = total_questions
        attempt.unanswered_count = unanswered_count
        attempt.score_percentage = score_pct

        db.commit()
        db.refresh(attempt)

        # Prepare breakdown items
        diff_breakdown = [
            ScoreBreakdownItem(
                category=k.capitalize(),
                total=v["total"],
                correct=v["correct"],
                percentage=round((v["correct"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0,
            )
            for k, v in diff_stats.items()
        ]

        topic_breakdown = [
            ScoreBreakdownItem(
                category=k,
                total=v["total"],
                correct=v["correct"],
                percentage=round((v["correct"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0,
            )
            for k, v in topic_stats.items()
        ]

        return AttemptResultResponse(
            attempt_id=attempt.id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            score=attempt.score,
            total_questions=attempt.total_questions,
            unanswered_count=attempt.unanswered_count,
            score_percentage=attempt.score_percentage,
            difficulty_breakdown=diff_breakdown,
            topic_breakdown=topic_breakdown,
            questions=detailed_question_results,
        )
