/**
 * Documents Service
 * Handles document upload, management, and processing
 */

import { apiClient } from './api';

export interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'xlsx' | 'pptx' | 'txt' | 'md' | 'csv' | 'json';
  size: number;
  path: string;
  url?: string;
  uploadedAt: string;
  processedAt?: string;
  status: 'uploading' | 'uploaded' | 'processing' | 'processed' | 'error';
  metadata?: {
    pages?: number;
    words?: number;
    language?: string;
    [key: string]: any;
  };
}

export interface UploadProgress {
  documentId: string;
  progress: number;
  status: string;
}

export interface ProcessingResult {
  documentId: string;
  success: boolean;
  extractedText?: string;
  metadata?: any;
  error?: string;
}

class DocumentsService {
  /**
   * Upload a document file
   */
  async uploadDocument(file: File, onProgress?: (progress: UploadProgress) => void): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress({
              documentId: 'temp-' + Date.now(),
              progress,
              status: 'uploading'
            });
          }
        },
      });

      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to upload document');
    }
  }

  /**
   * Upload multiple documents
   */
  async uploadMultipleDocuments(
    files: File[], 
    onProgress?: (progress: UploadProgress[]) => void
  ): Promise<Document[]> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`files`, file);
    });

    try {
      const response = await apiClient.post('/documents/upload-batch', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data.documents || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to upload documents');
    }
  }

  /**
   * Get all documents
   */
  async getDocuments(): Promise<Document[]> {
    try {
      const response = await apiClient.get('/documents/');
      return response.data.documents || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch documents');
    }
  }

  /**
   * Get a specific document by ID
   */
  async getDocument(documentId: string): Promise<Document> {
    try {
      const response = await apiClient.get(`/documents/${documentId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch document');
    }
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<void> {
    try {
      await apiClient.delete(`/documents/${documentId}`);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete document');
    }
  }

  /**
   * Process a document (extract text, etc.)
   */
  async processDocument(documentId: string): Promise<ProcessingResult> {
    try {
      const response = await apiClient.post(`/documents/${documentId}/process`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to process document');
    }
  }

  /**
   * Get document content/text
   */
  async getDocumentContent(documentId: string): Promise<string> {
    try {
      const response = await apiClient.get(`/documents/${documentId}/content`);
      return response.data.content || '';
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get document content');
    }
  }

  /**
   * Search documents
   */
  async searchDocuments(query: string, filters?: any): Promise<Document[]> {
    try {
      const response = await apiClient.post('/documents/search', {
        query,
        filters,
      });
      return response.data.documents || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to search documents');
    }
  }

  /**
   * Get document folders
   */
  async getFolders(): Promise<any[]> {
    try {
      const response = await apiClient.get('/documents/folders/');
      return response.data.folders || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch folders');
    }
  }

  /**
   * Create a new folder
   */
  async createFolder(name: string, parentId?: string): Promise<any> {
    try {
      const response = await apiClient.post('/documents/folders/', {
        name,
        parentId,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create folder');
    }
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File, maxSizeMB: number = 10): { valid: boolean; error?: string } {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
      'text/markdown',
      'text/csv',
      'application/json',
    ];

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'File type not supported. Please upload PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, or JSON files.',
      };
    }

    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return {
        valid: false,
        error: `File size exceeds ${maxSizeMB}MB limit.`,
      };
    }

    return { valid: true };
  }

  /**
   * Get supported file types
   */
  getSupportedFileTypes(): string[] {
    return ['pdf', 'docx', 'xlsx', 'pptx', 'txt', 'md', 'csv', 'json'];
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// Export singleton instance
export const documentsService = new DocumentsService();
export default documentsService;