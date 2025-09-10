import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

/**
 * Login page
 */
const LoginPage: React.FC = () => {
  return (
    <Box sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h4" gutterBottom align="center">
          Login
        </Typography>
        <Typography>Login form will be implemented here</Typography>
      </Paper>
    </Box>
  );
};

export default LoginPage;