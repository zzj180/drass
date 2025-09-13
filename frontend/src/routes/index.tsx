import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import { authService } from '../services/authService';

// Lazy load pages for code splitting
const ChatPage = lazy(() => import('@/pages/ChatPage'));
const KnowledgeBasePage = lazy(() => import('@/pages/KnowledgeBasePage'));
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));
const TestPage = lazy(() => import('@/pages/TestPage'));

// Loading component
const LoadingFallback = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
  >
    <CircularProgress />
  </Box>
);

// Protected Route component
const ProtectedRoute: React.FC<{ element: React.ReactElement }> = ({ element }) => {
  const isAuthenticated = authService.isAuthenticated();
  return isAuthenticated ? element : <Navigate to="/login" replace />;
};

/**
 * Application Routes Configuration
 */
const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Main routes - Protected */}
        <Route path="/" element={<ProtectedRoute element={<Navigate to="/test" replace />} />} />
        <Route path="/test" element={<ProtectedRoute element={<TestPage />} />} />
        <Route path="/chat" element={<ProtectedRoute element={<ChatPage />} />} />
        <Route path="/knowledge" element={<ProtectedRoute element={<KnowledgeBasePage />} />} />
        <Route path="/documents" element={<ProtectedRoute element={<DocumentsPage />} />} />
        <Route path="/settings" element={<ProtectedRoute element={<SettingsPage />} />} />

        {/* Auth routes - Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* 404 route */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;