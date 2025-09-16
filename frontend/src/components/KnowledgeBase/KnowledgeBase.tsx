import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, History as HistoryIcon } from '@mui/icons-material';

export const KnowledgeBase: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('knowledgeBase.title')}
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          {t('knowledgeBase.management')}
        </Typography>

        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => {}}
          >
            {t('knowledgeBase.upload')}
          </Button>

          <Button
            variant="outlined"
            startIcon={<HistoryIcon />}
            onClick={() => navigate('/knowledge-base/access-logs')}
          >
            {t('knowledgeBase.viewAccessLogs')}
          </Button>
        </Box>

        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            {t('knowledgeBase.recentDocuments')}
          </Typography>

          <Typography color="text.secondary">
            {t('table.noData')}
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};