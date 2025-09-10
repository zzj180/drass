import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { documentsService } from '@/services/documentsService';

interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'xlsx' | 'pptx' | 'txt' | 'md' | 'csv' | 'json';
  size: number;
  path: string;
  url?: string;
  content?: string;
  metadata: {
    pages?: number;
    words?: number;
    tables?: number;
    images?: number;
    extracted?: boolean;
    processed?: boolean;
  };
  status: 'uploaded' | 'processing' | 'ready' | 'failed';
  createdAt: Date;
  updatedAt: Date;
  tags?: string[];
}

interface DocumentFolder {
  id: string;
  name: string;
  path: string;
  parentId?: string;
  documents: Document[];
  subfolders: DocumentFolder[];
  createdAt: Date;
  updatedAt: Date;
}

interface DocumentsState {
  documents: Document[];
  folders: DocumentFolder[];
  selectedDocuments: string[];
  activeDocument: Document | null;
  activeFolder: DocumentFolder | null;
  uploadQueue: File[];
  isLoading: boolean;
  isUploading: boolean;
  processingDocuments: string[];
  error: string | null;
  filter: {
    type?: string;
    status?: string;
    tags?: string[];
    search?: string;
  };
}

const initialState: DocumentsState = {
  documents: [],
  folders: [],
  selectedDocuments: [],
  activeDocument: null,
  activeFolder: null,
  uploadQueue: [],
  isLoading: false,
  isUploading: false,
  processingDocuments: [],
  error: null,
  filter: {},
};

export const loadDocuments = createAsyncThunk(
  'documents/loadDocuments',
  async (folderId?: string) => {
    const documents = await documentsService.getDocuments(folderId);
    return documents;
  }
);

export const loadFolders = createAsyncThunk('documents/loadFolders', async () => {
  const folders = await documentsService.getFolders();
  return folders;
});

export const uploadDocument = createAsyncThunk(
  'documents/uploadDocument',
  async ({
    file,
    folderId,
    onProgress,
  }: {
    file: File;
    folderId?: string;
    onProgress?: (progress: number) => void;
  }) => {
    const document = await documentsService.uploadDocument(file, folderId, onProgress);
    return document;
  }
);

export const uploadBatch = createAsyncThunk(
  'documents/uploadBatch',
  async ({
    files,
    folderId,
    onProgress,
  }: {
    files: File[];
    folderId?: string;
    onProgress?: (current: number, total: number) => void;
  }) => {
    const documents = await documentsService.uploadBatch(files, folderId, onProgress);
    return documents;
  }
);

export const processDocument = createAsyncThunk(
  'documents/processDocument',
  async (documentId: string) => {
    const document = await documentsService.processDocument(documentId);
    return document;
  }
);

export const extractContent = createAsyncThunk(
  'documents/extractContent',
  async (documentId: string) => {
    const content = await documentsService.extractContent(documentId);
    return { documentId, content };
  }
);

export const deleteDocument = createAsyncThunk(
  'documents/deleteDocument',
  async (documentId: string) => {
    await documentsService.deleteDocument(documentId);
    return documentId;
  }
);

export const deleteBatch = createAsyncThunk(
  'documents/deleteBatch',
  async (documentIds: string[]) => {
    await documentsService.deleteBatch(documentIds);
    return documentIds;
  }
);

export const createFolder = createAsyncThunk(
  'documents/createFolder',
  async ({ name, parentId }: { name: string; parentId?: string }) => {
    const folder = await documentsService.createFolder(name, parentId);
    return folder;
  }
);

export const moveDocuments = createAsyncThunk(
  'documents/moveDocuments',
  async ({ documentIds, folderId }: { documentIds: string[]; folderId: string }) => {
    await documentsService.moveDocuments(documentIds, folderId);
    return { documentIds, folderId };
  }
);

export const tagDocuments = createAsyncThunk(
  'documents/tagDocuments',
  async ({ documentIds, tags }: { documentIds: string[]; tags: string[] }) => {
    const documents = await documentsService.tagDocuments(documentIds, tags);
    return documents;
  }
);

const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    setActiveDocument: (state, action: PayloadAction<Document | null>) => {
      state.activeDocument = action.payload;
    },
    setActiveFolder: (state, action: PayloadAction<DocumentFolder | null>) => {
      state.activeFolder = action.payload;
    },
    selectDocument: (state, action: PayloadAction<string>) => {
      if (!state.selectedDocuments.includes(action.payload)) {
        state.selectedDocuments.push(action.payload);
      }
    },
    deselectDocument: (state, action: PayloadAction<string>) => {
      state.selectedDocuments = state.selectedDocuments.filter((id) => id !== action.payload);
    },
    selectAll: (state) => {
      state.selectedDocuments = state.documents.map((doc) => doc.id);
    },
    clearSelection: (state) => {
      state.selectedDocuments = [];
    },
    addToUploadQueue: (state, action: PayloadAction<File[]>) => {
      state.uploadQueue.push(...action.payload);
    },
    removeFromUploadQueue: (state, action: PayloadAction<number>) => {
      state.uploadQueue.splice(action.payload, 1);
    },
    clearUploadQueue: (state) => {
      state.uploadQueue = [];
    },
    setFilter: (state, action: PayloadAction<DocumentsState['filter']>) => {
      state.filter = action.payload;
    },
    clearFilter: (state) => {
      state.filter = {};
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadDocuments.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(loadDocuments.fulfilled, (state, action) => {
        state.isLoading = false;
        state.documents = action.payload;
      })
      .addCase(loadDocuments.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to load documents';
      });

    builder
      .addCase(loadFolders.fulfilled, (state, action) => {
        state.folders = action.payload;
      });

    builder
      .addCase(uploadDocument.pending, (state) => {
        state.isUploading = true;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
        state.isUploading = false;
        state.documents.push(action.payload);
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.isUploading = false;
        state.error = action.error.message || 'Failed to upload document';
      });

    builder
      .addCase(uploadBatch.pending, (state) => {
        state.isUploading = true;
      })
      .addCase(uploadBatch.fulfilled, (state, action) => {
        state.isUploading = false;
        state.documents.push(...action.payload);
        state.uploadQueue = [];
      })
      .addCase(uploadBatch.rejected, (state, action) => {
        state.isUploading = false;
        state.error = action.error.message || 'Failed to upload documents';
      });

    builder
      .addCase(processDocument.pending, (state, action) => {
        state.processingDocuments.push(action.meta.arg);
      })
      .addCase(processDocument.fulfilled, (state, action) => {
        state.processingDocuments = state.processingDocuments.filter(
          (id) => id !== action.payload.id
        );
        const index = state.documents.findIndex((doc) => doc.id === action.payload.id);
        if (index !== -1) {
          state.documents[index] = action.payload;
        }
      })
      .addCase(processDocument.rejected, (state, action) => {
        state.processingDocuments = state.processingDocuments.filter(
          (id) => id !== action.meta.arg
        );
      });

    builder
      .addCase(extractContent.fulfilled, (state, action) => {
        const document = state.documents.find((doc) => doc.id === action.payload.documentId);
        if (document) {
          document.content = action.payload.content;
          document.metadata.extracted = true;
        }
      });

    builder
      .addCase(deleteDocument.fulfilled, (state, action) => {
        state.documents = state.documents.filter((doc) => doc.id !== action.payload);
        state.selectedDocuments = state.selectedDocuments.filter((id) => id !== action.payload);
        if (state.activeDocument?.id === action.payload) {
          state.activeDocument = null;
        }
      });

    builder
      .addCase(deleteBatch.fulfilled, (state, action) => {
        state.documents = state.documents.filter((doc) => !action.payload.includes(doc.id));
        state.selectedDocuments = [];
      });

    builder
      .addCase(createFolder.fulfilled, (state, action) => {
        if (action.payload.parentId) {
          const parent = state.folders.find((f) => f.id === action.payload.parentId);
          if (parent) {
            parent.subfolders.push(action.payload);
          }
        } else {
          state.folders.push(action.payload);
        }
      });

    builder
      .addCase(moveDocuments.fulfilled, (state, action) => {
        const folder = state.folders.find((f) => f.id === action.payload.folderId);
        if (folder) {
          const movedDocs = state.documents.filter((doc) =>
            action.payload.documentIds.includes(doc.id)
          );
          folder.documents.push(...movedDocs);
        }
      });

    builder
      .addCase(tagDocuments.fulfilled, (state, action) => {
        action.payload.forEach((updatedDoc) => {
          const index = state.documents.findIndex((doc) => doc.id === updatedDoc.id);
          if (index !== -1) {
            state.documents[index] = updatedDoc;
          }
        });
      });
  },
});

export const {
  setActiveDocument,
  setActiveFolder,
  selectDocument,
  deselectDocument,
  selectAll,
  clearSelection,
  addToUploadQueue,
  removeFromUploadQueue,
  clearUploadQueue,
  setFilter,
  clearFilter,
  clearError,
} = documentsSlice.actions;
export default documentsSlice.reducer;