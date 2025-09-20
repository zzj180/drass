/**
 * API configuration and base service
 */

import axios from 'axios';

// API base URL - pointing to the local backend (port 8888 for VLLM integration)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888/api/v1';

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
  // Send chat message using test endpoint (no auth required)
  sendMessage: async (
    message: string, 
    useRag: boolean = true, 
    options?: {
      model?: string;
      temperature?: number;
      maxTokens?: number;
      conversationId?: string;
    }
  ) => {
    const response = await apiClient.post('/test/chat', {
      message: message,
      use_rag: useRag ?? false, // 确保默认为false
      context: options?.conversationId,
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.maxTokens ?? 1024
    });
    return response.data;
  },

  // Send streaming chat message
  sendStreamingMessage: async (
    message: string,
    onChunk: (chunk: string) => void,
    options?: {
      model?: string;
      temperature?: number;
      maxTokens?: number;
      conversationId?: string;
      useRag?: boolean;
    }
  ) => {
    const response = await fetch(`${API_BASE_URL}/test/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        use_rag: options?.useRag ?? false, // 默认使用false，直接调用VLLM
        context: options?.conversationId,
        temperature: options?.temperature ?? 0.7, // 传递temperature参数
        max_tokens: options?.maxTokens ?? 1024 // 增加max_tokens参数，默认1024
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // For test endpoint, we get the full response and simulate streaming
    const data = await response.json();
    const content = data.response || '';
    
    // Simulate streaming by sending chunks of text
    const words = content.split('');
    for (let i = 0; i < words.length; i++) {
      onChunk(words[i]);
      // Small delay to simulate streaming
      await new Promise(resolve => setTimeout(resolve, 10));
    }
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

  // Get chat conversations
  getConversations: async () => {
    try {
      const response = await apiClient.get('/chat/conversations');
      return response.data;
    } catch (error) {
      console.error('Failed to get conversations:', error);
      return { conversations: [] };
    }
  },

  // Create new conversation
  createConversation: async (title?: string) => {
    try {
      const response = await apiClient.post('/chat/conversations', { title });
      return response.data;
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  },

  // Delete conversation
  deleteConversation: async (conversationId: string) => {
    try {
      const response = await apiClient.delete(`/chat/conversations/${conversationId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  },

  // Update conversation title
  updateConversationTitle: async (conversationId: string, title: string) => {
    try {
      const response = await apiClient.patch(`/chat/conversations/${conversationId}`, { title });
      return response.data;
    } catch (error) {
      console.error('Failed to update conversation title:', error);
      throw error;
    }
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
    const response = await axios.get('http://localhost:8888/health');
    return response.data;
  },
};

export default apiClient;