import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
} from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { LanguageSelector } from '../Settings/LanguageSelector';

export const Header: React.FC = () => {
  const { t } = useTranslation();

  return (
    <AppBar position="static" elevation={0}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {t('chat.title')}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Language Selector */}
          <Box sx={{ minWidth: 120 }}>
            <LanguageSelector />
          </Box>

          {/* Settings Icon */}
          <IconButton color="inherit" aria-label="settings">
            <SettingsIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};