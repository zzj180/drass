import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

/**
 * Chat page component - Main interface for chatting with the compliance assistant
 */
const ChatPage: React.FC = () => {
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom>
        Compliance Chat Assistant
      </Typography>
      <Paper sx={{ flex: 1, p: 2 }}>
        <Typography>Chat interface will be implemented here</Typography>
      </Paper>
    </Box>
  );
};

export default ChatPage;