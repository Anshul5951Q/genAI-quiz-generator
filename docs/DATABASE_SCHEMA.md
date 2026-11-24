# StudySet AI — Relational Database Schema & Architecture

## 1. Overview
StudySet AI uses SQLAlchemy ORM with multi-database compatibility (SQLite for local rapid development, PostgreSQL for scalable production deployments). The schema contains **29 relational tables** supporting both the **Academic Assessment** module and the **AI Interview Intelligence** module.

---

## 2. Entity-Relationship Overview

```
                                +-------------------+
                                |    users (RBAC)   |
                                +---------+---------+
                                          |
                +-------------------------+-------------------------+
                |                         |                         |
                v                         v                         v
     +--------------------+     +--------------------+    +--------------------+
     |      quizzes       |     |      resumes       |    | job_descriptions   |
     +---------+----------+     +---------+----------+    +---------+----------+
               |                          |                         |
               |                          +------------+------------+
               |                                       |
               v                                       v
     +--------------------+                  +--------------------+
     |     questions      |                  |  resume_jd_matches |
     +---------+----------+                  +--------------------+
               |                                       |
               v                                       v
     +--------------------+                  +--------------------+
     |      options       |                  |     interviews     |
     +--------------------+                  +---------+----------+
               |                                       |
               v                                       v
     +--------------------+                  +--------------------+
     |  batch_publications|                  |  interview_rounds  |
     +---------+----------+                  +---------+----------+
               |                                       |
               v                                       v
     +--------------------+                  +--------------------+
     |   quiz_attempts    |                  | interview_questions|
     +---------+----------+                  +---------+----------+
               |                                       |
               v                                       v
     +--------------------+                  +--------------------+
     |   student_answers  |                  | interview_sessions |
     +--------------------+                  +---------+----------+
                                                       |
                                             +---------+----------+
                                             |                    |
                                             v                    v
                                   +--------------------+ +--------------------+
                                   |interview_responses | | skill_profiles     |
                                   +---------+----------+ +--------------------+
                                             |
                                             v
                                   +--------------------+
                                   | answer_evaluations |
                                   +--------------------+
```

---

## 3. Detailed Table Dictionary

### 3.1 Identity & Access Management (IAM)
- **`users`**: Central authentication table.
  - `id` (VARCHAR PK): UUID v4.
  - `email` (VARCHAR UNIQUE, indexed): Primary user identity.
  - `hashed_password` (VARCHAR): Passlib/bcrypt salt + hash.
  - `full_name` (VARCHAR, nullable): Display name.
  - `role` (VARCHAR, default `STUDENT`): Role string (`ADMIN`, `STUDENT`, `RECRUITER`, `INTERVIEWER`).
  - `is_active` (BOOLEAN, default TRUE): Deactivation status.
  - `created_at`, `updated_at`, `last_login_at` (DATETIME).
- **`refresh_tokens`**: Rotating session tokens.
  - `id` (VARCHAR PK): UUID.
  - `user_id` (VARCHAR FK -> `users.id` on delete CASCADE).
  - `token_hash` (VARCHAR UNIQUE, indexed): SHA-256 hash of refresh token.
  - `expires_at` (DATETIME): Rotation expiry timestamp.
  - `revoked` (BOOLEAN, default FALSE).

### 3.2 Academic Assessment Module (Preserved & Enhanced)
- **`quizzes`**: Quiz parent entities with difficulty and source tracking.
- **`questions`**: MCQ questions linked to source chunk, Bloom's level, quality scores.
- **`options`**: 4 choices per question with `is_correct` boolean indicator.
- **`batches`**: Student batches / classes with unique alphanumeric `join_code`.
- **`batch_students`**: Junction table mapping enrolled students to batches.
- **`batch_publications`**: Exam publishing instances with scheduled windows and time limits.
- **`quiz_attempts`**: Student exam attempts with status (`in_progress`, `submitted`, `abandoned`).
- **`student_answers`**: Selected option IDs and deterministic grading marks.
- **`question_bank_items`**: Reusable question catalog with deduplication tags.

### 3.3 AI Interview Intelligence Module
- **`resumes`**: Uploaded candidate resumes (PDF / DOCX metadata and raw text).
- **`resume_extractions`**: Structured AI-parsed candidate identity, education, experience, summary, confidence score (0.00-1.00).
- **`resume_skills`**: Granular extracted skills with proficiency, category (`language`, `framework`, `database`, `cloud`, `concept`), and verification flag.
- **`resume_projects`**: Extracted project titles, descriptions, technologies used, and quantified metrics.
- **`job_descriptions`**: Company, title, raw JD, department, experience level.
- **`jd_requirements`**: Structured JD requirements split into `must_have`, `nice_to_have`, `domain_knowledge`, `behavioral`.
- **`resume_jd_matches`**: Calculated semantic and keyword overlap percentage, matched skills, missing skills, and interview focus recommendations.
- **`interviews`**: Configured interview blueprints with roles, difficulty, duration, question count, and category distributions.
- **`interview_rounds`**: Multi-round support (e.g. Round 1: Screening, Round 2: Architecture Deep Dive).
- **`interview_questions`**: Tailored interview questions with expected key concepts, difficulty, and category.
- **`interview_sessions`**: Active candidate interview runtime state (timers, status, final scores).
- **`interview_responses`**: Candidate responses (audio transcript / typed text / code submission) with response latency.
- **`answer_evaluations`**: Rubric scoring:
  - `technical_accuracy_score` (Weight: 35%)
  - `conceptual_depth_score` (Weight: 25%)
  - `completeness_score` (Weight: 20%)
  - `communication_clarity_score` (Weight: 10%)
  - `practical_examples_score` (Weight: 10%)
  - `overall_score` (0-100 weighted aggregate)
  - `feedback_markdown`, `strengths`, `improvements`, `model_ideal_answer`.

### 3.4 Growth & System Administration
- **`skill_profiles`**: Aggregated performance per skill across all academic quizzes and interview sessions.
- **`learning_recommendations`**: AI-generated remediation roadmaps with milestones, resources, and completion statuses.
- **`ai_model_logs`**: Latency, token usage, provider used, status, prompt metadata, and error tracing.
- **`audit_logs`**: Security audit trail tracking auth events, role changes, and administrative actions.

---

## 4. Indexing Strategy
- `users(email)`: Unique index for $O(1)$ authentication lookups.
- `refresh_tokens(token_hash)`: Fast token validation and revocation checks.
- `questions(quiz_id)` & `options(question_id)`: Foreign key index for instant assessment assembly.
- `quiz_attempts(publication_id, student_email)`: Composite index preventing duplicate submissions.
- `interview_questions(interview_id)`: Fast round-by-round retrieval.
- `interview_responses(session_id, question_id)`: Ordered chronological replay during evaluation.
- `skill_profiles(user_id, skill_name)`: Unique composite index for user mastery tracking.
