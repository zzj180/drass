import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslations from './locales/en.json';
import zhTranslations from './locales/zh.json';

const resources = {
  en: {
    translation: enTranslations
  },
  zh: {
    translation: zhTranslations
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('language') || 'zh', // Default to Chinese
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false // React already does escaping
    },
    react: {
      useSuspense: false // Avoid suspense for better compatibility
    }
  });

export default i18n;