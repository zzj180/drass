import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

/**
 * Settings page
 */
const SettingsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>Settings interface will be implemented here</Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;