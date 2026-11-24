import json
import random
from typing import Any

from sqlalchemy.orm import Session

from app.models.quiz import QuizModel
from app.models.version import QuizVersionMappingModel


class VersionServiceError(Exception):
    """Errors related to parallel exam version generation."""


class VersionService:
    @classmethod
    def generate_parallel_versions(
        cls,
        db: Session,
        quiz_id: str,
        version_labels: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generates parallel exam versions (e.g. A, B, C) from an approved quiz.
        Permutes question order and option order safely while keeping correct answers aligned.
        """
        quiz = db.query(QuizModel).filter(QuizModel.id == quiz_id).first()
        if not quiz:
            raise VersionServiceError(f"Quiz with ID '{quiz_id}' not found.")
        if not quiz.questions:
            raise VersionServiceError("Cannot generate versions for a quiz with no questions.")

        labels = version_labels or ["A", "B", "C"]
        generated_versions = []

        # Clear existing version mappings
        db.query(QuizVersionMappingModel).filter(QuizVersionMappingModel.quiz_id == quiz_id).delete()

        questions = list(quiz.questions)

        for label in labels:
            rnd = random.Random(f"{quiz.id}_{label}")
            shuffled_questions = list(questions)
            if label != "A":
                rnd.shuffle(shuffled_questions)

            q_order = [q.id for q in shuffled_questions]
            opt_order_map: dict[str, list[str]] = {}

            version_questions = []

            for q_idx, q in enumerate(shuffled_questions, start=1):
                opts = list(q.options)
                if label != "A":
                    rnd_opt = random.Random(f"{quiz.id}_{label}_{q.id}")
                    rnd_opt.shuffle(opts)

                opt_ids = [o.id for o in opts]
                opt_order_map[q.id] = opt_ids

                letters = ["A", "B", "C", "D"]
                version_options = []
                for o_idx, opt in enumerate(opts):
                    version_options.append({
                        "id": opt.id,
                        "option_letter": letters[o_idx % 4],
                        "option_text": opt.option_text,
                        "is_correct": opt.is_correct,
                    })

                version_questions.append({
                    "id": q.id,
                    "order_index": q_idx,
                    "question_text": q.question_text,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "explanation": q.explanation,
                    "evidence": q.evidence,
                    "source_page": q.source_page,
                    "options": version_options,
                })

            mapping = QuizVersionMappingModel(
                quiz_id=quiz_id,
                version_label=label,
                question_order_json=json.dumps(q_order),
                option_order_json=json.dumps(opt_order_map),
            )
            db.add(mapping)

            generated_versions.append({
                "version_label": label,
                "quiz_id": quiz_id,
                "quiz_title": quiz.title,
                "total_questions": len(version_questions),
                "questions": version_questions,
            })

        db.commit()
        return generated_versions
