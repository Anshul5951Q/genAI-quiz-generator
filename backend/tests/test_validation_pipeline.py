from app.services.llm_provider import BaseLLMProvider
from app.services.question_validator import QuestionValidator


class MockLLM(BaseLLMProvider):
    def __init__(self, response_text: str):
        self.response_text = response_text

    def generate(self, prompt: str, system_instruction: str = None, response_schema=None) -> str:
        return self.response_text


def test_deterministic_valid_question():
    source = "The quick brown fox jumps over the lazy dog."
    question = {
        "question_text": "What action does the brown fox perform?",
        "options": [
            {"option_letter": "A", "option_text": "Jumps over the lazy dog", "is_correct": True},
            {"option_letter": "B", "option_text": "Runs away into the forest", "is_correct": False},
            {"option_letter": "C", "option_text": "Sleeps under the tree", "is_correct": False},
            {"option_letter": "D", "option_text": "Barks at the moon", "is_correct": False}
        ],
        "explanation": "The text explicitly states that the fox jumps over the lazy dog.",
        "evidence": "jumps over the lazy dog",
        "difficulty": "easy"
    }

    res = QuestionValidator.run_deterministic_checks(question, source)
    assert res.is_valid is True
    assert len(res.issues) == 0


def test_deterministic_invalid_option_count():
    source = "Some source text."
    question = {
        "question_text": "Why is the sky blue?",
        "options": [
            {"option_letter": "A", "option_text": "Rayleigh scattering", "is_correct": True},
            {"option_letter": "B", "option_text": "Ocean reflection", "is_correct": False}
        ],
        "explanation": "Valid explanation.",
        "evidence": "Some source text",
        "difficulty": "medium"
    }

    res = QuestionValidator.run_deterministic_checks(question, source)
    assert res.is_valid is False
    assert any("exactly 4 options" in iss for iss in res.issues)


def test_deterministic_duplicate_options_and_forbidden_phrases():
    source = "Python uses indentation to define code blocks."
    question = {
        "question_text": "How does Python define code blocks?",
        "options": [
            {"option_letter": "A", "option_text": "Indentation", "is_correct": True},
            {"option_letter": "B", "option_text": "Indentation", "is_correct": False},  # duplicate text
            {"option_letter": "C", "option_text": "All of the above", "is_correct": False},  # forbidden phrase
            {"option_letter": "D", "option_text": "Curly braces", "is_correct": False}
        ],
        "explanation": "Valid explanation.",
        "evidence": "Python uses indentation",
        "difficulty": "easy"
    }

    res = QuestionValidator.run_deterministic_checks(question, source)
    assert res.is_valid is False
    assert any("Duplicate option text" in iss for iss in res.issues)
    assert any("all/none of the above" in iss for iss in res.issues)


def test_deterministic_multiple_or_zero_correct_answers():
    source = "Source text about physics."
    question = {
        "question_text": "What is the unit of force?",
        "options": [
            {"option_letter": "A", "option_text": "Newton", "is_correct": True},
            {"option_letter": "B", "option_text": "Joule", "is_correct": True},  # Two correct answers!
            {"option_letter": "C", "option_text": "Watt", "is_correct": False},
            {"option_letter": "D", "option_text": "Pascal", "is_correct": False}
        ],
        "explanation": "Newton is the SI unit.",
        "evidence": "Source text about physics.",
        "difficulty": "medium"
    }

    res = QuestionValidator.run_deterministic_checks(question, source)
    assert res.is_valid is False
    assert any("Must have exactly 1 correct option" in iss for iss in res.issues)


def test_near_duplicate_detection():
    source = "Source material regarding operating system concurrency."
    existing = [
        {"question_text": "What synchronization mechanism prevents race conditions in critical sections?"}
    ]
    new_q = {
        "question_text": "What synchronization mechanism prevents race conditions in a critical section?",  # near duplicate
        "options": [
            {"option_letter": "A", "option_text": "Mutex", "is_correct": True},
            {"option_letter": "B", "option_text": "Semaphore", "is_correct": False},
            {"option_letter": "C", "option_text": "Spinlock", "is_correct": False},
            {"option_letter": "D", "option_text": "Barrier", "is_correct": False}
        ],
        "explanation": "Mutex lock guarantees mutual exclusion.",
        "evidence": "operating system concurrency",
        "difficulty": "medium"
    }

    res = QuestionValidator.run_deterministic_checks(new_q, source, existing_questions=existing)
    assert any("Near-duplicate" in iss for iss in res.issues)


def test_semantic_review_rejection_policy():
    source = "Newtonian mechanics describes motion of bodies."
    question = {
        "question_text": "What does Newtonian mechanics describe?",
        "options": [
            {"option_letter": "A", "option_text": "Motion of bodies", "is_correct": True},
            {"option_letter": "B", "option_text": "Quantum teleportation", "is_correct": False},
            {"option_letter": "C", "option_text": "Relativistic black holes", "is_correct": False},
            {"option_letter": "D", "option_text": "String theory vibrations", "is_correct": False}
        ],
        "explanation": "Described in text.",
        "evidence": "Newtonian mechanics describes motion of bodies.",
        "difficulty": "easy"
    }

    # Mock semantic validation returning REJECT
    reject_json = """
    {
      "supported_by_source": false,
      "single_best_answer": false,
      "distractors_valid": false,
      "explanation_valid": false,
      "ambiguity_detected": true,
      "verdict": "REJECT",
      "issues": ["Severe contradiction with supplied source excerpt"]
    }
    """
    mock_llm = MockLLM(reject_json)

    verdict, issues, sem_result = QuestionValidator.evaluate_question(
        question=question,
        source_text=source,
        llm_provider=mock_llm,
        run_semantic=True
    )

    assert verdict == "reject"
    assert any("Severe contradiction" in iss for iss in issues)
