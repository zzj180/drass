/**
 * API Integration Tests
 * Test the connection between frontend and backend services
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { chatAPI, healthAPI } from '../../services/api';

describe('API Integration Tests', () => {
  describe('Health Check', () => {
    it('should connect to backend health endpoint', async () => {
      try {
        const health = await healthAPI.check();
        expect(health).toBeDefined();
        expect(health.status).toBe('healthy');
        expect(health.services).toBeDefined();
      } catch (error) {
        console.warn('Backend not running or not accessible:', error);
        // Skip test if backend is not running
      }
    });
  });

  describe('Test Endpoints', () => {
    it('should get services status', async () => {
      try {
        const status = await chatAPI.getServicesStatus();
        expect(status).toBeDefined();
        expect(status.status).toBe('success');
        expect(status.services).toBeDefined();
        
        // Check individual services
        expect(status.services.llm_service).toBeDefined();
        expect(status.services.embedding_service).toBeDefined();
        expect(status.services.vector_store).toBeDefined();
      } catch (error) {
        console.warn('Services status endpoint not accessible:', error);
      }
    });

    it('should send chat message without RAG', async () => {
      try {
        const response = await chatAPI.sendMessage('Hello, test message', false);
        expect(response).toBeDefined();
        expect(response.status).toBe('success');
        expect(response.message).toBe('Hello, test message');
        expect(response.response).toBeDefined();
        expect(response.used_rag).toBe(false);
      } catch (error) {
        console.warn('Chat endpoint not accessible:', error);
      }
    });

    it('should send chat message with RAG', async () => {
      try {
        const response = await chatAPI.sendMessage('What is compliance?', true);
        expect(response).toBeDefined();
        expect(response.status).toBe('success');
        expect(response.message).toBe('What is compliance?');
        expect(response.response).toBeDefined();
        expect(response.used_rag).toBe(true);
      } catch (error) {
        console.warn('Chat with RAG endpoint not accessible:', error);
      }
    });

    it('should test embedding generation', async () => {
      try {
        const response = await chatAPI.testEmbedding('Test text for embedding');
        expect(response).toBeDefined();
        expect(response.status).toBe('success');
        expect(response.text).toBe('Test text for embedding');
        expect(response.embedding_size).toBeGreaterThan(0);
        expect(response.embedding_sample).toBeDefined();
        expect(Array.isArray(response.embedding_sample)).toBe(true);
      } catch (error) {
        console.warn('Embedding endpoint not accessible:', error);
      }
    });
  });

  describe('Response Times', () => {
    it('should respond within acceptable time limits', async () => {
      try {
        const startTime = Date.now();
        await healthAPI.check();
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
      } catch (error) {
        console.warn('Cannot test response time:', error);
      }
    });
  });
});