import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.quiz import OptionModel, QuestionModel, QuizModel
from app.schemas.batch import BatchCreate, BatchMemberCreate, BatchUpdate
from app.schemas.blueprint import DifficultyDistribution, ExamBlueprint
from app.schemas.publication import (
    PublicationCreate,
    StudentAnswerItem,
    StudentAttemptStartRequest,
    StudentAttemptSubmitRequest,
)
from app.schemas.question import OptionUpdate, QuestionUpdate
from app.services.analytics_service import AnalyticsService
from app.services.batch_service import BatchService, BatchServiceError
from app.services.blueprint_service import BlueprintService
from app.services.export_service import ExportService
from app.services.google_forms_service import GoogleFormsService
from app.services.publication_service import PublicationService, PublicationServiceError
from app.services.question_bank_service import QuestionBankService
from app.services.quiz_service import QuizService, QuizServiceError
from app.services.text_chunker import TextChunk
from app.services.version_service import VersionService


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_approved_quiz(test_db):
    """Creates a sample quiz with 3 valid questions."""
    quiz = QuizModel(
        title="Distributed Systems Foundations",
        source_type="pasted",
        source_text_length=1200,
        difficulty="mixed",
        target_count=3,
        topic_focus="Consensus",
        status="draft",
        approval_status="approved",
        version=1,
    )
    test_db.add(quiz)
    test_db.flush()

    for idx in range(1, 4):
        q = QuestionModel(
            quiz_id=quiz.id,
            question_text=f"What is key property #{idx} of the Raft leader election mechanism?",
            explanation=f"Raft ensures safe transitions through term numbers (property {idx}).",
            evidence=f"Terms act as logical clocks in Raft (point {idx}).",
            topic="Consensus",
            difficulty="medium",
            validation_status="pass",
            order_index=idx,
        )
        test_db.add(q)
        test_db.flush()

        for letter in ["A", "B", "C", "D"]:
            opt = OptionModel(
                question_id=q.id,
                option_letter=letter,
                option_text=f"Property {letter} for question {idx}",
                is_correct=(letter == "A"),
            )
            test_db.add(opt)

    test_db.commit()
    test_db.refresh(quiz)
    return quiz


# ===========================================================================
# 1. BATCH MANAGEMENT TESTS
# ===========================================================================


def test_batch_creation_and_join_code(test_db):
    req = BatchCreate(name="Computer Science 2026", description="Morning lecture cohort")
    batch = BatchService.create_batch(test_db, req)

    assert batch.id is not None
    assert batch.name == "Computer Science 2026"
    assert batch.join_code.startswith("BCH-")
    assert not batch.is_archived

    # Disallow blank name
    with pytest.raises(BatchServiceError, match="cannot be empty"):
        BatchService.create_batch(test_db, BatchCreate(name="   "))


def test_batch_enrollment_and_duplicate_prevention(test_db):
    batch = BatchService.create_batch(test_db, BatchCreate(name="Algorithms Section B"))

    # Add member
    member = BatchService.add_member(
        test_db,
        batch.id,
        BatchMemberCreate(learner_name="Alice Smith", learner_email="alice@university.edu", learner_id="STU-001"),
    )
    assert member.id is not None
    assert member.learner_email == "alice@university.edu"

    # Reject duplicate email in same batch
    with pytest.raises(BatchServiceError, match="already enrolled"):
        BatchService.add_member(
            test_db,
            batch.id,
            BatchMemberCreate(learner_name="Alice Duplicate", learner_email="ALICE@university.edu"),
        )


def test_batch_archiving(test_db):
    batch = BatchService.create_batch(test_db, BatchCreate(name="Spring Term 2025"))
    BatchService.update_batch(test_db, batch.id, BatchUpdate(is_archived=True))

    detail = BatchService.get_batch_detail(test_db, batch.id)
    assert detail.is_archived is True

    # Cannot add learners to archived batch
    with pytest.raises(BatchServiceError, match="archived"):
        BatchService.add_member(
            test_db,
            batch.id,
            BatchMemberCreate(learner_name="Late Student", learner_email="late@student.edu"),
        )


# ===========================================================================
# 2. EXAM BLUEPRINT & COVERAGE PLANNING TESTS
# ===========================================================================


def test_blueprint_validation_success():
    bp = ExamBlueprint(
        title="Operating Systems Midterm",
        total_questions=10,
        difficulty_distribution=DifficultyDistribution(easy=3, medium=4, hard=3),
        included_topics=["Virtual Memory", "Process Scheduling"],
    )
    chunks = [
        TextChunk(chunk_index=0, text="Virtual Memory uses Paging to avoid external fragmentation.", page_number=1, char_count=60, token_estimate=15),
        TextChunk(chunk_index=1, text="Process Scheduling algorithms include Round Robin and Multi-Level Feedback.", page_number=2, char_count=75, token_estimate=18),
    ]

    result = BlueprintService.validate_and_plan_coverage(bp, chunks)
    assert result.is_valid is True
    assert len(result.issues) == 0
    assert len(result.coverage_matrix) >= 2


def test_blueprint_contradictory_distribution_rejected():
    # Sum of difficulties is 8, but total_questions requested is 10
    bp = ExamBlueprint(
        title="Contradictory Blueprint",
        total_questions=10,
        difficulty_distribution=DifficultyDistribution(easy=2, medium=4, hard=2),
    )
    chunks = [TextChunk(chunk_index=0, text="Sample text content for assessment blueprint.", page_number=1, char_count=45, token_estimate=10)]

    result = BlueprintService.validate_and_plan_coverage(bp, chunks)
    assert result.is_valid is False
    assert any("Difficulty distribution sum (8) must exactly equal total questions requested (10)" in err for err in result.issues)


# ===========================================================================
# 3. QUESTION REVIEW & REVALIDATION TESTS
# ===========================================================================


def test_question_revalidation_on_edit(test_db, sample_approved_quiz):
    q = sample_approved_quiz.questions[0]
    assert q.validation_status == "pass"

    # Instructor edits options making all options correct (invalid: must have exactly 1 correct option)
    invalid_options = [
        OptionUpdate(id=o.id, option_letter=o.option_letter, option_text=o.option_text, is_correct=True)
        for o in q.options
    ]
    update_data = QuestionUpdate(options=invalid_options)
    updated_q = QuizService.update_question(test_db, sample_approved_quiz.id, q.id, update_data)

    # Revalidation must have triggered and marked question as review/invalid!
    assert updated_q.validation_status in {"review", "reject"}
    issues = json.loads(updated_q.validation_issues)
    assert any("exactly 1 correct option" in iss for iss in issues)


def test_quiz_approval_blocks_rejected_questions(test_db, sample_approved_quiz):
    q = sample_approved_quiz.questions[0]
    q.validation_status = "reject"
    test_db.commit()

    with pytest.raises(QuizServiceError, match="Cannot approve quiz with 1 rejected"):
        QuizService.approve_quiz(test_db, sample_approved_quiz.id)


# ===========================================================================
# 4. PUBLISHING & STUDENT ASSESSMENT TESTS
# ===========================================================================


def test_publication_creation_and_zero_answer_leakage(test_db, sample_approved_quiz):
    batch = BatchService.create_batch(test_db, BatchCreate(name="Distributed Systems Batch A"))
    pub_req = PublicationCreate(
        quiz_id=sample_approved_quiz.id,
        batch_id=batch.id,
        time_limit_minutes=20,
        max_attempts=1,
    )
    pub = PublicationService.create_publication(test_db, pub_req)

    assert pub.id is not None
    assert pub.access_code.startswith("QZ-")

    # Fetch student assessment view
    student_view = PublicationService.get_student_assessment_view(test_db, pub.access_code)
    assert student_view.total_questions == 3

    # ZERO ANSWER KEY LEAKAGE: check question and option objects
    for q in student_view.questions:
        q_dict = q.model_dump()
        assert "explanation" not in q_dict
        assert "evidence" not in q_dict
        for opt in q.options:
            opt_dict = opt.model_dump()
            assert "is_correct" not in opt_dict


def test_student_attempt_lifecycle_and_grading(test_db, sample_approved_quiz):
    batch = BatchService.create_batch(test_db, BatchCreate(name="Networks Batch"))
    BatchService.add_member(
        test_db,
        batch.id,
        BatchMemberCreate(learner_name="Student Bob", learner_email="bob@campus.edu"),
    )

    pub = PublicationService.create_publication(
        test_db,
        PublicationCreate(quiz_id=sample_approved_quiz.id, batch_id=batch.id, time_limit_minutes=15),
    )

    # 1. Start Attempt
    start_resp = PublicationService.start_student_attempt(
        test_db,
        pub.access_code,
        StudentAttemptStartRequest(learner_name="Student Bob", learner_email="bob@campus.edu"),
    )
    assert start_resp.attempt_id is not None

    # 2. Submit Answers: Answer 2 questions correctly (option A) and leave 1 question unanswered
    questions = sample_approved_quiz.questions
    answers = []
    for idx, q in enumerate(questions):
        if idx < 2:
            correct_opt = next(o for o in q.options if o.is_correct)
            answers.append(StudentAnswerItem(question_id=q.id, selected_option_id=correct_opt.id))
        else:
            answers.append(StudentAnswerItem(question_id=q.id, selected_option_id=None))

    submit_req = StudentAttemptSubmitRequest(attempt_id=start_resp.attempt_id, answers=answers)
    result = PublicationService.submit_student_attempt(test_db, pub.access_code, submit_req)

    assert result.score == 2
    assert result.total_questions == 3
    assert result.unanswered_count == 1
    assert result.score_percentage == 66.7


def test_unauthorized_batch_student_blocked(test_db, sample_approved_quiz):
    batch = BatchService.create_batch(test_db, BatchCreate(name="Restricted Batch"))
    pub = PublicationService.create_publication(
        test_db,
        PublicationCreate(quiz_id=sample_approved_quiz.id, batch_id=batch.id),
    )

    # Learner NOT enrolled in this batch tries to take quiz
    with pytest.raises(PublicationServiceError, match="not enrolled in the Batch"):
        PublicationService.start_student_attempt(
            test_db,
            pub.access_code,
            StudentAttemptStartRequest(learner_name="Intruder", learner_email="intruder@external.com"),
        )


# ===========================================================================
# 5. BATCH RESULTS & PERFORMANCE ANALYTICS TESTS
# ===========================================================================


def test_batch_analytics_metrics(test_db, sample_approved_quiz):
    batch = BatchService.create_batch(test_db, BatchCreate(name="Analytics Cohort"))
    for i in range(1, 5):
        BatchService.add_member(
            test_db,
            batch.id,
            BatchMemberCreate(learner_name=f"Learner {i}", learner_email=f"learner{i}@school.edu"),
        )

    pub = PublicationService.create_publication(
        test_db,
        PublicationCreate(quiz_id=sample_approved_quiz.id, batch_id=batch.id),
    )

    # 3 learners submit
    for i in range(1, 4):
        start_res = PublicationService.start_student_attempt(
            test_db,
            pub.access_code,
            StudentAttemptStartRequest(learner_name=f"Learner {i}", learner_email=f"learner{i}@school.edu"),
        )
        # All correct
        answers = [
            StudentAnswerItem(question_id=q.id, selected_option_id=next(o.id for o in q.options if o.is_correct))
            for q in sample_approved_quiz.questions
        ]
        PublicationService.submit_student_attempt(test_db, pub.access_code, StudentAttemptSubmitRequest(attempt_id=start_res.attempt_id, answers=answers))

    analytics = AnalyticsService.get_publication_analytics(test_db, pub.id)
    assert analytics.overview.eligible_learners == 4
    assert analytics.overview.submitted_learners == 3
    assert analytics.overview.completion_rate == 75.0
    assert analytics.overview.average_score_percentage == 100.0
    assert len(analytics.learner_results) == 3


# ===========================================================================
# 6. PARALLEL EXAM VERSIONS (A, B, C) TESTS
# ===========================================================================


def test_parallel_versions_generation_and_scoring(test_db, sample_approved_quiz):
    versions = VersionService.generate_parallel_versions(test_db, sample_approved_quiz.id, ["A", "B", "C"])
    assert len(versions) == 3
    assert {v["version_label"] for v in versions} == {"A", "B", "C"}

    # Total questions preserved
    for v in versions:
        assert v["total_questions"] == 3
        for q in v["questions"]:
            # Exactly 1 option marked correct in each version
            corr = [o for o in q["options"] if o["is_correct"]]
            assert len(corr) == 1


# ===========================================================================
# 7. QUESTION BANK & REUSE PREVENTION TESTS
# ===========================================================================


def test_question_bank_sync_and_reuse_check(test_db, sample_approved_quiz):
    synced = QuestionBankService.sync_quiz_to_question_bank(test_db, sample_approved_quiz.id)
    assert synced == 3

    # Search bank
    results = QuestionBankService.search_question_bank(test_db, topic="Consensus")
    assert len(results) == 3

    # Check reuse detection
    stems = [sample_approved_quiz.questions[0].question_text]
    flags = QuestionBankService.check_reuse_for_batch(test_db, batch_id="any-batch", candidate_stems=stems)
    # Question was used, so it matches with similarity 1.0
    assert len(flags) == 1
    assert flags[0]["similarity"] >= 0.95


# ===========================================================================
# 8. EXPORTS (DOCX & GOOGLE FORMS) TESTS
# ===========================================================================


def test_docx_export(sample_approved_quiz):
    student_docx = ExportService.generate_quiz_docx(sample_approved_quiz, include_answers=False)
    instructor_docx = ExportService.generate_quiz_docx(sample_approved_quiz, include_answers=True)

    assert len(student_docx) > 500
    assert len(instructor_docx) > 500


def test_google_forms_schema_generation(sample_approved_quiz):
    forms_json = GoogleFormsService.export_google_forms_json(sample_approved_quiz)
    parsed = json.loads(forms_json)

    assert "info" in parsed
    assert "batchUpdate" in parsed
    assert len(parsed["batchUpdate"]["requests"]) == 3
    req0 = parsed["batchUpdate"]["requests"][0]
    assert "createItem" in req0
