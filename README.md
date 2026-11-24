# StudySet: Automatic MCQ Quiz Generator (PS 97)

StudySet is a full-stack, production-quality academic web application that converts study material (PDFs, plain text documents, and lecture notes) into reliable, source-grounded multiple-choice quizzes with deterministic scoring and a two-stage question validation pipeline.

---

## Key Features

1. **Document Ingestion with Page Tracking**:
   - Text-based PDF extraction via **PyMuPDF (`fitz`)**, mapping extracted excerpts directly to page numbers.
   - Text file (`.txt`) upload with multi-encoding fallback (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`).
   - Direct pasted text with character counts and semantic paragraph chunking.
   - Transparent detection and user-friendly error messages for empty or scanned image-only PDFs.

2. **Source-Grounded Question Generation**:
   - Powered by official Google Gemini SDK (`gemini-2.5-flash` or configurable model).
   - Structured JSON schema enforcing exactly 4 distinct options (A–D), exactly 1 intended correct option, concise explanation, and traceable source quotation.
   - Balanced difficulty distribution (**Easy**, **Medium**, **Hard**, and **Mixed**).
   - Distributed question sampling across document sections to avoid clustering only on the introduction.
   - Built-in, clearly labeled **Offline Demo Mode** allowing complete evaluation even if no API key is set.

3. **Two-Stage Validation Pipeline**:
   - **Stage A (Deterministic)**: Checks exact option counts, option uniqueness, single answer key, non-empty fields, forbidden patterns (`all/none of the above`), near-duplicate detection, and whitespace-normalized evidence traceability.
   - **Stage B (Semantic Audit)**: Independent model audit verifying single best answer, distractor plausibility, and evidence alignment.
   - **Acceptance Policy**: Classifies questions into `PASS`, `REVIEW`, and `REJECT` with bounded retries (up to 2 corrective attempts).

4. **Answer-Key Integrity & Deterministic Scoring**:
   - Strict separation: Taking endpoints (`/api/quizzes/{id}/take`) **never** expose correct answers, explanations, or validation issues prior to submission.
   - Deterministic backend grading based on immutable answer keys stored in SQLite.
   - Double-submission prevention and unanswered question confirmation modal.
   - Score breakdown by difficulty and topic.

5. **Downloadable Exports**:
   - **Student PDF**: Clean printable examination without answers.
   - **Instructor PDF**: Complete exam with bold answer keys, explanations, and evidence citations.
   - **Spreadsheet CSV**: Full question table or student attempt results.

---

## Tech Stack

- **Backend**: Python 3.11+ / 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite, PyMuPDF, ReportLab, pytest, HTTPX, Ruff.
- **Frontend**: React 19, TypeScript (strict mode), Vite, Tailwind CSS v4, Lucide React, React Router v7.

---

## Prerequisites

- **Python**: 3.11, 3.12, or 3.13 installed
- **Node.js**: v18+ or v20+ / v22+ with `npm`
- **Operating System**: Windows (PowerShell commands documented below) or Linux/macOS

---

## Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app and lifespan hooks
│   │   ├── core/                # Configuration and structured logging
│   │   ├── db/                  # SQLAlchemy SQLite session and init_db
│   │   ├── models/              # Quiz, Question, Option, Attempt ORM models
│   │   ├── schemas/             # Pydantic v2 validation contracts
│   │   ├── services/            # Document parsing, chunking, LLM, validator, scoring, export
│   │   └── api/routes/          # Health, documents, quizzes, attempts, export endpoints
│   ├── tests/                   # 16 automated pytest unit and integration tests
│   ├── requirements.txt         # Pinned backend dependencies
│   ├── pytest.ini               # Pytest configuration
│   └── ruff.toml                # Ruff linter and formatter configuration
├── frontend/
│   ├── src/
│   │   ├── components/          # Navbar, Badge, Modal dialogs
│   │   ├── pages/               # HomePage, CreateQuizPage, QuizReviewPage, TakeQuizPage, ResultsPage, HistoryPage
│   │   ├── services/            # Typed fetch API client
│   │   ├── types/               # TypeScript data interfaces
│   │   ├── App.tsx              # React router layout
│   │   └── index.css            # Academic design tokens & Tailwind v4
│   ├── package.json
│   └── vite.config.ts           # Vite + Tailwind plugin and API proxy
├── .env.example                 # Root configuration template
├── .gitignore
└── README.md
```

---

## Quick Start (Windows PowerShell)

### Step 1: Backend Setup

Open a PowerShell terminal and navigate to the `backend` directory:

```powershell
cd "d:\Projects\Automatic MCQ Quiz Generator\backend"

# Install backend dependencies
pip install -r requirements.txt

# (Optional) Create .env from template
Copy-Item .env.example .env
```

#### Configuring the Gemini API Key
To use live LLM synthesis, edit `.env` and provide your Google Gemini API key:

```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> **Note on Demo Mode**: If `GEMINI_API_KEY` is not provided or left as placeholder, StudySet automatically operates in **Demo Mode**. You can still test the entire lifecycle (document extraction, quiz creation, review/editing, taking the test, deterministic scoring, and PDF/CSV exports) without any API key or credit card.

Start the FastAPI backend server:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Backend API: `http://127.0.0.1:8000`
- Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

---

### Step 2: Frontend Setup

Open a second PowerShell terminal and navigate to `frontend`:

```powershell
cd "d:\Projects\Automatic MCQ Quiz Generator\frontend"

# Start the Vite development server
npm run dev
```

Open your browser and navigate to:
```text
http://localhost:5173
```

---

## Running Automated Tests & Code Quality Checks

### Backend Quality Suite

Run from `backend` directory:

```powershell
cd "d:\Projects\Automatic MCQ Quiz Generator\backend"

# Run all 16 automated tests
python -m pytest tests -v

# Run Ruff linter
ruff check app

# Check formatting
ruff format --check app
```

### Frontend Type-Checking & Production Bundle

Run from `frontend` directory:

```powershell
cd "d:\Projects\Automatic MCQ Quiz Generator\frontend"

# Strict TypeScript type check and production bundle build
npm run build
```

---

## API Documentation & Routes

| HTTP Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check and LLM readiness |
| `POST` | `/api/documents/extract` | Upload & extract text from PDF or TXT |
| `POST` | `/api/quizzes/generate` | Generate MCQs with two-stage validation |
| `GET` | `/api/quizzes` | List all saved quizzes with latest scores |
| `GET` | `/api/quizzes/{id}` | Full review details (questions, answers, evidence) |
| `PATCH` | `/api/quizzes/{id}/questions/{qid}` | Edit question stem, options, or explanation |
| `DELETE` | `/api/quizzes/{id}/questions/{qid}` | Delete an individual question |
| `POST` | `/api/quizzes/{id}/questions/{qid}/regenerate` | Regenerate a single question with feedback |
| `POST` | `/api/quizzes/{id}/publish` | Seal quiz version for testing |
| `DELETE` | `/api/quizzes/{id}` | Delete quiz and its history |
| `POST` | `/api/quizzes/{id}/attempts` | Initialize a new attempt session |
| `GET` | `/api/quizzes/{id}/take` | Fetch sanitized questions (answers stripped) |
| `POST` | `/api/attempts/{id}/submit` | Submit answers and receive deterministic score |
| `GET` | `/api/attempts/{id}/results` | Fetch scored attempt results and explanations |
| `GET` | `/api/quizzes/{id}/export` | Export Student PDF, Instructor PDF, or CSV |
| `GET` | `/api/attempts/{id}/export` | Export attempt performance breakdown as CSV |

---

## Security & Answer-Key Secrecy

- **Zero Client-Side Secrets**: Frontend never touches `GEMINI_API_KEY`.
- **Pre-Submission Protection**: The `/api/quizzes/{id}/take` endpoint strips `is_correct`, explanations, evidence, and audit logs.
- **Deterministic Backend Scoring**: Submission calculates scores from the stored SQLite answer key. The LLM is never involved in grading.
- **Temporary Upload Safety**: Uploaded files are processed in-memory or via ephemeral paths and are never executed.
