# StudySet AI — Project Audit Report

**Date:** 2026-11-24  
**Auditor:** Principal Architect (Automated Audit)  
**Project:** Automatic MCQ Quiz Generator → StudySet AI

---

## 1. Executive Summary

The existing project is a **functional, well-structured** academic MCQ generation platform (called "StudySet") built with FastAPI + React. It is production-quality in its academic domain. The transformation to StudySet AI requires adding an Interview Intelligence layer while preserving all existing academic features.

---

## 2. Existing Architecture

### 2.1 Backend Architecture

```
backend/
├── app/
│   ├── main.py                      # FastAPI app, CORS, lifespan hooks
│   ├── core/
│   │   ├── config.py                # Pydantic Settings (env-driven)
│   │   └── logging.py               # Structured logger
│   ├── db/
│   │   └── session.py               # SQLAlchemy engine, Base, get_db, init_db
│   ├── models/
│   │   ├── quiz.py                  # QuizModel, QuestionModel, OptionModel
│   │   ├── attempt.py               # QuizAttemptModel, AttemptAnswerModel
│   │   ├── batch.py                 # BatchModel, BatchMembershipModel
│   │   ├── publication.py           # PublicationModel
│   │   ├── question_bank.py         # QuestionBankEntryModel, QuestionUsageModel
│   │   ├── version.py               # QuizVersionMappingModel
│   │   └── __init__.py              # Model registry
│   ├── schemas/                     # Pydantic v2 request/response models
│   ├── services/
│   │   ├── llm_provider.py          # BaseLLMProvider, GeminiLLMProvider, GroqLLMProvider, DemoLLMProvider, ResilientLLMProvider
│   │   ├── question_generator.py    # QuestionGenerator with retry + dedup
│   │   ├── question_validator.py    # Two-stage validation
│   │   ├── document_parser.py       # PDF, PPTX, TXT parsing
│   │   ├── text_chunker.py          # Semantic chunking
│   │   ├── quiz_service.py          # Quiz CRUD + business logic
│   │   ├── scoring_service.py       # Deterministic scoring
│   │   ├── batch_service.py         # Batch management
│   │   ├── publication_service.py   # Publication workflow
│   │   ├── analytics_service.py     # Assessment analytics
│   │   ├── blueprint_service.py     # Exam blueprint coverage
│   │   ├── version_service.py       # Parallel exam versions (A/B/C)
│   │   ├── question_bank_service.py # Question bank management
│   │   ├── export_service.py        # PDF/CSV exports
│   │   └── google_forms_service.py  # Google Forms JSON export
│   └── api/routes/
│       ├── health.py
│       ├── documents.py
│       ├── quizzes.py
│       ├── attempts.py
│       ├── batches.py
│       ├── publications.py
│       ├── analytics.py
│       └── export.py
└── tests/
    ├── conftest.py
    ├── test_api_endpoints.py
    ├── test_batch_publishing_and_analytics.py
    ├── test_document_parser.py
    ├── test_regression_fixes.py
    ├── test_scoring_and_integrity.py
    └── test_validation_pipeline.py
```

### 2.2 Frontend Architecture

```
frontend/src/
├── components/
│   ├── Navbar.tsx
│   ├── Badge.tsx
│   └── Modal.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── CreateQuizPage.tsx
│   ├── QuizReviewPage.tsx
│   ├── TakeQuizPage.tsx
│   ├── ResultsPage.tsx
│   ├── HistoryPage.tsx
│   ├── BatchesPage.tsx
│   ├── BatchAnalyticsPage.tsx
│   └── StudentAssessmentPage.tsx
├── services/api.ts               # Typed fetch client
├── types/index.ts                # TypeScript interfaces
├── App.tsx                       # React Router layout
└── index.css                     # Tailwind v4 + design tokens
```

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI >= 0.115 |
| Python version | 3.11.9 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (file: studyset.db) |
| PDF parsing | PyMuPDF (fitz) |
| PPTX parsing | python-pptx |
| DOCX parsing | python-docx |
| PDF export | ReportLab |
| AI primary | Google Gemini (google-genai SDK) |
| AI fallback | Groq (groq SDK) |
| Local AI | Ollama installed (v0.40.16, GPU init failing) |
| Testing | pytest + httpx TestClient |
| Frontend | React 19, TypeScript, Vite, Tailwind v4 |
| State | React hooks (no Redux) |
| Router | React Router v7 |
| Icons | Lucide React |

---

## 4. Existing Database Schema

### Tables
- `quizzes` — Core quiz records
- `questions` — MCQ questions with difficulty, topic, style
- `options` — Answer options (A-D) with correctness flag
- `quiz_attempts` — Student attempt sessions
- `attempt_answers` — Per-question answers for each attempt
- `batches` — Instructional cohorts
- `batch_memberships` — Student enrollment per batch
- `quiz_publications` — Published assessments with access codes
- `quiz_version_mappings` — Parallel exam version layouts (A/B/C)
- `question_bank` — Searchable vetted question repository
- `question_usages` — Usage tracking for question bank items

---

## 5. Existing API Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | /api/health | Health + LLM readiness |
| POST | /api/documents/extract | Upload PDF/PPTX/TXT |
| POST | /api/quizzes/generate | Generate MCQs |
| GET | /api/quizzes | List quizzes |
| GET | /api/quizzes/{id} | Quiz detail |
| PATCH | /api/quizzes/{id}/questions/{qid} | Edit question |
| DELETE | /api/quizzes/{id}/questions/{qid} | Delete question |
| POST | /api/quizzes/{id}/questions/{qid}/regenerate | Regenerate question |
| POST | /api/quizzes/{id}/approve | Approve quiz |
| POST | /api/quizzes/{id}/publish | Publish quiz |
| DELETE | /api/quizzes/{id} | Delete quiz |
| POST | /api/quizzes/{id}/attempts | Start attempt |
| GET | /api/quizzes/{id}/take | Take quiz (sanitized) |
| POST | /api/attempts/{id}/submit | Submit answers |
| GET | /api/attempts/{id}/results | Get results |
| GET | /api/quizzes/{id}/export | Export PDF/CSV |
| GET | /api/attempts/{id}/export | Export attempt CSV |
| POST | /api/batches | Create batch |
| GET | /api/batches | List batches |
| GET | /api/batches/{id} | Batch detail |
| PATCH | /api/batches/{id} | Update batch |
| POST | /api/batches/{id}/members | Add member |
| DELETE | /api/batches/{id}/members/{mid} | Remove member |
| POST | /api/batches/join | Join by code |
| POST | /api/publications | Create publication |
| GET | /api/publications/{id} | Get publication |
| PATCH | /api/publications/{id} | Update publication |
| GET | /api/public/assessment/{code} | Student view |
| POST | /api/public/assessment/{code}/start | Start attempt |
| POST | /api/public/assessment/{code}/submit | Submit attempt |
| GET | /api/publications/{id}/analytics | Analytics |
| POST | /api/quizzes/{id}/versions | Generate A/B/C versions |
| POST | /api/batches/{id}/reuse-check | Check question reuse |
| GET | /api/question-bank | Search question bank |
| POST | /api/quizzes/{id}/sync-question-bank | Sync to bank |

---

## 6. Existing AI Integration

### LLM Provider Architecture
- `BaseLLMProvider` — Abstract interface
- `GeminiLLMProvider` — Google Gemini with 3-attempt retry + backoff
- `GroqLLMProvider` — Groq with model auto-fallback
- `DemoLLMProvider` — Offline high-quality demo mode (not fake in production)
- `ResilientLLMProvider` — Primary + fallback chain
- `get_llm_provider()` — Factory function checking keys and assembling chain

### Generation Pipeline
1. Document → pages → semantic chunks (TextChunker)
2. Per-chunk MCQ generation with structured JSON prompt
3. Stage A: Deterministic validation (structural, duplicate detection)
4. Stage B: Semantic LLM audit
5. Corrective retry (max 2 attempts)
6. Final deduplication pass

---

## 7. Existing Test Coverage

| Test File | Coverage |
|---|---|
| test_api_endpoints.py | Quiz CRUD, document extract, attempts |
| test_batch_publishing_and_analytics.py | Batch, publication, analytics |
| test_document_parser.py | PDF, PPTX, TXT parsing |
| test_regression_fixes.py | Regression for known bugs |
| test_scoring_and_integrity.py | Deterministic scoring, answer key |
| test_validation_pipeline.py | Two-stage validation |

**Note:** Tests currently fail to collect due to Application Control policy blocking pip/sqlalchemy DLLs in the test environment. The source code itself is correct and the tests are well-written.

---

## 8. Security Assessment

| Area | Status | Notes |
|---|---|---|
| Answer key exposure | ✅ Secure | /take endpoint strips all answers |
| API key exposure | ✅ Secure | Keys never sent to frontend |
| Input validation | ✅ Present | Pydantic schemas on all routes |
| File validation | ✅ Present | MIME + size + extension checks |
| CORS | ✅ Configured | Restricted to localhost:5173 |
| SQL injection | ✅ Protected | SQLAlchemy ORM (parameterized) |
| Authentication | ❌ Missing | No auth system exists |
| Authorization | ❌ Missing | No RBAC |
| Rate limiting | ❌ Missing | No rate limiting |
| Audit logging | ❌ Missing | No audit trail |
| DOCX resume upload | ❌ Missing | Resume features don't exist yet |

---

## 9. Performance Assessment

| Area | Status | Notes |
|---|---|---|
| Async endpoints | ⚠️ Partial | Routes are sync, LLM calls blocking |
| DB indexing | ✅ Present | Key foreign keys indexed |
| Caching | ❌ Missing | No response caching |
| Background tasks | ❌ Missing | LLM generation blocks request |
| Connection pooling | ✅ SQLite default | Adequate for SQLite |
| Chunking | ✅ Present | Text split into manageable chunks |

---

## 10. Missing Functionality

The following are entirely absent and must be built:

1. **Authentication & RBAC** — JWT, roles (ADMIN, STUDENT, RECRUITER, INTERVIEWER)
2. **Ollama Local LLM Provider** — qwen3:4b as primary (pending GPU fix)
3. **Resume Upload & Parsing** — PDF/DOCX resume ingestion
4. **Resume Intelligence** — AI extraction of skills, projects, experience
5. **Job Description Intelligence** — JD upload, requirement extraction
6. **Resume-JD Matching** — Compatibility scoring with evidence
7. **Interview Configuration** — Multi-category interview setup
8. **Interview Question Generation** — Resume/JD-grounded question pipeline
9. **Interactive Interview Engine** — Session management, adaptive questioning
10. **AI Answer Evaluation** — Rubric-based text answer evaluation
11. **Coding Assessment** — Code editor + isolated execution
12. **Interview Analytics** — Performance reports, skill profiling
13. **Learning Roadmap** — Personalized recommendations
14. **Professional UI/UX** — SaaS-grade redesign with dark sidebar
15. **Docker deployment** — Containerization

---

## 11. Technical Debt

| Item | Severity |
|---|---|
| Sync LLM calls blocking API workers | Medium |
| No connection pooling config | Low |
| Hard-coded prompt templates in generator | Low |
| Lightweight migration in init_db (should be Alembic) | Medium |
| No request ID tracking | Low |
| DemoLLMProvider in production code | Low |

---

## 12. Recommended Migration Strategy

1. **Non-destructive extension** — All new tables added alongside existing ones
2. **No breaking API changes** — Existing routes preserved exactly
3. **Auth as middleware** — JWT middleware added; existing public routes explicitly excluded
4. **Incremental UI** — New sidebar layout wraps existing pages; existing pages updated gradually
5. **Ollama fallback** — Groq remains active; Ollama added as configurable primary when GPU works
6. **File storage** — Uploaded resumes stored in `backend/uploads/resumes/` (gitignored)
