import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { MessageList } from './MessageList';
import { InputArea } from './InputArea';
import { ChatInterfaceProps, Message } from './types';
import { v4 as uuidv4 } from 'uuid';

/**
 * Main ChatInterface component container
 * Manages the overall chat UI layout and state coordination
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  userId,
  apiEndpoint = '/api/v1/chat',
  wsEndpoint,
  enableUpload = true,
  enableStreaming = true,
  maxFileSize = 10485760, // 10MB default
  placeholder = 'Type your message...',
  className,
}) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  
  // Local state for demo (will be connected to Redux)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uuidv4(),
      role: 'system',
      content: 'Welcome to the Compliance Assistant! How can I help you today?',
      timestamp: new Date(),
      status: 'sent',
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Handle message actions
  const handleMessageAction = useCallback(
    (action: string, messageId: string) => {
      console.log(`Message action: ${action} for message ${messageId}`);
      
      switch (action) {
        case 'copy':
          // Copy handled in MessageItem
          break;
        case 'edit':
          // TODO: Implement edit functionality
          console.log('Edit message:', messageId);
          break;
        case 'regenerate':
          // TODO: Implement regenerate functionality
          console.log('Regenerate response for:', messageId);
          break;
        case 'delete':
          setMessages((prev) =>
            prev.filter((msg) => msg.id !== messageId)
          );
          break;
        default:
          break;
      }
    },
    []
  );

  // Toggle sidebar
  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  // Create new session
  const createNewSession = useCallback(() => {
    console.log('Creating new session');
    // TODO: Implement new session creation
    setMessages([
      {
        id: uuidv4(),
        role: 'system',
        content: 'New conversation started. How can I help you?',
        timestamp: new Date(),
        status: 'sent',
      },
    ]);
  }, []);

  // Handle sending messages
  const handleSendMessage = useCallback((content: string) => {
    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
      status: 'sent',
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    
    // Simulate API response (TODO: Replace with actual API call)
    setTimeout(() => {
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: `I received your message: "${content}". This is a simulated response.`,
        timestamp: new Date(),
        status: 'sent',
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  }, []);

  // Handle file attachment
  const handleAttachment = useCallback(() => {
    console.log('File attachment clicked');
    // TODO: Implement file attachment
  }, []);

  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        height: '100vh',
        bgcolor: 'background.default',
      }}
    >
      {/* Main Chat Area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* Header */}
        <AppBar
          position="static"
          elevation={0}
          sx={{
            bgcolor: 'background.paper',
            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={toggleSidebar}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>

            <Typography
              variant="h6"
              component="div"
              sx={{ flexGrow: 1, color: 'text.primary' }}
            >
              Compliance Assistant
            </Typography>

            <IconButton
              color="inherit"
              aria-label="new chat"
              onClick={createNewSession}
              sx={{ mr: 1 }}
            >
              <AddIcon />
            </IconButton>

            <IconButton
              color="inherit"
              aria-label="settings"
            >
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Message List */}
        <MessageList
          messages={messages}
          isLoading={isLoading}
          onMessageAction={handleMessageAction}
        />

        {/* Input Area */}
        <InputArea
          onSend={handleSendMessage}
          onAttach={handleAttachment}
          placeholder={placeholder}
          maxLength={maxFileSize}
          isLoading={isLoading}
          enableAttachment={enableUpload}
          enableVoice={false}
        />
      </Box>

      {/* Sidebar Placeholder */}
      {sidebarOpen && (
        <Paper
          elevation={0}
          sx={{
            width: 300,
            borderLeft: `1px solid ${theme.palette.divider}`,
            display: 'flex',
            flexDirection: 'column',
            bgcolor: 'background.paper',
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6">Sessions</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Session management will be implemented in TASK-UI-002A
            </Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default ChatInterface;