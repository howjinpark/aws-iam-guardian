import React, { createContext, useContext, useState, useEffect } from 'react';
import { message } from 'antd';
import Cookies from 'js-cookie';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(Cookies.get('access_token'));

  // 토큰이 있으면 API 헤더에 설정
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // 앱 시작 시 사용자 정보 확인
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await api.get('/api/v1/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error('사용자 정보 조회 실패:', error);
          // 토큰이 유효하지 않으면 제거
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
          setToken(null);
          setUser(null);
          delete api.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await api.post('/api/v1/auth/login', {
        username,
        password
      });

      const { access_token, refresh_token, user: userData } = response.data;
      
      // 토큰들 저장
      Cookies.set('access_token', access_token, { expires: 1 }); // 1일
      Cookies.set('refresh_token', refresh_token, { expires: 7 }); // 7일
      setToken(access_token);
      setUser(userData);
      
      message.success('로그인 성공!');
      return true;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '로그인에 실패했습니다.';
      message.error(errorMessage);
      return false;
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await api.post('/api/v1/auth/logout');
      }
    } catch (error) {
      console.error('로그아웃 API 호출 실패:', error);
    } finally {
      // 로컬 상태 정리
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      setToken(null);
      setUser(null);
      delete api.defaults.headers.common['Authorization'];
      message.success('로그아웃되었습니다.');
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    updateUser,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
    userRole: user?.role || 'viewer',
    isAnalyst: user?.role === 'analyst',
    isAuditor: user?.role === 'auditor',
    isViewer: user?.role === 'viewer'
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};