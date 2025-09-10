import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  WebSocketService, 
  WebSocketStatus, 
  WebSocketMessage, 
  WebSocketConfig,
  getWebSocketService,
  resetWebSocketService 
} from '../WebSocketService';

interface UseWebSocketOptions extends Partial<WebSocketConfig> {
  autoConnect?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onStatusChange?: (status: WebSocketStatus) => void;
  onError?: (error: Error) => void;
}

interface UseWebSocketReturn {
  status: WebSocketStatus;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (message: Omit<WebSocketMessage, 'timestamp'>) => void;
  subscribe: (type: string, callback: (message: WebSocketMessage) => void) => () => void;
  lastMessage: WebSocketMessage | null;
  error: Error | null;
}

/**
 * Custom hook for WebSocket connection management
 */
export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    autoConnect = true,
    onMessage,
    onStatusChange,
    onError,
    ...config
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const wsRef = useRef<WebSocketService | null>(null);
  const unsubscribeRef = useRef<(() => void)[]>([]);

  // Initialize WebSocket service
  useEffect(() => {
    try {
      wsRef.current = getWebSocketService({ url, ...config });
    } catch {
      // Service not initialized, create new instance
      wsRef.current = getWebSocketService({ url, ...config });
    }

    return () => {
      // Cleanup subscriptions
      unsubscribeRef.current.forEach(unsub => unsub());
      unsubscribeRef.current = [];
    };
  }, [url]);

  // Set up status listener
  useEffect(() => {
    if (!wsRef.current) return;

    const unsubscribe = wsRef.current.onStatusChange((newStatus) => {
      setStatus(newStatus);
      setIsConnected(newStatus === 'connected');
      onStatusChange?.(newStatus);
      
      if (newStatus === 'error') {
        setError(new Error('WebSocket connection error'));
      } else {
        setError(null);
      }
    });

    unsubscribeRef.current.push(unsubscribe);

    return () => {
      const index = unsubscribeRef.current.indexOf(unsubscribe);
      if (index > -1) {
        unsubscribeRef.current.splice(index, 1);
      }
      unsubscribe();
    };
  }, [onStatusChange]);

  // Set up message listener
  useEffect(() => {
    if (!wsRef.current) return;

    const unsubscribe = wsRef.current.subscribe('*', (message) => {
      setLastMessage(message);
      onMessage?.(message);
    });

    unsubscribeRef.current.push(unsubscribe);

    return () => {
      const index = unsubscribeRef.current.indexOf(unsubscribe);
      if (index > -1) {
        unsubscribeRef.current.splice(index, 1);
      }
      unsubscribe();
    };
  }, [onMessage]);

  // Auto-connect
  useEffect(() => {
    if (autoConnect && wsRef.current) {
      connect();
    }
  }, [autoConnect]);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (!wsRef.current) {
      const error = new Error('WebSocket service not initialized');
      setError(error);
      onError?.(error);
      return;
    }

    try {
      await wsRef.current.connect();
      setError(null);
    } catch (err) {
      const error = err as Error;
      setError(error);
      onError?.(error);
      throw error;
    }
  }, [onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
    }
  }, []);

  // Send message
  const send = useCallback((message: Omit<WebSocketMessage, 'timestamp'>) => {
    if (!wsRef.current) {
      console.error('[useWebSocket] Cannot send: service not initialized');
      return;
    }

    if (!wsRef.current.isConnected()) {
      console.warn('[useWebSocket] Cannot send: not connected');
      return;
    }

    wsRef.current.send(message);
  }, []);

  // Subscribe to specific message type
  const subscribe = useCallback(
    (type: string, callback: (message: WebSocketMessage) => void): (() => void) => {
      if (!wsRef.current) {
        console.error('[useWebSocket] Cannot subscribe: service not initialized');
        return () => {};
      }

      const unsubscribe = wsRef.current.subscribe(type, callback);
      unsubscribeRef.current.push(unsubscribe);

      return () => {
        const index = unsubscribeRef.current.indexOf(unsubscribe);
        if (index > -1) {
          unsubscribeRef.current.splice(index, 1);
        }
        unsubscribe();
      };
    },
    []
  );

  return {
    status,
    isConnected,
    connect,
    disconnect,
    send,
    subscribe,
    lastMessage,
    error,
  };
};

export default useWebSocket;