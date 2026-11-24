from datetime import datetime

from pydantic import BaseModel


class BatchPerformanceOverview(BaseModel):
    batch_id: str | None = None
    batch_name: str | None = None
    publication_id: str
    quiz_title: str
    eligible_learners: int = 0
    started_learners: int = 0
    submitted_learners: int = 0
    completion_rate: float = 0.0
    average_score_percentage: float = 0.0
    median_score_percentage: float = 0.0
    highest_score_percentage: float = 0.0
    lowest_score_percentage: float = 0.0
    score_distribution: dict[str, int] = {
        "0-20%": 0,
        "21-40%": 0,
        "41-60%": 0,
        "61-80%": 0,
        "81-100%": 0,
    }


class QuestionAnalyticsItem(BaseModel):
    question_id: str
    order_index: int
    question_text: str
    topic: str
    difficulty: str
    correct_percentage: float = 0.0
    unanswered_count: int = 0
    most_common_wrong_letter: str | None = None
    most_common_wrong_text: str | None = None
    is_confusing_flag: bool = False  # Flagged if unusually low success rate (< 30%) with >= 3 responses


class TopicMasteryItem(BaseModel):
    topic: str
    total_questions: int
    average_mastery_percentage: float


class LearnerResultItem(BaseModel):
    attempt_id: str
    learner_name: str
    learner_email: str
    learner_id: str | None = None
    score: int
    total_questions: int
    score_percentage: float
    marks_obtained: float
    total_marks: float
    version_label: str = "A"
    completed_at: datetime | None = None


class FullBatchAnalyticsResponse(BaseModel):
    overview: BatchPerformanceOverview
    question_analytics: list[QuestionAnalyticsItem]
    topic_analytics: list[TopicMasteryItem]
    learner_results: list[LearnerResultItem]
