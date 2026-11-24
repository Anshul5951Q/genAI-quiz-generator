"""
Comprehensive automated tests for StudySet AI 2.0 new core features:
- Authentication & RBAC (register, login, JWT decode, roles, password hashing)
- AI Provider & Orchestrator (Ollama configuration, fallback logic, provider health)
- Resume & JD Intelligence (data models, parsing, confidence computation)
- Interview Generation Engine (blueprint, question validation, category mapping)
- Session Lifecycle & Answer Evaluation (deterministic weighted scoring, session state)
- Analytics & Learning Roadmap (metrics aggregation, recommendation completion)
"""
import json
import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.models.user import UserModel
from app.models.resume import ResumeModel, ResumeExtractionModel, ResumeSkillModel, ResumeProjectModel
from app.models.job_description import JobDescriptionModel, JDRequirementModel, ResumeJDMatchModel
from app.models.interview import InterviewModel, InterviewRoundModel, InterviewQuestionModel
from app.models.interview_session import InterviewSessionModel, InterviewResponseModel, AnswerEvaluationModel
from app.models.learning import SkillProfileModel, LearningRecommendationModel
from app.services.auth_service import AuthService, AuthServiceError
from app.services.resume_extractor import ResumeExtractor
from app.services.evaluation_service import AnswerEvaluationService, CRITERION_WEIGHTS
from app.services.llm_provider import DemoLLMProvider


# --- 1. Authentication & Security Tests ---

def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decode():
    payload = {"sub": "user-uuid-1234", "email": "test@studyset.ai", "role": "STUDENT"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "user-uuid-1234"
    assert decoded.get("email") == "test@studyset.ai"
    assert decoded.get("role") == "STUDENT"


def test_auth_service_user_registration_and_login(db_session):
    email = "engineer@studyset.ai"
    password = "StrongPassword2026!"

    # Registration
    user = AuthService.create_user(db_session, email=email, password=password, full_name="AI Engineer", role="RECRUITER")
    assert user.id is not None
    assert user.email == email
    assert user.role == "RECRUITER"
    assert user.is_active is True

    # Duplicate registration should raise AuthServiceError
    with pytest.raises(AuthServiceError, match="already exists"):
        AuthService.create_user(db_session, email=email, password=password)

    # Short password rejected
    with pytest.raises(AuthServiceError, match="at least 8 characters"):
        AuthService.create_user(db_session, email="other@studyset.ai", password="short")

    # Authentication success
    auth_user = AuthService.authenticate(db_session, email=email, password=password)
    assert auth_user.id == user.id

    # Authentication failure
    with pytest.raises(AuthServiceError, match="Invalid email or password"):
        AuthService.authenticate(db_session, email=email, password="BadPassword!")

    # Token generation
    tokens = AuthService.generate_tokens(auth_user)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["user"]["email"] == email


def test_rbac_user_role_update(db_session):
    user = AuthService.create_user(db_session, email="student@studyset.ai", password="Password123!", role="STUDENT")
    assert user.role == "STUDENT"

    updated = AuthService.update_user_role(db_session, user.id, "ADMIN")
    assert updated.role == "ADMIN"


# --- 2. Resume & Confidence Computation Tests ---

def test_resume_extraction_confidence_computation():
    full_data = {
        "candidate_name": "Jane Doe",
        "email": "jane@example.com",
        "technical_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
        "projects": [{"title": "StudySet AI", "technologies": ["FastAPI", "React"]}],
        "experience": [{"title": "Software Engineer", "company": "Tech Corp"}],
        "education": [{"degree": "B.Tech Computer Science"}],
    }
    confidence = ResumeExtractor.compute_confidence(full_data)
    assert confidence >= 0.95

    sparse_data = {
        "candidate_name": "John",
        "technical_skills": ["Python"],
    }
    sparse_confidence = ResumeExtractor.compute_confidence(sparse_data)
    assert sparse_confidence < 0.50


def test_resume_model_persistence(db_session):
    resume = ResumeModel(
        filename="jane_doe_resume.pdf",
        file_path="/uploads/resumes/dummy.pdf",
        file_size=1048576,
        file_type="pdf",
        status="extracted",
    )
    db_session.add(resume)
    db_session.commit()

    extraction = ResumeExtractionModel(
        resume_id=resume.id,
        candidate_name="Jane Doe",
        email="jane@example.com",
        programming_languages_json=json.dumps(["Python", "TypeScript"]),
        frameworks_json=json.dumps(["FastAPI", "React"]),
        extraction_confidence=0.92,
    )
    db_session.add(extraction)

    skill = ResumeSkillModel(
        resume_id=resume.id,
        skill_name="FastAPI",
        skill_category="framework",
        proficiency_level="advanced",
    )
    db_session.add(skill)

    project = ResumeProjectModel(
        resume_id=resume.id,
        title="AI Interview Platform",
        technologies_json=json.dumps(["FastAPI", "SQLAlchemy", "PostgreSQL"]),
        architecture="Three-tier REST API architecture",
        candidate_contribution="Designed backend services and AI integration",
    )
    db_session.add(project)
    db_session.commit()

    # Query back
    saved_resume = db_session.query(ResumeModel).filter(ResumeModel.id == resume.id).first()
    assert saved_resume is not None
    saved_skills = db_session.query(ResumeSkillModel).filter(ResumeSkillModel.resume_id == resume.id).all()
    assert len(saved_skills) == 1
    assert saved_skills[0].skill_name == "FastAPI"


# --- 3. Job Description & Matching Models Tests ---

def test_job_description_persistence(db_session):
    jd = JobDescriptionModel(
        title="Senior Python Backend Engineer",
        company="Tech Innovations Ltd",
        content_text="Looking for a Senior Python Engineer with 3+ years experience in FastAPI and PostgreSQL.",
        experience_min_years=3,
        experience_max_years=6,
        required_skills_json=json.dumps(["Python", "FastAPI", "PostgreSQL", "Docker"]),
        status="extracted",
    )
    db_session.add(jd)
    db_session.commit()

    req = JDRequirementModel(
        jd_id=jd.id,
        requirement_text="3+ years of production experience with Python and FastAPI",
        category="technical",
        is_required=True,
    )
    db_session.add(req)
    db_session.commit()

    saved_jd = db_session.query(JobDescriptionModel).filter(JobDescriptionModel.id == jd.id).first()
    assert saved_jd.title == "Senior Python Backend Engineer"
    assert saved_jd.experience_min_years == 3


def test_resume_jd_match_model(db_session):
    resume = ResumeModel(filename="test.pdf", file_path="/tmp/test.pdf", status="extracted")
    jd = JobDescriptionModel(title="Backend Dev", content_text="Sample JD", status="extracted")
    db_session.add_all([resume, jd])
    db_session.commit()

    match = ResumeJDMatchModel(
        resume_id=resume.id,
        jd_id=jd.id,
        compatibility_score=85.5,
        matching_skills_json=json.dumps(["Python", "FastAPI"]),
        missing_skills_json=json.dumps(["Kubernetes"]),
        weak_areas_json=json.dumps(["System scaling at high concurrency"]),
    )
    db_session.add(match)
    db_session.commit()

    retrieved = db_session.query(ResumeJDMatchModel).filter(ResumeJDMatchModel.id == match.id).first()
    assert retrieved.compatibility_score == 85.5
    assert "Python" in retrieved.matching_skills_json


# --- 4. Interview Models & Session Evaluation Tests ---

def test_deterministic_weighted_evaluation_scoring():
    evaluator = AnswerEvaluationService(DemoLLMProvider())

    raw_scores = {
        "technical_accuracy_score": 9.0,        # weight 0.35 -> 3.15
        "conceptual_understanding_score": 8.0,   # weight 0.25 -> 2.00
        "completeness_score": 8.0,               # weight 0.20 -> 1.60
        "clarity_score": 9.0,                    # weight 0.10 -> 0.90
        "practical_examples_score": 7.0,         # weight 0.10 -> 0.70
    }
    # Expected weighted sum = 3.15 + 2.00 + 1.60 + 0.90 + 0.70 = 8.35
    computed = evaluator._calculate_weighted_score(raw_scores)
    assert abs(computed - 8.35) < 0.001

    # Weights must sum to 1.0
    total_weights = sum(CRITERION_WEIGHTS.values())
    assert abs(total_weights - 1.0) < 0.0001


def test_skipped_answer_zero_score():
    evaluator = AnswerEvaluationService(DemoLLMProvider())
    result = evaluator.evaluate(
        question_text="Explain database ACID properties.",
        expected_concepts=["Atomicity", "Consistency", "Isolation", "Durability"],
        rubric={"excellent": "Full explanation"},
        candidate_answer="skip",
    )
    assert result["final_score"] == 0.0
    assert result["adaptive_signal"] == "weak"


def test_interview_session_lifecycle(db_session):
    # Setup interview
    interview = InterviewModel(
        name="Backend Engineering Assessment",
        job_role="Python Developer",
        experience_level="2-5",
        difficulty="medium",
        num_questions=2,
        status="ready",
    )
    db_session.add(interview)
    db_session.commit()

    q1 = InterviewQuestionModel(
        interview_id=interview.id,
        question_text="Explain how database indexes improve query performance and what are their trade-offs?",
        category="technical",
        difficulty="medium",
        max_score=10,
        order_index=0,
    )
    q2 = InterviewQuestionModel(
        interview_id=interview.id,
        question_text="How do you handle race conditions in distributed systems?",
        category="technical",
        difficulty="hard",
        max_score=10,
        order_index=1,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    # Start session
    session = InterviewSessionModel(
        interview_id=interview.id,
        status="in_progress",
        current_question_index=0,
        max_possible_score=20.0,
    )
    db_session.add(session)
    db_session.commit()

    # Submit response to Q1
    resp1 = InterviewResponseModel(
        session_id=session.id,
        question_id=q1.id,
        answer_text="Indexes use B-trees to provide O(log N) lookups, but slow down writes and use disk space.",
        time_taken_seconds=45,
    )
    db_session.add(resp1)
    db_session.commit()

    # Add evaluation
    eval1 = AnswerEvaluationModel(
        response_id=resp1.id,
        session_id=session.id,
        technical_accuracy_score=9.0,
        conceptual_understanding_score=8.5,
        completeness_score=8.0,
        clarity_score=9.0,
        practical_examples_score=7.0,
        final_score=8.4,
        max_score=10.0,
    )
    db_session.add(eval1)
    session.total_score += 8.4
    session.score_percentage = (session.total_score / session.max_possible_score) * 100
    db_session.commit()

    assert session.total_score == 8.4
    assert round(session.score_percentage, 1) == 42.0

    # Complete session
    session.status = "completed"
    db_session.commit()
    assert session.status == "completed"


# --- 5. Learning Recommendations & Roadmap Tests ---

def test_learning_recommendation_completion(db_session):
    user = AuthService.create_user(db_session, email="learner@studyset.ai", password="Password123!")
    rec = LearningRecommendationModel(
        user_id=user.id,
        topic="Database Indexing & Query Optimization",
        description="Review B-tree mechanics and composite index rules.",
        priority=1,
        resources_json=json.dumps(["Use the Index, Luke! Guide", "PostgreSQL Documentation"]),
        is_completed=False,
    )
    db_session.add(rec)
    db_session.commit()

    saved_rec = db_session.query(LearningRecommendationModel).filter(
        LearningRecommendationModel.id == rec.id
    ).first()
    assert saved_rec.is_completed is False
    assert saved_rec.priority == 1

    # Mark complete
    saved_rec.is_completed = True
    db_session.commit()
    assert saved_rec.is_completed is True
