// Dify Web Configuration
// Based on official Dify documentation

window.global_config = {
  // API Configuration
  consoleApiUrl: process.env.CONSOLE_API_URL || 'http://localhost/v1',
  appApiUrl: process.env.APP_API_URL || 'http://localhost/v1',
  workflowApiUrl: process.env.WORKFLOW_API_URL || 'http://localhost/v1',
  filesUrl: process.env.FILES_URL || 'http://localhost',
  
  // Platform Configuration
  edition: process.env.EDITION || 'SELF_HOSTED',
  version: '1.0.0',
  
  // Feature Flags
  features: {
    workflow: true,
    knowledge: true,
    tools: true,
    plugins: true,
    annotation: true,
    monitoring: true,
    extension: true,
    collaboration: true,
    management: true
  },
  
  // UI Configuration
  ui: {
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'YYYY-MM-DD',
    timeFormat: 'HH:mm:ss'
  },
  
  // Drass Specific Configuration
  drass: {
    enabled: true,
    applications: [
      {
        name: 'Data Regulation Assistant',
        description: 'AI-powered assistant for data regulation compliance',
        category: 'compliance',
        icon: '🤖',
        tags: ['data-regulation', 'compliance', 'legal']
      },
      {
        name: 'Legal Document Analyzer',
        description: 'AI-powered legal document analysis and compliance checking',
        category: 'legal',
        icon: '📋',
        tags: ['legal', 'document-analysis', 'compliance']
      }
    ]
  },
  
  // Monitoring Configuration
  monitoring: {
    enabled: process.env.MONITORING_ENABLED === 'true',
    prometheusUrl: process.env.PROMETHEUS_URL || 'http://localhost:9090',
    grafanaUrl: process.env.GRAFANA_URL || 'http://localhost:3000'
  },
  
  // Security Configuration
  security: {
    corsEnabled: true,
    rateLimiting: true,
    sslRequired: false,
    allowedOrigins: ['*']
  }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = window.global_config;
}
