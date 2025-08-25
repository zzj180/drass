# Dify API Configuration
# Based on official Dify documentation

import os

# Core Settings
EDITION = os.getenv('EDITION', 'SELF_HOSTED')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Database Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'dify')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'dify')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'dify_password')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Weaviate Configuration
WEAVIATE_ENDPOINT = os.getenv('WEAVIATE_ENDPOINT', 'http://weaviate:8080')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY', '')

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-encryption-key-here')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')

# API URLs
CONSOLE_URL = os.getenv('CONSOLE_URL', 'http://localhost')
SERVICE_API_URL = os.getenv('SERVICE_API_URL', 'http://localhost/v1')
APP_API_URL = os.getenv('APP_API_URL', 'http://localhost/v1')
WEB_API_URL = os.getenv('WEB_API_URL', 'http://localhost/v1')
WORKFLOW_API_URL = os.getenv('WORKFLOW_API_URL', 'http://localhost/v1')
FILES_URL = os.getenv('FILES_URL', 'http://localhost')

# Drass Specific Configuration
DIFY_API_KEY = os.getenv('DIFY_API_KEY', '')
DIFY_WORKSPACE_ID = os.getenv('DIFY_WORKSPACE_ID', '')
DIFY_PLATFORM_URL = os.getenv('DIFY_PLATFORM_URL', '')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# File Upload Configuration
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
UPLOAD_FOLDER = '/app/api/storage'

# Rate Limiting
RATELIMIT_ENABLED = True
RATELIMIT_STORAGE_URL = CELERY_BROKER_URL
RATELIMIT_DEFAULT = "100 per minute"
RATELIMIT_STORAGE_URL = CELERY_BROKER_URL
