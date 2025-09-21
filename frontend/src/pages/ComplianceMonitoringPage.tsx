import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import RealTimeMonitor from '../components/ComplianceMonitoring/RealTimeMonitor';

const ComplianceMonitoringPage: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box mb={3}>
          <Typography variant="h4" component="h1" gutterBottom>
            合规监控中心
          </Typography>
          <Typography variant="body1" color="text.secondary">
            实时监控系统合规状态，及时发现和处理安全风险
          </Typography>
        </Box>
        
        <RealTimeMonitor userId="default" />
      </Paper>
    </Container>
  );
};

export default ComplianceMonitoringPage;
