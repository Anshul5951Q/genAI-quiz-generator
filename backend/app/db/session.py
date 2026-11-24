from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# For SQLite, check_same_thread=False allows multi-threaded requests in FastAPI
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import all models before create_all to ensure registration
    import app.models  # noqa: F401

    # create_all is safe and idempotent — it only creates missing tables
    Base.metadata.create_all(bind=engine)

    # Lightweight migration for existing SQLite database to add columns safely without data loss
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # 1. quizzes migrations
            res = conn.execute(text("PRAGMA table_info(quizzes)")).fetchall()
            quiz_cols = [r[1] for r in res]
            if "quiz_origin" not in quiz_cols:
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN quiz_origin VARCHAR(32) DEFAULT 'document_generated'"))
                conn.execute(text("UPDATE quizzes SET quiz_origin = 'demo' WHERE is_demo = 1"))
            if "approval_status" not in quiz_cols:
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN approval_status VARCHAR(20) DEFAULT 'draft'"))
            if "batch_id" not in quiz_cols:
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN batch_id VARCHAR(36) NULL"))
            if "blueprint_config" not in quiz_cols:
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN blueprint_config TEXT NULL"))

            # 2. questions migrations
            res = conn.execute(text("PRAGMA table_info(questions)")).fetchall()
            q_cols = [r[1] for r in res]
            if "question_style" not in q_cols:
                conn.execute(text("ALTER TABLE questions ADD COLUMN question_style VARCHAR(50) DEFAULT 'recall'"))

            # 3. quiz_attempts migrations
            res = conn.execute(text("PRAGMA table_info(quiz_attempts)")).fetchall()
            att_cols = [r[1] for r in res]
            if "publication_id" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN publication_id VARCHAR(36) NULL"))
            if "batch_id" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN batch_id VARCHAR(36) NULL"))
            if "learner_name" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN learner_name VARCHAR(255) NULL"))
            if "learner_email" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN learner_email VARCHAR(255) NULL"))
            if "learner_id" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN learner_id VARCHAR(100) NULL"))
            if "version_label" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN version_label VARCHAR(10) DEFAULT 'A'"))
            if "marks_obtained" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN marks_obtained FLOAT DEFAULT 0.0"))
            if "total_marks" not in att_cols:
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN total_marks FLOAT DEFAULT 0.0"))

            conn.commit()
    except Exception as e:
        import logging
        logging.getLogger("studyset").warning(f"Lightweight DB migration notice: {e}")
