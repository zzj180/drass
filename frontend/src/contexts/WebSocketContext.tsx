import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  sendMessage: (event: string, data: any) => void;
  onMessage: (event: string, callback: (data: any) => void) => void;
  offMessage: (event: string, callback?: (data: any) => void) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

/**
 * WebSocket Provider for real-time communication
 */
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // WebSocket is disabled for now - using HTTP API instead
    console.log('WebSocket connection disabled - using HTTP API');
    
    // TODO: Enable WebSocket when backend supports it
    // const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    // const newSocket = io(wsUrl, {
    //   transports: ['websocket'],
    //   autoConnect: true,
    //   reconnection: true,
    //   reconnectionAttempts: 5,
    //   reconnectionDelay: 1000,
    // });
    
    // For now, just set as disconnected
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((event: string, data: any) => {
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const onMessage = useCallback((event: string, callback: (data: any) => void) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback);
    }
  }, []);

  const offMessage = useCallback((event: string, callback?: (data: any) => void) => {
    if (socketRef.current) {
      if (callback) {
        socketRef.current.off(event, callback);
      } else {
        socketRef.current.off(event);
      }
    }
  }, []);

  const value: WebSocketContextType = {
    socket,
    isConnected,
    sendMessage,
    onMessage,
    offMessage,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};

/**
 * Hook to use WebSocket context
 */
export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};