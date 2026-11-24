import statistics
from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attempt import AttemptAnswerModel, QuizAttemptModel
from app.models.batch import BatchMembershipModel
from app.models.publication import PublicationModel
from app.schemas.analytics import (
    BatchPerformanceOverview,
    FullBatchAnalyticsResponse,
    LearnerResultItem,
    QuestionAnalyticsItem,
    TopicMasteryItem,
)


class AnalyticsServiceError(Exception):
    """Business logic errors for Analytics."""


class AnalyticsService:
    @classmethod
    def get_publication_analytics(cls, db: Session, publication_id: str) -> FullBatchAnalyticsResponse:
        pub = db.query(PublicationModel).filter(PublicationModel.id == publication_id).first()
        if not pub:
            raise AnalyticsServiceError(f"Publication with ID '{publication_id}' not found.")

        # Ensure we only analyze real attempts and exclude demo attempts
        attempts = (
            db.query(QuizAttemptModel)
            .filter(
                QuizAttemptModel.publication_id == publication_id,
                QuizAttemptModel.status == "completed",
            )
            .all()
        )

        started_count = (
            db.query(func.count(QuizAttemptModel.id))
            .filter(QuizAttemptModel.publication_id == publication_id)
            .scalar()
            or 0
        )

        # Enrolled learners count if assigned to a batch
        eligible_learners = 0
        if pub.batch_id:
            eligible_learners = (
                db.query(func.count(BatchMembershipModel.id))
                .filter(BatchMembershipModel.batch_id == pub.batch_id)
                .scalar()
                or 0
            )
        else:
            eligible_learners = started_count

        submitted_count = len(attempts)
        completion_rate = round((submitted_count / eligible_learners * 100.0), 1) if eligible_learners > 0 else 0.0

        scores = [a.score_percentage for a in attempts]
        score_distribution = {
            "0-20%": sum(1 for s in scores if 0 <= s <= 20),
            "21-40%": sum(1 for s in scores if 20 < s <= 40),
            "41-60%": sum(1 for s in scores if 40 < s <= 60),
            "61-80%": sum(1 for s in scores if 60 < s <= 80),
            "81-100%": sum(1 for s in scores if 80 < s <= 100),
        }

        avg_score = round(statistics.mean(scores), 1) if scores else 0.0
        med_score = round(statistics.median(scores), 1) if scores else 0.0
        highest_score = max(scores) if scores else 0.0
        lowest_score = min(scores) if scores else 0.0

        overview = BatchPerformanceOverview(
            batch_id=pub.batch_id,
            batch_name=pub.batch.name if pub.batch else None,
            publication_id=pub.id,
            quiz_title=pub.quiz.title,
            eligible_learners=eligible_learners,
            started_learners=started_count,
            submitted_learners=submitted_count,
            completion_rate=completion_rate,
            average_score_percentage=avg_score,
            median_score_percentage=med_score,
            highest_score_percentage=highest_score,
            lowest_score_percentage=lowest_score,
            score_distribution=score_distribution,
        )

        # Question analytics
        quiz_questions = sorted(pub.quiz.questions, key=lambda x: x.order_index)
        question_analytics: list[QuestionAnalyticsItem] = []
        topic_totals: dict[str, list[float]] = {}

        # Fetch all answers for these completed attempts
        attempt_ids = [a.id for a in attempts]
        all_answers = (
            db.query(AttemptAnswerModel)
            .filter(AttemptAnswerModel.attempt_id.in_(attempt_ids))
            .all()
            if attempt_ids
            else []
        )

        answers_by_question: dict[str, list[AttemptAnswerModel]] = {}
        for ans in all_answers:
            answers_by_question.setdefault(ans.question_id, []).append(ans)

        for q in quiz_questions:
            q_answers = answers_by_question.get(q.id, [])
            total_responses = len(q_answers)
            correct_responses = sum(1 for a in q_answers if a.is_correct)
            unanswered = sum(1 for a in q_answers if not a.selected_option_id)

            correct_pct = round((correct_responses / total_responses * 100.0), 1) if total_responses > 0 else 0.0

            # Find most common wrong distractor
            wrong_option_counts = Counter(
                a.selected_option_id for a in q_answers if not a.is_correct and a.selected_option_id
            )
            most_wrong_id, _ = wrong_option_counts.most_common(1)[0] if wrong_option_counts else (None, 0)

            wrong_opt_letter = None
            wrong_opt_text = None
            if most_wrong_id:
                matching_opt = next((o for o in q.options if o.id == most_wrong_id), None)
                if matching_opt:
                    wrong_opt_letter = matching_opt.option_letter
                    wrong_opt_text = matching_opt.option_text

            is_confusing = total_responses >= 3 and correct_pct < 30.0

            question_analytics.append(
                QuestionAnalyticsItem(
                    question_id=q.id,
                    order_index=q.order_index,
                    question_text=q.question_text,
                    topic=q.topic,
                    difficulty=q.difficulty,
                    correct_percentage=correct_pct,
                    unanswered_count=unanswered,
                    most_common_wrong_letter=wrong_opt_letter,
                    most_common_wrong_text=wrong_opt_text,
                    is_confusing_flag=is_confusing,
                )
            )

            topic_totals.setdefault(q.topic, []).append(correct_pct)

        # Topic mastery
        topic_analytics: list[TopicMasteryItem] = []
        for topic, pcts in topic_totals.items():
            topic_analytics.append(
                TopicMasteryItem(
                    topic=topic,
                    total_questions=len(pcts),
                    average_mastery_percentage=round(statistics.mean(pcts), 1) if pcts else 0.0,
                )
            )

        # Learner results
        learner_results = [
            LearnerResultItem(
                attempt_id=a.id,
                learner_name=a.learner_name or "Anonymous",
                learner_email=a.learner_email or "N/A",
                learner_id=a.learner_id,
                score=a.score,
                total_questions=a.total_questions,
                score_percentage=a.score_percentage,
                marks_obtained=a.marks_obtained,
                total_marks=a.total_marks,
                version_label=a.version_label or "A",
                completed_at=a.completed_at,
            )
            for a in sorted(attempts, key=lambda x: x.score_percentage, reverse=True)
        ]

        return FullBatchAnalyticsResponse(
            overview=overview,
            question_analytics=question_analytics,
            topic_analytics=topic_analytics,
            learner_results=learner_results,
        )
