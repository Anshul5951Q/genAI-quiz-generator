# StudySet AI — Project Changelog

## [2.0.0] - 2026-11-24
### Major Evolution: Transformation from "Automatic MCQ Quiz Generator" to "StudySet AI"

#### Added
- **Core Architecture & Brand**:
  - Rebranded application to **StudySet AI** (*"Intelligent Assessment. Personalized Interviews. Measurable Growth."*).
  - Implemented modular backend domain architecture (`backend/app/modules/` and `backend/app/services/`).
  - Added dual SQLite and PostgreSQL support via SQLAlchemy ORM.
  - Added 29 relational database tables supporting authentication, resumes, job descriptions, interviews, evaluations, and skill profiles.
- **Security & RBAC**:
  - Passlib bcrypt password hashing with salt.
  - JWT access tokens (HS256) and refresh token rotation with revocation tracking.
  - Role-Based Access Control (`ADMIN`, `STUDENT`, `RECRUITER`, `INTERVIEWER`) with backend permission dependencies.
- **AI Engine & Local Inference**:
  - Added `OllamaProvider` connecting to local Ollama instances (`qwen3:4b`, `qwen2.5:3b`).
  - Multi-tier failover orchestration: Local Ollama -> Groq -> Google Gemini -> Demo.
  - JSON schema-constrained generation with Pydantic validation and regex extractors.
  - AI admin dashboard with health checks, live latency benchmarking, and execution logs.
- **AI Interview Intelligence**:
  - Resume ingestion and text parsing for PDF and DOCX files.
  - Structured candidate extraction (education, skills, projects, confidence score).
  - Job description requirement extraction and semantic resume-JD matching.
  - Interview blueprint wizard across 7 categories (Technical, Project-based, HR, Behavioural, Coding, Managerial, Aptitude).
  - Interactive live interview session with timer, code editor, and adaptive follow-up prompts.
  - Deterministic 5-criterion rubric scoring: Technical (35%), Depth (25%), Completeness (20%), Clarity (10%), Examples (10%).
  - Skill mastery tracking and dynamic personalized learning roadmap.
- **Frontend Modernization**:
  - Redesigned UI into a SaaS dashboard with dark collapsible sidebar, purple/blue accents, and Lucide icons.
  - 24 functional routes and views built with React Router 7 and Tailwind CSS v4.
  - Verified clean production build with Vite.

#### Preserved
- 100% of existing Academic Assessment capabilities:
  - Document ingestion (PDF, PPTX, TXT, pasted text).
  - MCQ generation with Bloom's taxonomy filtering and duplicate detection.
  - Batch management, student join codes, and publication scheduling.
  - Parallel exam versions (A, B, C) with randomized choices.
  - Deterministic server-side scoring without client answer key leakage.
  - Export to PDF, Word DOCX, CSV, and Google Forms JSON.
- All existing 10 quizzes, 77 questions, 308 options, 12 attempts, and 55 answers in `studyset.db`.

#### Fixed
- Windows WDAC / AppLocker execution blocks by switching SQLAlchemy to pure-Python execution.
- Pytest collection error when optional binary PyMuPDF is absent by adding `pypdf` fallback and graceful test skipping.
- Frontend TypeScript unused import and variable strictness flags.
- API service syntax closure in `frontend/src/services/api.ts`.
