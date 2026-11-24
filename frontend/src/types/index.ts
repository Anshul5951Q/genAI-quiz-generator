export type DifficultyLevel = "easy" | "medium" | "hard" | "mixed";
export type ValidationVerdict = "pass" | "review" | "reject";
export type SourceType = "pdf" | "txt" | "pasted" | "pptx" | "ppt";
export type QuizOrigin = "demo" | "document_generated";

export interface OptionReview {
  id: string;
  option_letter: string;
  option_text: string;
  is_correct: boolean;
}

export interface OptionAttempt {
  id: string;
  option_letter: string;
  option_text: string;
}

export interface QuestionReview {
  id: string;
  quiz_id: string;
  question_text: string;
  explanation: string;
  evidence: string;
  source_page?: number | null;
  topic: string;
  difficulty: "easy" | "medium" | "hard";
  distractor_rationale?: string | null;
  validation_status: ValidationVerdict;
  validation_issues: string[];
  order_index: number;
  options: OptionReview[];
}

export interface QuestionTaking {
  id: string;
  question_text: string;
  order_index: number;
  options: OptionAttempt[];
}

export interface QuestionResult {
  id: string;
  question_text: string;
  order_index: number;
  topic: string;
  difficulty: string;
  explanation: string;
  evidence: string;
  source_page?: number | null;
  options: OptionReview[];
  selected_option_id: string | null;
  correct_option_id: string;
  is_correct: boolean;
}

export interface ValidationSummary {
  total_generated: number;
  passed_count: number;
  flagged_review_count: number;
  regenerated_count: number;
  rejected_count: number;
}

export type ApprovalStatus = "draft" | "under_review" | "approved" | "published";

export interface QuizSummary {
  id: string;
  title: string;
  source_type: SourceType;
  source_filename?: string | null;
  question_count: number;
  difficulty: string;
  status: "draft" | "published";
  approval_status?: ApprovalStatus;
  batch_id?: string | null;
  is_demo: boolean;
  quiz_origin?: QuizOrigin;
  created_at: string;
  latest_score_percentage?: number | null;
  latest_attempt_id?: string | null;
  attempts_count: number;
}

export interface QuizDetail {
  id: string;
  title: string;
  source_type: SourceType;
  source_filename?: string | null;
  difficulty: DifficultyLevel;
  target_count: number;
  topic_focus?: string | null;
  status: "draft" | "published";
  approval_status?: ApprovalStatus;
  batch_id?: string | null;
  question_style?: string;
  version: number;
  is_demo: boolean;
  quiz_origin?: QuizOrigin;
  created_at: string;
  updated_at: string;
  questions: QuestionReview[];
  validation_summary?: ValidationSummary | null;
}

export interface BatchMember {
  id: string;
  batch_id: string;
  learner_name: string;
  learner_email: string;
  learner_identifier?: string | null;
  enrolled_at: string;
}

export interface BatchSummary {
  id: string;
  name: string;
  description?: string | null;
  join_code: string;
  is_archived: boolean;
  created_at: string;
  member_count: number;
  publication_count: number;
}

export interface BatchDetail extends BatchSummary {
  members: BatchMember[];
  publications: PublicationSummary[];
}

export interface PublicationSummary {
  id: string;
  quiz_id: string;
  batch_id: string;
  quiz_title: string;
  access_code: string;
  instructions?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  time_limit_minutes?: number | null;
  max_attempts: number;
  is_active: boolean;
  negative_marking: boolean;
  answer_visibility: string;
  created_at: string;
  attempts_count: number;
}

export interface StudentAssessmentView {
  id: string;
  quiz_title: string;
  batch_name?: string | null;
  access_code: string;
  instructions?: string | null;
  time_limit_minutes?: number | null;
  negative_marking: boolean;
  questions: QuestionTaking[];
}

export interface StudentAttemptStartResponse {
  attempt_id: string;
  publication_id: string;
  quiz_title: string;
  started_at: string;
  time_limit_minutes?: number | null;
  expires_at?: string | null;
  total_questions: number;
}

export interface StudentAttemptResultResponse {
  attempt_id: string;
  publication_id: string;
  quiz_title: string;
  score_percentage: number;
  marks_obtained: number;
  total_marks: number;
  total_questions: number;
  correct_count: number;
  unanswered_count: number;
  completed_at: string;
  answer_visibility: string;
  breakdown_by_topic: ScoreBreakdownItem[];
  breakdown_by_difficulty: ScoreBreakdownItem[];
}

export interface QuestionAnalyticsItem {
  question_id: string;
  order_index: number;
  question_text: string;
  topic: string;
  difficulty: string;
  correct_percentage: number;
  unanswered_count: number;
  most_common_wrong_letter?: string | null;
  most_common_wrong_text?: string | null;
  is_confusing_flag: boolean;
}

export interface TopicMasteryItem {
  topic: string;
  total_questions: number;
  average_mastery_percentage: number;
}

export interface LearnerResultItem {
  attempt_id: string;
  learner_name?: string | null;
  learner_email?: string | null;
  learner_id?: string | null;
  score: number;
  total_questions: number;
  score_percentage: number;
  marks_obtained: number;
  total_marks: number;
  version_label: string;
  completed_at?: string | null;
}

export interface FullBatchAnalytics {
  overview: {
    batch_id?: string | null;
    batch_name?: string | null;
    publication_id: string;
    quiz_title: string;
    eligible_learners: number;
    started_learners: number;
    submitted_learners: number;
    completion_rate: number;
    average_score_percentage: number;
    median_score_percentage: number;
    highest_score_percentage: number;
    lowest_score_percentage: number;
    score_distribution: Record<string, number>;
  };
  question_analytics: QuestionAnalyticsItem[];
  topic_analytics: TopicMasteryItem[];
  learner_results: LearnerResultItem[];
}

export interface ExamBlueprint {
  target_count: number;
  difficulty_distribution: {
    easy: number;
    medium: number;
    hard: number;
  };
  include_topics: string[];
  exclude_topics: string[];
  question_style: string;
  time_limit_minutes?: number | null;
  negative_marking: boolean;
  show_explanations: boolean;
}

export interface QuizVersionInfo {
  version_label: string;
  quiz_id: string;
  question_count: number;
  questions: {
    order_index: number;
    question_id: string;
    question_text: string;
    options: {
      option_letter: string;
      option_text: string;
      is_correct: boolean;
    }[];
  }[];
}

export interface QuizTakingView {
  id: string;
  title: string;
  version: number;
  total_questions: number;
  questions: QuestionTaking[];
}

export interface ScoreBreakdownItem {
  category: string;
  total: number;
  correct: number;
  percentage: number;
}

export interface AttemptResult {
  attempt_id: string;
  quiz_id: string;
  quiz_title: string;
  started_at: string;
  completed_at: string;
  score: number;
  total_questions: number;
  unanswered_count: number;
  score_percentage: number;
  difficulty_breakdown: ScoreBreakdownItem[];
  topic_breakdown: ScoreBreakdownItem[];
  questions: QuestionResult[];
}

export interface AttemptStartResponse {
  attempt_id: string;
  quiz_id: string;
  quiz_title: string;
  quiz_version: number;
  total_questions: number;
  started_at: string;
}

export interface HealthStatus {
  status: string;
  environment: string;
  llm_provider: string;
  llm_model: string;
  gemini_api_key_configured: boolean;
  groq_api_key_configured?: boolean;
  ai_provider_configured?: boolean;
  active_providers?: string[];
  gemini_model?: string;
  groq_model?: string;
  demo_mode_available: boolean;
}

export interface PageContent {
  page_number: number;
  text: string;
  char_count: number;
}

export interface DocumentExtractResult {
  source_type: SourceType;
  filename?: string | null;
  total_characters: number;
  pages: PageContent[];
  full_text: string;
}
// ============================================================
// StudySet AI 2.0 — Extended TypeScript Interfaces
// ============================================================

export type UserRole = "ADMIN" | "STUDENT" | "RECRUITER" | "INTERVIEWER";

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: UserRole;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// --- Resume Intelligence ---

export interface ResumeSkill {
  name: string;
  category: string;
}

export interface ResumeProject {
  id: string;
  title: string;
  description?: string | null;
  problem_statement?: string | null;
  technologies: string[];
  architecture?: string | null;
  contribution?: string | null;
  key_features: string[];
  achievements?: string | null;
  concepts: string[];
}

export interface ResumeAnalysis {
  resume_id: string;
  filename: string;
  status: string;
  candidate_name?: string | null;
  email?: string | null;
  phone?: string | null;
  extraction_confidence: number;
  technical_skills: string[];
  programming_languages: string[];
  frameworks: string[];
  databases: string[];
  tools: string[];
  all_skills: ResumeSkill[];
  education: Array<{ degree?: string; institution?: string; year?: string; field?: string }>;
  experience: Array<{ title?: string; company?: string; duration?: string; responsibilities?: string[] }>;
  internships: Array<{ title?: string; company?: string; duration?: string }>;
  certifications: string[];
  achievements: string[];
  projects: ResumeProject[];
}

export interface ResumeSummary {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  created_at: string;
}

// --- Job Description Intelligence ---

export interface JDRequirement {
  text: string;
  category: string;
  is_required: boolean;
}

export interface JDAnalysis {
  jd_id: string;
  title: string;
  company?: string | null;
  status: string;
  experience_range: string;
  education_requirement?: string | null;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  domain_knowledge: string[];
  soft_skills: string[];
  requirements: JDRequirement[];
}

export interface JDSummary {
  id: string;
  title: string;
  company?: string | null;
  status: string;
  created_at: string;
}

// --- Resume-JD Matching ---

export interface MatchingResult {
  id: string;
  resume_id: string;
  jd_id: string;
  compatibility_score: number;
  matching_skills: Array<{ skill: string; evidence?: string; strength?: string }>;
  missing_skills: Array<{ skill: string; importance?: string }>;
  partial_matches: Array<{ requirement: string; evidence?: string; gap?: string }>;
  weak_areas: string[];
  strengths: string[];
  recommendations: string[];
  interview_focus: string[];
  created_at: string;
}

// --- Interview Intelligence ---

export type InterviewCategory =
  | "technical"
  | "hr"
  | "managerial"
  | "behavioural"
  | "coding"
  | "aptitude"
  | "project-based"
  | "mixed";

export interface InterviewSummary {
  id: string;
  name: string;
  job_role: string;
  experience_level: string;
  difficulty: string;
  num_questions: number;
  num_rounds: number;
  status: "draft" | "generating" | "ready" | "failed" | "archived";
  generation_progress: number;
  created_at: string;
}

export interface InterviewDetail extends InterviewSummary {
  resume_id?: string | null;
  jd_id?: string | null;
  categories: string[];
  duration_minutes?: number | null;
  custom_instructions?: string | null;
  questions_generated: number;
  rounds: Array<{ id: string; number: number; name: string; type: string }>;
}

export interface InterviewQuestionItem {
  id: string;
  question_text: string;
  category: string;
  difficulty: string;
  related_skill?: string | null;
  source_type: string;
  source_evidence?: string | null;
  expected_concepts: string[];
  rubric: Record<string, string>;
  max_score: number;
  suggested_time_seconds: number;
  order_index: number;
}

export interface QuestionTakingView {
  id: string;
  question_text: string;
  category: string;
  difficulty: string;
  related_skill?: string | null;
  suggested_time_seconds: number;
  order_index: number;
}

// --- Interview Session & Evaluation ---

export interface AnswerEvaluationFeedback {
  final_score: number;
  max_score: number;
  technical_accuracy_score?: number;
  conceptual_understanding_score?: number;
  completeness_score?: number;
  clarity_score?: number;
  practical_examples_score?: number;
  correct_concepts?: string[];
  missing_concepts: string[];
  incorrect_statements?: string[];
  strengths: string[];
  weaknesses: string[];
  suggested_improvement?: string | null;
  adaptive_signal?: string;
  model_confidence?: number;
}

export interface SubmitAnswerResult {
  response_id: string;
  question_id: string;
  is_skipped: boolean;
  evaluation?: AnswerEvaluationFeedback | null;
  adaptive_signal: string;
  session_progress: {
    answered: number;
    total_score: number;
    score_percentage: number;
  };
}

export interface SessionResponseItem {
  question_id: string;
  question_text: string;
  category: string;
  difficulty: string;
  answer_text?: string | null;
  is_skipped: boolean;
  time_taken_seconds: number;
  evaluation?: {
    final_score: number;
    max_score: number;
    technical_accuracy: number;
    conceptual_understanding: number;
    completeness: number;
    clarity: number;
    practical_examples: number;
    strengths: string[];
    weaknesses: string[];
    missing_concepts: string[];
    suggested_improvement?: string | null;
  } | null;
}

export interface InterviewReport {
  session_id: string;
  interview_name: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  total_score: number;
  max_possible_score: number;
  score_percentage: number;
  total_questions: number;
  answered_count: number;
  skipped_count: number;
  responses: SessionResponseItem[];
  category_breakdown: Array<{
    category: string;
    questions_answered: number;
    score_earned: number;
    max_score: number;
    percentage: number;
  }>;
}

// --- Analytics & Learning Roadmap ---

export interface CategoryPerformanceItem {
  category: string;
  questions: number;
  score_earned: number;
  max_score: number;
  percentage: number;
}

export interface DifficultyPerformanceItem {
  difficulty: string;
  questions: number;
  percentage: number;
}

export interface AnalyticsDashboardData {
  total_interviews: number;
  completed_interviews: number;
  average_score_percentage: number;
  best_score_percentage: number;
  total_questions_answered: number;
  category_performance: CategoryPerformanceItem[];
  difficulty_performance: DifficultyPerformanceItem[];
  recent_sessions: Array<{
    session_id: string;
    interview_name: string;
    score_percentage: number;
    started_at: string;
    completed_at?: string | null;
  }>;
}

export interface LearningRecommendation {
  id: string;
  topic: string;
  description?: string | null;
  priority: number;
  resources: string[];
  is_completed: boolean;
  created_at: string;
}

export interface LearningRoadmapData {
  recommendations: LearningRecommendation[];
  total: number;
  pending: number;
}

export interface SkillProfileItem {
  skill: string;
  category: string;
  proficiency_score: number;
  attempts: number;
  last_updated: string;
}

// --- Admin AI Settings ---

export interface AIProviderConfig {
  primary_provider: string;
  fallback_provider: string;
  providers: {
    ollama: {
      configured: boolean;
      base_url: string;
      model: string;
      timeout_seconds: number;
      num_ctx: number;
    };
    gemini: {
      configured: boolean;
      model: string;
      api_key_set: boolean;
    };
    groq: {
      configured: boolean;
      model: string;
      api_key_set: boolean;
    };
  };
}

export interface AIHealthStatus {
  ollama?: {
    status: string;
    latency_ms?: number;
    available_models?: string[];
    target_model?: string;
    target_model_available?: boolean;
    detail?: string;
  };
  gemini?: {
    status: string;
    detail?: string;
  };
  groq?: {
    status: string;
    latency_ms?: number;
    configured_model?: string;
    detail?: string;
  };
}
