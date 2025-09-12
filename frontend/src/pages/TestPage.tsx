import React from 'react';
import { Box, Typography } from '@mui/material';

const TestPage: React.FC = () => {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h3" gutterBottom>
        Test Page
      </Typography>
      <Typography variant="body1">
        If you can see this, the frontend is working correctly!
      </Typography>
    </Box>
  );
};

export default TestPage;