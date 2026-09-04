import axios from 'axios';

const rawEnv = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'https://sih-b9dp.onrender.com';
let targetHost = rawEnv.trim().replace(/\/+$/, '');

// Ensure HTTPS scheme for production remote hosts to prevent Mixed Content security blocks
if (targetHost.includes('onrender.com') && targetHost.startsWith('http://')) {
  targetHost = targetHost.replace('http://', 'https://');
}

// Fallback to live production backend if local URL is evaluated on a production browser origin
if ((targetHost.includes('localhost') || targetHost.includes('127.0.0.1')) && typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
  targetHost = 'https://sih-b9dp.onrender.com';
}

// Construct clean baseURL without duplicate /api suffix
const baseURL = targetHost.endsWith('/api') ? targetHost : `${targetHost}/api`;

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
