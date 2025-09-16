import React from 'react';
import { Box, Paper, Typography, Divider, FormControl } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { LanguageSelector } from './LanguageSelector';

export const Settings: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t('settings.title')}
        </Typography>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          {t('settings.appearance')}
        </Typography>

        <Box sx={{ mt: 2, maxWidth: 300 }}>
          <LanguageSelector />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          {t('settings.general')}
        </Typography>

        <Typography variant="body2" color="text.secondary">
          {t('settings.version')}: v1.0.0
        </Typography>
      </Paper>
    </Box>
  );
};