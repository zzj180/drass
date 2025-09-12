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
import { InputArea, AttachedFile, AttachmentPurpose } from './InputArea';
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
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);

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
  const handleSendMessage = useCallback(async (content: string) => {
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
    
    try {
      // 分离不同用途的附件
      const knowledgeBaseFiles = attachedFiles.filter(af => af.purpose === 'knowledge_base');
      const businessContextFiles = attachedFiles.filter(af => af.purpose === 'business_context');
      
      // 如果有知识库更新的附件，先处理知识库更新
      if (knowledgeBaseFiles.length > 0) {
        console.log('Updating knowledge base with files:', knowledgeBaseFiles.map(af => af.file.name));
        // TODO: 实现知识库更新API调用
        // await updateKnowledgeBase(knowledgeBaseFiles);
      }
      
      // 准备请求数据
      const requestData: any = { 
        message: content,
        attachments: businessContextFiles.map(af => ({
          filename: af.file.name,
          size: af.file.size,
          type: af.file.type,
          purpose: af.purpose
        }))
      };
      
      // 如果有业务上下文附件，添加文件内容
      if (businessContextFiles.length > 0) {
        // TODO: 实现文件内容读取和发送
        console.log('Including business context files:', businessContextFiles.map(af => af.file.name));
      }
      
      // Make API call to backend
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: data.response || 'No response from assistant',
        timestamp: new Date(),
        status: 'sent',
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      
      // 清空已发送的附件
      setAttachedFiles([]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        status: 'error',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [attachedFiles]);

  // Handle file attachment
  const handleAttachment = useCallback(() => {
    console.log('File attachment clicked');
    
    // Create a file input element
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls'; // Common document formats
    
    input.onchange = (event) => {
      const files = (event.target as HTMLInputElement).files;
      if (files && files.length > 0) {
        console.log(`Selected ${files.length} file(s):`, Array.from(files).map(f => f.name));
        
        const validFiles: AttachedFile[] = [];
        
        // Process each file
        Array.from(files).forEach((file) => {
          // Check file size
          if (file.size > maxFileSize) {
            console.error(`File ${file.name} is too large. Max size: ${maxFileSize} bytes`);
            return;
          }
          
          const attachedFile: AttachedFile = {
            file,
            purpose: 'business_context', // 默认用途
            id: uuidv4()
          };
          
          validFiles.push(attachedFile);
          console.log(`File: ${file.name}, Size: ${file.size} bytes, Type: ${file.type}`);
        });
        
        // Update attached files state
        if (validFiles.length > 0) {
          setAttachedFiles(prev => [...prev, ...validFiles]);
        }
      }
    };
    
    // Trigger file selection dialog
    input.click();
  }, [maxFileSize]);

  // Handle file removal
  const handleRemoveFile = useCallback((index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  // Handle file purpose change
  const handleFilePurposeChange = useCallback((fileId: string, purpose: AttachmentPurpose) => {
    setAttachedFiles(prev => 
      prev.map(attachedFile => 
        attachedFile.id === fileId 
          ? { ...attachedFile, purpose }
          : attachedFile
      )
    );
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
          onRemoveFile={handleRemoveFile}
          onFilePurposeChange={handleFilePurposeChange}
          attachedFiles={attachedFiles}
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