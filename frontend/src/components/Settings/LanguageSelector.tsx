import React from 'react';
import {
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { setLanguage } from '../../store/slices/settingsSlice';

const languages = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' },
];

export const LanguageSelector: React.FC = () => {
  const { t, i18n } = useTranslation();
  const dispatch = useDispatch();
  const currentLanguage = useSelector((state: RootState) => state.settings.system.language);

  const handleLanguageChange = (event: SelectChangeEvent) => {
    const newLanguage = event.target.value as 'en' | 'zh';

    // Update i18n
    i18n.changeLanguage(newLanguage);

    // Update Redux store
    dispatch(setLanguage(newLanguage));

    // Save to localStorage
    localStorage.setItem('language', newLanguage);
  };

  return (
    <FormControl fullWidth size="small">
      <InputLabel id="language-select-label">{t('settings.language')}</InputLabel>
      <Select
        labelId="language-select-label"
        id="language-select"
        value={currentLanguage}
        label={t('settings.language')}
        onChange={handleLanguageChange}
      >
        {languages.map((lang) => (
          <MenuItem key={lang.code} value={lang.code}>
            {lang.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};