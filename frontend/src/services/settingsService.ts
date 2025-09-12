/**
 * Settings Service
 * Handles application settings, user preferences, and configuration management
 */

import { apiClient } from './api';

export interface UserSettings {
  id: string;
  userId: string;
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
    notifications: {
      email: boolean;
      push: boolean;
      desktop: boolean;
    };
    chat: {
      streamingEnabled: boolean;
      autoSave: boolean;
      showSources: boolean;
      maxTokens: number;
      temperature: number;
    };
    ui: {
      sidebarCollapsed: boolean;
      compactMode: boolean;
      showLineNumbers: boolean;
    };
  };
  createdAt: Date;
  updatedAt: Date;
}

export interface SystemSettings {
  llm: {
    provider: string;
    model: string;
    apiKey?: string;
    baseUrl?: string;
    maxTokens: number;
    temperature: number;
    streamingEnabled: boolean;
  };
  embedding: {
    provider: string;
    model: string;
    apiKey?: string;
    baseUrl?: string;
    dimensions: number;
  };
  vectorStore: {
    type: string;
    host?: string;
    port?: number;
    apiKey?: string;
    collection?: string;
  };
  reranking: {
    enabled: boolean;
    provider?: string;
    model?: string;
    apiKey?: string;
    topK?: number;
  };
  security: {
    jwtExpiration: number;
    rateLimiting: {
      enabled: boolean;
      maxRequests: number;
      windowMs: number;
    };
    cors: {
      origins: string[];
      credentials: boolean;
    };
  };
}

export interface AppConfig {
  version: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    chatEnabled: boolean;
    documentsEnabled: boolean;
    knowledgeBaseEnabled: boolean;
    agentEnabled: boolean;
    ragEnabled: boolean;
    streamingEnabled: boolean;
  };
  limits: {
    maxFileSize: number;
    maxDocuments: number;
    maxKnowledgeBases: number;
    maxChatSessions: number;
  };
  integrations: {
    difyEnabled: boolean;
    figmaEnabled: boolean;
    githubEnabled: boolean;
    webhooksEnabled: boolean;
  };
}

export interface ThemeSettings {
  mode: 'light' | 'dark' | 'auto';
  primaryColor: string;
  accentColor: string;
  fontFamily: string;
  fontSize: 'small' | 'medium' | 'large';
  borderRadius: number;
  animations: boolean;
}

class SettingsService {
  /**
   * Get user settings
   */
  async getUserSettings(userId?: string): Promise<UserSettings> {
    try {
      const endpoint = userId ? `/settings/users/${userId}` : '/settings/user';
      const response = await apiClient.get(endpoint);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get user settings');
    }
  }

  /**
   * Update user settings
   */
  async updateUserSettings(
    settings: Partial<UserSettings['preferences']>,
    userId?: string
  ): Promise<UserSettings> {
    try {
      const endpoint = userId ? `/settings/users/${userId}` : '/settings/user';
      const response = await apiClient.patch(endpoint, { preferences: settings });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update user settings');
    }
  }

  /**
   * Get system settings (admin only)
   */
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      const response = await apiClient.get('/settings/system');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get system settings');
    }
  }

  /**
   * Update system settings (admin only)
   */
  async updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    try {
      const response = await apiClient.patch('/settings/system', settings);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update system settings');
    }
  }

  /**
   * Get application configuration
   */
  async getAppConfig(): Promise<AppConfig> {
    try {
      const response = await apiClient.get('/settings/config');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get app config');
    }
  }

  /**
   * Get theme settings
   */
  async getThemeSettings(userId?: string): Promise<ThemeSettings> {
    try {
      const endpoint = userId ? `/settings/theme/${userId}` : '/settings/theme';
      const response = await apiClient.get(endpoint);
      return response.data;
    } catch (error: any) {
      // Return default theme if not found
      return {
        mode: 'auto',
        primaryColor: '#1976d2',
        accentColor: '#ff4081',
        fontFamily: 'Inter, sans-serif',
        fontSize: 'medium',
        borderRadius: 8,
        animations: true,
      };
    }
  }

  /**
   * Update theme settings
   */
  async updateThemeSettings(
    theme: Partial<ThemeSettings>,
    userId?: string
  ): Promise<ThemeSettings> {
    try {
      const endpoint = userId ? `/settings/theme/${userId}` : '/settings/theme';
      const response = await apiClient.patch(endpoint, theme);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update theme settings');
    }
  }

  /**
   * Reset user settings to defaults
   */
  async resetUserSettings(userId?: string): Promise<UserSettings> {
    try {
      const endpoint = userId ? `/settings/users/${userId}/reset` : '/settings/user/reset';
      const response = await apiClient.post(endpoint);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to reset user settings');
    }
  }

  /**
   * Export user settings
   */
  async exportSettings(userId?: string, format: 'json' | 'yaml' = 'json'): Promise<string> {
    try {
      const endpoint = userId ? `/settings/users/${userId}/export` : '/settings/user/export';
      const response = await apiClient.get(endpoint, { params: { format } });
      return response.data.data || '';
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to export settings');
    }
  }

  /**
   * Import user settings
   */
  async importSettings(
    settingsData: string,
    format: 'json' | 'yaml' = 'json',
    userId?: string
  ): Promise<UserSettings> {
    try {
      const endpoint = userId ? `/settings/users/${userId}/import` : '/settings/user/import';
      const response = await apiClient.post(endpoint, {
        data: settingsData,
        format,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to import settings');
    }
  }

  /**
   * Test LLM connection
   */
  async testLLMConnection(config?: Partial<SystemSettings['llm']>): Promise<{
    success: boolean;
    model?: string;
    latency?: number;
    error?: string;
  }> {
    try {
      const response = await apiClient.post('/settings/test/llm', config || {});
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || 'Connection test failed',
      };
    }
  }

  /**
   * Test embedding service connection
   */
  async testEmbeddingConnection(config?: Partial<SystemSettings['embedding']>): Promise<{
    success: boolean;
    model?: string;
    dimensions?: number;
    error?: string;
  }> {
    try {
      const response = await apiClient.post('/settings/test/embedding', config || {});
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || 'Connection test failed',
      };
    }
  }

  /**
   * Test vector store connection
   */
  async testVectorStoreConnection(config?: Partial<SystemSettings['vectorStore']>): Promise<{
    success: boolean;
    collections?: string[];
    error?: string;
  }> {
    try {
      const response = await apiClient.post('/settings/test/vector-store', config || {});
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || 'Connection test failed',
      };
    }
  }

  /**
   * Get available LLM models
   */
  async getAvailableModels(provider?: string): Promise<Array<{
    id: string;
    name: string;
    description?: string;
    contextLength?: number;
    pricing?: {
      input: number;
      output: number;
    };
  }>> {
    try {
      const response = await apiClient.get('/settings/models', {
        params: provider ? { provider } : {},
      });
      return response.data.models || [];
    } catch (error: any) {
      return [];
    }
  }

  /**
   * Get available embedding models
   */
  async getAvailableEmbeddingModels(provider?: string): Promise<Array<{
    id: string;
    name: string;
    dimensions: number;
    description?: string;
  }>> {
    try {
      const response = await apiClient.get('/settings/embedding-models', {
        params: provider ? { provider } : {},
      });
      return response.data.models || [];
    } catch (error: any) {
      return [];
    }
  }

  /**
   * Get system health status
   */
  async getSystemHealth(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: Array<{
      name: string;
      status: 'up' | 'down' | 'unknown';
      lastCheck: Date;
      error?: string;
    }>;
    uptime: number;
  }> {
    try {
      const response = await apiClient.get('/settings/health');
      return response.data;
    } catch (error: any) {
      return {
        status: 'unhealthy',
        services: [],
        uptime: 0,
      };
    }
  }

  /**
   * Validate settings before saving
   */
  validateSettings(settings: Partial<UserSettings['preferences']>): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (settings.chat) {
      const { maxTokens, temperature } = settings.chat;
      if (maxTokens && (maxTokens < 1 || maxTokens > 32000)) {
        errors.push('Max tokens must be between 1 and 32000');
      }
      if (temperature && (temperature < 0 || temperature > 2)) {
        errors.push('Temperature must be between 0 and 2');
      }
    }

    if (settings.language && !['en', 'zh', 'es', 'fr', 'de', 'ja'].includes(settings.language)) {
      errors.push('Unsupported language');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme: ThemeSettings): void {
    const root = document.documentElement;
    
    // Apply CSS custom properties
    root.style.setProperty('--primary-color', theme.primaryColor);
    root.style.setProperty('--accent-color', theme.accentColor);
    root.style.setProperty('--font-family', theme.fontFamily);
    root.style.setProperty('--border-radius', `${theme.borderRadius}px`);
    
    // Apply theme mode
    root.setAttribute('data-theme', theme.mode);
    
    // Apply font size
    root.setAttribute('data-font-size', theme.fontSize);
    
    // Apply animations
    if (!theme.animations) {
      root.style.setProperty('--transition-duration', '0ms');
    } else {
      root.style.removeProperty('--transition-duration');
    }
  }

  /**
   * Get default user settings
   */
  getDefaultUserSettings(): UserSettings['preferences'] {
    return {
      theme: 'auto',
      language: 'en',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      notifications: {
        email: true,
        push: false,
        desktop: false,
      },
      chat: {
        streamingEnabled: true,
        autoSave: true,
        showSources: true,
        maxTokens: 2048,
        temperature: 0.7,
      },
      ui: {
        sidebarCollapsed: false,
        compactMode: false,
        showLineNumbers: true,
      },
    };
  }
}

// Export singleton instance
export const settingsService = new SettingsService();
export default settingsService;