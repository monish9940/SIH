import axios from 'axios';

let envUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '';
if (!envUrl || envUrl.includes('localhost') || envUrl.includes('127.0.0.1')) {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    envUrl = 'https://sih-b9dp.onrender.com';
  } else {
    envUrl = envUrl || 'http://localhost:8000';
  }
}
const cleanUrl = envUrl.replace(/\/+$/, '');
const baseURL = cleanUrl.endsWith('/api') ? cleanUrl : `${cleanUrl}/api`;

const api = axios.create({
  baseURL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('compliance_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle expired or unauthorized responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('compliance_token');
      localStorage.removeItem('compliance_user');
      if (window.location.pathname.startsWith('/dashboard') || window.location.pathname.startsWith('/inspection')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
