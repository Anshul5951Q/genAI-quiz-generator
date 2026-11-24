import re
from collections import Counter

from app.schemas.blueprint import (
    BlueprintValidationResult,
    ExamBlueprint,
    TopicCoverageItem,
)
from app.services.text_chunker import TextChunk


class BlueprintServiceError(Exception):
    """Validation or execution error for Blueprint operations."""


class BlueprintService:
    @staticmethod
    def extract_candidate_topics(chunks: list[TextChunk], max_topics: int = 8) -> list[str]:
        """
        Extracts salient subject topics from chunks using capitalized terminology,
        heading patterns, and term frequency analysis.
        """
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "which", "into", "their",
            "have", "been", "also", "each", "were", "when", "more", "other", "some", "such",
            "what", "then", "them", "these", "only", "first", "page", "slide", "chapter",
        }

        # Look for title/heading patterns (lines ending without period or CamelCase terms)
        heading_candidates = []
        term_counter = Counter()

        for chunk in chunks:
            lines = chunk.text.split("\n")
            for line in lines:
                clean_line = line.strip()
                if 4 <= len(clean_line) <= 45 and not clean_line.endswith((".", ",", ";")):
                    # Heading-like line
                    heading_candidates.append(clean_line)

            # Extract 2-3 word capitalized phrases or significant nouns
            phrases = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{2,}(?:\s+[A-Z][a-zA-Z0-9_\-]+)?\b", chunk.text)
            for p in phrases:
                p_norm = p.strip()
                if p_norm.lower() not in stop_words and len(p_norm) > 3:
                    term_counter[p_norm] += 1

        # Combine headings and top recurring domain terms
        combined_topics = []
        seen = set()

        # Prioritize headings
        for h in heading_candidates:
            h_clean = h.title()
            if h_clean.lower() not in seen and len(h_clean) >= 4:
                combined_topics.append(h_clean)
                seen.add(h_clean.lower())
                if len(combined_topics) >= max_topics // 2:
                    break

        # Then top frequent terms
        for term, _ in term_counter.most_common(max_topics):
            if term.lower() not in seen:
                combined_topics.append(term)
                seen.add(term.lower())
                if len(combined_topics) >= max_topics:
                    break

        if not combined_topics:
            combined_topics = ["Foundations", "Core Principles", "Implementation", "Analysis"]

        return combined_topics[:max_topics]

    @classmethod
    def validate_and_plan_coverage(
        cls,
        blueprint: ExamBlueprint,
        chunks: list[TextChunk],
    ) -> BlueprintValidationResult:
        issues: list[str] = []
        warnings: list[str] = []

        total_diff_sum = (
            blueprint.difficulty_distribution.easy
            + blueprint.difficulty_distribution.medium
            + blueprint.difficulty_distribution.hard
        )

        if total_diff_sum != blueprint.total_questions:
            issues.append(
                f"Difficulty distribution sum ({total_diff_sum}) must exactly equal total questions requested ({blueprint.total_questions}). "
                f"(Easy: {blueprint.difficulty_distribution.easy}, Medium: {blueprint.difficulty_distribution.medium}, Hard: {blueprint.difficulty_distribution.hard})"
            )

        extracted = cls.extract_candidate_topics(chunks)

        # Filter out excluded topics
        active_topics = [t for t in (blueprint.included_topics or extracted) if t not in blueprint.excluded_topics]
        if not active_topics:
            active_topics = extracted[:4]
            warnings.append("All requested topics were excluded or missing; defaulted to extracted document topics.")

        # Estimate chunk mentions for active topics
        coverage_matrix: list[TopicCoverageItem] = []
        num_topics = len(active_topics)
        base_alloc = blueprint.total_questions // max(1, num_topics)
        remainder = blueprint.total_questions % max(1, num_topics)

        # Distribute difficulties across topics
        diff_pool = (
            ["easy"] * blueprint.difficulty_distribution.easy
            + ["medium"] * blueprint.difficulty_distribution.medium
            + ["hard"] * blueprint.difficulty_distribution.hard
        )

        curr_pool_idx = 0
        for i, topic in enumerate(active_topics):
            topic_pattern = re.compile(re.escape(topic), re.IGNORECASE)
            mention_count = sum(1 for c in chunks if topic_pattern.search(c.text))

            q_for_topic = base_alloc + (1 if i < remainder else 0)
            topic_diffs: dict[str, int] = {"easy": 0, "medium": 0, "hard": 0}

            for _ in range(q_for_topic):
                if curr_pool_idx < len(diff_pool):
                    d = diff_pool[curr_pool_idx]
                    topic_diffs[d] = topic_diffs.get(d, 0) + 1
                    curr_pool_idx += 1

            if mention_count >= 2:
                status = "adequate"
                notes = "Solid coverage in source text."
            elif mention_count == 1:
                status = "underrepresented"
                notes = "Topic only appears in 1 text segment."
                warnings.append(f"Topic '{topic}' is sparsely mentioned in the uploaded material.")
            else:
                status = "insufficient"
                notes = "Topic not explicitly located in document text."
                warnings.append(f"Topic '{topic}' has minimal direct evidence in the source text.")

            coverage_matrix.append(
                TopicCoverageItem(
                    topic=topic,
                    chunk_mentions=mention_count,
                    allocated_questions=q_for_topic,
                    difficulty_breakdown=topic_diffs,
                    coverage_status=status,
                    notes=notes,
                )
            )

        # Check total chunk length vs requested question count
        total_chars = sum(len(c.text) for c in chunks)
        if total_chars < blueprint.total_questions * 150:
            warnings.append(
                f"Source document contains {total_chars} characters. Generating {blueprint.total_questions} distinct "
                "questions may produce near-duplicate concepts due to limited source text volume."
            )

        return BlueprintValidationResult(
            is_valid=(len(issues) == 0),
            issues=issues,
            warnings=warnings,
            coverage_matrix=coverage_matrix,
            extracted_topics=extracted,
        )
