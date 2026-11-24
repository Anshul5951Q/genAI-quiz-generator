# StudySet AI — User Guide & Product Walkthrough

Welcome to **StudySet AI** (*"Intelligent Assessment. Personalized Interviews. Measurable Growth."*). This guide walks you through both core modules: **Academic Assessment** and **AI Interview Intelligence**.

---

## 1. Getting Started & Authentication

### 1.1 Logging In & Roles
1. Navigate to `http://localhost:5173`.
2. Click **Sign Up** to create an account or **Sign In** with existing credentials.
3. Available Roles:
   - **Student / Candidate**: Take academic quizzes, analyze resumes, practice mock interviews, view personal learning roadmaps.
   - **Interviewer / Recruiter**: Upload candidate resumes, create job descriptions, configure interview blueprints, inspect candidate reports.
   - **Admin**: Full system management, user role updates, AI provider and model configuration, audit log inspection.

---

## 2. AI Interview Intelligence Module

### 2.1 Resume Analyzer
1. In the sidebar, click **Resume Analyzer**.
2. Click **Upload Resume** and select a `.pdf` or `.docx` file.
3. StudySet AI extracts:
   - **Contact & Profile**: Education, years of experience, current job title.
   - **Skills Taxonomy**: Languages, frameworks, databases, cloud tools, and conceptual principles.
   - **Project Intelligence**: Key accomplishments, tech stacks, and quantified business impact.
   - **Extraction Confidence**: System transparency rating on document legibility.

### 2.2 Job Description Matching
1. In the Resume Analyzer view, paste an active Job Description.
2. Click **Run Match Analysis**.
3. View Match Score, matched skills, missing prerequisites, and recommended interview focus areas.

### 2.3 Configuring an Interview Blueprint
1. Click **Interview Preparation** -> **Create Blueprint**.
2. Follow the 8-step wizard:
   - Step 1: Select target categories (Technical, Project-Based, HR, Behavioural, Coding, Managerial, Aptitude).
   - Step 2: Set Job Role & Target Experience Level.
   - Step 3: Choose Difficulty & Question Count (e.g. 10 questions, 30 minutes).
   - Step 4: Link candidate resume and target JD.
   - Step 5: Review question distribution.
3. Click **Generate Interview Blueprint**.

### 2.4 Taking an Interactive Mock Interview
1. Click **Start Session** on an interview blueprint.
2. An interactive timer begins counting down.
3. **Response Modes**:
   - **Text Mode**: Type your verbal technical response.
   - **Code Mode**: Write clean code in the integrated code editor.
4. **Adaptive Follow-up**: If your response is brief or lacks conceptual depth, the AI interviewer will automatically ask an adaptive follow-up prompt.
5. Click **Submit Interview** when finished.

### 2.5 Detailed Evaluation Report
- View overall score and breakdown across the 5 rubric criteria:
  - Technical Accuracy (35%)
  - Conceptual Depth (25%)
  - Completeness (20%)
  - Communication Clarity (10%)
  - Practical Examples (10%)
- Inspect specific strengths, improvement areas, and the model's reference answer for each question.

### 2.6 Learning Roadmap & Growth Intelligence
1. Navigate to **Insights** -> **Learning Roadmap**.
2. Review personalized skill milestones generated based on your weak areas.
3. Mark milestones as completed as you study to watch your skill mastery metrics grow.

---

## 3. Academic Assessment Module

### 3.1 Generating a Quiz
1. Click **Academic Assessment** -> **Create Assessment**.
2. Upload source material (PDF, PPTX, or TXT) or paste study notes.
3. Select difficulty, Bloom's taxonomy focus, and number of questions.
4. The engine splits text into semantic chunks, validates questions, eliminates duplicates, and generates a verified MCQ assessment.

### 3.2 Publishing & Examination
1. Create a student **Batch** and share the 6-character Join Code.
2. Click **Publish Assessment** to set scheduled test dates and duration.
3. Students join and take the assessment with randomized question ordering.
4. Review student attempt results with automated server-side deterministic grading.
5. Export quizzes to **PDF**, **DOCX**, **CSV**, or **Google Forms**.
