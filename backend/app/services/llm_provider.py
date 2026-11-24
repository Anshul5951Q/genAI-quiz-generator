import json
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings
from app.core.logging import logger


class LLMProviderError(Exception):
    """User-safe exception for LLM provider errors."""


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        """Generates text/JSON from the LLM."""


class GeminiLLMProvider(BaseLLMProvider):
    """Production Gemini API provider supporting Google's official SDK."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise LLMProviderError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file or use Demo Mode."
            )

        # Initialize modern google-genai SDK
        try:
            from google import genai

            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini SDK: {type(e).__name__}")
            raise LLMProviderError("Failed to initialize Gemini SDK client. Verify your dependencies and API key.")

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        max_attempts = 3
        backoff_delay = 2.0

        for attempt in range(1, max_attempts + 1):
            try:
                from google.genai import types

                config_params: dict[str, Any] = {"response_mime_type": "application/json"}
                if system_instruction:
                    config_params["system_instruction"] = system_instruction

                config = types.GenerateContentConfig(**config_params)
                response = self.client.models.generate_content(model=self.model_name, contents=prompt, config=config)
                if not response or not response.text:
                    raise LLMProviderError("Received empty response from Gemini model.")
                return response.text.strip()

            except Exception as e:
                err_str = str(e).lower()
                logger.warning(f"Gemini API attempt {attempt}/{max_attempts} failed: {type(e).__name__}")

                # Check for quota or auth errors
                if "api_key" in err_str or "unauthorized" in err_str or "403" in err_str:
                    raise LLMProviderError("Invalid or unauthorized Gemini API key. Please check your credentials.")
                if "quota" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                    if attempt == max_attempts:
                        raise LLMProviderError(
                            "Gemini API quota exhausted (Rate limit exceeded). Please try again in a moment."
                        )
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                if "timeout" in err_str or "504" in err_str:
                    if attempt == max_attempts:
                        raise LLMProviderError("Gemini API request timed out. Please try with shorter content.")
                    time.sleep(backoff_delay)
                    continue

                if attempt == max_attempts:
                    raise LLMProviderError(f"Gemini API request failed: {str(e)[:150]}")
                time.sleep(backoff_delay)

        raise LLMProviderError("Failed to generate content after multiple attempts.")


class DemoLLMProvider(BaseLLMProvider):
    """High quality offline demo provider to allow full end-to-end evaluation without an API key."""

    def __init__(self):
        self._call_count = 0

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        # Check whether this is a generation prompt or validation prompt
        if "validate" in prompt.lower() or "verdict" in prompt.lower():
            return json.dumps(
                {
                    "supported_by_source": True,
                    "single_best_answer": True,
                    "distractors_valid": True,
                    "explanation_valid": True,
                    "ambiguity_detected": False,
                    "verdict": "PASS",
                    "issues": [],
                }
            )

        # Detect slot index from prompt if provided
        import re

        slot_match = re.search(r"SLOT_INDEX:\s*(\d+)", prompt)
        if slot_match:
            slot_idx = int(slot_match.group(1))
        else:
            slot_idx = self._call_count
            self._call_count += 1

        # Check if the prompt text is grounded in Raft / Distributed Systems (the sample study set)
        is_raft = "raft" in prompt.lower() or "consensus" in prompt.lower() or "leader" in prompt.lower()

        if is_raft:
            raft_questions = [
                {
                    "question_text": "How does the Raft consensus algorithm structure time into logical intervals?",
                    "options": [
                        {
                            "option_letter": "A",
                            "option_text": "By dividing time into terms of arbitrary length, numbered with consecutive integers.",
                            "is_correct": True,
                        },
                        {
                            "option_letter": "B",
                            "option_text": "By enforcing strict 100-millisecond synchronized wall-clock epochs.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "C",
                            "option_text": "By executing transactions only during pre-scheduled maintenance windows.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "D",
                            "option_text": "By delegating timekeeping to an external centralized NTP time server.",
                            "is_correct": False,
                        },
                    ],
                    "explanation": "Raft organizes time into numbered terms of arbitrary length, each starting with an election.",
                    "evidence": "The Raft consensus algorithm organizes time into terms of arbitrary length, numbered with consecutive integers.",
                    "topic": "Consensus Protocols",
                    "difficulty": "easy",
                    "distractor_rationale": "Distractors propose wall-clock epochs, maintenance windows, or NTP servers instead of logical terms.",
                },
                {
                    "question_text": "What marks the beginning of each new term in the Raft consensus algorithm?",
                    "options": [
                        {
                            "option_letter": "A",
                            "option_text": "A global database snapshot operation across all cluster nodes.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "B",
                            "option_text": "An election in which one or more candidate servers attempt to become leader.",
                            "is_correct": True,
                        },
                        {
                            "option_letter": "C",
                            "option_text": "A full restart of all participating replica server instances.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "D",
                            "option_text": "A manual handshake initiated by the cluster systems administrator.",
                            "is_correct": False,
                        },
                    ],
                    "explanation": "Each term in Raft begins with an election where candidate servers compete to become the leader.",
                    "evidence": "Each term begins with an election, in which one or more candidates attempt to become leader.",
                    "topic": "Consensus Protocols",
                    "difficulty": "medium",
                    "distractor_rationale": "Distractors suggest snapshots, restarts, or manual intervention rather than an election.",
                },
                {
                    "question_text": "What are the core operational responsibilities of an elected Raft leader?",
                    "options": [
                        {
                            "option_letter": "A",
                            "option_text": "Accepting log entries from clients, replicating them across servers, and managing state machine commits.",
                            "is_correct": True,
                        },
                        {
                            "option_letter": "B",
                            "option_text": "Generating cryptographic key pairs and encrypting all disk storage blocks.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "C",
                            "option_text": "Compiling source code and deploying microservice containers to worker nodes.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "D",
                            "option_text": "Assigning IP addresses dynamically using DHCP protocol extensions.",
                            "is_correct": False,
                        },
                    ],
                    "explanation": "The Raft leader manages client log entries, replicates them to followers, and tells servers when to apply entries to state machines.",
                    "evidence": "A leader accepts log entries from clients, replicates them across other servers, and tells servers when it is safe to apply log entries to their state machines.",
                    "topic": "Consensus Protocols",
                    "difficulty": "medium",
                    "distractor_rationale": "Distractors mention unrelated IT tasks such as disk encryption, container deployment, or DHCP.",
                },
                {
                    "question_text": "What safety guarantee is established by the Leader Completeness Property in Raft?",
                    "options": [
                        {
                            "option_letter": "A",
                            "option_text": "A leader will immediately step down if any single follower experiences a network timeout.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "B",
                            "option_text": "If a log entry is committed in a given term, it will be present in the logs of leaders for all higher-numbered terms.",
                            "is_correct": True,
                        },
                        {
                            "option_letter": "C",
                            "option_text": "Every server must write log entries to magnetic tape backup before acknowledging writes.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "D",
                            "option_text": "Leader elections can only occur during daylight hours in the primary cluster timezone.",
                            "is_correct": False,
                        },
                    ],
                    "explanation": "Leader Completeness ensures that committed entries persist across all subsequent leaders in higher terms.",
                    "evidence": "Safety in Raft is guaranteed through the Leader Completeness Property: if a log entry is committed in a given term, then that entry will be present in the logs of the leaders for all higher-numbered terms.",
                    "topic": "Consensus Protocols",
                    "difficulty": "hard",
                    "distractor_rationale": "Distractors invent timeout behaviors, backup rules, or arbitrary timezone constraints.",
                },
                {
                    "question_text": "How do distributed systems fundamentally achieve fault tolerance?",
                    "options": [
                        {
                            "option_letter": "A",
                            "option_text": "By relying solely on uninterruptible power supplies and dual power grids.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "B",
                            "option_text": "By implementing replication and consensus algorithms across participating machines.",
                            "is_correct": True,
                        },
                        {
                            "option_letter": "C",
                            "option_text": "By disabling network switches whenever a hardware fault is detected.",
                            "is_correct": False,
                        },
                        {
                            "option_letter": "D",
                            "option_text": "By restricting the cluster to a single high-performance mainframe computer.",
                            "is_correct": False,
                        },
                    ],
                    "explanation": "Replication combined with consensus protocols allows distributed systems to continue operating despite node failures.",
                    "evidence": "Distributed systems achieve fault tolerance through replication and consensus algorithms.",
                    "topic": "Consensus Protocols",
                    "difficulty": "easy",
                    "distractor_rationale": "Distractors propose hardware redundancy alone, switch shutdowns, or single-machine architectures.",
                },
            ]
            selected_q = raft_questions[slot_idx % len(raft_questions)]
            return json.dumps(selected_q)

        # General educational sample questions for generic offline evaluation
        sample_questions = [
            {
                "question_text": "What is the primary role of deterministic validation in an automated question generation system?",
                "options": [
                    {
                        "option_letter": "A",
                        "option_text": "To enforce structural rules such as option counts, unique identifiers, and evidence presence before semantic analysis.",
                        "is_correct": True,
                    },
                    {
                        "option_letter": "B",
                        "option_text": "To calculate calibrated mathematical confidence scores for language model outputs.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "C",
                        "option_text": "To translate source documents into multiple target languages prior to chunking.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "D",
                        "option_text": "To replace the need for original reference documents during quiz grading.",
                        "is_correct": False,
                    },
                ],
                "explanation": "Deterministic checks enforce structural integrity (four unique options, single answer, valid fields) independently of semantic model evaluation.",
                "evidence": prompt[:60].strip() or "Deterministic validation enforces structural rules.",
                "topic": "Validation Architecture",
                "difficulty": "medium",
                "distractor_rationale": "Distractors confuse structural rule checking with calibration, translation, or grading substitution.",
            },
            {
                "question_text": "Why must the test answer key remain separate from the quiz-taking interface endpoint?",
                "options": [
                    {
                        "option_letter": "A",
                        "option_text": "To reduce network payload size during high-concurrency test sessions.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "B",
                        "option_text": "To prevent answer-key leakage and inspectable solutions before the student submits their attempt.",
                        "is_correct": True,
                    },
                    {
                        "option_letter": "C",
                        "option_text": "To allow questions to be regenerated dynamically while the student is actively answering them.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "D",
                        "option_text": "To enable third-party grading plugins without database access.",
                        "is_correct": False,
                    },
                ],
                "explanation": "Separating the answer key ensures test integrity so students cannot inspect correct answers prior to completing the quiz.",
                "evidence": prompt[:60].strip() or "Separating the answer key ensures test integrity.",
                "topic": "Exam Security",
                "difficulty": "easy",
                "distractor_rationale": "Distractors propose performance, dynamic mutation, or plugin reasons rather than testing integrity.",
            },
            {
                "question_text": "How does the evaluation engine guarantee scoring reliability upon submission of an attempt?",
                "options": [
                    {
                        "option_letter": "A",
                        "option_text": "By executing an LLM prompt to grade student explanations qualitatively.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "B",
                        "option_text": "By calculating score deterministically against the immutable stored answer key.",
                        "is_correct": True,
                    },
                    {
                        "option_letter": "C",
                        "option_text": "By averaging peer scores across all users who attempted the quiz.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "D",
                        "option_text": "By comparing fuzzy embeddings of submitted option texts.",
                        "is_correct": False,
                    },
                ],
                "explanation": "Scoring is calculated deterministically on the backend using the immutable question key, strictly avoiding non-deterministic LLM grading.",
                "evidence": prompt[:60].strip() or "Scoring is calculated deterministically on the backend.",
                "topic": "Assessment Integrity",
                "difficulty": "hard",
                "distractor_rationale": "Distractors introduce non-deterministic methods like LLM grading, peer averaging, or fuzzy embeddings.",
            },
            {
                "question_text": "What is the recommended behavior when an uploaded presentation has no usable text or is image-only?",
                "options": [
                    {
                        "option_letter": "A",
                        "option_text": "Synthesize questions based on general world knowledge related to the file title.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "B",
                        "option_text": "Return a clear error message stating that scanned or image-only slides require OCR or text content.",
                        "is_correct": True,
                    },
                    {
                        "option_letter": "C",
                        "option_text": "Silently mark the document as passed and generate placeholder questions.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "D",
                        "option_text": "Convert the image to ASCII art and retry parsing.",
                        "is_correct": False,
                    },
                ],
                "explanation": "The parser must detect empty or image-only presentations and provide transparent error feedback rather than fabricating content.",
                "evidence": prompt[:60].strip() or "Detect empty or image-only documents and return a clear message.",
                "topic": "Document Ingestion",
                "difficulty": "easy",
                "distractor_rationale": "Distractors suggest fabricating questions, silent placeholders, or unfeasible conversions.",
            },
            {
                "question_text": "Under what circumstance does a generated question receive a 'REVIEW' validation verdict?",
                "options": [
                    {
                        "option_letter": "A",
                        "option_text": "When there is uncertainty, weak evidence, questionable distractors, or potential ambiguity.",
                        "is_correct": True,
                    },
                    {
                        "option_letter": "B",
                        "option_text": "When the question text exceeds 1,000 characters in length.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "C",
                        "option_text": "When the question difficulty is classified as 'Hard'.",
                        "is_correct": False,
                    },
                    {
                        "option_letter": "D",
                        "option_text": "When the user requests more than twenty questions simultaneously.",
                        "is_correct": False,
                    },
                ],
                "explanation": "REVIEW status highlights potential issues such as weak source evidence or distractor ambiguity for human verification.",
                "evidence": prompt[:60].strip() or "REVIEW indicates uncertainty, weak evidence, or potential ambiguity.",
                "topic": "Quality Assurance",
                "difficulty": "medium",
                "distractor_rationale": "Distractors cite arbitrary length, difficulty tier, or question quantity triggers.",
            },
        ]

        selected_q = sample_questions[slot_idx % len(sample_questions)]
        return json.dumps(selected_q)


class GroqLLMProvider(BaseLLMProvider):
    """Production Groq API provider supporting high-speed inference (Llama-3.3-70B, etc.)."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_name = model_name or settings.GROQ_MODEL

        if not self.api_key or self.api_key == "your_groq_api_key_here":
            raise LLMProviderError("Groq API key is not configured. Please set GROQ_API_KEY in backend/.env.")

        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Groq SDK client: {e}")
            raise LLMProviderError("Failed to initialize Groq client. Verify your dependencies and API key.")

    def _find_available_model(self) -> str | None:
        try:
            available = [m.id for m in self.client.models.list().data]
            priorities = [
                "openai/gpt-oss-120b",
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "openai/gpt-oss-20b",
                "qwen/qwen3.8-27b",
                "llama-3.1-8b-instant",
                "allam-2-7b",
            ]
            for p in priorities:
                if p in available:
                    return p
            for m_id in available:
                if not any(skip in m_id.lower() for skip in ["guard", "whisper", "embedding", "orpheus"]):
                    return m_id
            return available[0] if available else None
        except Exception as e:
            logger.warning(f"Could not query available Groq models: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        max_attempts = 3
        backoff_delay = 1.5

        for attempt in range(1, max_attempts + 1):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
                if not chat_completion.choices or not chat_completion.choices[0].message.content:
                    raise LLMProviderError("Received empty completion from Groq model.")
                return chat_completion.choices[0].message.content.strip()

            except Exception as e:
                err_str = str(e).lower()
                logger.warning(f"Groq API attempt {attempt}/{max_attempts} failed: {type(e).__name__} - {e}")

                if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str:
                    fallback_model = self._find_available_model()
                    if fallback_model and fallback_model != self.model_name:
                        logger.warning(
                            f"Groq model '{self.model_name}' not available. Auto-switching to '{fallback_model}'."
                        )
                        self.model_name = fallback_model
                        time.sleep(0.5)
                        continue

                if "api_key" in err_str or "unauthorized" in err_str or "401" in err_str:
                    raise LLMProviderError("Invalid or unauthorized Groq API key. Please check your credentials.")
                if "rate_limit" in err_str or "429" in err_str or "too many requests" in err_str:
                    if attempt == max_attempts:
                        raise LLMProviderError("Groq API rate limit reached. Please try again shortly.")
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                if "timeout" in err_str or "504" in err_str:
                    if attempt == max_attempts:
                        raise LLMProviderError("Groq API request timed out. Please try again with shorter content.")
                    time.sleep(backoff_delay)
                    continue

                if attempt == max_attempts:
                    raise LLMProviderError(f"Groq API request failed: {str(e)[:150]}")
                time.sleep(backoff_delay)

        raise LLMProviderError("Failed to generate content from Groq after multiple attempts.")


class ResilientLLMProvider(BaseLLMProvider):
    """
    Combines a primary provider (e.g. Gemini) with a fallback provider (e.g. Groq).
    If the primary provider encounters an error (rate limits, quota, timeout, API issue),
    it automatically fails over to the fallback provider seamlessly.
    """

    def __init__(self, primary: BaseLLMProvider, fallback: BaseLLMProvider):
        self.primary = primary
        self.fallback = fallback

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        try:
            return self.primary.generate(
                prompt=prompt, system_instruction=system_instruction, response_schema=response_schema
            )
        except Exception as primary_err:
            logger.warning(
                f"Primary LLM ({type(self.primary).__name__}) failed ({primary_err}). "
                f"Failing over to fallback ({type(self.fallback).__name__})..."
            )
            try:
                return self.fallback.generate(
                    prompt=prompt, system_instruction=system_instruction, response_schema=response_schema
                )
            except Exception as fallback_err:
                logger.error(f"Fallback LLM ({type(self.fallback).__name__}) also failed ({fallback_err}).")
                raise LLMProviderError(
                    f"Both primary ({type(self.primary).__name__}: {str(primary_err)[:80]}) and "
                    f"fallback ({type(self.fallback).__name__}: {str(fallback_err)[:80]}) failed."
                )


def get_llm_provider(force_demo: bool = False, task_type: str = "general") -> BaseLLMProvider:
    """
    Factory function to get the appropriate LLM provider chain.
    Provider selection order: Ollama (if primary) → Gemini → Groq → Demo
    Configuration via LLM_PRIMARY_PROVIDER and LLM_FALLBACK_PROVIDER env vars.
    """
    if force_demo:
        return DemoLLMProvider()

    providers: list[BaseLLMProvider] = []

    # Try to load Ollama provider first if configured as primary
    if settings.LLM_PRIMARY_PROVIDER == "ollama":
        try:
            from app.services.ollama_provider import OllamaProvider
            ollama = OllamaProvider()
            if ollama._check_connectivity():
                providers.append(ollama)
                logger.info("Ollama provider available and responsive.")
            else:
                logger.warning(f"Ollama not reachable at {settings.OLLAMA_BASE_URL}. Skipping Ollama.")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")

    # Gemini
    if settings.has_gemini_key:
        try:
            providers.append(GeminiLLMProvider())
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini provider: {e}")

    # Groq
    if settings.has_groq_key:
        try:
            providers.append(GroqLLMProvider())
        except Exception as e:
            logger.warning(f"Failed to initialize Groq provider: {e}")

    # Ollama as fallback (if not primary)
    if settings.LLM_PRIMARY_PROVIDER != "ollama" and not any(
        hasattr(p, 'base_url') for p in providers
    ):
        try:
            from app.services.ollama_provider import OllamaProvider
            ollama = OllamaProvider()
            if ollama._check_connectivity():
                providers.append(ollama)
        except Exception:
            pass

    if not providers:
        raise LLMProviderError(
            "No AI provider is available. Please configure GEMINI_API_KEY or GROQ_API_KEY in backend/.env, "
            "or start Ollama with 'ollama serve'. For demo mode, use 'Try sample study set'."
        )

    # Build resilient chain: primary → fallback → ...
    if len(providers) == 1:
        return providers[0]

    # Chain multiple providers
    result = providers[-1]
    for provider in reversed(providers[:-1]):
        result = ResilientLLMProvider(primary=provider, fallback=result)
    return result

