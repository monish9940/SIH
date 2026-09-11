import axios from 'axios';

const rawEnv = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
let targetHost = rawEnv.trim().replace(/\/+$/, '');

// Construct clean baseURL without duplicate /api suffix
const baseURL = targetHost.endsWith('/api') ? targetHost : `${targetHost}/api`;

const api = axios.create({
  baseURL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT Bearer token and handle FormData headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('compliance_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
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
