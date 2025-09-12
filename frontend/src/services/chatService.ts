/**
 * Chat Service
 * Handles chat conversations, message sending, and streaming responses
 */

import { apiClient, chatAPI } from './api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error' | 'streaming';
  error?: string;
  isStreaming?: boolean;
  streamingComplete?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
  isActive?: boolean;
}

export interface ChatResponse {
  message: ChatMessage;
  sources?: any[];
  usage?: {
    tokens: number;
    cost?: number;
  };
}

class ChatService {
  /**
   * Send a chat message
   */
  async sendMessage(
    message: string,
    sessionId?: string,
    options?: {
      useRag?: boolean;
      model?: string;
      temperature?: number;
      maxTokens?: number;
    }
  ): Promise<ChatResponse> {
    try {
      // Use our test API endpoint for now
      const response = await chatAPI.sendMessage(message, options?.useRag ?? true);
      
      return {
        message: {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          status: 'sent',
        },
        sources: response.sources || [],
      };
    } catch (error: any) {
      throw new Error(error.message || 'Failed to send message');
    }
  }

  /**
   * Send a streaming message
   */
  async sendStreamingMessage(
    message: string,
    onChunk: (chunk: string) => void,
    sessionId?: string,
    options?: any
  ): Promise<void> {
    try {
      // For now, simulate streaming by splitting the response
      const response = await this.sendMessage(message, sessionId, options);
      const content = response.message.content;
      
      // Simulate streaming by sending chunks
      const words = content.split(' ');
      for (let i = 0; i < words.length; i++) {
        const chunk = i === 0 ? words[i] : ' ' + words[i];
        onChunk(chunk);
        await new Promise(resolve => setTimeout(resolve, 50)); // 50ms delay between words
      }
    } catch (error: any) {
      throw new Error(error.message || 'Failed to stream message');
    }
  }

  /**
   * Get chat sessions
   */
  async getSessions(): Promise<ChatSession[]> {
    try {
      const response = await apiClient.get('/chat/conversations');
      return response.data.conversations || [];
    } catch (error: any) {
      // Return empty array if API not available
      return [];
    }
  }

  /**
   * Get a specific session
   */
  async getSession(sessionId: string): Promise<ChatSession | null> {
    try {
      const response = await apiClient.get(`/chat/conversations/${sessionId}`);
      return response.data;
    } catch (error: any) {
      return null;
    }
  }

  /**
   * Create a new chat session
   */
  async createSession(title?: string): Promise<ChatSession> {
    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      title: title || 'New Conversation',
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: [],
      isActive: true,
    };

    // In a real app, this would save to the backend
    return newSession;
  }

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      await apiClient.delete(`/chat/conversations/${sessionId}`);
    } catch (error: any) {
      // Ignore errors for now
    }
  }

  /**
   * Update session title
   */
  async updateSessionTitle(sessionId: string, title: string): Promise<void> {
    try {
      await apiClient.patch(`/chat/conversations/${sessionId}`, { title });
    } catch (error: any) {
      // Ignore errors for now
    }
  }

  /**
   * Clear all messages in a session
   */
  async clearSession(sessionId: string): Promise<void> {
    // In a real app, this would clear messages on the backend
  }

  /**
   * Export chat session
   */
  async exportSession(sessionId: string, format: 'json' | 'txt' | 'pdf' = 'json'): Promise<string> {
    try {
      const response = await apiClient.get(`/chat/conversations/${sessionId}/export`, {
        params: { format }
      });
      return response.data.exportUrl || '';
    } catch (error: any) {
      throw new Error('Failed to export session');
    }
  }

  /**
   * Search chat history
   */
  async searchMessages(query: string, sessionId?: string): Promise<ChatMessage[]> {
    try {
      const response = await apiClient.post('/chat/search', {
        query,
        sessionId,
      });
      return response.data.messages || [];
    } catch (error: any) {
      return [];
    }
  }

  /**
   * Get chat statistics
   */
  async getStats(): Promise<any> {
    try {
      const response = await apiClient.get('/chat/stats');
      return response.data;
    } catch (error: any) {
      return {
        totalSessions: 0,
        totalMessages: 0,
        tokensUsed: 0,
      };
    }
  }

  /**
   * Test chat service connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await chatAPI.getServicesStatus();
      return response.status === 'success';
    } catch (error) {
      return false;
    }
  }

  /**
   * Format message for display
   */
  formatMessage(message: ChatMessage): string {
    const timestamp = message.timestamp.toLocaleTimeString();
    const role = message.role.charAt(0).toUpperCase() + message.role.slice(1);
    return `[${timestamp}] ${role}: ${message.content}`;
  }

  /**
   * Generate session title from first message
   */
  generateSessionTitle(firstMessage: string): string {
    // Take first 50 characters and add ellipsis if longer
    const title = firstMessage.length > 50 
      ? firstMessage.substring(0, 50) + '...'
      : firstMessage;
    
    return title || 'New Conversation';
  }
}

// Export singleton instance
export const chatService = new ChatService();
export default chatService;