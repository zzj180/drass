import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

/**
 * Documents management page
 */
const DocumentsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Documents
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>Document management interface will be implemented here</Typography>
      </Paper>
    </Box>
  );
};

export default DocumentsPage;