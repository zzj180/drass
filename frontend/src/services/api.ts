/**
 * API configuration and base service
 */

import axios from 'axios';

// API base URL - pointing to the local backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Chat API endpoints
export const chatAPI = {
  // Send chat message (without auth for testing)
  sendMessage: async (message: string, useRag: boolean = true) => {
    const response = await apiClient.post('/test/chat', {
      message,
      use_rag: useRag,
    });
    return response.data;
  },

  // Get services status
  getServicesStatus: async () => {
    const response = await apiClient.get('/test/services-status');
    return response.data;
  },

  // Test embedding
  testEmbedding: async (text: string) => {
    const response = await apiClient.post('/test/embedding', { text });
    return response.data;
  },

  // Stream chat message (WebSocket will be used for this)
  streamMessage: async (message: string, onChunk: (chunk: string) => void) => {
    // This would use WebSocket in real implementation
    // For now, we'll use the regular endpoint
    return chatAPI.sendMessage(message);
  },
};

// Knowledge base API
export const knowledgeAPI = {
  // Upload document
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Search knowledge base
  search: async (query: string) => {
    const response = await apiClient.post('/test/search', null, {
      params: { query, k: 5 },
    });
    return response.data;
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await axios.get('http://localhost:8000/health');
    return response.data;
  },
};

export default apiClient;