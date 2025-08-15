import axios from 'axios';
import { message } from 'antd';
import Cookies from 'js-cookie';

// API 기본 설정
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 401 에러 처리 (토큰 만료) - refresh 요청은 제외
    if (error.response?.status === 401 && 
        !originalRequest._retry && 
        !originalRequest.url?.includes('/auth/refresh')) {
      
      originalRequest._retry = true;

      try {
        // 리프레시 토큰으로 새 토큰 요청
        const refreshToken = Cookies.get('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        // 별도의 axios 인스턴스로 refresh 요청 (인터셉터 우회)
        const refreshResponse = await axios.post(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
          {
            headers: { 'Content-Type': 'application/json' },
            timeout: 10000
          }
        );

        const { access_token, refresh_token: newRefreshToken } = refreshResponse.data;
        
        // 새 토큰들 저장
        Cookies.set('access_token', access_token, { expires: 1 }); // 1일
        Cookies.set('refresh_token', newRefreshToken, { expires: 7 }); // 7일
        
        // 원래 요청에 새 토큰 적용
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // 토큰 갱신 실패 시 로그아웃
        console.warn('토큰 갱신에 실패했습니다. 다시 로그인해주세요.');
        message.warning('세션이 만료되었습니다. 다시 로그인해주세요.');
        
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');
        
        // 현재 페이지가 로그인 페이지가 아닌 경우에만 리다이렉트
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }

    // 기타 에러 처리
    if (error.response?.status >= 500) {
      message.error('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } else if (error.response?.status === 403) {
      message.error('접근 권한이 없습니다.');
    } else if (error.code === 'ECONNABORTED') {
      message.error('요청 시간이 초과되었습니다.');
    }

    return Promise.reject(error);
  }
);

export default api;