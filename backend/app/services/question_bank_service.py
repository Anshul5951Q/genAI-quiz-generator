import json
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.question_bank import QuestionBankEntryModel, QuestionUsageModel
from app.models.quiz import QuizModel
from app.services.question_validator import QuestionValidator


class QuestionBankService:
    @classmethod
    def sync_quiz_to_question_bank(cls, db: Session, quiz_id: str) -> int:
        """Adds approved questions from a quiz to the reusable Question Bank."""
        quiz = db.query(QuizModel).filter(QuizModel.id == quiz_id).first()
        if not quiz:
            return 0

        synced_count = 0
        now = datetime.now(UTC)

        for q in quiz.questions:
            if q.validation_status == "reject":
                continue

            stem_norm = QuestionValidator.normalize_stem(q.question_text)

            # Check if identical question already exists in bank
            existing = None
            all_entries = db.query(QuestionBankEntryModel).all()
            for entry in all_entries:
                if QuestionValidator.normalize_stem(entry.question_text) == stem_norm:
                    existing = entry
                    break

            options_data = [
                {
                    "option_letter": o.option_letter,
                    "option_text": o.option_text,
                    "is_correct": o.is_correct,
                }
                for o in q.options
            ]

            if existing:
                existing.times_used += 1
                existing.last_used_at = now
                entry_id = existing.id
            else:
                new_entry = QuestionBankEntryModel(
                    question_text=q.question_text,
                    options_json=json.dumps(options_data),
                    explanation=q.explanation,
                    evidence=q.evidence,
                    topic=q.topic,
                    difficulty=q.difficulty,
                    question_style=getattr(q, "question_style", "recall"),
                    source_filename=quiz.source_filename,
                    validation_verdict=q.validation_status,
                    times_used=1,
                    created_at=now,
                    last_used_at=now,
                )
                db.add(new_entry)
                db.flush()
                entry_id = new_entry.id
                synced_count += 1

            # Record usage
            usage = QuestionUsageModel(
                question_bank_id=entry_id,
                quiz_id=quiz.id,
                batch_id=quiz.batch_id,
                used_at=now,
            )
            db.add(usage)

        db.commit()
        return synced_count

    @classmethod
    def check_reuse_for_batch(
        cls,
        db: Session,
        batch_id: str,
        candidate_stems: list[str],
        window_days: int = 180,
    ) -> list[dict[str, Any]]:
        """
        Checks whether any candidate questions have already been used for the specified Batch
        within the given window, preventing repetitive assessments.
        """
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        query = (
            db.query(QuestionBankEntryModel)
            .join(QuestionUsageModel, QuestionUsageModel.question_bank_id == QuestionBankEntryModel.id)
            .filter(QuestionUsageModel.used_at >= cutoff)
        )
        if batch_id and batch_id != "all":
            query = query.filter(
                (QuestionUsageModel.batch_id == batch_id) | (QuestionUsageModel.batch_id.is_(None))
            )
        recent_usages = query.all()

        flags = []
        for stem in candidate_stems:
            norm_cand = QuestionValidator.normalize_stem(stem)
            for prior in recent_usages:
                norm_prior = QuestionValidator.normalize_stem(prior.question_text)
                sim = SequenceMatcher(None, norm_cand, norm_prior).ratio()
                if sim >= 0.75:
                    flags.append({
                        "candidate_stem": stem,
                        "previously_used_stem": prior.question_text,
                        "similarity": round(sim, 2),
                        "last_used_at": prior.last_used_at.isoformat(),
                        "topic": prior.topic,
                    })
                    break

        return flags

    @classmethod
    def search_question_bank(
        cls,
        db: Session,
        topic: str | None = None,
        difficulty: str | None = None,
        keyword: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Searches vetted questions in the Question Bank."""
        query = db.query(QuestionBankEntryModel)
        if topic:
            query = query.filter(func.lower(QuestionBankEntryModel.topic) == topic.strip().lower())
        if difficulty:
            query = query.filter(QuestionBankEntryModel.difficulty == difficulty.strip().lower())
        if keyword:
            query = query.filter(QuestionBankEntryModel.question_text.ilike(f"%{keyword.strip()}%"))

        entries = query.order_by(desc(QuestionBankEntryModel.times_used)).limit(limit).all()

        results = []
        for e in entries:
            try:
                opts = json.loads(e.options_json)
            except Exception:
                opts = []
            results.append({
                "id": e.id,
                "question_text": e.question_text,
                "topic": e.topic,
                "difficulty": e.difficulty,
                "question_style": e.question_style,
                "explanation": e.explanation,
                "evidence": e.evidence,
                "source_filename": e.source_filename,
                "times_used": e.times_used,
                "last_used_at": e.last_used_at,
                "options": opts,
            })
        return results
