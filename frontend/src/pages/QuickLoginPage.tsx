import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, CircularProgress } from '@mui/material';

/**
 * Quick login page for development/testing
 * Automatically sets a test token and redirects to knowledge base
 */
const QuickLoginPage: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Set a test token for development
    const testToken = 'test-token-' + Date.now();
    localStorage.setItem('access_token', testToken);
    localStorage.setItem('auth_token', testToken);
    
    // Set a fake user
    const testUser = {
      id: 'test-user-id',
      email: 'test@example.com',
      name: 'Test User',
      role: 'admin',
      created_at: new Date().toISOString()
    };
    localStorage.setItem('current_user', JSON.stringify(testUser));
    
    // Set token expiry (1 hour from now)
    const expiresAt = new Date().getTime() + (3600 * 1000);
    localStorage.setItem('token_expires_at', expiresAt.toString());
    
    console.log('Test authentication set successfully');
    
    // Redirect to knowledge base after a short delay
    setTimeout(() => {
      navigate('/knowledge');
    }, 1000);
  }, [navigate]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
    >
      <CircularProgress />
      <Typography variant="h6" sx={{ mt: 2 }}>
        Setting up test authentication...
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        Redirecting to Knowledge Base...
      </Typography>
    </Box>
  );
};

export default QuickLoginPage;
