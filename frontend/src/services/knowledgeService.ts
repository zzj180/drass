/**
 * Knowledge Service
 * Handles knowledge base management, document vectors, and semantic search
 */

import { apiClient } from './api';

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  documents: string[];
  createdAt: Date;
  updatedAt: Date;
  status: 'active' | 'inactive' | 'processing';
  vectorCount?: number;
  metadata?: {
    embeddingModel?: string;
    chunkSize?: number;
    overlap?: number;
  };
}

export interface SearchResult {
  id: string;
  content: string;
  metadata: {
    source: string;
    documentId: string;
    pageNumber?: number;
    chunkIndex: number;
  };
  score: number;
  relevance: 'high' | 'medium' | 'low';
}

export interface VectorStats {
  totalVectors: number;
  dimensions: number;
  indexedDocuments: number;
  lastUpdated: Date;
  storageSize: string;
}

export interface EmbeddingRequest {
  text: string;
  model?: string;
  normalize?: boolean;
}

export interface EmbeddingResponse {
  embedding: number[];
  model: string;
  dimensions: number;
  tokens: number;
}

class KnowledgeService {
  /**
   * Get all knowledge bases
   */
  async getKnowledgeBases(): Promise<KnowledgeBase[]> {
    try {
      const response = await apiClient.get('/knowledge/bases/');
      return response.data.knowledge_bases || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch knowledge bases');
    }
  }

  /**
   * Get a specific knowledge base
   */
  async getKnowledgeBase(baseId: string): Promise<KnowledgeBase> {
    try {
      const response = await apiClient.get(`/knowledge/bases/${baseId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch knowledge base');
    }
  }

  /**
   * Create a new knowledge base
   */
  async createKnowledgeBase(
    name: string, 
    description?: string, 
    config?: any
  ): Promise<KnowledgeBase> {
    try {
      const response = await apiClient.post('/knowledge/bases/', {
        name,
        description,
        config,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create knowledge base');
    }
  }

  /**
   * Update a knowledge base
   */
  async updateKnowledgeBase(
    baseId: string, 
    updates: Partial<KnowledgeBase>
  ): Promise<KnowledgeBase> {
    try {
      const response = await apiClient.patch(`/knowledge/bases/${baseId}`, updates);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update knowledge base');
    }
  }

  /**
   * Delete a knowledge base
   */
  async deleteKnowledgeBase(baseId: string): Promise<void> {
    try {
      await apiClient.delete(`/knowledge/bases/${baseId}`);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to delete knowledge base');
    }
  }

  /**
   * Add documents to knowledge base
   */
  async addDocuments(baseId: string, documentIds: string[]): Promise<void> {
    try {
      await apiClient.post(`/knowledge/bases/${baseId}/documents`, {
        document_ids: documentIds,
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to add documents to knowledge base');
    }
  }

  /**
   * Remove documents from knowledge base
   */
  async removeDocuments(baseId: string, documentIds: string[]): Promise<void> {
    try {
      await apiClient.delete(`/knowledge/bases/${baseId}/documents`, {
        data: { document_ids: documentIds },
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to remove documents from knowledge base');
    }
  }

  /**
   * Search within knowledge base
   */
  async search(
    baseId: string,
    query: string,
    options?: {
      limit?: number;
      threshold?: number;
      includeMetadata?: boolean;
      rerank?: boolean;
    }
  ): Promise<SearchResult[]> {
    try {
      const response = await apiClient.post(`/knowledge/bases/${baseId}/search`, {
        query,
        ...options,
      });
      return response.data.results || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to search knowledge base');
    }
  }

  /**
   * Semantic search across all knowledge bases
   */
  async globalSearch(
    query: string,
    options?: {
      baseIds?: string[];
      limit?: number;
      threshold?: number;
    }
  ): Promise<SearchResult[]> {
    try {
      const response = await apiClient.post('/knowledge/search', {
        query,
        ...options,
      });
      return response.data.results || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to perform global search');
    }
  }

  /**
   * Get vector store statistics
   */
  async getVectorStats(baseId?: string): Promise<VectorStats> {
    try {
      const endpoint = baseId 
        ? `/knowledge/bases/${baseId}/stats`
        : '/knowledge/stats';
      const response = await apiClient.get(endpoint);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get vector statistics');
    }
  }

  /**
   * Generate embeddings for text
   */
  async generateEmbedding(request: EmbeddingRequest): Promise<EmbeddingResponse> {
    try {
      const response = await apiClient.post('/knowledge/embeddings', request);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to generate embeddings');
    }
  }

  /**
   * Rebuild vector index for knowledge base
   */
  async rebuildIndex(baseId: string): Promise<{ taskId: string }> {
    try {
      const response = await apiClient.post(`/knowledge/bases/${baseId}/rebuild`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to rebuild index');
    }
  }

  /**
   * Get indexing status
   */
  async getIndexingStatus(baseId: string): Promise<{
    status: 'idle' | 'indexing' | 'completed' | 'error';
    progress?: number;
    message?: string;
  }> {
    try {
      const response = await apiClient.get(`/knowledge/bases/${baseId}/status`);
      return response.data;
    } catch (error: any) {
      return { status: 'idle' };
    }
  }

  /**
   * Export knowledge base
   */
  async exportKnowledgeBase(
    baseId: string,
    format: 'json' | 'csv' | 'jsonl' = 'json'
  ): Promise<string> {
    try {
      const response = await apiClient.get(`/knowledge/bases/${baseId}/export`, {
        params: { format },
      });
      return response.data.downloadUrl || '';
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to export knowledge base');
    }
  }

  /**
   * Import knowledge base from file
   */
  async importKnowledgeBase(
    file: File,
    name?: string,
    options?: {
      overwrite?: boolean;
      chunkSize?: number;
      overlap?: number;
    }
  ): Promise<KnowledgeBase> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (name) formData.append('name', name);
      if (options) {
        Object.entries(options).forEach(([key, value]) => {
          formData.append(key, value.toString());
        });
      }

      const response = await apiClient.post('/knowledge/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to import knowledge base');
    }
  }

  /**
   * Get similar documents
   */
  async getSimilarDocuments(
    documentId: string,
    limit: number = 10,
    threshold: number = 0.5
  ): Promise<SearchResult[]> {
    try {
      const response = await apiClient.get(`/knowledge/similar/${documentId}`, {
        params: { limit, threshold },
      });
      return response.data.results || [];
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get similar documents');
    }
  }

  /**
   * Test knowledge base connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await apiClient.get('/knowledge/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  /**
   * Format search results for display
   */
  formatSearchResults(results: SearchResult[]): string[] {
    return results.map(result => {
      const source = result.metadata.source;
      const score = (result.score * 100).toFixed(1);
      return `[${score}%] ${source}: ${result.content.substring(0, 100)}...`;
    });
  }

  /**
   * Calculate relevance score
   */
  calculateRelevance(score: number): 'high' | 'medium' | 'low' {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  }
}

// Export singleton instance
export const knowledgeService = new KnowledgeService();
export default knowledgeService;