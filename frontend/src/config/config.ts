/**
 * Frontend Configuration
 * Central configuration management for frontend components
 */

export interface AppConfig {
  api: {
    baseUrl: string;
    backendUrl: string;
    llmUrl: string;
    embeddingUrl: string;
    rerankingUrl: string;
  };
  websocket: {
    enabled: boolean;
    backendUrl: string;
  };
  upload: {
    maxFileSize: number;
    allowedTypes: string[];
  };
  features: {
    fileUpload: boolean;
    websocket: boolean;
    streaming: boolean;
    knowledgeBase: boolean;
  };
  environment: string;
}

class ConfigManager {
  private config: AppConfig;

  constructor() {
    this.config = this.loadConfig();
  }

  private loadConfig(): AppConfig {
    // Try to load from environment variables first
    const backendPort = import.meta.env.VITE_BACKEND_PORT || '8000';
    const frontendPort = import.meta.env.VITE_FRONTEND_PORT || '3000';
    const llmPort = import.meta.env.VITE_LLM_PORT || '8001';
    const embeddingPort = import.meta.env.VITE_EMBEDDING_PORT || '8002';
    const rerankingPort = import.meta.env.VITE_RERANKING_PORT || '8003';

    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost';
    const backendUrl = import.meta.env.VITE_BACKEND_URL || `${baseUrl}:${backendPort}`;
    const llmUrl = import.meta.env.VITE_LLM_URL || `${baseUrl}:${llmPort}`;
    const embeddingUrl = import.meta.env.VITE_EMBEDDING_URL || `${baseUrl}:${embeddingPort}`;
    const rerankingUrl = import.meta.env.VITE_RERANKING_URL || `${baseUrl}:${rerankingPort}`;

    return {
      api: {
        baseUrl,
        backendUrl,
        llmUrl,
        embeddingUrl,
        rerankingUrl,
      },
      websocket: {
        enabled: import.meta.env.VITE_WEBSOCKET_ENABLED === 'true' || true,
        backendUrl: import.meta.env.VITE_WEBSOCKET_BACKEND_URL || `ws://localhost:${backendPort}`,
      },
      upload: {
        maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE || '10485760'), // 10MB
        allowedTypes: (import.meta.env.VITE_ALLOWED_FILE_TYPES || 
          'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown,application/json,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ).split(','),
      },
      features: {
        fileUpload: import.meta.env.VITE_FEATURE_FILE_UPLOAD === 'true' || true,
        websocket: import.meta.env.VITE_FEATURE_WEBSOCKET === 'true' || true,
        streaming: import.meta.env.VITE_FEATURE_STREAMING === 'true' || true,
        knowledgeBase: import.meta.env.VITE_FEATURE_KNOWLEDGE_BASE === 'true' || true,
      },
      environment: import.meta.env.MODE || 'development',
    };
  }

  public get<K extends keyof AppConfig>(key: K): AppConfig[K] {
    return this.config[key];
  }

  public getApiUrl(service: keyof AppConfig['api']): string {
    return this.config.api[service];
  }

  public getWebSocketUrl(): string {
    return this.config.websocket.backendUrl;
  }

  public getUploadConfig() {
    return this.config.upload;
  }

  public isFeatureEnabled(feature: keyof AppConfig['features']): boolean {
    return this.config.features[feature];
  }

  public isDevelopment(): boolean {
    return this.config.environment === 'development';
  }

  public isProduction(): boolean {
    return this.config.environment === 'production';
  }

  public reload(): void {
    this.config = this.loadConfig();
  }

  public toJSON(): AppConfig {
    return { ...this.config };
  }
}

// Global config instance
export const config = new ConfigManager();

// Convenience functions
export const getApiUrl = (service: keyof AppConfig['api']) => config.getApiUrl(service);
export const getWebSocketUrl = () => config.getWebSocketUrl();
export const getUploadConfig = () => config.getUploadConfig();
export const isFeatureEnabled = (feature: keyof AppConfig['features']) => config.isFeatureEnabled(feature);
export const isDevelopment = () => config.isDevelopment();
export const isProduction = () => config.isProduction();

export default config;
