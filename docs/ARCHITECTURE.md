# StudySet AI — System Architecture

**Version:** 2.0  
**Date:** 2026-11-24

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        StudySet AI                               │
│                                                                   │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │  React 19   │◄──►│  FastAPI Backend │◄──►│   SQLite DB    │  │
│  │  Vite + TS  │    │  Python 3.11     │    │  (studyset.db) │  │
│  │  Tailwind 4 │    │  SQLAlchemy 2.0  │    └────────────────┘  │
│  └─────────────┘    └────────┬─────────┘                        │
│                              │                                    │
│                    ┌─────────▼─────────┐                        │
│                    │  AI Orchestrator   │                        │
│                    └─────────┬─────────┘                        │
│                    ┌─────────┼──────────┐                       │
│                    ▼         ▼          ▼                       │
│              ┌──────────┐ ┌──────┐ ┌───────┐                   │
│              │  Ollama  │ │Gemini│ │ Groq  │                   │
│              │ (local)  │ │(API) │ │ (API) │                   │
│              └──────────┘ └──────┘ └───────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Backend Module Structure

```
backend/app/
├── core/
│   ├── config.py          # All env-driven settings (Pydantic Settings)
│   ├── security.py        # JWT create/verify, password hashing
│   ├── permissions.py     # RBAC decorators and role checks
│   ├── audit.py           # Audit log middleware
│   └── logging.py         # Structured logger
│
├── db/
│   └── session.py         # SQLAlchemy engine, Base, get_db
│
├── models/                # SQLAlchemy ORM models
│   ├── user.py            # User (auth, roles)
│   ├── quiz.py            # QuizModel, QuestionModel, OptionModel [EXISTING]
│   ├── attempt.py         # QuizAttemptModel, AttemptAnswerModel [EXISTING]
│   ├── batch.py           # BatchModel, BatchMembershipModel [EXISTING]
│   ├── publication.py     # PublicationModel [EXISTING]
│   ├── question_bank.py   # QuestionBankEntryModel [EXISTING]
│   ├── version.py         # QuizVersionMappingModel [EXISTING]
│   ├── resume.py          # Resume, ResumeExtraction, ResumeSkill, ResumeProject [NEW]
│   ├── job_description.py # JobDescription, JDRequirement [NEW]
│   ├── interview.py       # Interview, InterviewRound, InterviewQuestion [NEW]
│   ├── interview_session.py # InterviewSession, InterviewResponse [NEW]
│   ├── evaluation.py      # AnswerEvaluation [NEW]
│   ├── learning.py        # SkillProfile, LearningRecommendation [NEW]
│   └── ai_log.py          # AIModelLog, AuditLog [NEW]
│
├── schemas/               # Pydantic v2 request/response schemas
│
├── services/              # Business logic
│   ├── [existing services preserved]
│   ├── auth_service.py    # JWT, password, token management [NEW]
│   ├── llm_provider.py    # + OllamaProvider [EXTENDED]
│   ├── ai_orchestrator.py # Task routing, health, logging [NEW]
│   ├── resume_parser.py   # PDF + DOCX resume text extraction [NEW]
│   ├── resume_extractor.py # AI-driven resume field extraction [NEW]
│   ├── jd_extractor.py    # AI-driven JD requirement extraction [NEW]
│   ├── matching_service.py # Resume-JD compatibility scoring [NEW]
│   ├── interview_blueprint.py # Interview structure planning [NEW]
│   ├── interview_question_generator.py # AI question generation [NEW]
│   ├── interview_session_service.py # Session lifecycle [NEW]
│   ├── adaptive_policy.py # Adaptive questioning rules [NEW]
│   ├── evaluation_service.py # Answer rubric evaluation [NEW]
│   ├── interview_analytics.py # Performance analytics [NEW]
│   └── learning_roadmap.py # Learning recommendation engine [NEW]
│
└── api/routes/            # FastAPI routers
    ├── [existing routes preserved]
    ├── auth.py            # Register, login, refresh, me [NEW]
    ├── admin.py           # AI settings, user management [NEW]
    ├── resumes.py         # Resume CRUD + analysis [NEW]
    ├── job_descriptions.py # JD CRUD + analysis [NEW]
    ├── matching.py        # Resume-JD matching [NEW]
    ├── interviews.py      # Interview config + generation [NEW]
    ├── interview_sessions.py # Session lifecycle [NEW]
    └── interview_analytics.py # Analytics + roadmap [NEW]
```

---

## 3. Data Flow Diagrams

### 3.1 Academic Assessment Flow (Existing — Preserved)
```
Upload PDF/PPTX/TXT
       │
       ▼
DocumentParser → TextChunker → chunks[]
       │
       ▼
QuestionGenerator.generate_quiz_questions()
  ├── _prompt_generation() → LLM → JSON
  ├── QuestionValidator.evaluate_question() (Stage A: deterministic)
  ├── QuestionValidator (Stage B: semantic LLM audit)
  └── Deduplication
       │
       ▼
QuizService.save() → SQLite
       │
       ▼
Review → Approve → Publish → PublicationModel
       │
       ▼
Student takes quiz → AttemptModel → ScoringService (deterministic)
```

### 3.2 Interview Intelligence Flow (New)
```
Upload Resume (PDF/DOCX)
       │
       ▼
ResumeParser → text extraction
       │
       ▼
ResumeExtractor (Ollama/Gemini) → structured JSON
  ├── skills[], projects[], experience[], education[]
  └── Store in Resume + ResumeExtraction + ResumeSkill + ResumeProject
       │
Upload JD (text/PDF/DOCX)
       │
       ▼
JDExtractor (Ollama) → structured requirements
  └── Store in JobDescription + JDRequirement[]
       │
       ▼
MatchingService → compatibility_score, matching_skills, missing_skills
       │
       ▼
InterviewConfig (categories, difficulty, rounds, distribution)
       │
       ▼
InterviewBlueprint → question_allocation_plan
       │
       ▼
InterviewQuestionGenerator (batched)
  ├── Resume-grounded questions (project-specific)
  ├── JD-grounded questions (required skills)
  ├── Technical questions (general)
  └── Behavioural questions (STAR format)
       │
       ▼
Validation + Deduplication → InterviewQuestion[]
       │
       ▼
InterviewSession starts
  ├── Q1 displayed → candidate answers → saved
  ├── AdaptivePolicy evaluates previous answer
  │   ├── Strong → next harder question
  │   ├── Partial → follow-up generated
  │   └── Weak → foundational question
  └── Session completed
       │
       ▼
EvaluationService → AnswerEvaluation per question
  ├── Technical accuracy: 35%
  ├── Conceptual understanding: 25%
  ├── Completeness: 20%
  ├── Clarity: 10%
  └── Practical examples: 10%
       │
       ▼
InterviewReport → SkillProfile → LearningRecommendation
```

---

## 4. AI Provider Architecture

```
AIOrchestrator
├── route_task(task_type) → provider selection
├── OllamaProvider (primary when available)
│   ├── POST /api/generate (aiohttp async)
│   ├── Timeout: 180s
│   ├── Context: 8192 tokens
│   └── Model: qwen3:4b
├── GeminiLLMProvider (secondary / fallback)
│   ├── google-genai SDK
│   └── 3-attempt retry with backoff
├── GroqLLMProvider (tertiary fallback)
│   ├── groq SDK
│   └── Auto model selection from available list
└── DemoLLMProvider (offline demo only)
```

### Task Routing Table
| Task | Primary | Fallback |
|---|---|---|
| Resume extraction | Ollama | Gemini → Groq |
| JD extraction | Ollama | Gemini → Groq |
| MCQ generation | Ollama | Gemini → Groq |
| Interview question generation | Ollama | Gemini → Groq |
| Answer evaluation | Ollama | Gemini → Groq |
| Follow-up generation | Ollama | Gemini → Groq |

---

## 5. Authentication Architecture

```
POST /api/auth/login → JWT access_token (30min) + refresh_token (7d)
       │
All protected routes:
Authorization: Bearer <access_token>
       │
       ▼
get_current_user() dependency → decode JWT → User from DB
       │
require_role(["ADMIN", "RECRUITER"]) → RBAC check
```

### Roles
| Role | Access |
|---|---|
| ADMIN | All features, user management, AI config |
| STUDENT | Academic assessments, own interview sessions |
| RECRUITER | Interview creation, resume analysis, candidate management |
| INTERVIEWER | Interview session management, evaluation review |

---

## 6. Database Architecture

### New Tables (additive — no existing tables modified)

```sql
users (id, email, hashed_password, full_name, role, is_active, created_at)
resumes (id, user_id, filename, file_path, file_size, status, created_at)
resume_extractions (id, resume_id, raw_json, candidate_name, email, phone, extraction_confidence, created_at)
resume_skills (id, resume_id, skill_name, skill_category, proficiency_level)
resume_projects (id, resume_id, title, description, technologies_json, contribution, achievements)
job_descriptions (id, user_id, title, company, content_text, status, created_at)
jd_requirements (id, jd_id, requirement_text, category, is_required)
interviews (id, user_id, resume_id, jd_id, name, job_role, experience_level, status, config_json, created_at)
interview_rounds (id, interview_id, round_number, round_name, round_type)
interview_questions (id, interview_id, round_id, question_text, category, difficulty, source_type, expected_concepts_json, rubric_json, max_score, suggested_time_seconds)
interview_sessions (id, interview_id, user_id, status, started_at, completed_at, total_score, max_score)
interview_responses (id, session_id, question_id, answer_text, time_taken_seconds, is_skipped)
answer_evaluations (id, response_id, session_id, technical_score, conceptual_score, completeness_score, clarity_score, examples_score, final_score, max_score, strengths_json, weaknesses_json, model_confidence)
skill_profiles (id, user_id, skill_name, proficiency_level, last_updated)
learning_recommendations (id, user_id, topic, priority, resources_json, is_completed, created_at)
ai_model_logs (id, provider, model, task_type, prompt_tokens, latency_ms, success, error_message, created_at)
audit_logs (id, user_id, action, resource_type, resource_id, ip_address, created_at)
```

---

## 7. Frontend Architecture

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx         # Dark compact sidebar with nav groups
│   │   ├── AppLayout.tsx       # Sidebar + content area
│   │   └── TopBar.tsx          # Breadcrumb + user menu
│   ├── ui/                     # Reusable components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Modal.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── EmptyState.tsx
│   │   └── ErrorState.tsx
│   └── charts/                 # Analytics visualizations
│
├── pages/
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   ├── dashboard/
│   │   └── DashboardPage.tsx
│   ├── academic/               # Existing pages (preserved + restyled)
│   │   ├── CreateQuizPage.tsx
│   │   ├── QuizReviewPage.tsx
│   │   ├── TakeQuizPage.tsx
│   │   ├── ResultsPage.tsx
│   │   ├── HistoryPage.tsx
│   │   ├── BatchesPage.tsx
│   │   └── BatchAnalyticsPage.tsx
│   ├── interview/
│   │   ├── InterviewCreatePage.tsx
│   │   ├── InterviewPage.tsx
│   │   ├── InterviewHistoryPage.tsx
│   │   └── InterviewReportPage.tsx
│   ├── resume/
│   │   ├── ResumeAnalyzerPage.tsx
│   │   └── ResumeDetailPage.tsx
│   ├── analytics/
│   │   ├── PerformanceAnalyticsPage.tsx
│   │   └── LearningRoadmapPage.tsx
│   └── admin/
│       ├── UserManagementPage.tsx
│       ├── AISettingsPage.tsx
│       └── AuditLogsPage.tsx
│
├── contexts/
│   └── AuthContext.tsx
│
├── hooks/
│   ├── useAuth.ts
│   └── useApi.ts
│
├── services/
│   └── api.ts                  # Extended with new endpoints
│
└── types/
    └── index.ts                # Extended TypeScript interfaces
```

---

## 8. Security Architecture

| Concern | Solution |
|---|---|
| Authentication | JWT (HS256), 30min access token, 7d refresh token |
| Password storage | bcrypt with work factor 12 |
| Token storage | Frontend: httpOnly cookie or localStorage with XSS mitigations |
| RBAC | Backend decorator `require_role([...])` on all protected routes |
| Input validation | Pydantic v2 strict models on all request bodies |
| File validation | MIME type + extension + size + content checks |
| Answer key | Never exposed before submission (existing pattern preserved) |
| AI privacy | Resume/interview data routed to Ollama (local) by default |
| API keys | Never in frontend, never in logs |
| Rate limiting | slowapi middleware (10 req/s per IP on AI endpoints) |
| CORS | Explicit origin whitelist from environment |
| Audit trail | AuditLog model for all create/update/delete operations |
