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
    // Check environment variables first, then use defaults
    const baseUrl = import.meta.env.VITE_BASE_URL || 'http://localhost';
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';  // Changed to 8888
    const llmUrl = import.meta.env.VITE_LLM_URL || 'http://localhost:8001';
    const embeddingUrl = import.meta.env.VITE_EMBEDDING_URL || 'http://localhost:8010';  // Updated to 8010
    const rerankingUrl = import.meta.env.VITE_RERANKING_URL || 'http://localhost:8012';  // Updated to 8012

    // Debug logging
    console.log('Config loaded:', {
      baseUrl,
      backendUrl,
      llmUrl,
      embeddingUrl,
      rerankingUrl
    });

    const config = {
      api: {
        baseUrl,
        backendUrl,
        llmUrl,
        embeddingUrl,
        rerankingUrl,
      },
      websocket: {
        enabled: false, // Disabled for now - using HTTP API
        backendUrl: backendUrl.replace('http://', 'ws://').replace('https://', 'wss://'),  // Dynamic websocket URL
      upload: {
        maxFileSize: 10485760, // 10MB
        allowedTypes: [
          'application/pdf',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'text/plain',
          'text/markdown',
          'application/json',
          'text/csv',
          'application/vnd.ms-excel',
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ],
      },
      features: {
        fileUpload: true,
        websocket: false, // Disabled for now
        streaming: true,
        knowledgeBase: true,
      },
      environment: 'development',
    };
    
    console.log('Final config object:', config);
    return config;
  }

  public get<K extends keyof AppConfig>(key: K): AppConfig[K] {
    return this.config[key];
  }

  public getApiUrl(service: keyof AppConfig['api']): string {
    const url = this.config.api[service];
    console.log(`Getting API URL for ${service}:`, url);
    return url;
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

// Debug: Log configuration on load
console.log('Frontend Config Manager initialized:', {
  backendUrl: config.getApiUrl('backendUrl'),
  websocketUrl: config.getWebSocketUrl(),
  features: config.get('features')
});

// Convenience functions
export const getApiUrl = (service: keyof AppConfig['api']) => config.getApiUrl(service);
export const getWebSocketUrl = () => config.getWebSocketUrl();
export const getUploadConfig = () => config.getUploadConfig();
export const isFeatureEnabled = (feature: keyof AppConfig['features']) => config.isFeatureEnabled(feature);
export const isDevelopment = () => config.isDevelopment();
export const isProduction = () => config.isProduction();

export default config;
