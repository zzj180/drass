import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { settingsService } from '@/services/settingsService';

interface ModelConfig {
  provider: 'openrouter' | 'openai' | 'anthropic' | 'custom';
  model: string;
  apiKey?: string;
  endpoint?: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
}

interface EmbeddingConfig {
  provider: 'openai' | 'cohere' | 'huggingface' | 'custom';
  model: string;
  apiKey?: string;
  endpoint?: string;
  dimensions: number;
  batchSize: number;
}

interface VectorStoreConfig {
  type: 'chromadb' | 'weaviate' | 'pinecone' | 'qdrant';
  endpoint: string;
  apiKey?: string;
  collection: string;
  indexName?: string;
  similarity: 'cosine' | 'euclidean' | 'dot_product';
}

interface RerankingConfig {
  enabled: boolean;
  provider: 'cohere' | 'custom';
  model: string;
  apiKey?: string;
  endpoint?: string;
  topK: number;
}

interface SystemSettings {
  language: 'en' | 'zh' | 'es' | 'fr' | 'de' | 'ja';
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    sound: boolean;
  };
  privacy: {
    telemetry: boolean;
    crashReports: boolean;
    analytics: boolean;
  };
  autoSave: boolean;
  autoSaveInterval: number;
}

interface SettingsState {
  modelConfig: ModelConfig;
  embeddingConfig: EmbeddingConfig;
  vectorStoreConfig: VectorStoreConfig;
  rerankingConfig: RerankingConfig;
  systemSettings: SystemSettings;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  isDirty: boolean;
}

const initialState: SettingsState = {
  modelConfig: {
    provider: 'openrouter',
    model: 'anthropic/claude-3-opus',
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.9,
    frequencyPenalty: 0,
    presencePenalty: 0,
  },
  embeddingConfig: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    dimensions: 1536,
    batchSize: 100,
  },
  vectorStoreConfig: {
    type: 'chromadb',
    endpoint: 'http://localhost:8000',
    collection: 'default',
    similarity: 'cosine',
  },
  rerankingConfig: {
    enabled: false,
    provider: 'cohere',
    model: 'rerank-english-v2.0',
    topK: 10,
  },
  systemSettings: {
    language: 'en',
    theme: 'system',
    notifications: {
      email: true,
      push: true,
      sound: false,
    },
    privacy: {
      telemetry: false,
      crashReports: true,
      analytics: false,
    },
    autoSave: true,
    autoSaveInterval: 30,
  },
  isLoading: false,
  isSaving: false,
  error: null,
  isDirty: false,
};

export const loadSettings = createAsyncThunk('settings/load', async () => {
  const settings = await settingsService.getSettings();
  return settings;
});

export const saveSettings = createAsyncThunk(
  'settings/save',
  async (settings: Partial<SettingsState>) => {
    const saved = await settingsService.saveSettings(settings);
    return saved;
  }
);

export const testModelConnection = createAsyncThunk(
  'settings/testModel',
  async (config: ModelConfig) => {
    const result = await settingsService.testModelConnection(config);
    return result;
  }
);

export const testEmbeddingConnection = createAsyncThunk(
  'settings/testEmbedding',
  async (config: EmbeddingConfig) => {
    const result = await settingsService.testEmbeddingConnection(config);
    return result;
  }
);

export const testVectorStoreConnection = createAsyncThunk(
  'settings/testVectorStore',
  async (config: VectorStoreConfig) => {
    const result = await settingsService.testVectorStoreConnection(config);
    return result;
  }
);

export const resetSettings = createAsyncThunk('settings/reset', async () => {
  const settings = await settingsService.resetSettings();
  return settings;
});

export const exportSettings = createAsyncThunk('settings/export', async () => {
  const data = await settingsService.exportSettings();
  return data;
});

export const importSettings = createAsyncThunk(
  'settings/import',
  async (data: string | File) => {
    const settings = await settingsService.importSettings(data);
    return settings;
  }
);

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    updateModelConfig: (state, action: PayloadAction<Partial<ModelConfig>>) => {
      state.modelConfig = { ...state.modelConfig, ...action.payload };
      state.isDirty = true;
    },
    updateEmbeddingConfig: (state, action: PayloadAction<Partial<EmbeddingConfig>>) => {
      state.embeddingConfig = { ...state.embeddingConfig, ...action.payload };
      state.isDirty = true;
    },
    updateVectorStoreConfig: (state, action: PayloadAction<Partial<VectorStoreConfig>>) => {
      state.vectorStoreConfig = { ...state.vectorStoreConfig, ...action.payload };
      state.isDirty = true;
    },
    updateRerankingConfig: (state, action: PayloadAction<Partial<RerankingConfig>>) => {
      state.rerankingConfig = { ...state.rerankingConfig, ...action.payload };
      state.isDirty = true;
    },
    updateSystemSettings: (state, action: PayloadAction<Partial<SystemSettings>>) => {
      state.systemSettings = { ...state.systemSettings, ...action.payload };
      state.isDirty = true;
    },
    setTheme: (state, action: PayloadAction<SystemSettings['theme']>) => {
      state.systemSettings.theme = action.payload;
      state.isDirty = true;
    },
    setLanguage: (state, action: PayloadAction<SystemSettings['language']>) => {
      state.systemSettings.language = action.payload;
      state.isDirty = true;
    },
    toggleNotification: (
      state,
      action: PayloadAction<keyof SystemSettings['notifications']>
    ) => {
      state.systemSettings.notifications[action.payload] =
        !state.systemSettings.notifications[action.payload];
      state.isDirty = true;
    },
    clearError: (state) => {
      state.error = null;
    },
    markClean: (state) => {
      state.isDirty = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadSettings.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(loadSettings.fulfilled, (state, action) => {
        state.isLoading = false;
        Object.assign(state, action.payload);
        state.isDirty = false;
      })
      .addCase(loadSettings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to load settings';
      });

    builder
      .addCase(saveSettings.pending, (state) => {
        state.isSaving = true;
      })
      .addCase(saveSettings.fulfilled, (state, action) => {
        state.isSaving = false;
        Object.assign(state, action.payload);
        state.isDirty = false;
      })
      .addCase(saveSettings.rejected, (state, action) => {
        state.isSaving = false;
        state.error = action.error.message || 'Failed to save settings';
      });

    builder
      .addCase(testModelConnection.fulfilled, (state) => {
        state.error = null;
      })
      .addCase(testModelConnection.rejected, (state, action) => {
        state.error = action.error.message || 'Model connection test failed';
      });

    builder
      .addCase(testEmbeddingConnection.fulfilled, (state) => {
        state.error = null;
      })
      .addCase(testEmbeddingConnection.rejected, (state, action) => {
        state.error = action.error.message || 'Embedding connection test failed';
      });

    builder
      .addCase(testVectorStoreConnection.fulfilled, (state) => {
        state.error = null;
      })
      .addCase(testVectorStoreConnection.rejected, (state, action) => {
        state.error = action.error.message || 'Vector store connection test failed';
      });

    builder
      .addCase(resetSettings.fulfilled, (state, action) => {
        Object.assign(state, action.payload);
        state.isDirty = false;
      });

    builder
      .addCase(importSettings.fulfilled, (state, action) => {
        Object.assign(state, action.payload);
        state.isDirty = false;
      });
  },
});

export const {
  updateModelConfig,
  updateEmbeddingConfig,
  updateVectorStoreConfig,
  updateRerankingConfig,
  updateSystemSettings,
  setTheme,
  setLanguage,
  toggleNotification,
  clearError,
  markClean,
} = settingsSlice.actions;
export default settingsSlice.reducer;