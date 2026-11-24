import json
import uuid
from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.schemas.validation import QuestionValidationSummary
from app.services.llm_provider import BaseLLMProvider
from app.services.question_validator import QuestionValidator
from app.services.text_chunker import TextChunk


class QuestionGenerator:
    """Orchestrates MCQ generation from source text with bounded regeneration and two-stage validation."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def generate_quiz_questions(
        self,
        chunks: list[TextChunk],
        num_questions: int = 5,
        target_difficulty: str = "mixed",
        topic_focus: str | None = None,
        difficulty_distribution: dict[str, int] | None = None,
        included_topics: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], QuestionValidationSummary]:
        summary = QuestionValidationSummary()

        # Determine difficulty distribution
        difficulties: list[str] = []
        if difficulty_distribution:
            difficulties = (
                ["easy"] * difficulty_distribution.get("easy", 0)
                + ["medium"] * difficulty_distribution.get("medium", 0)
                + ["hard"] * difficulty_distribution.get("hard", 0)
            )
            # Pad if distribution was shorter than requested count
            while len(difficulties) < num_questions:
                difficulties.append("medium")
            difficulties = difficulties[:num_questions]
        elif target_difficulty == "mixed":
            pattern = ["easy", "medium", "hard"]
            for i in range(num_questions):
                difficulties.append(pattern[i % 3])
        else:
            difficulties = [target_difficulty] * num_questions

        final_questions: list[dict[str, Any]] = []

        # Distribute questions across chunks and topics
        chunk_count = len(chunks)
        topic_list = included_topics or ([topic_focus] if topic_focus else [])

        for idx in range(num_questions):
            assigned_chunk = chunks[idx % chunk_count]
            assigned_difficulty = difficulties[idx]
            assigned_topic = topic_list[idx % len(topic_list)] if topic_list else topic_focus

            # Generate question with corrective retry loop and chunk rotation on duplicate
            question, retries_taken = self._generate_single_question_with_retry(
                chunk=assigned_chunk,
                all_chunks=chunks,
                difficulty=assigned_difficulty,
                topic_focus=assigned_topic,
                existing_questions=final_questions,
            )

            summary.total_generated += 1
            if retries_taken > 0:
                summary.regenerated_count += retries_taken

            if not question:
                summary.rejected_count += 1
                logger.warning(f"Could not generate a distinct valid question for slot {idx + 1}.")
                continue

            status = question.get("validation_status", "review")
            if status == "pass":
                summary.passed_count += 1
            elif status == "reject":
                # Hard reject (e.g. duplicate stem or options) - do not include in quiz
                summary.rejected_count += 1
                logger.warning(
                    f"Question candidate for slot {idx + 1} was rejected ({question.get('validation_issues')}). Discarding."
                )
                continue
            else:
                summary.flagged_review_count += 1

            question["order_index"] = len(final_questions) + 1
            final_questions.append(question)

        # Content-based deduplication pass before returning: guarantee zero duplicates
        from difflib import SequenceMatcher

        deduped_questions: list[dict[str, Any]] = []
        for q in final_questions:
            q_stem = QuestionValidator.normalize_stem(q.get("question_text", ""))
            is_dup = False
            for d in deduped_questions:
                d_stem = QuestionValidator.normalize_stem(d.get("question_text", ""))
                if q_stem == d_stem or SequenceMatcher(None, q_stem, d_stem).ratio() > 0.82:
                    is_dup = True
                    break
            if not is_dup:
                q["order_index"] = len(deduped_questions) + 1
                deduped_questions.append(q)
            else:
                summary.rejected_count += 1

        if len(deduped_questions) < num_questions:
            logger.warning(
                f"Generated {len(deduped_questions)} distinct questions out of {num_questions} requested "
                "due to deduplication constraints."
            )

        return deduped_questions, summary

    def _generate_single_question_with_retry(
        self,
        chunk: TextChunk,
        all_chunks: list[TextChunk] | None,
        difficulty: str,
        topic_focus: str | None = None,
        existing_questions: list[dict[str, Any]] | None = None,
        initial_feedback: str | None = None,
    ) -> tuple[dict[str, Any] | None, int]:
        retries = 0
        corrective_feedback: str | None = initial_feedback
        best_candidate: dict[str, Any] | None = None
        current_chunk = chunk
        chunks_list = all_chunks or [chunk]

        while retries <= settings.MAX_REGENERATION_ATTEMPTS:
            candidate = self._prompt_generation(
                chunk=current_chunk,
                difficulty=difficulty,
                topic_focus=topic_focus,
                corrective_feedback=corrective_feedback,
                slot_index=len(existing_questions or []) + retries,
                existing_stems=[q.get("question_text", "") for q in (existing_questions or [])],
            )

            # Evaluate candidate through QuestionValidator
            verdict, issues, sem_result = QuestionValidator.evaluate_question(
                question=candidate,
                source_text=current_chunk.text,
                llm_provider=self.llm,
                existing_questions=existing_questions,
                run_semantic=True,
            )

            candidate["validation_status"] = verdict
            candidate["validation_issues"] = issues
            candidate["source_page"] = current_chunk.page_number
            candidate["semantic_details"] = sem_result.model_dump() if sem_result else None

            if verdict == "pass":
                return candidate, retries

            # If rejected because of duplicate stem or option overlap, try next chunk if available
            is_dup = any(
                "duplicate" in iss.lower() or "identical" in iss.lower() or "shares 3" in iss.lower()
                for iss in issues
            )
            if is_dup and len(chunks_list) > 1:
                next_chunk_idx = (chunks_list.index(current_chunk) + 1) % len(chunks_list)
                current_chunk = chunks_list[next_chunk_idx]

            if verdict != "reject":
                best_candidate = candidate

            # If rejected or flagged with clear issues, formulate targeted corrective feedback for retry
            if retries < settings.MAX_REGENERATION_ATTEMPTS:
                logger.info(f"Question candidate failed validation ({verdict}). Retrying with feedback.")
                issues_text = "; ".join(issues)
                corrective_feedback = (
                    f"Previous attempt had issues: {issues_text}. "
                    "Ensure exact 4 options with letters A-D, strictly 1 correct answer, "
                    "a completely distinct question concept not covered by earlier questions, "
                    "no 'all/none of above', and direct exact quotes for evidence."
                )
                retries += 1
            else:
                break

        # Only return non-rejected candidates; never return duplicates
        if best_candidate and best_candidate.get("validation_status") != "reject":
            return best_candidate, retries
        return None, retries

    def _prompt_generation(
        self,
        chunk: TextChunk,
        difficulty: str,
        topic_focus: str | None = None,
        corrective_feedback: str | None = None,
        slot_index: int = 0,
        existing_stems: list[str] | None = None,
    ) -> dict[str, Any]:
        target_letter = ["A", "B", "C", "D"][slot_index % 4]

        focus_instruction = f"Focus particularly on the topic '{topic_focus}' if mentioned." if topic_focus else ""
        retry_instruction = (
            f"\nCORRECTIVE FEEDBACK FROM PREVIOUS FAILED VALIDATION:\n{corrective_feedback}\n"
            if corrective_feedback
            else ""
        )
        anti_dup_instruction = ""
        if existing_stems:
            stems_text = "\n".join(f"- {s}" for s in existing_stems if s)
            anti_dup_instruction = (
                f"\nDO NOT repeat, rephrase, or duplicate any of these already covered questions:\n{stems_text}\n"
            )

        system_instruction = (
            "You are an expert academic assessment specialist creating grounded multiple-choice questions (MCQs). "
            "Output only valid JSON."
        )

        if difficulty == "easy":
            style_guide = (
                "COGNITIVE FOCUS: Recall and core factual understanding. Test explicit definitions, stated terminology, "
                "or direct principles. Stem should test recognition of key concepts."
            )
            detected_style = "recall"
        elif difficulty == "hard":
            style_guide = (
                "COGNITIVE FOCUS: Deep analysis, case-based evaluation, or error identification. Require multi-step "
                "deduction, determining why a plausible misconception fails, or applying constraints to a practical scenario."
            )
            detected_style = "case_based" if slot_index % 2 == 0 else "error_analysis"
        else:
            style_guide = (
                "COGNITIVE FOCUS: Application and comparison. Require the learner to distinguish between two related concepts "
                "or apply a principle to a concrete example."
            )
            detected_style = "application" if slot_index % 2 == 0 else "comparison"

        prompt = f"""
SOURCE TEXT (Page {chunk.page_number}):
\"\"\"
{chunk.text}
\"\"\"

TASK:
Create exactly 1 high-quality multiple choice question (MCQ) testing {difficulty.upper()} level understanding based strictly on the source text.
{style_guide}
{focus_instruction}
{retry_instruction}
{anti_dup_instruction}
SLOT_INDEX: {slot_index}

STRICT ACADEMIC GUIDELINES:
1. The question stem must be clear, concise, and self-contained.
2. Provide exactly 4 options labeled A, B, C, D.
3. For this question, set the correct answer to option {target_letter} to ensure an even distribution.
4. Exactly one option must be correct; the other three must be plausible distractors that are definitely incorrect according to the source.
5. Do NOT use 'all of the above' or 'none of the above'.
6. Do NOT invent facts or external citations. Every fact must be verifiable in the source excerpt.
7. 'evidence' MUST be an exact sentence or clause quoted directly from the provided source text.
8. 'explanation' must explain why the correct option is true and why other options fail.
9. 'distractor_rationale' should concisely state why the 3 incorrect options are plausible but wrong.

REQUIRED JSON FORMAT:
{{
  "question_text": "Stem of the question",
  "options": [
    {{"option_letter": "A", "option_text": "Option text A", "is_correct": {"true" if target_letter == "A" else "false"}}},
    {{"option_letter": "B", "option_text": "Option text B", "is_correct": {"true" if target_letter == "B" else "false"}}},
    {{"option_letter": "C", "option_text": "Option text C", "is_correct": {"true" if target_letter == "C" else "false"}}},
    {{"option_letter": "D", "option_text": "Option text D", "is_correct": {"true" if target_letter == "D" else "false"}}}
  ],
  "explanation": "Clear explanation referencing source facts",
  "evidence": "Direct quote from the source excerpt",
  "topic": "{topic_focus or "General"}",
  "difficulty": "{difficulty}",
  "question_style": "{detected_style}",
  "distractor_rationale": "Why incorrect options are plausible but wrong"
}}
"""
        raw = self.llm.generate(prompt=prompt, system_instruction=system_instruction)

        # Parse JSON safely
        cleaned = raw
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        import re
        try:
            data = json.loads(cleaned)
            # If model returned wrapped under questions array
            if "questions" in data and isinstance(data["questions"], list) and len(data["questions"]) > 0:
                data = data["questions"][slot_index % len(data["questions"])]
        except Exception as e:
            logger.warning(f"Model response could not be parsed directly ({e}). Attempting regex recovery.")
            json_match = re.search(r"\{[\s\S]*\}", raw)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except Exception:
                    data = None
            else:
                data = None

            if not data or not isinstance(data, dict) or "question_text" not in data:
                from app.services.llm_provider import LLMProviderError
                raise LLMProviderError(f"Model output did not produce valid question JSON: {raw[:120]}")

        # Ensure option IDs exist
        for opt in data.get("options", []):
            if "id" not in opt or not opt["id"]:
                opt["id"] = str(uuid.uuid4())

        data["id"] = str(uuid.uuid4())
        data["question_style"] = data.get("question_style", detected_style)
        return data

    def regenerate_single_question(
        self,
        current_question: dict[str, Any],
        source_text: str,
        user_notes: str | None = None,
        existing_questions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Regenerates a specific question with optional reviewer feedback."""
        page_num = current_question.get("source_page", 1)
        chunk = TextChunk(
            chunk_index=0,
            text=source_text,
            page_number=page_num,
            char_count=len(source_text),
            token_estimate=len(source_text) // 4,
        )

        feedback = user_notes or "Reviewer requested regeneration for improved clarity and evidence alignment."
        new_q, _ = self._generate_single_question_with_retry(
            chunk=chunk,
            all_chunks=[chunk],
            difficulty=current_question.get("difficulty", "medium"),
            topic_focus=current_question.get("topic", "General"),
            existing_questions=existing_questions or [],
            initial_feedback=feedback,
        )
        if not new_q:
            from app.services.llm_provider import LLMProviderError
            raise LLMProviderError("Failed to generate a valid replacement question from source excerpt.")

        new_q["id"] = current_question.get("id", str(uuid.uuid4()))
        new_q["order_index"] = current_question.get("order_index", 1)
        return new_q
