import React from 'react';
import { Box } from '@mui/material';
import { ChatInterface } from '../components/ChatInterface/ChatInterface';

/**
 * Chat page component - Main interface for chatting with the compliance assistant
 */
const ChatPage: React.FC = () => {
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <ChatInterface 
        sessionId="default-session"
        userId="test-user"
      />
    </Box>
  );
};

export default ChatPage;