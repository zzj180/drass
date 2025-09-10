import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

/**
 * Knowledge Base management page
 */
const KnowledgeBasePage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Knowledge Base Management
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>Knowledge base interface will be implemented here</Typography>
      </Paper>
    </Box>
  );
};

export default KnowledgeBasePage;