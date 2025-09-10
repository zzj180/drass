import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { knowledgeService } from '@/services/knowledgeService';

interface KnowledgeSource {
  id: string;
  name: string;
  type: 'file' | 'url' | 'text';
  content?: string;
  url?: string;
  metadata: {
    size?: number;
    mimeType?: string;
    lastModified?: Date;
    chunks?: number;
    embeddings?: number;
  };
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  createdAt: Date;
  updatedAt: Date;
}

interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  sources: KnowledgeSource[];
  vectorStore: {
    type: string;
    size: number;
    dimensions: number;
  };
  createdAt: Date;
  updatedAt: Date;
}

interface SearchResult {
  id: string;
  content: string;
  score: number;
  metadata: {
    source: string;
    chunk: number;
    page?: number;
  };
}

interface KnowledgeState {
  knowledgeBases: KnowledgeBase[];
  activeKnowledgeBase: KnowledgeBase | null;
  sources: KnowledgeSource[];
  searchResults: SearchResult[];
  isLoading: boolean;
  isProcessing: boolean;
  uploadProgress: number;
  error: string | null;
}

const initialState: KnowledgeState = {
  knowledgeBases: [],
  activeKnowledgeBase: null,
  sources: [],
  searchResults: [],
  isLoading: false,
  isProcessing: false,
  uploadProgress: 0,
  error: null,
};

export const loadKnowledgeBases = createAsyncThunk('knowledge/loadBases', async () => {
  const bases = await knowledgeService.getKnowledgeBases();
  return bases;
});

export const createKnowledgeBase = createAsyncThunk(
  'knowledge/createBase',
  async ({ name, description }: { name: string; description?: string }) => {
    const base = await knowledgeService.createKnowledgeBase(name, description);
    return base;
  }
);

export const uploadDocument = createAsyncThunk(
  'knowledge/uploadDocument',
  async ({
    file,
    knowledgeBaseId,
    onProgress,
  }: {
    file: File;
    knowledgeBaseId: string;
    onProgress?: (progress: number) => void;
  }) => {
    const source = await knowledgeService.uploadDocument(file, knowledgeBaseId, onProgress);
    return source;
  }
);

export const addUrlSource = createAsyncThunk(
  'knowledge/addUrl',
  async ({ url, knowledgeBaseId }: { url: string; knowledgeBaseId: string }) => {
    const source = await knowledgeService.addUrlSource(url, knowledgeBaseId);
    return source;
  }
);

export const addTextSource = createAsyncThunk(
  'knowledge/addText',
  async ({
    text,
    name,
    knowledgeBaseId,
  }: {
    text: string;
    name: string;
    knowledgeBaseId: string;
  }) => {
    const source = await knowledgeService.addTextSource(text, name, knowledgeBaseId);
    return source;
  }
);

export const searchKnowledge = createAsyncThunk(
  'knowledge/search',
  async ({
    query,
    knowledgeBaseId,
    limit = 10,
  }: {
    query: string;
    knowledgeBaseId?: string;
    limit?: number;
  }) => {
    const results = await knowledgeService.search(query, knowledgeBaseId, limit);
    return results;
  }
);

export const deleteSource = createAsyncThunk(
  'knowledge/deleteSource',
  async ({ sourceId, knowledgeBaseId }: { sourceId: string; knowledgeBaseId: string }) => {
    await knowledgeService.deleteSource(sourceId, knowledgeBaseId);
    return { sourceId, knowledgeBaseId };
  }
);

export const reindexSource = createAsyncThunk(
  'knowledge/reindexSource',
  async ({ sourceId, knowledgeBaseId }: { sourceId: string; knowledgeBaseId: string }) => {
    const source = await knowledgeService.reindexSource(sourceId, knowledgeBaseId);
    return source;
  }
);

const knowledgeSlice = createSlice({
  name: 'knowledge',
  initialState,
  reducers: {
    setActiveKnowledgeBase: (state, action: PayloadAction<KnowledgeBase | null>) => {
      state.activeKnowledgeBase = action.payload;
      if (action.payload) {
        state.sources = action.payload.sources;
      } else {
        state.sources = [];
      }
    },
    updateUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
    clearSearchResults: (state) => {
      state.searchResults = [];
    },
    clearError: (state) => {
      state.error = null;
    },
    updateSourceStatus: (
      state,
      action: PayloadAction<{
        sourceId: string;
        status: KnowledgeSource['status'];
      }>
    ) => {
      const source = state.sources.find((s) => s.id === action.payload.sourceId);
      if (source) {
        source.status = action.payload.status;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadKnowledgeBases.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(loadKnowledgeBases.fulfilled, (state, action) => {
        state.isLoading = false;
        state.knowledgeBases = action.payload;
      })
      .addCase(loadKnowledgeBases.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to load knowledge bases';
      });

    builder
      .addCase(createKnowledgeBase.fulfilled, (state, action) => {
        state.knowledgeBases.push(action.payload);
        state.activeKnowledgeBase = action.payload;
      });

    builder
      .addCase(uploadDocument.pending, (state) => {
        state.isProcessing = true;
        state.uploadProgress = 0;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
        state.isProcessing = false;
        state.uploadProgress = 100;
        state.sources.push(action.payload);
        if (state.activeKnowledgeBase) {
          state.activeKnowledgeBase.sources.push(action.payload);
        }
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.isProcessing = false;
        state.uploadProgress = 0;
        state.error = action.error.message || 'Failed to upload document';
      });

    builder
      .addCase(addUrlSource.fulfilled, (state, action) => {
        state.sources.push(action.payload);
        if (state.activeKnowledgeBase) {
          state.activeKnowledgeBase.sources.push(action.payload);
        }
      });

    builder
      .addCase(addTextSource.fulfilled, (state, action) => {
        state.sources.push(action.payload);
        if (state.activeKnowledgeBase) {
          state.activeKnowledgeBase.sources.push(action.payload);
        }
      });

    builder
      .addCase(searchKnowledge.pending, (state) => {
        state.isLoading = true;
        state.searchResults = [];
      })
      .addCase(searchKnowledge.fulfilled, (state, action) => {
        state.isLoading = false;
        state.searchResults = action.payload;
      })
      .addCase(searchKnowledge.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Search failed';
      });

    builder
      .addCase(deleteSource.fulfilled, (state, action) => {
        state.sources = state.sources.filter((s) => s.id !== action.payload.sourceId);
        if (state.activeKnowledgeBase) {
          state.activeKnowledgeBase.sources = state.activeKnowledgeBase.sources.filter(
            (s) => s.id !== action.payload.sourceId
          );
        }
      });

    builder
      .addCase(reindexSource.fulfilled, (state, action) => {
        const index = state.sources.findIndex((s) => s.id === action.payload.id);
        if (index !== -1) {
          state.sources[index] = action.payload;
        }
      });
  },
});

export const {
  setActiveKnowledgeBase,
  updateUploadProgress,
  clearSearchResults,
  clearError,
  updateSourceStatus,
} = knowledgeSlice.actions;
export default knowledgeSlice.reducer;