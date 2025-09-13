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
    // Use hardcoded values for now to fix the immediate issue
    const baseUrl = 'http://localhost';
    const backendUrl = 'http://localhost:8000';
    const llmUrl = 'http://localhost:8001';
    const embeddingUrl = 'http://localhost:8002';
    const rerankingUrl = 'http://localhost:8003';
    
    // Debug logging
    console.log('Config loaded (hardcoded):', {
      baseUrl,
      backendUrl,
      llmUrl
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
        enabled: true,
        backendUrl: 'ws://localhost:8000',
      },
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
        websocket: true,
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
