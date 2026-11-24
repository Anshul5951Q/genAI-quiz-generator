"""
AI answer evaluation engine.
Evaluates interview responses using configurable weighted rubrics.
"""
import json
import re
from typing import Any

from app.core.logging import logger
from app.services.llm_provider import BaseLLMProvider, LLMProviderError

EVALUATION_SYSTEM = """You are an expert technical interviewer evaluating candidate responses.
Score answers objectively based on the rubric criteria.
Output only valid JSON. Base scores on evidence in the candidate's response only."""

EVALUATION_TEMPLATE = """
Evaluate the following interview answer against the question rubric.

QUESTION: {question}

QUESTION RUBRIC:
{rubric}

EXPECTED KEY CONCEPTS:
{expected_concepts}

CANDIDATE'S ANSWER:
\"\"\"
{answer}
\"\"\"

Score each criterion on a 0-10 scale and provide detailed feedback.

Return JSON:
{{
  "technical_accuracy_score": 0_to_10,
  "conceptual_understanding_score": 0_to_10,
  "completeness_score": 0_to_10,
  "clarity_score": 0_to_10,
  "practical_examples_score": 0_to_10,
  "correct_concepts": ["Concept correctly mentioned"],
  "missing_concepts": ["Key concept not mentioned"],
  "incorrect_statements": ["Any factually incorrect claim"],
  "strengths": ["Strength of the answer"],
  "weaknesses": ["Weakness of the answer"],
  "suggested_improvement": "What would make this a better answer",
  "model_confidence": 0.0_to_1.0,
  "adaptive_signal": "strong|partial|weak|incomplete"
}}

SCORING RULES:
- technical_accuracy: How factually correct are the technical claims?
- conceptual_understanding: Does the candidate grasp the underlying concepts?
- completeness: Did they address all aspects of the question?
- clarity: Is the answer well-structured and easy to follow?
- practical_examples: Did they use relevant real-world examples?
- If answer is empty or "skip", all scores = 0
- adaptive_signal: "strong" (avg>7), "partial" (avg 5-7), "weak" (avg<5), "incomplete" (missed key aspects)
"""

# Criterion weights (must sum to 1.0)
CRITERION_WEIGHTS = {
    "technical_accuracy_score": 0.35,
    "conceptual_understanding_score": 0.25,
    "completeness_score": 0.20,
    "clarity_score": 0.10,
    "practical_examples_score": 0.10,
}


class AnswerEvaluationService:
    """
    Evaluates interview answers using LLM + deterministic weighted scoring.
    Final score calculation is always done in Python code, not by the model.
    """

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def evaluate(
        self,
        question_text: str,
        expected_concepts: list[str],
        rubric: dict,
        candidate_answer: str,
        provider_name: str = "unknown",
    ) -> dict[str, Any]:
        """Evaluate a single interview answer. Returns scored evaluation dict."""
        if not candidate_answer or candidate_answer.strip() in ("", "skip", "skipped"):
            return self._zero_score_evaluation("Answer was skipped.")

        rubric_str = json.dumps(rubric, indent=2) if rubric else "{}"
        concepts_str = "\n".join(f"- {c}" for c in (expected_concepts or []))

        prompt = EVALUATION_TEMPLATE.format(
            question=question_text,
            rubric=rubric_str,
            expected_concepts=concepts_str or "No specific concepts required.",
            answer=candidate_answer[:3000],
        )

        for attempt in range(1, 3):
            try:
                raw = self.llm.generate(prompt=prompt, system_instruction=EVALUATION_SYSTEM)
                data = self._parse(raw)
                if data:
                    # Calculate final weighted score in Python (never trust model's final score)
                    final_score = self._calculate_weighted_score(data)
                    data["final_score"] = round(final_score, 2)
                    data["max_score"] = 10.0
                    data["evaluation_provider"] = provider_name
                    return data
            except LLMProviderError:
                raise
            except Exception as e:
                logger.warning(f"Evaluation attempt {attempt} failed: {e}")

        return self._zero_score_evaluation("Evaluation failed due to an error.")

    def _calculate_weighted_score(self, data: dict) -> float:
        """
        Calculate final score deterministically from criterion scores.
        Never uses a model-produced final score.
        """
        total = 0.0
        for criterion, weight in CRITERION_WEIGHTS.items():
            raw_score = data.get(criterion, 0)
            try:
                score = max(0.0, min(10.0, float(raw_score)))
            except (TypeError, ValueError):
                score = 0.0
            total += score * weight
        return total

    def _parse(self, raw: str) -> dict | None:
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return self._normalize(data)
        except Exception:
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return self._normalize(data)
                except Exception:
                    pass
        return None

    def _normalize(self, data: dict) -> dict:
        def as_float(v, default=0.0):
            try:
                return max(0.0, min(10.0, float(v)))
            except Exception:
                return default

        def as_list(v):
            return v if isinstance(v, list) else []

        def as_str(v):
            return str(v).strip() if v else ""

        return {
            "technical_accuracy_score": as_float(data.get("technical_accuracy_score")),
            "conceptual_understanding_score": as_float(data.get("conceptual_understanding_score")),
            "completeness_score": as_float(data.get("completeness_score")),
            "clarity_score": as_float(data.get("clarity_score")),
            "practical_examples_score": as_float(data.get("practical_examples_score")),
            "correct_concepts": as_list(data.get("correct_concepts")),
            "missing_concepts": as_list(data.get("missing_concepts")),
            "incorrect_statements": as_list(data.get("incorrect_statements")),
            "strengths": as_list(data.get("strengths")),
            "weaknesses": as_list(data.get("weaknesses")),
            "suggested_improvement": as_str(data.get("suggested_improvement")),
            "model_confidence": max(0.0, min(1.0, float(data.get("model_confidence", 0.7)))),
            "adaptive_signal": data.get("adaptive_signal", "partial"),
        }

    @staticmethod
    def _zero_score_evaluation(reason: str) -> dict:
        return {
            "technical_accuracy_score": 0.0,
            "conceptual_understanding_score": 0.0,
            "completeness_score": 0.0,
            "clarity_score": 0.0,
            "practical_examples_score": 0.0,
            "final_score": 0.0,
            "max_score": 10.0,
            "correct_concepts": [],
            "missing_concepts": [],
            "incorrect_statements": [],
            "strengths": [],
            "weaknesses": [reason],
            "suggested_improvement": "Please provide a substantive answer.",
            "model_confidence": 1.0,
            "adaptive_signal": "weak",
            "evaluation_provider": "system",
        }
