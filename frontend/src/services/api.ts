import type {
  QuizSummary,
  QuizDetail,
  QuizTakingView,
  AttemptStartResponse,
  AttemptResult,
  HealthStatus,
  DocumentExtractResult,
  QuestionReview
} from '../types';

const API_BASE = '/api';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred.';
    try {
      const data = await response.json();
      if (data && data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new ApiError(errorDetail, response.status);
  }
  if (response.status === 204) {
    return {} as T;
  }
  return response.json();
}

export const api = {
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthStatus>(res);
  },

  async extractDocument(file?: File, pastedText?: string): Promise<DocumentExtractResult> {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    if (pastedText && pastedText.trim()) {
      formData.append('pasted_text', pastedText);
    }

    const res = await fetch(`${API_BASE}/documents/extract`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentExtractResult>(res);
  },

  async generateQuiz(payload: {
    title: string;
    source_text: string;
    source_type: string;
    source_filename?: string | null;
    num_questions: number;
    difficulty: string;
    topic_focus?: string | null;
    use_demo_mode: boolean;
  }): Promise<QuizDetail> {
    const res = await fetch(`${API_BASE}/quizzes/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<QuizDetail>(res);
  },

  async listQuizzes(): Promise<QuizSummary[]> {
    const res = await fetch(`${API_BASE}/quizzes`);
    return handleResponse<QuizSummary[]>(res);
  },

  async getQuiz(quizId: string): Promise<QuizDetail> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}`);
    return handleResponse<QuizDetail>(res);
  },

  async updateQuestion(
    quizId: string,
    questionId: string,
    updateData: {
      question_text?: string;
      explanation?: string;
      evidence?: string;
      source_page?: number | null;
      topic?: string;
      difficulty?: string;
      distractor_rationale?: string | null;
      options?: { id?: string; option_letter: string; option_text: string; is_correct: boolean }[];
      validation_status?: string;
    }
  ): Promise<QuestionReview> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/questions/${questionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData),
    });
    return handleResponse<QuestionReview>(res);
  },

  async deleteQuestion(quizId: string, questionId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/questions/${questionId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async regenerateQuestion(
    quizId: string,
    questionId: string,
    feedback?: string
  ): Promise<QuestionReview> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/questions/${questionId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback }),
    });
    return handleResponse<QuestionReview>(res);
  },

  async approveQuiz(quizId: string): Promise<QuizDetail> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/approve`, {
      method: 'POST',
    });
    return handleResponse<QuizDetail>(res);
  },

  async publishQuiz(quizId: string): Promise<QuizDetail> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/publish`, {
      method: 'POST',
    });
    return handleResponse<QuizDetail>(res);
  },

  async deleteQuiz(quizId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  // --- BATCH MANAGEMENT ---
  async listBatches(includeArchived = false) {
    const res = await fetch(`${API_BASE}/batches?include_archived=${includeArchived}`);
    return handleResponse<import('../types').BatchSummary[]>(res);
  },

  async createBatch(payload: { name: string; description?: string }) {
    const res = await fetch(`${API_BASE}/batches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').BatchDetail>(res);
  },

  async getBatch(batchId: string) {
    const res = await fetch(`${API_BASE}/batches/${batchId}`);
    return handleResponse<import('../types').BatchDetail>(res);
  },

  async updateBatch(batchId: string, payload: { name?: string; description?: string; is_archived?: boolean }) {
    const res = await fetch(`${API_BASE}/batches/${batchId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').BatchDetail>(res);
  },

  async archiveBatch(batchId: string) {
    const res = await fetch(`${API_BASE}/batches/${batchId}/archive`, {
      method: 'POST',
    });
    return handleResponse<import('../types').BatchSummary>(res);
  },

  async unarchiveBatch(batchId: string) {
    const res = await fetch(`${API_BASE}/batches/${batchId}/unarchive`, {
      method: 'POST',
    });
    return handleResponse<import('../types').BatchSummary>(res);
  },

  async addBatchMember(batchId: string, payload: { learner_name: string; learner_email: string; learner_identifier?: string }) {
    const res = await fetch(`${API_BASE}/batches/${batchId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').BatchMember>(res);
  },

  async removeBatchMember(batchId: string, memberId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/batches/${batchId}/members/${memberId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async joinBatch(payload: { join_code: string; learner_name: string; learner_email: string; learner_identifier?: string }) {
    const res = await fetch(`${API_BASE}/batches/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').BatchMember>(res);
  },

  // --- PUBLICATION & ONLINE ASSESSMENT ---
  async publishAssessment(payload: {
    quiz_id: string;
    batch_id: string;
    instructions?: string;
    start_time?: string;
    end_time?: string;
    time_limit_minutes?: number | null;
    max_attempts?: number;
    negative_marking?: boolean;
    answer_visibility?: string;
  }) {
    const res = await fetch(`${API_BASE}/publications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').PublicationSummary>(res);
  },

  async getStudentAssessment(accessCode: string) {
    const res = await fetch(`${API_BASE}/public/assessment/${accessCode}`);
    return handleResponse<import('../types').StudentAssessmentView>(res);
  },

  async startStudentAttempt(accessCode: string, payload: { learner_email: string; learner_name?: string }) {
    const res = await fetch(`${API_BASE}/public/assessment/${accessCode}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').StudentAttemptStartResponse>(res);
  },

  async submitStudentAttempt(
    accessCode: string,
    payload: {
      attempt_id: string;
      learner_email: string;
      answers: { question_id: string; selected_option_id: string | null }[];
    }
  ) {
    const res = await fetch(`${API_BASE}/public/assessment/${accessCode}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').StudentAttemptResultResponse>(res);
  },

  async getStudentResult(accessCode: string, attemptId: string, email: string) {
    const res = await fetch(`${API_BASE}/public/assessment/${accessCode}/results/${attemptId}?email=${encodeURIComponent(email)}`);
    return handleResponse<import('../types').StudentAttemptResultResponse>(res);
  },

  // --- ANALYTICS & VERSIONS ---
  async getPublicationAnalytics(publicationId: string) {
    const res = await fetch(`${API_BASE}/publications/${publicationId}/analytics`);
    return handleResponse<import('../types').FullBatchAnalytics>(res);
  },

  async generateVersions(quizId: string) {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/versions`, {
      method: 'POST',
    });
    return handleResponse<import('../types').QuizVersionInfo[]>(res);
  },

  async syncQuestionBank(quizId: string) {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/sync-question-bank`, {
      method: 'POST',
    });
    return handleResponse<{ synced_questions: number; message: string }>(res);
  },

  // --- ATTEMPTS & TAKING ---
  async startAttempt(quizId: string): Promise<AttemptStartResponse> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/attempts`, {
      method: 'POST',
    });
    return handleResponse<AttemptStartResponse>(res);
  },

  async getQuizForTaking(quizId: string): Promise<QuizTakingView> {
    const res = await fetch(`${API_BASE}/quizzes/${quizId}/take`);
    return handleResponse<QuizTakingView>(res);
  },

  async submitAttempt(
    attemptId: string,
    answers: { question_id: string; selected_option_id: string | null }[]
  ): Promise<AttemptResult> {
    const res = await fetch(`${API_BASE}/attempts/${attemptId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers }),
    });
    return handleResponse<AttemptResult>(res);
  },

  async getAttemptResult(attemptId: string): Promise<AttemptResult> {
    const res = await fetch(`${API_BASE}/attempts/${attemptId}/results`);
    return handleResponse<AttemptResult>(res);
  },

  getExportUrl(quizId: string, format: 'student_pdf' | 'instructor_pdf' | 'student_docx' | 'instructor_docx' | 'csv' | 'google_forms_json'): string {
    return `${API_BASE}/quizzes/${quizId}/export?format=${format}`;
  },

  getPublicationExportUrl(publicationId: string, format = 'csv'): string {
    return `${API_BASE}/publications/${publicationId}/export?format=${format}`;
  },

  getAttemptExportUrl(attemptId: string, format: 'csv' = 'csv'): string {
    return `${API_BASE}/attempts/${attemptId}/export?format=${format}`;
  },

  // ============================================================
  // StudySet AI 2.0 — Extended API Client
  // ============================================================

  // --- AUTHENTICATION & USERS ---
  async register(payload: { email: string; password: string; full_name?: string; role?: string }): Promise<import('../types').AuthTokens> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').AuthTokens>(res);
  },

  async login(payload: { email: string; password: string }): Promise<import('../types').AuthTokens> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').AuthTokens>(res);
  },

  async getMe(token?: string): Promise<import('../types').User> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/auth/me`, { headers });
    return handleResponse<import('../types').User>(res);
  },

  async listUsers(token?: string): Promise<import('../types').User[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/auth/users`, { headers });
    return handleResponse<import('../types').User[]>(res);
  },

  async updateUserRole(userId: string, role: string, token?: string): Promise<import('../types').User> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/auth/users/${userId}/role`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ role }),
    });
    return handleResponse<import('../types').User>(res);
  },

  // --- RESUME INTELLIGENCE ---
  async uploadResume(file: File, token?: string): Promise<{
    id: string;
    filename: string;
    file_type: string;
    file_size: number;
    status: string;
    created_at: string;
    extraction_confidence: number;
    candidate_name?: string | null;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/resumes/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return handleResponse(res);
  },

  async listResumes(token?: string): Promise<import('../types').ResumeSummary[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/resumes`, { headers });
    return handleResponse<import('../types').ResumeSummary[]>(res);
  },

  async getResumeAnalysis(resumeId: string): Promise<import('../types').ResumeAnalysis> {
    const res = await fetch(`${API_BASE}/resumes/${resumeId}/analysis`);
    return handleResponse<import('../types').ResumeAnalysis>(res);
  },

  async deleteResume(resumeId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/resumes/${resumeId}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  // --- JOB DESCRIPTION INTELLIGENCE ---
  async createJD(payload: { title: string; company?: string; content_text: string }, token?: string): Promise<import('../types').JDSummary> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/job-descriptions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').JDSummary>(res);
  },

  async listJDs(token?: string): Promise<import('../types').JDSummary[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/job-descriptions`, { headers });
    return handleResponse<import('../types').JDSummary[]>(res);
  },

  async getJDAnalysis(jdId: string): Promise<import('../types').JDAnalysis> {
    const res = await fetch(`${API_BASE}/job-descriptions/${jdId}/analysis`);
    return handleResponse<import('../types').JDAnalysis>(res);
  },

  // --- RESUME-JD MATCHING ---
  async analyzeMatch(payload: { resume_id: string; jd_id: string }): Promise<import('../types').MatchingResult> {
    const res = await fetch(`${API_BASE}/matching/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').MatchingResult>(res);
  },

  // --- INTERVIEW INTELLIGENCE ---
  async createInterview(payload: {
    name: string;
    job_role: string;
    experience_level: string;
    categories: string[];
    difficulty: string;
    num_questions: number;
    duration_minutes?: number | null;
    num_rounds?: number;
    difficulty_distribution?: Record<string, number> | null;
    resume_id?: string | null;
    jd_id?: string | null;
    custom_instructions?: string | null;
  }, token?: string): Promise<import('../types').InterviewSummary> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interviews`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').InterviewSummary>(res);
  },

  async listInterviews(token?: string): Promise<import('../types').InterviewSummary[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interviews`, { headers });
    return handleResponse<import('../types').InterviewSummary[]>(res);
  },

  async getInterview(interviewId: string): Promise<import('../types').InterviewDetail> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}`);
    return handleResponse<import('../types').InterviewDetail>(res);
  },

  async getInterviewQuestions(interviewId: string): Promise<{
    interview_id: string;
    interview_name: string;
    status: string;
    generation_progress: number;
    total_questions: number;
    questions: import('../types').InterviewQuestionItem[];
  }> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}/questions`);
    return handleResponse(res);
  },

  async triggerInterviewGeneration(interviewId: string): Promise<{ message: string; interview_id: string }> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}/generate`, { method: 'POST' });
    return handleResponse(res);
  },

  async deleteInterview(interviewId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}`, { method: 'DELETE' });
    return handleResponse<void>(res);
  },

  // --- INTERVIEW SESSIONS ---
  async startInterviewSession(interviewId: string, token?: string): Promise<{
    session_id: string;
    interview_id: string;
    interview_name: string;
    total_questions: number;
    max_possible_score: number;
    duration_minutes?: number | null;
    started_at: string;
    first_question?: import('../types').QuestionTakingView | null;
  }> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interview-sessions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ interview_id: interviewId }),
    });
    return handleResponse(res);
  },

  async getInterviewSession(sessionId: string): Promise<{
    session_id: string;
    status: string;
    current_question_index: number;
    total_questions: number;
    answered_count: number;
    total_score: number;
    max_possible_score: number;
    score_percentage: number;
    next_question?: import('../types').QuestionTakingView | null;
    is_complete: boolean;
  }> {
    const res = await fetch(`${API_BASE}/interview-sessions/${sessionId}`);
    return handleResponse(res);
  },

  async submitInterviewAnswer(
    sessionId: string,
    payload: {
      question_id: string;
      answer_text?: string | null;
      code_answer?: string | null;
      time_taken_seconds?: number;
      is_skipped?: boolean;
    }
  ): Promise<import('../types').SubmitAnswerResult> {
    const res = await fetch(`${API_BASE}/interview-sessions/${sessionId}/responses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<import('../types').SubmitAnswerResult>(res);
  },

  async submitInterviewSession(sessionId: string): Promise<{
    message: string;
    session_id: string;
    total_score: number;
    max_possible_score: number;
    score_percentage: number;
  }> {
    const res = await fetch(`${API_BASE}/interview-sessions/${sessionId}/submit`, { method: 'POST' });
    return handleResponse(res);
  },

  async getInterviewReport(sessionId: string): Promise<import('../types').InterviewReport> {
    const res = await fetch(`${API_BASE}/interview-sessions/${sessionId}/report`);
    return handleResponse<import('../types').InterviewReport>(res);
  },

  // --- ANALYTICS & LEARNING ROADMAP ---
  async getAnalyticsDashboard(token?: string): Promise<import('../types').AnalyticsDashboardData> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interview-analytics/dashboard`, { headers });
    return handleResponse<import('../types').AnalyticsDashboardData>(res);
  },

  async getSkillAnalysis(token?: string): Promise<{ skills: import('../types').SkillProfileItem[]; message?: string }> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interview-analytics/skills`, { headers });
    return handleResponse(res);
  },

  async getInterviewHistory(token?: string): Promise<{ sessions: any[]; total: number }> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interview-analytics/history`, { headers });
    return handleResponse(res);
  },

  async getLearningRoadmap(token?: string): Promise<import('../types').LearningRoadmapData> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/interview-analytics/learning-roadmap`, { headers });
    return handleResponse<import('../types').LearningRoadmapData>(res);
  },

  async markRecommendationComplete(recId: string): Promise<{ id: string; is_completed: boolean }> {
    const res = await fetch(`${API_BASE}/interview-analytics/learning-roadmap/${recId}/complete`, {
      method: 'PATCH',
    });
    return handleResponse(res);
  },

  // --- ADMIN AI SETTINGS ---
  async getAIProviders(token?: string): Promise<import('../types').AIProviderConfig> {
    const t = token || (typeof localStorage !== 'undefined' ? localStorage.getItem('studyset_token') : null);
    const headers: Record<string, string> = t ? { Authorization: `Bearer ${t}` } : {};
    const res = await fetch(`${API_BASE}/admin/ai/providers`, { headers });
    return handleResponse<import('../types').AIProviderConfig>(res);
  },

  async checkAIHealth(token?: string): Promise<import('../types').AIHealthStatus> {
    const t = token || (typeof localStorage !== 'undefined' ? localStorage.getItem('studyset_token') : null);
    const headers: Record<string, string> = t ? { Authorization: `Bearer ${t}` } : {};
    const res = await fetch(`${API_BASE}/admin/ai/health`, { headers });
    return handleResponse<import('../types').AIHealthStatus>(res);
  },

  async testAIConnection(token?: string): Promise<{ status: string; latency_ms: number; provider: string; response_preview: string }> {
    const t = token || (typeof localStorage !== 'undefined' ? localStorage.getItem('studyset_token') : null);
    const headers: Record<string, string> = t ? { Authorization: `Bearer ${t}` } : {};
    const res = await fetch(`${API_BASE}/admin/ai/test-connection`, {
      method: 'POST',
      headers,
    });
    return handleResponse(res);
  },

  async getAILogs(limit = 50, token?: string): Promise<{ logs: any[] }> {
    const t = token || (typeof localStorage !== 'undefined' ? localStorage.getItem('studyset_token') : null);
    const headers: Record<string, string> = t ? { Authorization: `Bearer ${t}` } : {};
    const res = await fetch(`${API_BASE}/admin/ai/logs?limit=${limit}`, { headers });
    return handleResponse(res);
  },

  async updateAIConfig(payload: { primary_provider?: string; ollama_model?: string; ollama_base_url?: string }, token?: string): Promise<any> {
    const t = token || (typeof localStorage !== 'undefined' ? localStorage.getItem('studyset_token') : null);
    const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(t ? { Authorization: `Bearer ${t}` } : {}) };
    const res = await fetch(`${API_BASE}/admin/ai/configuration`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  }
};
