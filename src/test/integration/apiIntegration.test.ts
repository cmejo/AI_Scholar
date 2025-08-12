/**
 * Comprehensive API integration tests
 * Tests API endpoints, error handling, and data flow
 */

import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { errorTrackingService } from '../../services/errorTrackingService';
import {
    createMockEventSource,
    createMockWebSocket,
    mockAllAPIEndpoints,
    type APIMockManager,
} from '../utils/apiMocks';

describe('API Integration Tests', () => {
  let apiMockManager: APIMockManager;

  beforeAll(() => {
    apiMockManager = mockAllAPIEndpoints();
  });

  afterAll(() => {
    apiMockManager.restore();
  });

  beforeEach(() => {
    apiMockManager.reset();
    vi.clearAllMocks();
  });

  describe('Chat API Integration', () => {
    it('should send chat messages and receive responses', async () => {
      const mockResponse = {
        content: 'This is a test response from the AI',
        role: 'assistant',
        sources: [
          { document: 'test.pdf', page: 1, relevance: 0.9 },
        ],
      };

      apiMockManager.mockEndpoint('/api/chat/send', {
        response: mockResponse,
        delay: 100,
      });

      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'What is machine learning?',
          conversation_id: 'test-conversation',
        }),
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockResponse);
    });

    it('should handle chat API errors gracefully', async () => {
      apiMockManager.mockEndpoint('/api/chat/send', {
        shouldFail: true,
        error: {
          type: 'RATE_LIMIT_EXCEEDED',
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests',
          severity: 'medium',
          timestamp: new Date(),
          details: { retry_after: 60 },
        },
      });

      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Test message',
          conversation_id: 'test-conversation',
        }),
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(429);
    });

    it('should handle streaming chat responses', async () => {
      const streamingResponse = [
        'This is ',
        'a streaming ',
        'response from ',
        'the AI assistant.',
      ];

      apiMockManager.mockStreamingEndpoint('/api/chat/stream', streamingResponse);

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Tell me about AI',
          conversation_id: 'test-conversation',
        }),
      });

      expect(response.ok).toBe(true);
      expect(response.headers.get('content-type')).toContain('text/stream');

      const reader = response.body?.getReader();
      const chunks: string[] = [];

      if (reader) {
        let done = false;
        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            chunks.push(new TextDecoder().decode(value));
          }
        }
      }

      expect(chunks.join('')).toBe(streamingResponse.join(''));
    });
  });

  describe('Document API Integration', () => {
    it('should upload documents successfully', async () => {
      const mockDocument = {
        id: 'doc-123',
        name: 'test.pdf',
        size: 1024,
        type: 'application/pdf',
        status: 'processing',
      };

      apiMockManager.mockEndpoint('/api/documents/upload', {
        response: mockDocument,
        delay: 500,
      });

      const formData = new FormData();
      formData.append('file', new File(['test content'], 'test.pdf', { type: 'application/pdf' }));

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockDocument);
    });

    it('should handle document upload errors', async () => {
      apiMockManager.mockEndpoint('/api/documents/upload', {
        shouldFail: true,
        error: {
          type: 'FILE_TOO_LARGE',
          code: 'FILE_TOO_LARGE',
          message: 'File size exceeds 10MB limit',
          severity: 'medium',
          timestamp: new Date(),
          details: { max_size: '10MB', file_size: '15MB' },
        },
      });

      const formData = new FormData();
      formData.append('file', new File(['large content'], 'large.pdf', { type: 'application/pdf' }));

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(413);
    });

    it('should get document processing status', async () => {
      const mockStatus = {
        id: 'doc-123',
        status: 'ready',
        progress: 100,
        processed_pages: 10,
        total_pages: 10,
        processing_time: 5000,
      };

      apiMockManager.mockEndpoint('/api/documents/doc-123/status', {
        response: mockStatus,
      });

      const response = await fetch('/api/documents/doc-123/status');

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockStatus);
    });

    it('should delete documents successfully', async () => {
      apiMockManager.mockEndpoint('/api/documents/doc-123', {
        response: { success: true },
        method: 'DELETE',
      });

      const response = await fetch('/api/documents/doc-123', {
        method: 'DELETE',
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data.success).toBe(true);
    });
  });

  describe('Search API Integration', () => {
    it('should perform semantic search successfully', async () => {
      const mockResults = {
        results: [
          {
            document: 'test.pdf',
            page: 1,
            content: 'Machine learning is a subset of artificial intelligence...',
            relevance: 0.95,
          },
          {
            document: 'guide.pdf',
            page: 3,
            content: 'Deep learning uses neural networks...',
            relevance: 0.87,
          },
        ],
        total: 2,
        query_time: 150,
      };

      apiMockManager.mockEndpoint('/api/search', {
        response: mockResults,
        delay: 200,
      });

      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'machine learning',
          limit: 10,
          filters: { document_type: 'pdf' },
        }),
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockResults);
      expect(data.results).toHaveLength(2);
      expect(data.results[0].relevance).toBeGreaterThan(0.9);
    });

    it('should handle empty search results', async () => {
      apiMockManager.mockEndpoint('/api/search', {
        response: {
          results: [],
          total: 0,
          query_time: 50,
        },
      });

      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'nonexistent topic',
          limit: 10,
        }),
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data.results).toHaveLength(0);
      expect(data.total).toBe(0);
    });
  });

  describe('Voice API Integration', () => {
    it('should process voice input successfully', async () => {
      const mockTranscription = {
        text: 'What is artificial intelligence?',
        confidence: 0.95,
        language: 'en-US',
        duration: 3.5,
      };

      apiMockManager.mockEndpoint('/api/voice/transcribe', {
        response: mockTranscription,
        delay: 1000,
      });

      const audioBlob = new Blob(['mock audio data'], { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('audio', audioBlob);

      const response = await fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData,
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockTranscription);
      expect(data.confidence).toBeGreaterThan(0.9);
    });

    it('should handle voice synthesis requests', async () => {
      const mockAudioResponse = new ArrayBuffer(1024);

      apiMockManager.mockEndpoint('/api/voice/synthesize', {
        response: mockAudioResponse,
        responseType: 'arrayBuffer',
      });

      const response = await fetch('/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: 'Hello, this is a test message',
          voice: 'en-US-female',
          speed: 1.0,
        }),
      });

      expect(response.ok).toBe(true);
      const audioData = await response.arrayBuffer();
      expect(audioData.byteLength).toBe(1024);
    });
  });

  describe('Analytics API Integration', () => {
    it('should track user interactions', async () => {
      apiMockManager.mockEndpoint('/api/analytics/track', {
        response: { success: true, event_id: 'event-123' },
      });

      const eventData = {
        event_type: 'chat_message_sent',
        user_id: 'user-123',
        session_id: 'session-456',
        properties: {
          message_length: 25,
          response_time: 1500,
          feature: 'chat',
        },
      };

      const response = await fetch('/api/analytics/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData),
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.event_id).toBeDefined();
    });

    it('should get analytics dashboard data', async () => {
      const mockDashboardData = {
        total_users: 1250,
        active_sessions: 45,
        messages_today: 3420,
        documents_processed: 156,
        average_response_time: 850,
        error_rate: 0.02,
        top_features: ['chat', 'document_upload', 'search'],
        performance_metrics: {
          cpu_usage: 65,
          memory_usage: 78,
          disk_usage: 45,
        },
      };

      apiMockManager.mockEndpoint('/api/analytics/dashboard', {
        response: mockDashboardData,
      });

      const response = await fetch('/api/analytics/dashboard');

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockDashboardData);
      expect(data.total_users).toBeGreaterThan(1000);
      expect(data.error_rate).toBeLessThan(0.05);
    });
  });

  describe('Error Tracking Integration', () => {
    it('should integrate with error tracking service', async () => {
      const mockErrorId = 'error-123';
      apiMockManager.mockEndpoint('/api/error-tracking/errors/report', {
        response: { error_id: mockErrorId },
      });

      const errorId = await errorTrackingService.reportError({
        error_type: 'IntegrationTestError',
        error_message: 'Test error for integration',
        severity: 'medium',
        category: 'application',
      });

      expect(errorId).toBe(mockErrorId);
    });

    it('should track API call performance', async () => {
      const mockErrorId = 'perf-error-123';
      apiMockManager.mockEndpoint('/api/error-tracking/errors/report', {
        response: { error_id: mockErrorId },
      });

      // Simulate slow API call
      apiMockManager.mockEndpoint('/api/slow-endpoint', {
        response: { data: 'slow response' },
        delay: 12000, // 12 seconds
      });

      const startTime = Date.now();
      await fetch('/api/slow-endpoint');
      const duration = Date.now() - startTime;

      errorTrackingService.trackApiCall('/api/slow-endpoint', 'GET', 200, duration);

      // Verify performance issue was reported
      expect(apiMockManager.getCallHistory('/api/error-tracking/errors/report')).toHaveLength(1);
    });
  });

  describe('Real-time Communication', () => {
    it('should handle WebSocket connections', async () => {
      const { mockWebSocket, simulateOpen, simulateMessage, simulateClose } = createMockWebSocket();

      // Simulate connection
      simulateOpen();
      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN);

      // Simulate receiving a message
      const testMessage = {
        type: 'chat_response',
        content: 'Real-time response',
        timestamp: Date.now(),
      };

      simulateMessage(testMessage);
      expect(mockWebSocket.onmessage).toBeDefined();

      // Simulate sending a message
      mockWebSocket.send(JSON.stringify({
        type: 'chat_message',
        content: 'Hello WebSocket',
      }));

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'chat_message',
          content: 'Hello WebSocket',
        })
      );

      // Simulate connection close
      simulateClose();
      expect(mockWebSocket.readyState).toBe(WebSocket.CLOSED);
    });

    it('should handle Server-Sent Events', async () => {
      const { mockEventSource, simulateOpen, simulateMessage } = createMockEventSource();

      // Simulate connection
      simulateOpen();

      // Simulate receiving events
      simulateMessage({
        type: 'document_processed',
        data: JSON.stringify({
          document_id: 'doc-123',
          status: 'ready',
          pages: 10,
        }),
      });

      expect(mockEventSource.addEventListener).toHaveBeenCalledWith(
        'message',
        expect.any(Function)
      );
    });
  });

  describe('Authentication Integration', () => {
    it('should handle authenticated requests', async () => {
      const mockUserData = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user',
      };

      apiMockManager.mockEndpoint('/api/auth/me', {
        response: mockUserData,
        requiresAuth: true,
      });

      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': 'Bearer test-token',
        },
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toEqual(mockUserData);
    });

    it('should handle unauthorized requests', async () => {
      apiMockManager.mockEndpoint('/api/auth/me', {
        shouldFail: true,
        error: {
          type: 'UNAUTHORIZED',
          code: 'UNAUTHORIZED',
          message: 'Invalid or expired token',
          severity: 'medium',
          timestamp: new Date(),
          details: {},
        },
        requiresAuth: true,
      });

      const response = await fetch('/api/auth/me');

      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);
    });
  });

  describe('Rate Limiting', () => {
    it('should handle rate limiting correctly', async () => {
      // Mock rate limit exceeded
      apiMockManager.mockEndpoint('/api/chat/send', {
        shouldFail: true,
        error: {
          type: 'RATE_LIMIT_EXCEEDED',
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Rate limit exceeded',
          severity: 'medium',
          timestamp: new Date(),
          details: { retry_after: 60 },
        },
      });

      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'Test' }),
      });

      expect(response.status).toBe(429);
      expect(response.headers.get('Retry-After')).toBe('60');
    });
  });

  describe('Data Validation', () => {
    it('should validate request data', async () => {
      apiMockManager.mockEndpoint('/api/chat/send', {
        shouldFail: true,
        error: {
          type: 'VALIDATION_ERROR',
          code: 'VALIDATION_ERROR',
          message: 'Invalid request data',
          severity: 'low',
          timestamp: new Date(),
          details: {
            errors: [
              { field: 'message', message: 'Message is required' },
              { field: 'conversation_id', message: 'Invalid conversation ID format' },
            ],
          },
        },
      });

      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: '', // Empty message
          conversation_id: 'invalid-id',
        }),
      });

      expect(response.status).toBe(400);
      const errorData = await response.json();
      expect(errorData.details.errors).toHaveLength(2);
    });
  });

  describe('Performance Monitoring', () => {
    it('should monitor API response times', async () => {
      const responses = [];
      const testEndpoints = [
        '/api/chat/send',
        '/api/documents/upload',
        '/api/search',
        '/api/analytics/track',
      ];

      for (const endpoint of testEndpoints) {
        apiMockManager.mockEndpoint(endpoint, {
          response: { success: true },
          delay: Math.random() * 1000, // Random delay up to 1 second
        });

        const startTime = performance.now();
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ test: true }),
        });
        const endTime = performance.now();

        responses.push({
          endpoint,
          responseTime: endTime - startTime,
          status: response.status,
        });
      }

      // Verify all responses were successful
      responses.forEach(({ endpoint, responseTime, status }) => {
        expect(status).toBe(200);
        expect(responseTime).toBeLessThan(2000); // Should respond within 2 seconds
      });

      // Calculate average response time
      const avgResponseTime = responses.reduce((sum, r) => sum + r.responseTime, 0) / responses.length;
      expect(avgResponseTime).toBeLessThan(1500); // Average should be under 1.5 seconds
    });
  });

  describe('Error Recovery', () => {
    it('should handle network failures gracefully', async () => {
      // Mock network failure
      apiMockManager.mockNetworkFailure('/api/chat/send');

      try {
        await fetch('/api/chat/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'Test' }),
        });
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toContain('Network error');
      }
    });

    it('should implement retry logic for failed requests', async () => {
      let callCount = 0;
      apiMockManager.mockEndpoint('/api/retry-test', {
        response: () => {
          callCount++;
          if (callCount < 3) {
            throw new Error('Temporary failure');
          }
          return { success: true, attempts: callCount };
        },
      });

      // Implement simple retry logic
      const maxRetries = 3;
      let lastError: Error | null = null;

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          const response = await fetch('/api/retry-test');
          if (response.ok) {
            const data = await response.json();
            expect(data.success).toBe(true);
            expect(data.attempts).toBe(3);
            break;
          }
        } catch (error) {
          lastError = error as Error;
          if (attempt === maxRetries) {
            throw lastError;
          }
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 100 * attempt));
        }
      }
    });
  });
});