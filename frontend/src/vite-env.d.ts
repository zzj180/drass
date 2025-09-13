/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_PORT: string
  readonly VITE_FRONTEND_PORT: string
  readonly VITE_LLM_PORT: string
  readonly VITE_EMBEDDING_PORT: string
  readonly VITE_RERANKING_PORT: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_BACKEND_URL: string
  readonly VITE_LLM_URL: string
  readonly VITE_EMBEDDING_URL: string
  readonly VITE_RERANKING_URL: string
  readonly VITE_WEBSOCKET_ENABLED: string
  readonly VITE_WEBSOCKET_BACKEND_URL: string
  readonly VITE_MAX_FILE_SIZE: string
  readonly VITE_ALLOWED_FILE_TYPES: string
  readonly VITE_FEATURE_FILE_UPLOAD: string
  readonly VITE_FEATURE_WEBSOCKET: string
  readonly VITE_FEATURE_STREAMING: string
  readonly VITE_FEATURE_KNOWLEDGE_BASE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
