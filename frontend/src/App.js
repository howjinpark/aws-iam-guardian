import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import koKR from 'antd/locale/ko_KR';
import 'antd/dist/reset.css';
import './App.css';

import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import IAMUsers from './pages/IAMUsers';
import IAMRoles from './pages/IAMRoles';
import IAMPolicies from './pages/IAMPolicies';
import Analysis from './pages/Analysis';
import AuditLogs from './pages/AuditLogs';
import Settings from './pages/Settings';

// React Query 클라이언트 설정
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={koKR}>
        <AuthProvider>
          <Router>
            <div className="App">
              <Routes>
                {/* 로그인 페이지 */}
                <Route path="/login" element={<Login />} />
                
                {/* 보호된 라우트들 */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard" element={<Dashboard />} />
                  <Route path="users" element={<Users />} />
                  <Route path="iam/users" element={<IAMUsers />} />
                  <Route path="iam/roles" element={<IAMRoles />} />
                  <Route path="iam/policies" element={<IAMPolicies />} />
                  <Route path="analysis" element={<Analysis />} />
                  <Route path="audit" element={<AuditLogs />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
                
                {/* 404 처리 */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          </Router>
        </AuthProvider>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;