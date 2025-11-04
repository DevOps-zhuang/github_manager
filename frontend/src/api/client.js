import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('username');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => 
    client.post('/auth/login', { username, password }),
};

export const normalizeAPI = {
  createTask: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/normalize/tasks', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  getTask: (taskId) => 
    client.get(`/normalize/tasks/${taskId}`),
  
  chat: (taskId, message) => 
    client.post(`/normalize/tasks/${taskId}/chat`, { message }),
  
  apply: (taskId) => 
    client.post(`/normalize/tasks/${taskId}/apply`),
  
  download: (taskId) => 
    client.get(`/normalize/tasks/${taskId}/download`, { responseType: 'blob' }),
  
  downloadErrors: (taskId) => 
    client.get(`/normalize/tasks/${taskId}/errors`, { responseType: 'blob' }),
};

export default client;
