# StudySet AI — AI Pipeline & Prompt Engineering

## 1. Pipeline Architecture
StudySet AI utilizes an adaptive, multi-tier AI orchestration pipeline designed to maximize accuracy, prevent hallucinations, and guarantee structured JSON generation across diverse LLM backends (Ollama local primary, Groq / Gemini cloud fallbacks).

```
   Raw Input (Resume / JD / Answer)
                  │
                  ▼
   Document Extraction & Cleaning
                  │
                  ▼
   Prompt Assembly & Few-Shot Ingestion
                  │
                  ▼
   AI Orchestrator (Ollama -> Groq -> Gemini)
                  │
                  ▼
   JSON Schema Extraction & Pydantic Validation
                  │
        ┌─────────┴─────────┐
        │ Valid             │ Invalid
        ▼                   ▼
   Persistence & Scoring   Bounded Retries & Error Handling
```

---

## 2. Extraction & Evaluation Modules

### 2.1 Resume Extraction Pipeline
- **Input**: Raw text extracted via PyMuPDF or `python-docx`.
- **System Prompt**: Instructs model to behave as an elite technical recruiter and parser.
- **Output Schema**:
  - `candidate_name`, `email`, `phone`, `education_summary`, `experience_years`, `current_title`.
  - `skills`: Categorized into `language`, `framework`, `database`, `cloud`, `concept` with confidence rating.
  - `projects`: Identified titles, technologies, and quantified accomplishments.
  - `overall_confidence`: Floating point score from 0.00 to 1.00 based on completeness of contact details, employment history, and education.

### 2.2 Job Description Analysis & Matching
- **Input**: Raw employer posting.
- **Output**: Core title, company, experience range, must-have requirements, nice-to-have requirements, and architectural domains.
- **Matching Metric**:
  $$\text{Match Score} = \left( 0.6 \times \frac{\text{Matched Must-Have}}{\text{Total Must-Have}} + 0.4 \times \frac{\text{Matched Nice-to-Have}}{\text{Total Nice-to-Have}} \right) \times 100$$

### 2.3 Contextual Question Blueprinting
Questions are generated across 7 supported interview categories:
1. `technical`: Core languages, architectural patterns, concurrency, memory management.
2. `project-based`: Probes into specific claims and metrics cited in candidate resume projects.
3. `hr`: Cultural alignment, career trajectory, expectations.
4. `behavioural`: Formulated using the STAR (Situation, Task, Action, Result) methodology.
5. `coding`: Algorithmic logic, edge case handling, time/space complexity trade-offs.
6. `managerial`: Prioritization, stakeholder communication, dispute resolution.
7. `aptitude`: Critical thinking, Fermi estimates, problem structuring.

### 2.4 Adaptive Follow-up Logic
When a candidate submits an answer during a live interview session:
- If response length < 25 words or conceptual depth is rated under 60%:
  The engine triggers an automated adaptive follow-up prompt:
  > *"Could you elaborate on how you handled edge cases or state synchronization in that design?"*

### 2.5 Rubric-Based Evaluation & Scoring
Every answer is scored deterministically against 5 core criteria:
1. **Technical Accuracy (35%)**: Factual precision, correct API usage, appropriate algorithmic choices.
2. **Conceptual Depth (25%)**: Understanding of underlying mechanics, trade-offs, and failure modes.
3. **Completeness (20%)**: Direct coverage of all facets requested by the question.
4. **Communication Clarity (10%)**: Structured, unambiguous explanation without filler.
5. **Practical Examples (10%)**: Inclusion of concrete scenarios, benchmarks, or real-world experience.

$$\text{Final Score} = 0.35 A_{\text{tech}} + 0.25 A_{\text{depth}} + 0.20 A_{\text{comp}} + 0.10 A_{\text{clarity}} + 0.10 A_{\text{examples}}$$

---

## 3. Resilient Failover Strategy
1. **Primary Provider (Local)**: `Ollama` running `qwen3:4b` or `qwen2.5:3b`.
2. **Fallback 1 (Cloud)**: `Groq` with high-speed Llama models.
3. **Fallback 2 (Cloud)**: `Google Gemini 2.5 Flash`.
4. **Safety Net**: Strict JSON regex extractors that locate `{` and `}` blocks within markdown-wrapped model responses.
