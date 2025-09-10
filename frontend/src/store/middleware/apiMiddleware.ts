import { Middleware } from '@reduxjs/toolkit';
import { RootState } from '../index';

interface ApiAction {
  type: string;
  payload?: any;
  meta?: {
    api?: {
      url: string;
      method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
      headers?: Record<string, string>;
      body?: any;
      onSuccess?: (data: any) => any;
      onError?: (error: Error) => any;
      transformResponse?: (response: any) => any;
      retries?: number;
      timeout?: number;
    };
  };
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Custom API middleware for handling API calls with Redux
 */
export const apiMiddleware: Middleware<{}, RootState> =
  (store) => (next) => async (action: ApiAction) => {
    // Pass through non-API actions
    if (!action.meta?.api) {
      return next(action);
    }

    const {
      url,
      method = 'GET',
      headers = {},
      body,
      onSuccess,
      onError,
      transformResponse,
      retries = 0,
      timeout = 30000,
    } = action.meta.api;

    // Get auth token from state
    const state = store.getState();
    const token = state.auth.token;

    // Prepare request headers
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // Helper function to make the API call
    const makeRequest = async (attemptNumber: number = 0): Promise<any> => {
      try {
        // Dispatch pending action
        next({
          type: `${action.type}_PENDING`,
          payload: action.payload,
        });

        // Make the API call
        const response = await fetch(`${API_BASE_URL}${url}`, {
          method,
          headers: requestHeaders,
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Check response status
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        // Parse response
        let data = await response.json().catch(() => null);

        // Transform response if needed
        if (transformResponse) {
          data = transformResponse(data);
        }

        // Dispatch success action
        next({
          type: `${action.type}_SUCCESS`,
          payload: data,
          meta: {
            originalAction: action,
          },
        });

        // Call success callback if provided
        if (onSuccess) {
          onSuccess(data);
        }

        return data;
      } catch (error: any) {
        clearTimeout(timeoutId);

        // Handle timeout
        if (error.name === 'AbortError') {
          error.message = 'Request timeout';
        }

        // Retry logic
        if (attemptNumber < retries) {
          console.log(`Retrying API call (attempt ${attemptNumber + 1}/${retries})...`);
          await new Promise((resolve) => setTimeout(resolve, 1000 * (attemptNumber + 1)));
          return makeRequest(attemptNumber + 1);
        }

        // Dispatch failure action
        next({
          type: `${action.type}_FAILURE`,
          payload: error.message,
          error: true,
          meta: {
            originalAction: action,
          },
        });

        // Call error callback if provided
        if (onError) {
          onError(error);
        }

        throw error;
      }
    };

    return makeRequest();
  };

/**
 * Helper function to create API action
 */
export const createApiAction = (
  type: string,
  api: ApiAction['meta']['api'],
  payload?: any
): ApiAction => ({
  type,
  payload,
  meta: { api },
});

/**
 * Common API endpoints
 */
export const apiEndpoints = {
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    validate: '/auth/validate',
  },
  chat: {
    conversations: '/chat/conversations',
    conversation: (id: string) => `/chat/conversations/${id}`,
    message: '/chat/message',
    stream: '/chat/stream',
  },
  knowledge: {
    bases: '/knowledge/bases',
    base: (id: string) => `/knowledge/bases/${id}`,
    sources: (baseId: string) => `/knowledge/bases/${baseId}/sources`,
    source: (baseId: string, sourceId: string) => `/knowledge/bases/${baseId}/sources/${sourceId}`,
    search: '/knowledge/search',
    upload: '/knowledge/upload',
  },
  documents: {
    list: '/documents',
    document: (id: string) => `/documents/${id}`,
    upload: '/documents/upload',
    process: (id: string) => `/documents/${id}/process`,
    extract: (id: string) => `/documents/${id}/extract`,
    folders: '/documents/folders',
    folder: (id: string) => `/documents/folders/${id}`,
  },
  settings: {
    get: '/settings',
    save: '/settings',
    test: {
      model: '/settings/test/model',
      embedding: '/settings/test/embedding',
      vectorStore: '/settings/test/vector-store',
    },
    export: '/settings/export',
    import: '/settings/import',
  },
};

/**
 * WebSocket connection for real-time features
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingTimer: NodeJS.Timeout | null = null;
  private handlers: Map<string, Set<(data: any) => void>> = new Map();

  connect(token: string) {
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws').replace('/api', '/ws');
    this.ws = new WebSocket(`${wsUrl}?token=${token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.startPing();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const handlers = this.handlers.get(data.type) || new Set();
        handlers.forEach((handler) => handler(data.payload));
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.stopPing();
      this.scheduleReconnect();
    };
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopPing();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(type: string, payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  on(type: string, handler: (data: any) => void) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
  }

  off(type: string, handler: (data: any) => void) {
    this.handlers.get(type)?.delete(handler);
  }

  private startPing() {
    this.pingTimer = setInterval(() => {
      this.send('ping', {});
    }, 30000);
  }

  private stopPing() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private scheduleReconnect() {
    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      const state = (window as any).__REDUX_STORE__?.getState();
      if (state?.auth?.token) {
        this.connect(state.auth.token);
      }
    }, 5000);
  }
}

export const wsManager = new WebSocketManager();