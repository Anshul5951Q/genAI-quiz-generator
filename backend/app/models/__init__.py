from app.models.attempt import AttemptAnswerModel, QuizAttemptModel
from app.models.batch import BatchMembershipModel, BatchModel
from app.models.interview import InterviewModel, InterviewQuestionModel, InterviewRoundModel
from app.models.interview_session import AnswerEvaluationModel, InterviewResponseModel, InterviewSessionModel
from app.models.job_description import JDRequirementModel, JobDescriptionModel, ResumeJDMatchModel
from app.models.learning import AIModelLogModel, AuditLogModel, LearningRecommendationModel, SkillProfileModel
from app.models.publication import PublicationModel
from app.models.question_bank import QuestionBankEntryModel, QuestionUsageModel
from app.models.quiz import OptionModel, QuestionModel, QuizModel
from app.models.resume import ResumeExtractionModel, ResumeModel, ResumeProjectModel, ResumeSkillModel
from app.models.user import UserModel
from app.models.version import QuizVersionMappingModel

__all__ = [
    # Existing academic models
    "QuizModel",
    "QuestionModel",
    "OptionModel",
    "QuizAttemptModel",
    "AttemptAnswerModel",
    "BatchModel",
    "BatchMembershipModel",
    "PublicationModel",
    "QuizVersionMappingModel",
    "QuestionBankEntryModel",
    "QuestionUsageModel",
    # New identity models
    "UserModel",
    # New resume intelligence models
    "ResumeModel",
    "ResumeExtractionModel",
    "ResumeSkillModel",
    "ResumeProjectModel",
    # New JD intelligence models
    "JobDescriptionModel",
    "JDRequirementModel",
    "ResumeJDMatchModel",
    # New interview models
    "InterviewModel",
    "InterviewRoundModel",
    "InterviewQuestionModel",
    # New session models
    "InterviewSessionModel",
    "InterviewResponseModel",
    "AnswerEvaluationModel",
    # New analytics models
    "SkillProfileModel",
    "LearningRecommendationModel",
    "AIModelLogModel",
    "AuditLogModel",
]
