import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@presentation/pages/auth/LoginPage';
import { SignUpPage } from '@presentation/pages/auth/SignUpPage';
import { EmailVerificationPage } from '@presentation/pages/auth/EmailVerificationPage';
import { VerifyEmailPage } from '@presentation/pages/auth/VerifyEmailPage';
import { ForgotPasswordPage } from '@presentation/pages/auth/ForgotPasswordPage';
import { VerifyRecoveryCodePage } from '@presentation/pages/auth/VerifyRecoveryCodePage';
import { ResetPasswordPage } from '@presentation/pages/auth/ResetPasswordPage';
import { TermsPage } from '@presentation/pages/legal/TermsPage';
import { PrivacyPage } from '@presentation/pages/legal/PrivacyPage';
import { DashboardPage } from '@presentation/pages/dashboard/DashboardPage';
import { ExamsPage } from '@presentation/pages/exams/ExamsPage';
import { CreateExamPage } from '@presentation/pages/exams/CreateExamPage';
import { EditExamPage } from '@presentation/pages/exams/EditExamPage';
import { ExamDetailsPage } from '@presentation/pages/exams/ExamDetailsPage';
import { ExamReviewPage } from '@presentation/pages/exams/ExamReviewPage';
import { ClassesPage } from '@presentation/pages/classes/ClassesPage';
import { StudentsPage } from '@presentation/pages/students/StudentsPage';
import { AnalyticsPage } from '@presentation/pages/analytics/AnalyticsPage';
import { ClassAnalyticsPage } from '@presentation/pages/analytics/ClassAnalyticsPage';
import { StudentPerformancePage } from '@presentation/pages/analytics/StudentPerformancePage';
import { SettingsPage } from '@presentation/pages/settings/SettingsPage';
import { NotFoundPage } from '@presentation/pages/error/NotFoundPage';
import { PrivateRoute } from '@presentation/components/auth/PrivateRoute';

export const AppRoutes: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/email-verification" element={<EmailVerificationPage />} />
        <Route path="/verify-email/:uuid" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/forgot-password/verify-code" element={<VerifyRecoveryCodePage />} />
        <Route path="/forgot-password/reset" element={<ResetPasswordPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        
        {/* Private Routes */}
        <Route element={<PrivateRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/exams" element={<ExamsPage />} />
          <Route path="/dashboard/exams/create" element={<CreateExamPage />} />
          <Route path="/dashboard/exams/:examUuid" element={<ExamDetailsPage />} />
          <Route path="/dashboard/exams/:examUuid/edit" element={<EditExamPage />} />
          <Route path="/dashboard/exams/:examUuid/review" element={<ExamReviewPage />} />
          <Route path="/exams" element={<ExamsPage />} />
          <Route path="/classes" element={<ClassesPage />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/analytics/classes/:classUuid" element={<ClassAnalyticsPage />} />
          <Route path="/analytics/classes/:classUuid/students/:studentUuid" element={<StudentPerformancePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        
        {/* Default Redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* 404 Not Found */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};
