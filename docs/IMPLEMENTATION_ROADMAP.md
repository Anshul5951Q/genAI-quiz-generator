# StudySet AI — Implementation Roadmap

**Version:** 1.0  
**Date:** 2026-11-24  
**Status:** Active

---

## Execution Phases

### Phase 0 — Audit (COMPLETE)
- [x] Repository inspection
- [x] Architecture documentation
- [x] PROJECT_AUDIT.md
- [x] IMPLEMENTATION_ROADMAP.md
- [x] ARCHITECTURE.md

---

### Phase 1 — Foundation & Authentication

**Goal:** Add JWT auth, RBAC, User model, Alembic setup without breaking existing APIs.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 1.1 | Add `python-jose[cryptography]`, `passlib[bcrypt]`, `alembic`, `aiohttp` to requirements | requirements.txt | Pending |
| 1.2 | Add Alembic configuration | alembic.ini, alembic/env.py | Pending |
| 1.3 | Create User model (id, email, hashed_password, role, is_active) | models/user.py | Pending |
| 1.4 | Create auth service (hashing, JWT create/verify) | services/auth_service.py | Pending |
| 1.5 | Create auth routes (register, login, refresh, me) | api/routes/auth.py | Pending |
| 1.6 | Add JWT middleware / dependency | core/security.py | Pending |
| 1.7 | Add RBAC permission system | core/permissions.py | Pending |
| 1.8 | Extend Settings with auth config | core/config.py | Pending |
| 1.9 | Create initial Alembic migration | alembic/versions/ | Pending |
| 1.10 | Add auth to main.py | main.py | Pending |
| 1.11 | Frontend: Auth context + Login/Register pages | frontend/src/ | Pending |
| 1.12 | Frontend: Protected route wrapper | frontend/src/ | Pending |

**Testing criteria:** Backend starts, /api/auth/register works, /api/auth/login returns JWT, protected routes return 401 without token.

---

### Phase 2 — Ollama & LLM Provider Extension

**Goal:** Add OllamaProvider, make primary provider configurable, preserve existing Groq/Gemini.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 2.1 | Add Ollama config to Settings | core/config.py | Pending |
| 2.2 | Implement OllamaProvider (async httpx calls) | services/llm_provider.py | Pending |
| 2.3 | Add AIOrchestrator (task routing) | services/ai_orchestrator.py | Pending |
| 2.4 | Add ProviderHealthService | services/provider_health.py | Pending |
| 2.5 | Add AIModelLog model | models/ai_log.py | Pending |
| 2.6 | Add AI admin routes | api/routes/admin.py | Pending |
| 2.7 | Add Alembic migration for ai_model_logs | alembic/versions/ | Pending |
| 2.8 | Update get_llm_provider() to check Ollama first | services/llm_provider.py | Pending |

**Testing criteria:** Health endpoint shows provider status. Groq generates successfully. OllamaProvider initializes without crashing when Ollama unavailable (graceful fallback).

---

### Phase 3 — Resume Intelligence Engine

**Goal:** Upload, parse, extract and store resume data.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 3.1 | Create uploads directory structure | backend/uploads/ | Pending |
| 3.2 | Add Resume, ResumeExtraction, ResumeSkill, ResumeProject models | models/resume.py | Pending |
| 3.3 | Add Alembic migration | alembic/versions/ | Pending |
| 3.4 | Implement resume file parsing service (PDF + DOCX) | services/resume_parser.py | Pending |
| 3.5 | Implement resume AI extraction service | services/resume_extractor.py | Pending |
| 3.6 | Implement resume API routes | api/routes/resumes.py | Pending |
| 3.7 | Add resume schemas | schemas/resume.py | Pending |
| 3.8 | Frontend: Resume upload page | frontend/src/pages/ResumeAnalyzerPage.tsx | Pending |
| 3.9 | Frontend: Resume analysis display | frontend/src/pages/ResumeDetailPage.tsx | Pending |

**Testing criteria:** Upload PDF resume → extraction JSON contains name, skills, projects. Upload DOCX resume → same. Invalid file type rejected. Missing fields handled gracefully.

---

### Phase 4 — Job Description Intelligence

**Goal:** Upload and analyze JDs, generate resume-JD matching.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 4.1 | Add JobDescription, JDRequirement models | models/job_description.py | Pending |
| 4.2 | Add Alembic migration | alembic/versions/ | Pending |
| 4.3 | Implement JD extraction service | services/jd_extractor.py | Pending |
| 4.4 | Implement resume-JD matching service | services/matching_service.py | Pending |
| 4.5 | Add JD API routes | api/routes/job_descriptions.py | Pending |
| 4.6 | Add matching API routes | api/routes/matching.py | Pending |
| 4.7 | Add JD schemas | schemas/job_description.py | Pending |
| 4.8 | Frontend: JD upload page | frontend/src/ | Pending |
| 4.9 | Frontend: Matching report page | frontend/src/ | Pending |

---

### Phase 5 — Interview Generation Engine

**Goal:** End-to-end interview configuration and question generation.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 5.1 | Add Interview, InterviewRound, InterviewQuestion models | models/interview.py | Pending |
| 5.2 | Add Alembic migration | alembic/versions/ | Pending |
| 5.3 | Implement interview blueprint service | services/interview_blueprint.py | Pending |
| 5.4 | Implement interview question generator | services/interview_question_generator.py | Pending |
| 5.5 | Add interview API routes | api/routes/interviews.py | Pending |
| 5.6 | Add interview schemas | schemas/interview.py | Pending |
| 5.7 | Frontend: Interview creation wizard (8 steps) | frontend/src/pages/InterviewCreatePage.tsx | Pending |
| 5.8 | Frontend: Question preview page | frontend/src/ | Pending |

---

### Phase 6 — Interactive Interview Engine

**Goal:** Interview session execution, adaptive questioning, session persistence.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 6.1 | Add InterviewSession, InterviewResponse models | models/interview_session.py | Pending |
| 6.2 | Add Alembic migration | alembic/versions/ | Pending |
| 6.3 | Implement session service | services/interview_session_service.py | Pending |
| 6.4 | Implement adaptive policy | services/adaptive_policy.py | Pending |
| 6.5 | Add session API routes | api/routes/interview_sessions.py | Pending |
| 6.6 | Frontend: Interview interface | frontend/src/pages/InterviewPage.tsx | Pending |

---

### Phase 7 — AI Answer Evaluation

**Goal:** Rubric-based text answer evaluation with structured output.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 7.1 | Add AnswerEvaluation model | models/evaluation.py | Pending |
| 7.2 | Implement evaluation service | services/evaluation_service.py | Pending |
| 7.3 | Add evaluation API routes | api/routes/evaluations.py | Pending |
| 7.4 | Add evaluation schemas | schemas/evaluation.py | Pending |
| 7.5 | Frontend: Evaluation report page | frontend/src/ | Pending |
| 7.6 | Coding assessment (editor UI + sandbox placeholder) | frontend/src/ + backend | Pending |

---

### Phase 8 — Analytics & Learning Intelligence

**Goal:** Performance dashboards, skill profiling, learning roadmap.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 8.1 | Add SkillProfile, LearningRecommendation models | models/learning.py | Pending |
| 8.2 | Implement interview analytics service | services/interview_analytics.py | Pending |
| 8.3 | Implement learning roadmap service | services/learning_roadmap.py | Pending |
| 8.4 | Add analytics API routes | api/routes/interview_analytics.py | Pending |
| 8.5 | Frontend: Performance Analytics page | frontend/src/pages/PerformanceAnalyticsPage.tsx | Pending |
| 8.6 | Frontend: Learning Roadmap page | frontend/src/pages/LearningRoadmapPage.tsx | Pending |

---

### Phase 9 — UI/UX Redesign

**Goal:** Complete SaaS-grade interface redesign.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 9.1 | Create new Sidebar layout component | frontend/src/components/Sidebar.tsx | Pending |
| 9.2 | Create AppLayout (Sidebar + main) | frontend/src/components/AppLayout.tsx | Pending |
| 9.3 | Redesign Dashboard | frontend/src/pages/DashboardPage.tsx | Pending |
| 9.4 | Redesign all existing academic pages | frontend/src/pages/ | Pending |
| 9.5 | Add design system tokens | frontend/src/index.css | Pending |
| 9.6 | Add Recharts for data visualization | package.json | Pending |
| 9.7 | Update App.tsx routing | frontend/src/App.tsx | Pending |

---

### Phase 10 — Production Readiness

**Goal:** Docker, CI, security hardening, documentation.

#### Tasks

| # | Task | Files Affected | Status |
|---|---|---|---|
| 10.1 | Dockerfile (backend) | Dockerfile.backend | Pending |
| 10.2 | Dockerfile (frontend) | Dockerfile.frontend | Pending |
| 10.3 | docker-compose.yml | docker-compose.yml | Pending |
| 10.4 | .env.example (complete) | .env.example | Pending |
| 10.5 | API rate limiting | main.py | Pending |
| 10.6 | Audit logging middleware | core/audit.py | Pending |
| 10.7 | Complete test suite | backend/tests/ | Pending |
| 10.8 | CHANGELOG.md | docs/CHANGELOG.md | Pending |
| 10.9 | USER_GUIDE.md | docs/USER_GUIDE.md | Pending |
| 10.10 | DEPLOYMENT.md | docs/DEPLOYMENT.md | Pending |

---

## Dependency Order

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 10
                 ↘ (can parallelize 2 + 3 after 1 is done)
```

Phases 3 and 4 can be developed in parallel after Phase 1 is complete.
Phases 5-7 depend on 3 and 4.
Phase 9 (UI redesign) proceeds in parallel with Phases 5-8.
