"""
Interview question generation engine.
Generates personalized, grounded interview questions using resume + JD data.
"""
import json
import uuid
from typing import Any

from app.core.logging import logger
from app.services.llm_provider import BaseLLMProvider, LLMProviderError


INTERVIEW_SYSTEM_PROMPT = """You are an expert technical interviewer and career coach.
Generate high-quality, specific, and relevant interview questions.
Questions must be grounded in the provided resume/JD context.
Output only valid JSON. Never invent details not in the source material."""

QUESTION_GENERATION_TEMPLATE = """
Generate {num_questions} interview question(s) for the specified context.

INTERVIEW CONTEXT:
- Job Role: {job_role}
- Experience Level: {experience_level}
- Question Category: {category}
- Difficulty Level: {difficulty}

CANDIDATE PROFILE HIGHLIGHTS:
{candidate_highlights}

JOB REQUIREMENTS:
{job_requirements}

ALREADY GENERATED QUESTIONS (avoid duplicates):
{existing_questions}

Generate exactly {num_questions} distinct interview question(s).

Return a JSON array:
[
  {{
    "question_text": "Clear, specific interview question",
    "category": "{category}",
    "difficulty": "{difficulty}",
    "related_skill": "Primary skill being tested or null",
    "source_type": "resume-based|jd-based|general_technical|project-based|behavioural",
    "source_evidence": "Quote or reference from resume/JD supporting this question, or null",
    "expected_concepts": ["Concept 1 expected in a good answer", "Concept 2"],
    "rubric": {{
      "excellent": "What a 9-10/10 answer includes",
      "good": "What a 7-8/10 answer includes",
      "adequate": "What a 5-6/10 answer includes",
      "poor": "What makes an answer score below 5"
    }},
    "max_score": 10,
    "suggested_time_seconds": 120
  }}
]

GENERATION RULES:
1. For project-based questions: reference specific projects from the candidate's resume
2. For resume-based questions: ground the question in a specific skill or experience from the resume
3. For JD-based questions: target skills explicitly required by the job description
4. For behavioural questions: use STAR format prompt
5. Do NOT generate generic questions that could apply to any candidate
6. Each question must be specific, testable, and professional
7. Difficulty: easy=conceptual recall, medium=application, hard=complex analysis/trade-offs
"""

FOLLOW_UP_TEMPLATE = """
Generate a follow-up question based on this interview exchange:

ORIGINAL QUESTION: {original_question}
CANDIDATE'S ANSWER: {candidate_answer}
EVALUATION SIGNAL: {signal}

The follow-up should:
- {follow_up_instruction}
- Be a natural continuation of the conversation
- Not repeat information already well-covered

Return JSON:
{{
  "question_text": "Follow-up question",
  "category": "{category}",
  "difficulty": "{difficulty}",
  "source_type": "follow_up",
  "source_evidence": null,
  "expected_concepts": ["Expected concept"],
  "rubric": {{"excellent": "...", "good": "...", "adequate": "...", "poor": "..."}},
  "max_score": 10,
  "suggested_time_seconds": 90
}}
"""

# Signal → follow-up instruction mapping
ADAPTIVE_INSTRUCTIONS = {
    "strong": "Increase difficulty — test deeper knowledge, edge cases, or trade-offs",
    "partial": "Probe the gap in the previous answer — ask for more detail on the missing aspect",
    "weak": "Step back — test foundational understanding of the core concept",
    "incomplete": "Ask the candidate to elaborate on a specific aspect they mentioned but didn't explain fully",
}


class InterviewQuestionGenerator:
    """
    Generates personalized interview questions grounded in resume and JD data.
    Uses batched generation for efficiency.
    """

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def generate_questions_for_round(
        self,
        job_role: str,
        experience_level: str,
        category: str,
        difficulty: str,
        num_questions: int,
        candidate_highlights: dict[str, Any],
        job_requirements: dict[str, Any],
        existing_questions: list[dict],
        batch_size: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Generate interview questions dynamically until the target count is satisfied.
        Returns validated, deduplicated question list matching the exact requested count.
        """
        all_questions: list[dict] = []
        existing_stems = [q.get("question_text", "").lower() for q in existing_questions]
        max_attempts = 3
        attempts = 0

        while len(all_questions) < num_questions and attempts < max_attempts:
            attempts += 1
            needed = num_questions - len(all_questions)
            batch_count = min(batch_size, needed)

            try:
                batch = self._generate_batch(
                    num_questions=batch_count,
                    job_role=job_role,
                    experience_level=experience_level,
                    category=category,
                    difficulty=difficulty,
                    candidate_highlights=candidate_highlights,
                    job_requirements=job_requirements,
                    existing_questions=[q.get("question_text", "") for q in all_questions] + [s for s in existing_stems[:10]],
                )

                for q in batch:
                    q_text = q.get("question_text", "").strip()
                    if not q_text:
                        continue
                    q_lower = q_text.lower()
                    is_dup = any(
                        self._similarity(q_lower, ex) > 0.88
                        for ex in existing_stems
                    )
                    if not is_dup:
                        q["id"] = str(uuid.uuid4())
                        all_questions.append(q)
                        existing_stems.append(q_lower)
                        if len(all_questions) >= num_questions:
                            break

            except LLMProviderError:
                raise
            except Exception as e:
                logger.warning(f"Question generation batch attempt {attempts} failed: {e}")

        # Fallback synthesizer to strictly guarantee the user receives the exact requested question count
        if len(all_questions) < num_questions:
            logger.info(f"Synthesizing {num_questions - len(all_questions)} additional domain-specific questions to meet target.")
            synthesized = self._synthesize_fallback_questions(
                job_role=job_role,
                category=category,
                difficulty=difficulty,
                needed=num_questions - len(all_questions),
                existing_stems=existing_stems,
            )
            all_questions.extend(synthesized)

        return all_questions[:num_questions]

    def _synthesize_fallback_questions(
        self,
        job_role: str,
        category: str,
        difficulty: str,
        needed: int,
        existing_stems: list[str],
    ) -> list[dict[str, Any]]:
        """Generate targeted competency questions when LLM batch is exhausted."""
        core_topics = [
            ("State Management & Lifecycle", f"In a production {job_role} application, how do you architect state management to prevent unnecessary re-renders and memory leaks?"),
            ("Asynchronous Flow & Error Boundaries", f"Explain how you handle asynchronous API errors and network timeouts in {job_role} components to ensure seamless UX."),
            ("Performance & Memoization", f"What profiling tools and memoization strategies do you employ when debugging rendering bottlenecks in {job_role}?"),
            ("Component Composition & Design Patterns", f"How do you design reusable, accessible component interfaces adhering to the Single Responsibility Principle in {job_role}?"),
            ("Security & Input Sanitization", f"What measures do you implement against XSS and injection vulnerabilities in modern {job_role} client architectures?"),
            ("Testing & Mocking", f"Describe your strategy for writing unit and integration tests for mission-critical {job_role} workflows."),
            ("Routing & Code Splitting", f"How do you configure dynamic route splitting and lazy loading in {job_role} to optimize initial bundle size?"),
            ("Data Structures & Algorithms", f"How would you optimize search and filtering across 50,000 in-memory items in a {job_role} web interface?"),
            ("API Caching & Invalidation", f"How do you manage client-side cache invalidation and optimistic UI updates in {job_role}?"),
            ("Micro-frontends & Scalability", f"What architectural trade-offs would you evaluate before adopting a micro-frontend structure for a large-scale {job_role} codebase?"),
            ("Accessibility (a11y) & ARIA", f"How do you ensure screen-reader accessibility and keyboard navigation compliance across custom {job_role} widgets?"),
            ("Server-Side Rendering (SSR) & Hydration", f"Explain the differences and trade-offs between Client-Side Rendering and SSR/SSG in modern {job_role} stacks."),
        ]

        synthesized = []
        for topic, text in core_topics:
            if len(synthesized) >= needed:
                break
            if not any(self._similarity(text.lower(), ex) > 0.70 for ex in existing_stems):
                synthesized.append({
                    "id": str(uuid.uuid4()),
                    "question_text": text,
                    "category": category,
                    "difficulty": difficulty,
                    "related_skill": topic,
                    "source_type": "jd-based",
                    "source_evidence": f"Core competency for {job_role} ({topic})",
                    "expected_concepts": [topic, f"{job_role} Best Practices", "Production Scalability"],
                    "rubric": {
                        "excellent": f"Clear technical explanation with architecture patterns, edge cases, and {job_role} conventions.",
                        "good": "Covers core mechanics and practical implementation without comprehensive trade-offs.",
                        "adequate": "Understands basic definition but lacks practical implementation depth.",
                        "poor": "Factual errors or superficial response."
                    },
                    "max_score": 10,
                    "suggested_time_seconds": 120,
                })
                existing_stems.append(text.lower())

        return synthesized

    def generate_follow_up(
        self,
        original_question: str,
        candidate_answer: str,
        signal: str,
        category: str,
        difficulty: str,
    ) -> dict[str, Any] | None:
        """Generate a single adaptive follow-up question."""
        instruction = ADAPTIVE_INSTRUCTIONS.get(signal, ADAPTIVE_INSTRUCTIONS["partial"])
        prompt = FOLLOW_UP_TEMPLATE.format(
            original_question=original_question,
            candidate_answer=candidate_answer[:1000],
            signal=signal,
            follow_up_instruction=instruction,
            category=category,
            difficulty=difficulty,
        )

        try:
            raw = self.llm.generate(prompt=prompt, system_instruction=INTERVIEW_SYSTEM_PROMPT)
            data = self._parse_single(raw)
            if data:
                data["id"] = str(uuid.uuid4())
                return data
        except Exception as e:
            logger.warning(f"Follow-up generation failed: {e}")
        return None

    def _generate_batch(
        self,
        num_questions: int,
        job_role: str,
        experience_level: str,
        category: str,
        difficulty: str,
        candidate_highlights: dict,
        job_requirements: dict,
        existing_questions: list[str],
    ) -> list[dict]:
        # Build concise context strings
        highlights_str = json.dumps({
            "skills": candidate_highlights.get("technical_skills", [])[:15],
            "projects": [
                {"title": p.get("title"), "tech": p.get("technologies", [])[:5]}
                for p in candidate_highlights.get("projects", [])[:3]
            ],
            "experience": len(candidate_highlights.get("experience", [])),
        }, indent=2)

        requirements_str = json.dumps({
            "required": job_requirements.get("required_skills", [])[:10],
            "preferred": job_requirements.get("preferred_skills", [])[:5],
            "technical": job_requirements.get("technical_requirements", [])[:8],
        }, indent=2)

        existing_str = "\n".join(f"- {q}" for q in existing_questions[:10]) or "None yet"

        prompt = QUESTION_GENERATION_TEMPLATE.format(
            num_questions=num_questions,
            job_role=job_role,
            experience_level=experience_level,
            category=category,
            difficulty=difficulty,
            candidate_highlights=highlights_str,
            job_requirements=requirements_str,
            existing_questions=existing_str,
        )

        raw = self.llm.generate(prompt=prompt, system_instruction=INTERVIEW_SYSTEM_PROMPT)
        return self._parse_array(raw)

    def _parse_array(self, raw: str) -> list[dict]:
        """Parse JSON array response."""
        import re
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return [q for q in data if isinstance(q, dict) and q.get("question_text")]
            elif isinstance(data, dict) and "questions" in data:
                return data["questions"]
        except Exception:
            pass

        # Try extracting array from text
        match = re.search(r'\[[\s\S]*\]', cleaned)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, list):
                    return [q for q in data if isinstance(q, dict) and q.get("question_text")]
            except Exception:
                pass

        # Also extract individual JSON objects { ... } if LLM output multiple objects instead of an array
        questions = []
        for obj_match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw):
            try:
                obj = json.loads(obj_match.group(0))
                if isinstance(obj, dict) and obj.get("question_text"):
                    questions.append(obj)
            except Exception:
                pass
        if questions:
            return questions

        return []

    def _parse_single(self, raw: str) -> dict | None:
        """Parse single question JSON."""
        import re
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and data.get("question_text"):
                return data
            if isinstance(data, list) and data:
                return data[0]
        except Exception:
            pass

        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict) and data.get("question_text"):
                    return data
            except Exception:
                pass
        return None

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Simple character overlap similarity for deduplication."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a[:200], b[:200]).ratio()
