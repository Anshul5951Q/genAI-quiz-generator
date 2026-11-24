# StudySet AI — RESTful API Documentation

## 1. Overview
The StudySet AI backend provides **68 endpoints** covering Authentication, Academic Assessments, Resume Parsing, Job Description Analysis, Matchmaking, Interview Blueprints, Interactive Interview Sessions, Performance Analytics, and Admin Settings.

Base URL: `http://localhost:8000/api`

---

## 2. Authentication & Authorization
All authenticated routes require standard OAuth2 Bearer JWT authorization:
```http
Authorization: Bearer <access_token>
```

### Endpoints:
- `POST /api/auth/register`: Create user account (`email`, `password`, `full_name`, `role`).
- `POST /api/auth/login`: Authenticate and receive `access_token` and `refresh_token`.
- `POST /api/auth/refresh`: Rotate refresh token and obtain fresh access token.
- `GET /api/auth/me`: Get current authenticated user profile and permissions.
- `GET /api/auth/users`: List registered users (`ADMIN` only).
- `PUT /api/auth/users/{user_id}/role`: Update user role (`ADMIN` only).
- `DELETE /api/auth/users/{user_id}/deactivate`: Deactivate user account (`ADMIN` only).

---

## 3. Resume Analysis & Parsing
- `POST /api/resumes/upload`: Multipart file upload (PDF or DOCX). Parses text, extracts structured candidate identity, experience, skills, and projects using AI.
- `GET /api/resumes`: List all uploaded resumes for current user.
- `GET /api/resumes/{resume_id}`: Get metadata and parsed text for specific resume.
- `GET /api/resumes/{resume_id}/analysis`: Get comprehensive AI breakdown (taxonomy, skills, projects, confidence score).
- `DELETE /api/resumes/{resume_id}`: Remove resume and associated extractions.

---

## 4. Job Description & Matching
- `POST /api/job-descriptions`: Submit job title, company, and raw JD text. AI extracts structured requirements.
- `GET /api/job-descriptions`: List all processed job descriptions.
- `GET /api/job-descriptions/{jd_id}`: Get raw and structured requirements for a JD.
- `POST /api/matching/analyze`: Compute semantic & skill overlap between a resume and JD:
  ```json
  {
    "resume_id": "uuid",
    "jd_id": "uuid"
  }
  ```
  Returns:
  ```json
  {
    "match_score": 82.5,
    "matching_skills": ["FastAPI", "React", "Docker", "SQLAlchemy"],
    "missing_skills": ["Kubernetes", "Redis"],
    "recommendations": "Candidate possesses strong backend foundation but lacks distributed caching experience."
  }
  ```

---

## 5. Interview Configuration & Generation
- `POST /api/interviews`: Create configured interview blueprint:
  ```json
  {
    "name": "Full Stack Engineer Technical Interview",
    "job_role": "Full Stack Engineer",
    "target_categories": ["technical", "project-based", "coding"],
    "experience_level": "2-5",
    "difficulty": "medium",
    "num_questions": 10,
    "duration_minutes": 30,
    "resume_id": "uuid",
    "jd_id": "uuid"
  }
  ```
- `POST /api/interviews/{interview_id}/generate`: Trigger AI generation of customized questions and expected criteria.
- `GET /api/interviews`: List interviews.
- `GET /api/interviews/{interview_id}`: Retrieve interview details with rounds and questions.
- `DELETE /api/interviews/{interview_id}`: Delete interview blueprint.

---

## 6. Interactive Interview Execution & Evaluation
- `POST /api/interview-sessions/start`: Start a live interview session.
- `GET /api/interview-sessions/{session_id}`: Get session state, elapsed time, and current question.
- `POST /api/interview-sessions/{session_id}/responses`: Submit candidate answer (text or code). Generates adaptive follow-up prompt if conceptual depth is lacking.
- `POST /api/interview-sessions/{session_id}/submit`: Complete interview session and trigger synchronous/asynchronous rubric evaluation.
- `GET /api/interview-sessions/{session_id}/report`: Retrieve comprehensive evaluation report:
  - 5-part rubric score breakdown (Technical 35%, Conceptual 25%, Completeness 20%, Clarity 10%, Practical 10%).
  - Strengths and actionable improvement areas.
  - Model reference answer comparison.

---

## 7. Performance Analytics & Growth Intelligence
- `GET /api/interview-analytics/dashboard`: Key performance indicators (interviews completed, average score, skill radar, score trajectory).
- `GET /api/interview-analytics/skills`: Granular skill mastery breakdown across languages, frameworks, and architecture.
- `GET /api/interview-analytics/history`: Chronological interview history with score badges.
- `GET /api/interview-analytics/roadmap`: Dynamic personalized learning recommendations with status tracking.
- `PUT /api/interview-analytics/roadmap/{recommendation_id}/complete`: Mark recommendation milestone as completed.

---

## 8. Academic Assessment Module (Preserved)
- `POST /api/documents/extract`: Extract text from PDF, PPTX, or TXT.
- `POST /api/quizzes/generate`: Generate validated MCQ assessment from document chunks.
- `GET /api/quizzes/{quiz_id}`: Retrieve full quiz with questions and options.
- `POST /api/batches`: Create student batch.
- `POST /api/batches/{batch_id}/publications`: Publish assessment with scheduling.
- `POST /api/publications/{pub_id}/attempts`: Student starts timed attempt.
- `POST /api/attempts/{attempt_id}/submit`: Submit student answers with server-side grading.
- `GET /api/quizzes/{quiz_id}/export`: Export quiz in PDF, DOCX, CSV, or Google Forms JSON.

---

## 9. Administration & AI Monitoring
- `GET /api/admin/ai/providers`: View active LLM provider configurations.
- `GET /api/admin/ai/health`: Check health of Ollama, Gemini, Groq.
- `POST /api/admin/ai/test-connection`: Execute benchmark inference call and report latency.
- `GET /api/admin/ai/logs`: Inspect detailed AI execution logs.
- `POST /api/admin/ai/configuration`: Dynamically update active LLM provider and model settings.
