import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';

// New StudySet AI Pages
import { DashboardPage } from './pages/DashboardPage';
import { AcademicHubPage } from './pages/AcademicHubPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ResumeAnalyzerPage } from './pages/ResumeAnalyzerPage';
import { InterviewListPage } from './pages/InterviewListPage';
import { InterviewCreatePage } from './pages/InterviewCreatePage';
import { InterviewDetailPage } from './pages/InterviewDetailPage';
import { InterviewSessionPage } from './pages/InterviewSessionPage';
import { InterviewReportPage } from './pages/InterviewReportPage';
import { InterviewHistoryPage } from './pages/InterviewHistoryPage';
import { PerformanceAnalyticsPage } from './pages/PerformanceAnalyticsPage';
import { LearningRoadmapPage } from './pages/LearningRoadmapPage';
import { SkillAssessmentPage } from './pages/SkillAssessmentPage';
import { QuestionBankPage } from './pages/QuestionBankPage';
import { AISettingsPage } from './pages/AISettingsPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

// Existing Academic Assessment Pages (100% Preserved!)
import { CreateQuizPage } from './pages/CreateQuizPage';
import { QuizReviewPage } from './pages/QuizReviewPage';
import { TakeQuizPage } from './pages/TakeQuizPage';
import { ResultsPage } from './pages/ResultsPage';
import { HistoryPage } from './pages/HistoryPage';
import { BatchesPage } from './pages/BatchesPage';
import { StudentAssessmentPage } from './pages/StudentAssessmentPage';
import { BatchAnalyticsPage } from './pages/BatchAnalyticsPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Primary Workspace */}
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />

          {/* Academic Assessment Module (Existing Preserved) */}
          <Route path="/academic" element={<AcademicHubPage />} />
          <Route path="/create" element={<CreateQuizPage />} />
          <Route path="/review/:quizId" element={<QuizReviewPage />} />
          <Route path="/take/:quizId" element={<TakeQuizPage />} />
          <Route path="/results/:attemptId" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/batches" element={<BatchesPage />} />
          <Route path="/batches/:batchId/analytics/:pubId" element={<BatchAnalyticsPage />} />
          <Route path="/take/published/:accessCode" element={<StudentAssessmentPage />} />

          {/* AI Interview Intelligence Module */}
          <Route path="/resumes" element={<ResumeAnalyzerPage />} />
          <Route path="/interviews" element={<InterviewListPage />} />
          <Route path="/interviews/create" element={<InterviewCreatePage />} />
          <Route path="/interviews/:interviewId" element={<InterviewDetailPage />} />
          <Route path="/interviews/:interviewId/start" element={<InterviewSessionPage />} />
          <Route path="/interview-sessions/:sessionId" element={<InterviewSessionPage />} />
          <Route path="/interview-sessions/:sessionId/report" element={<InterviewReportPage />} />
          <Route path="/interview-history" element={<InterviewHistoryPage />} />

          {/* Insights & Skill Intelligence */}
          <Route path="/skills" element={<SkillAssessmentPage />} />
          <Route path="/question-bank" element={<QuestionBankPage />} />
          <Route path="/analytics" element={<PerformanceAnalyticsPage />} />
          <Route path="/roadmap" element={<LearningRoadmapPage />} />

          {/* Administration (Role-gated for ADMIN) */}
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/ai-settings"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AISettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/audit-logs"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AuditLogsPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
