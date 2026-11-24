import json
import re
from difflib import SequenceMatcher
from typing import Any

from app.core.logging import logger
from app.schemas.validation import (
    DeterministicCheckResult,
    SemanticValidationResult,
)
from app.services.llm_provider import BaseLLMProvider


class QuestionValidator:
    """Two-stage validation pipeline: deterministic structural checks and independent semantic review."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes whitespace and lowercases for comparison."""
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def normalize_stem(text: str) -> str:
        """Normalizes whitespace, lowercases, and removes punctuation for robust stem deduplication."""
        lowered = text.strip().lower()
        no_punct = re.sub(r"[^\w\s]", "", lowered)
        return re.sub(r"\s+", " ", no_punct).strip()

    @classmethod
    def run_deterministic_checks(
        cls,
        question: dict[str, Any],
        source_text: str,
        existing_questions: list[dict[str, Any]] | None = None,
    ) -> DeterministicCheckResult:
        issues: list[str] = []

        q_text = question.get("question_text", "").strip()
        if not q_text or len(q_text) < 5:
            issues.append("Question stem is missing or too short.")

        # Exactly 4 options
        options = question.get("options", [])
        if len(options) != 4:
            issues.append(f"Question must have exactly 4 options, found {len(options)}.")

        # Check options uniqueness and single correct answer
        seen_letters = set()
        seen_texts = set()
        correct_count = 0

        for opt in options:
            letter = opt.get("option_letter", "").strip().upper()
            opt_text = opt.get("option_text", "").strip()

            if letter not in {"A", "B", "C", "D"}:
                issues.append(f"Invalid option letter '{letter}'. Must be A, B, C, or D.")
            if letter in seen_letters:
                issues.append(f"Duplicate option letter '{letter}'.")
            seen_letters.add(letter)

            if not opt_text:
                issues.append(f"Option {letter} text is empty.")
            norm_opt = cls.normalize_text(opt_text)
            if norm_opt in seen_texts:
                issues.append(f"Duplicate option text found for option {letter}.")
            seen_texts.add(norm_opt)

            # Avoid "all of the above" or "none of the above"
            if "all of the above" in norm_opt or "none of the above" in norm_opt:
                issues.append(f"Forbidden option pattern ('all/none of the above') in option {letter}.")

            if opt.get("is_correct") is True:
                correct_count += 1

        if correct_count != 1:
            issues.append(f"Must have exactly 1 correct option, found {correct_count}.")

        # Required fields
        explanation = question.get("explanation", "").strip()
        if not explanation or len(explanation) < 5:
            issues.append("Explanation is missing or too short.")

        evidence = question.get("evidence", "").strip()
        if not evidence or len(evidence) < 5:
            issues.append("Source evidence is missing or too short.")
        else:
            # Check evidence traceability in source text with whitespace normalization
            norm_source = cls.normalize_text(source_text)
            norm_evidence = cls.normalize_text(evidence)
            if norm_evidence not in norm_source:
                # Check if high similarity substring exists
                words = norm_evidence.split()
                if len(words) >= 4:
                    phrase_match = " ".join(words[:4]) in norm_source or " ".join(words[-4:]) in norm_source
                else:
                    phrase_match = norm_evidence in norm_source

                if not phrase_match:
                    issues.append("Evidence quote cannot be traced back to the supplied source text.")

        # Difficulty check
        diff = question.get("difficulty", "medium").lower()
        if diff not in {"easy", "medium", "hard"}:
            issues.append(f"Invalid difficulty '{diff}'. Must be easy, medium, or hard.")

        # Duplicate / Near-duplicate check against other questions
        if existing_questions and q_text:
            norm_stem_q = cls.normalize_stem(q_text)
            curr_opts = {cls.normalize_stem(opt.get("option_text", "")) for opt in options if opt.get("option_text")}

            for ex in existing_questions:
                ex_text = ex.get("question_text", "")
                norm_stem_ex = cls.normalize_stem(ex_text)

                if norm_stem_q == norm_stem_ex:
                    issues.append("Identical question stem already exists in this quiz set.")
                    break

                # Near-duplicate check with SequenceMatcher
                ratio = SequenceMatcher(None, norm_stem_q, norm_stem_ex).ratio()
                if ratio > 0.82:
                    issues.append(f"Near-duplicate question stem detected (similarity {int(ratio * 100)}%).")
                    break

                # Option overlap check
                ex_opts = {
                    cls.normalize_stem(opt.get("option_text", ""))
                    for opt in ex.get("options", [])
                    if opt.get("option_text")
                }
                if len(curr_opts) >= 3 and len(ex_opts) >= 3:
                    overlap = len(curr_opts.intersection(ex_opts))
                    if overlap >= 3:
                        issues.append("Question shares 3 or more identical options with an existing question.")
                        break

        return DeterministicCheckResult(is_valid=(len(issues) == 0), issues=issues, normalized_evidence=evidence)

    @classmethod
    def run_semantic_validation(
        cls,
        llm_provider: BaseLLMProvider,
        question: dict[str, Any],
        source_context: str,
    ) -> SemanticValidationResult:
        """Executes independent semantic review using separate LLM prompt."""
        correct_opt = next((o for o in question.get("options", []) if o.get("is_correct")), None)
        correct_letter = correct_opt.get("option_letter") if correct_opt else "None"
        correct_text = correct_opt.get("option_text") if correct_opt else "None"

        options_str = "\n".join(
            f"- {o.get('option_letter')}: {o.get('option_text')}" for o in question.get("options", [])
        )

        validation_prompt = f"""
You are an independent academic quiz validator conducting a strict, factual audit of a generated multiple-choice question against the source text.

SOURCE TEXT EXCERPT:
\"\"\"
{source_context[:3000]}
\"\"\"

QUESTION TO AUDIT:
Stem: {question.get("question_text")}
Options:
{options_str}
Proposed Correct Option: {correct_letter} - {correct_text}
Explanation: {question.get("explanation")}
Claimed Evidence: \"{question.get("evidence")}\"

Perform these 7 audit steps:
1. Is the cited evidence accurate and does it strictly support the proposed correct answer?
2. Is the question factually answerable purely from the supplied source text?
3. Is any distractor (incorrect option) also defensible or accidentally correct?
4. Are the distractors plausible and grammatically aligned?
5. Does the explanation align with the source facts?
6. Is the question ambiguous or tricky?
7. Is the assigned difficulty reasonable?

Output a JSON object with this exact structure:
{{
  "supported_by_source": true/false,
  "single_best_answer": true/false,
  "distractors_valid": true/false,
  "explanation_valid": true/false,
  "ambiguity_detected": true/false,
  "verdict": "PASS" | "REVIEW" | "REJECT",
  "issues": ["Concise description of any issue or concern"]
}}

Policy:
- PASS: Supported by source, single best answer, valid distractors, no material issues.
- REVIEW: Minor uncertainty, weak evidence, slight distractor weakness, or potential ambiguity.
- REJECT: Structurally invalid, answer contradicted by source, multiple defensible answers, or severe ambiguity.
"""
        try:
            raw_response = llm_provider.generate(
                prompt=validation_prompt,
                system_instruction="You are a strict, objective academic exam validator. Output only JSON.",
            )
            # Parse JSON
            cleaned_json = raw_response
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()

            parsed = json.loads(cleaned_json)
            return SemanticValidationResult(
                supported_by_source=bool(parsed.get("supported_by_source", False)),
                single_best_answer=bool(parsed.get("single_best_answer", False)),
                distractors_valid=bool(parsed.get("distractors_valid", False)),
                explanation_valid=bool(parsed.get("explanation_valid", False)),
                ambiguity_detected=bool(parsed.get("ambiguity_detected", False)),
                verdict=str(parsed.get("verdict", "REVIEW")).upper(),
                issues=list(parsed.get("issues", [])),
            )
        except Exception as e:
            logger.warning(f"Semantic validation call or parsing failed: {type(e).__name__}")
            return SemanticValidationResult(
                supported_by_source=False,
                single_best_answer=False,
                distractors_valid=False,
                explanation_valid=False,
                ambiguity_detected=True,
                verdict="REVIEW",
                issues=[f"Automated semantic validation could not complete: {str(e)[:100]}"],
            )

    @classmethod
    def evaluate_question(
        cls,
        question: dict[str, Any],
        source_text: str,
        llm_provider: BaseLLMProvider | None = None,
        existing_questions: list[dict[str, Any]] | None = None,
        run_semantic: bool = True,
    ) -> tuple[str, list[str], SemanticValidationResult | None]:
        """
        Runs Stage A then Stage B.
        Returns (verdict: 'pass' | 'review' | 'reject', all_issues: List[str], semantic_result)
        """
        # Stage A: Deterministic
        det_result = cls.run_deterministic_checks(question, source_text, existing_questions)

        if not det_result.is_valid:
            # Deterministic failure immediately marks as REJECT or REVIEW depending on severity
            critical_errors = [
                iss
                for iss in det_result.issues
                if any(
                    kw in iss.lower()
                    for kw in [
                        "4 options",
                        "correct option",
                        "duplicate option",
                        "identical question stem",
                        "near-duplicate",
                        "shares 3 or more",
                        "empty",
                        "missing or too short",
                    ]
                )
            ]
            verdict = "reject" if critical_errors else "review"
            return verdict, det_result.issues, None

        # Stage B: Semantic Validation
        if run_semantic and llm_provider:
            sem_result = cls.run_semantic_validation(llm_provider, question, source_text)
            all_issues = det_result.issues + sem_result.issues

            # Acceptance policy mapping
            if sem_result.verdict == "PASS" and not all_issues:
                verdict = "pass"
            elif sem_result.verdict == "REJECT":
                verdict = "reject"
            else:
                verdict = "review"

            return verdict, all_issues, sem_result

        # If semantic validation skipped, mark as review if there are any issues else pass
        return "pass" if not det_result.issues else "review", det_result.issues, None
