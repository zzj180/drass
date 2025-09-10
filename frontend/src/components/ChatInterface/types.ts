/**
 * Type definitions for ChatInterface components
 */

export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'sending' | 'sent' | 'error' | 'streaming';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  status?: MessageStatus;
  error?: string;
  attachments?: Attachment[];
  references?: Reference[];
  isStreaming?: boolean;
  streamingComplete?: boolean;
}

export interface Attachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
}

export interface Reference {
  id: string;
  source: string;
  content: string;
  relevance: number;
  url?: string;
}

export interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
  isActive?: boolean;
}

export interface ChatInterfaceProps {
  sessionId?: string;
  userId?: string;
  apiEndpoint?: string;
  wsEndpoint?: string;
  enableUpload?: boolean;
  enableStreaming?: boolean;
  maxFileSize?: number;
  placeholder?: string;
  className?: string;
}

export interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  onMessageAction?: (action: string, messageId: string) => void;
  className?: string;
}

export interface MessageItemProps {
  message: Message;
  onAction?: (action: string) => void;
  showActions?: boolean;
  className?: string;
}

export interface ChatState {
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  uploadProgress: number;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
}