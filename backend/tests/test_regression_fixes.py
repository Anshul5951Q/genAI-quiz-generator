import io
import json
import uuid

import pytest
from pptx import Presentation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import Base
from app.models.attempt import QuizAttemptModel
from app.models.quiz import OptionModel, QuestionModel, QuizModel
from app.schemas.attempt import AnswerSubmissionItem, AttemptSubmissionRequest
from app.schemas.quiz import QuizGenerateRequest
from app.services.document_parser import DocumentParser, DocumentParserError
from app.services.export_service import ExportService
from app.services.llm_provider import BaseLLMProvider
from app.services.question_generator import QuestionGenerator
from app.services.question_validator import QuestionValidator
from app.services.quiz_service import QuizService, QuizServiceError
from app.services.scoring_service import ScoringService
from app.services.text_chunker import TextChunk


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


class MockConstantLLMProvider(BaseLLMProvider):
    """Mock provider that always returns the exact same question to simulate duplicate generator outputs."""

    def __init__(self, question_data: dict):
        self.question_data = question_data

    def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
        if "validate" in prompt.lower() or "verdict" in prompt.lower():
            return json.dumps({
                "supported_by_source": True,
                "single_best_answer": True,
                "distractors_valid": True,
                "explanation_valid": True,
                "ambiguity_detected": False,
                "verdict": "PASS",
                "issues": [],
            })
        return json.dumps(self.question_data)


# ---------------------------------------------------------------------------
# Test 1: Five identical questions returned by the generator are rejected/reduced
# ---------------------------------------------------------------------------
def test_1_five_identical_questions_rejected_or_reduced():
    constant_question = {
        "question_text": "What is the primary role of the CPU program counter?",
        "options": [
            {"option_letter": "A", "option_text": "Holds the address of the next instruction to be fetched", "is_correct": True},
            {"option_letter": "B", "option_text": "Performs integer addition and subtraction", "is_correct": False},
            {"option_letter": "C", "option_text": "Stores intermediate floating point results", "is_correct": False},
            {"option_letter": "D", "option_text": "Manages virtual memory page table swaps", "is_correct": False},
        ],
        "explanation": "The program counter contains the memory address of the next sequential instruction.",
        "evidence": "The program counter holds the memory address of the next instruction to be fetched.",
        "difficulty": "medium",
        "topic": "Architecture",
        "distractor_rationale": "ALU and FPU options describe other CPU components.",
    }

    mock_llm = MockConstantLLMProvider(constant_question)
    generator = QuestionGenerator(mock_llm)

    chunks = [
        TextChunk(
            chunk_index=0,
            text="The program counter holds the memory address of the next instruction to be fetched.",
            page_number=1,
            char_count=85,
            token_estimate=21,
        )
    ]

    # Request 5 questions from a generator that continually outputs the identical MCQ
    questions, summary = generator.generate_quiz_questions(chunks, num_questions=5)

    # Must be reduced to exactly 1 question, never duplicated to 5
    assert len(questions) == 1
    assert summary.rejected_count > 0
    assert questions[0]["question_text"] == "What is the primary role of the CPU program counter?"


# ---------------------------------------------------------------------------
# Test 2: Duplicate questions with different IDs are rejected
# ---------------------------------------------------------------------------
def test_2_duplicate_questions_with_different_ids():
    source = "RISC-V architecture defines 32 general-purpose integer registers named x0 through x31."

    q1 = {
        "id": str(uuid.uuid4()),
        "question_text": "How many general-purpose integer registers are defined in the standard RISC-V base architecture?",
        "options": [
            {"id": str(uuid.uuid4()), "option_letter": "A", "option_text": "32 registers named x0 through x31", "is_correct": True},
            {"id": str(uuid.uuid4()), "option_letter": "B", "option_text": "16 registers named r0 through r15", "is_correct": False},
            {"id": str(uuid.uuid4()), "option_letter": "C", "option_text": "64 registers named reg0 through reg63", "is_correct": False},
            {"id": str(uuid.uuid4()), "option_letter": "D", "option_text": "8 registers named a0 through a7", "is_correct": False},
        ],
        "explanation": "Standard RISC-V specifies 32 integer registers x0-x31.",
        "evidence": "RISC-V architecture defines 32 general-purpose integer registers named x0 through x31.",
        "difficulty": "easy",
    }

    # q2 has completely different IDs, but identical normalized question stem
    q2 = {
        "id": str(uuid.uuid4()),
        "question_text": "How many general-purpose integer registers are defined in the standard RISC-V base architecture?",
        "options": [
            {"id": str(uuid.uuid4()), "option_letter": "A", "option_text": "32 registers named x0 through x31", "is_correct": True},
            {"id": str(uuid.uuid4()), "option_letter": "B", "option_text": "16 registers named r0 through r15", "is_correct": False},
            {"id": str(uuid.uuid4()), "option_letter": "C", "option_text": "64 registers named reg0 through reg63", "is_correct": False},
            {"id": str(uuid.uuid4()), "option_letter": "D", "option_text": "8 registers named a0 through a7", "is_correct": False},
        ],
        "explanation": "Standard RISC-V specifies 32 integer registers x0-x31.",
        "evidence": "RISC-V architecture defines 32 general-purpose integer registers named x0 through x31.",
        "difficulty": "easy",
    }

    verdict, issues, _ = QuestionValidator.evaluate_question(
        question=q2,
        source_text=source,
        existing_questions=[q1],
        run_semantic=False,
    )

    assert verdict == "reject"
    assert any("identical question stem" in iss.lower() for iss in issues)


# ---------------------------------------------------------------------------
# Test 3: Similar but legitimately distinct questions are accepted
# ---------------------------------------------------------------------------
def test_3_similar_but_distinct_questions_accepted():
    source = (
        "In a pipelined CPU, pipeline registers isolate successive stages. "
        "Data hazards occur when an instruction depends on the result of a previous instruction still in the pipeline."
    )

    q1 = {
        "question_text": "What is the primary function of pipeline registers in a processor?",
        "options": [
            {"option_letter": "A", "option_text": "To isolate successive stages and hold intermediate results", "is_correct": True},
            {"option_letter": "B", "option_text": "To replace the main cache hierarchy", "is_correct": False},
            {"option_letter": "C", "option_text": "To perform branch prediction arithmetic", "is_correct": False},
            {"option_letter": "D", "option_text": "To decode microcode instructions", "is_correct": False},
        ],
        "explanation": "Pipeline registers separate execution stages.",
        "evidence": "In a pipelined CPU, pipeline registers isolate successive stages.",
        "difficulty": "medium",
    }

    q2 = {
        "question_text": "Which condition causes a data hazard in an instruction pipeline?",
        "options": [
            {"option_letter": "A", "option_text": "An instruction depends on results from an instruction still in flight", "is_correct": True},
            {"option_letter": "B", "option_text": "A hardware interrupt halts clock oscillation", "is_correct": False},
            {"option_letter": "C", "option_text": "A branch condition changes target addresses", "is_correct": False},
            {"option_letter": "D", "option_text": "Virtual memory pages are evicted to secondary storage", "is_correct": False},
        ],
        "explanation": "Data hazards arise from data dependencies.",
        "evidence": "Data hazards occur when an instruction depends on the result of a previous instruction still in the pipeline.",
        "difficulty": "medium",
    }

    det_check = QuestionValidator.run_deterministic_checks(q2, source_text=source, existing_questions=[q1])
    assert det_check.is_valid is True
    assert len(det_check.issues) == 0


# ---------------------------------------------------------------------------
# Test 4: Questions generated across multiple text chunks preserve page/slide
# ---------------------------------------------------------------------------
def test_4_questions_across_multiple_text_chunks():
    chunks = [
        TextChunk(chunk_index=0, text="Slide 1: Cache hit rate measures cache efficiency.", page_number=1, char_count=50, token_estimate=12),
        TextChunk(chunk_index=1, text="Slide 2: Virtual memory uses translation lookaside buffers.", page_number=2, char_count=60, token_estimate=15),
        TextChunk(chunk_index=2, text="Slide 3: Superscalar processors issue multiple instructions per cycle.", page_number=3, char_count=70, token_estimate=17),
    ]

    class CyclingChunkLLMProvider(BaseLLMProvider):
        def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
            if "validate" in prompt.lower() or "verdict" in prompt.lower():
                return json.dumps({"supported_by_source": True, "single_best_answer": True, "distractors_valid": True, "explanation_valid": True, "ambiguity_detected": False, "verdict": "PASS", "issues": []})

            if "Page 1" in prompt:
                return json.dumps({
                    "question_text": "What metric evaluates cache performance on Slide 1?",
                    "options": [
                        {"option_letter": "A", "option_text": "Cache hit rate", "is_correct": True},
                        {"option_letter": "B", "option_text": "Bus clock frequency", "is_correct": False},
                        {"option_letter": "C", "option_text": "TLB miss count", "is_correct": False},
                        {"option_letter": "D", "option_text": "Core voltage drop", "is_correct": False},
                    ],
                    "explanation": "Cache hit rate evaluates performance.",
                    "evidence": "Cache hit rate measures cache efficiency.",
                    "difficulty": "easy",
                })
            elif "Page 2" in prompt:
                return json.dumps({
                    "question_text": "Which structure accelerates virtual address translation on Slide 2?",
                    "options": [
                        {"option_letter": "A", "option_text": "Translation lookaside buffers", "is_correct": True},
                        {"option_letter": "B", "option_text": "Direct memory access controller", "is_correct": False},
                        {"option_letter": "C", "option_text": "Write buffer fifo", "is_correct": False},
                        {"option_letter": "D", "option_text": "Instruction reorder buffer", "is_correct": False},
                    ],
                    "explanation": "TLB accelerates translation.",
                    "evidence": "Virtual memory uses translation lookaside buffers.",
                    "difficulty": "medium",
                })
            else:
                return json.dumps({
                    "question_text": "How do superscalar architectures achieve parallelism on Slide 3?",
                    "options": [
                        {"option_letter": "A", "option_text": "By issuing multiple instructions per clock cycle", "is_correct": True},
                        {"option_letter": "B", "option_text": "By executing microcode in serial order", "is_correct": False},
                        {"option_letter": "C", "option_text": "By lowering memory bus clock width", "is_correct": False},
                        {"option_letter": "D", "option_text": "By disabling pipeline registers", "is_correct": False},
                    ],
                    "explanation": "Superscalar issues multiple instructions per cycle.",
                    "evidence": "Superscalar processors issue multiple instructions per cycle.",
                    "difficulty": "hard",
                })

    generator = QuestionGenerator(CyclingChunkLLMProvider())
    questions, summary = generator.generate_quiz_questions(chunks, num_questions=3)

    assert len(questions) == 3
    pages = [q["source_page"] for q in questions]
    assert pages == [1, 2, 3]


# ---------------------------------------------------------------------------
# Test 5: Questions grounded in actual extracted PPTX content
# ---------------------------------------------------------------------------
def test_5_pptx_extraction_and_grounding():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Computer Architecture: Cache Coherence"
    slide.placeholders[1].text = "MESI protocol maintains cache consistency with four states: Modified, Exclusive, Shared, Invalid."

    pptx_io = io.BytesIO()
    prs.save(pptx_io)
    pptx_bytes = pptx_io.getvalue()

    result = DocumentParser.parse_pptx_bytes(pptx_bytes, filename="cache_coherence.pptx")
    assert result.source_type == "pptx"
    assert len(result.pages) == 1
    assert "MESI protocol" in result.full_text
    assert result.pages[0].page_number == 1


# ---------------------------------------------------------------------------
# Test 6: Empty, unreadable, or image-only PPT input rejected with clear error
# ---------------------------------------------------------------------------
def test_6_empty_or_image_only_pptx_rejected():
    prs = Presentation()
    # Add a blank slide with no text shapes
    blank_layout = prs.slide_layouts[6]
    prs.slides.add_slide(blank_layout)

    empty_io = io.BytesIO()
    prs.save(empty_io)
    empty_bytes = empty_io.getvalue()

    with pytest.raises(DocumentParserError, match="No usable text found in this presentation"):
        DocumentParser.parse_pptx_bytes(empty_bytes, filename="blank_deck.pptx")

    # Also test completely empty byte buffer
    with pytest.raises(DocumentParserError, match="Presentation file is empty"):
        DocumentParser.parse_pptx_bytes(b"", filename="zero.pptx")


# ---------------------------------------------------------------------------
# Test 7: Gemini/API failure without silently returning demo questions
# ---------------------------------------------------------------------------
def test_7_api_failure_does_not_silently_return_demo(in_memory_db, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    req = QuizGenerateRequest(
        title="Operating Systems Memory Management",
        source_text="Paging avoids external fragmentation and the need for contiguous allocation of the physical memory.",
        source_type="pasted",
        num_questions=5,
        use_demo_mode=False,
    )

    # When no AI API key is configured and use_demo_mode is False,
    # generate_quiz must raise QuizServiceError and NEVER return demo questions silently
    with pytest.raises(QuizServiceError, match="No AI provider API key is configured"):
        QuizService.generate_quiz(in_memory_db, req)

    # Database must have 0 persisted quizzes
    assert in_memory_db.query(QuizModel).count() == 0


# ---------------------------------------------------------------------------
# Test 8: Insufficient valid questions after bounded retries
# ---------------------------------------------------------------------------
def test_8_bounded_retries_stop_without_padding():
    class InvalidFailingLLMProvider(BaseLLMProvider):
        def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
            # Returns an invalid question missing required options
            return json.dumps({
                "question_text": "Bad question",
                "options": [],
                "explanation": "",
                "evidence": "",
            })

    generator = QuestionGenerator(InvalidFailingLLMProvider())
    chunks = [TextChunk(chunk_index=0, text="Sample text for testing bounded retry limitations.", page_number=1, char_count=50, token_estimate=12)]

    questions, summary = generator.generate_quiz_questions(chunks, num_questions=5)

    # Should not crash, should not loop infinitely, and should return 0 valid questions
    assert len(questions) == 0
    assert summary.rejected_count > 0


# ---------------------------------------------------------------------------
# Test 9: Normal workspace opening without unwanted sample quiz creation
# ---------------------------------------------------------------------------
def test_9_normal_workspace_no_unwanted_seeding(in_memory_db):
    # Calling list_quizzes on an empty workspace should return [] and NOT auto-seed sample quizzes
    summaries = QuizService.list_quizzes(in_memory_db)
    assert len(summaries) == 0
    assert in_memory_db.query(QuizModel).count() == 0


# ---------------------------------------------------------------------------
# Test 10: Explicit “Try sample study set” behavior
# ---------------------------------------------------------------------------
def test_10_explicit_sample_quiz_behavior(in_memory_db):
    sample_text = (
        "Distributed systems achieve fault tolerance through replication and consensus algorithms. "
        "The Raft consensus algorithm organizes time into terms of arbitrary length, numbered with consecutive integers. "
        "Each term begins with an election, in which one or more candidates attempt to become leader. "
        "If a candidate wins the election, then it serves as leader for the rest of the term. "
        "A leader accepts log entries from clients, replicates them across other servers, and tells servers when it is safe to apply log entries to their state machines. "
        "Safety in Raft is guaranteed through the Leader Completeness Property: if a log entry is committed in a given term, then that entry will be present in the logs of the leaders for all higher-numbered terms."
    )

    req = QuizGenerateRequest(
        title="Distributed Systems & Raft Consensus",
        source_text=sample_text,
        source_type="pasted",
        num_questions=5,
        use_demo_mode=True,
    )

    quiz, summary = QuizService.generate_quiz(in_memory_db, req)

    assert quiz.is_demo is True
    assert quiz.quiz_origin == "demo"
    assert len(quiz.questions) == 5

    # Verify that all 5 questions are distinct (not identical duplicates!)
    stems = [q.question_text for q in quiz.questions]
    assert len(set(stems)) == 5


# ---------------------------------------------------------------------------
# Test 11: Persistence and retrieval of real and demo quizzes
# ---------------------------------------------------------------------------
def test_11_real_and_demo_quiz_persistence_separation(in_memory_db):
    # 1. Create a demo quiz
    demo_quiz = QuizModel(
        title="Demo Quiz Set",
        source_type="pasted",
        source_text_length=100,
        is_demo=True,
        quiz_origin="demo",
    )
    in_memory_db.add(demo_quiz)

    # 2. Create a real document generated quiz
    real_quiz = QuizModel(
        title="Computer Architecture Lecture 4",
        source_type="pptx",
        source_filename="lecture4.pptx",
        source_text_length=5000,
        is_demo=False,
        quiz_origin="document_generated",
    )
    in_memory_db.add(real_quiz)
    in_memory_db.commit()

    summaries = QuizService.list_quizzes(in_memory_db)
    assert len(summaries) == 2

    demo_sum = next(s for s in summaries if s.id == demo_quiz.id)
    real_sum = next(s for s in summaries if s.id == real_quiz.id)

    assert demo_sum.is_demo is True
    assert demo_sum.quiz_origin == "demo"

    assert real_sum.is_demo is False
    assert real_sum.quiz_origin == "document_generated"


# ---------------------------------------------------------------------------
# Test 12: PDF export containing only correct distinct questions
# ---------------------------------------------------------------------------
def test_12_pdf_export_contains_distinct_questions(in_memory_db):
    quiz = QuizModel(
        title="Advanced Microprocessor Systems",
        source_type="pdf",
        difficulty="hard",
        is_demo=False,
        quiz_origin="document_generated",
    )
    in_memory_db.add(quiz)
    in_memory_db.flush()

    for i in range(1, 4):
        q = QuestionModel(
            quiz_id=quiz.id,
            question_text=f"Distinct Microprocessor Question {i}?",
            explanation=f"Explanation for question {i}.",
            evidence=f"Evidence text for question {i}.",
            order_index=i,
        )
        in_memory_db.add(q)
        in_memory_db.flush()

        for letter in ["A", "B", "C", "D"]:
            opt = OptionModel(
                question_id=q.id,
                option_letter=letter,
                option_text=f"Option {letter} text for question {i}",
                is_correct=(letter == "A"),
            )
            in_memory_db.add(opt)

    in_memory_db.commit()

    student_pdf = ExportService.generate_quiz_pdf(quiz, include_answers=False)
    assert student_pdf.startswith(b"%PDF-")
    assert len(student_pdf) > 1000

    instructor_pdf = ExportService.generate_quiz_pdf(quiz, include_answers=True)
    assert instructor_pdf.startswith(b"%PDF-")
    assert len(instructor_pdf) > 1000


# ---------------------------------------------------------------------------
# Test 13: Answer-key confidentiality and scoring correctness
# ---------------------------------------------------------------------------
def test_13_answer_key_confidentiality_and_scoring(in_memory_db):
    quiz = QuizModel(
        title="Deterministic Grading Audit",
        source_type="pasted",
        difficulty="medium",
        is_demo=False,
        quiz_origin="document_generated",
    )
    in_memory_db.add(quiz)
    in_memory_db.flush()

    q_models = []
    correct_options = {}

    for i in range(1, 6):
        q = QuestionModel(
            quiz_id=quiz.id,
            question_text=f"Exam Question {i}?",
            explanation=f"Confidential explanation for question {i}.",
            evidence=f"Confidential evidence for question {i}.",
            order_index=i,
        )
        in_memory_db.add(q)
        in_memory_db.flush()
        q_models.append(q)

        for letter in ["A", "B", "C", "D"]:
            is_corr = (letter == "B")
            opt = OptionModel(
                question_id=q.id,
                option_letter=letter,
                option_text=f"Option {letter}",
                is_correct=is_corr,
            )
            in_memory_db.add(opt)
            in_memory_db.flush()
            if is_corr:
                correct_options[q.id] = opt.id

    in_memory_db.commit()

    # 1. Test Answer Key Confidentiality
    taking_view = QuizService.get_quiz_taking_view(in_memory_db, quiz.id)
    for q_view in taking_view.questions:
        # Must not expose explanation or evidence
        assert not hasattr(q_view, "explanation")
        assert not hasattr(q_view, "evidence")
        for opt_view in q_view.options:
            # Must not expose is_correct
            assert not hasattr(opt_view, "is_correct")

    # 2. Test Scoring Correctness (e.g., answer 3 correctly, 2 incorrectly)
    attempt = QuizAttemptModel(quiz_id=quiz.id, quiz_version=quiz.version, status="in_progress")
    in_memory_db.add(attempt)
    in_memory_db.commit()
    in_memory_db.refresh(attempt)

    user_answers = []
    for idx, q in enumerate(q_models):
        if idx < 3:
            user_answers.append(AnswerSubmissionItem(question_id=q.id, selected_option_id=correct_options[q.id]))
        else:
            wrong_opt = next(o for o in q.options if not o.is_correct)
            user_answers.append(AnswerSubmissionItem(question_id=q.id, selected_option_id=wrong_opt.id))

    attempt_req = AttemptSubmissionRequest(answers=user_answers)
    attempt_res = ScoringService.calculate_attempt_results(in_memory_db, attempt, attempt_req)

    # 3 out of 5 = 60.0%
    assert attempt_res.score == 3
    assert attempt_res.total_questions == 5
    assert attempt_res.score_percentage == 60.0


# ---------------------------------------------------------------------------
# Optional: Live Gemini Integration Test (Executed only if key is configured)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not settings.has_gemini_key,
    reason="GEMINI_API_KEY is not configured in backend/.env; skipping live Gemini API integration call.",
)
def test_live_gemini_generation():
    from app.services.llm_provider import GeminiLLMProvider
    provider = GeminiLLMProvider()
    response = provider.generate("Output a JSON object with key 'status' equal to 'live_ok'.")
    data = json.loads(response)
    assert data.get("status") == "live_ok"


@pytest.mark.skipif(
    not settings.has_groq_key,
    reason="GROQ_API_KEY is not configured in backend/.env; skipping live Groq API integration call.",
)
def test_live_groq_generation():
    from app.services.llm_provider import GroqLLMProvider
    provider = GroqLLMProvider()
    response = provider.generate("Output a JSON object with key 'status' equal to 'live_groq_ok'.")
    data = json.loads(response)
    assert data.get("status") == "live_groq_ok"


# ---------------------------------------------------------------------------
# Test: ResilientLLMProvider failover from primary to fallback
# ---------------------------------------------------------------------------
def test_resilient_llm_provider_failover():
    from app.services.llm_provider import LLMProviderError, ResilientLLMProvider

    class FailingPrimary(BaseLLMProvider):
        def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
            raise LLMProviderError("Primary Gemini rate limit 429 quota exhausted")

    class WorkingFallback(BaseLLMProvider):
        def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
            return json.dumps({"source": "groq_fallback", "success": True})

    resilient = ResilientLLMProvider(primary=FailingPrimary(), fallback=WorkingFallback())
    result = resilient.generate("Generate question")
    parsed = json.loads(result)

    assert parsed.get("source") == "groq_fallback"
    assert parsed.get("success") is True


def test_resilient_llm_provider_both_fail():
    from app.services.llm_provider import LLMProviderError, ResilientLLMProvider

    class FailingPrimary(BaseLLMProvider):
        def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
            raise LLMProviderError("Primary error")

    class FailingFallback(BaseLLMProvider):
        def generate(self, prompt: str, system_instruction: str | None = None, response_schema: dict | None = None) -> str:
            raise LLMProviderError("Fallback error")

    resilient = ResilientLLMProvider(primary=FailingPrimary(), fallback=FailingFallback())
    with pytest.raises(LLMProviderError, match="Both primary"):
        resilient.generate("Generate question")


# ---------------------------------------------------------------------------
# Test: get_llm_provider handles Groq as primary or fallback
# ---------------------------------------------------------------------------
def test_get_llm_provider_resolution(monkeypatch):
    from app.services.llm_provider import DemoLLMProvider, GroqLLMProvider, ResilientLLMProvider, get_llm_provider

    # 1. Force demo
    demo_provider = get_llm_provider(force_demo=True)
    assert isinstance(demo_provider, DemoLLMProvider)

    # 2. Only Groq configured
    monkeypatch.setattr(settings, "LLM_PRIMARY_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test123")
    with monkeypatch.context() as m:
        # Mock Groq client and ensure Ollama connectivity check returns False during unit test
        from unittest.mock import MagicMock
        m.setattr("groq.Groq", MagicMock())
        try:
            from app.services.ollama_provider import OllamaProvider
            m.setattr(OllamaProvider, "_check_connectivity", lambda self: False)
        except Exception:
            pass
        groq_provider = get_llm_provider(force_demo=False)
        assert isinstance(groq_provider, GroqLLMProvider)

    # 3. Both Gemini and Groq configured -> ResilientLLMProvider
    monkeypatch.setattr(settings, "LLM_PRIMARY_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIzaSyTest123")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test123")
    with monkeypatch.context() as m:
        import sys
        mock_google = MagicMock()
        m.setitem(sys.modules, "google.genai", mock_google)
        m.setattr("groq.Groq", MagicMock())
        try:
            from app.services.ollama_provider import OllamaProvider
            m.setattr(OllamaProvider, "_check_connectivity", lambda self: False)
        except Exception:
            pass
        resilient_provider = get_llm_provider(force_demo=False)
        assert isinstance(resilient_provider, ResilientLLMProvider)
        assert isinstance(resilient_provider.fallback, GroqLLMProvider)

