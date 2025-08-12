/**
 * API integration testing utilities
 */

import { expect } from 'vitest';
import { APIMockManager } from '../utils/apiMocks';

/**
 * Interface for API test configuration
 */
interface APITestConfig {
  timeout?: number;
  retries?: number;
  baseURL?: string;
}

/**
 * API integration test utilities
 */
export class APIIntegrationTester {
  private mockManager: APIMockManager;
  private config: APITestConfig;

  constructor(mockManager: APIMockManager, config: APITestConfig = {}) {
    this.mockManager = mockManager;
    this.config = {
      timeout: 10000,
      retries: 3,
      baseURL: 'http://localhost:3000/api',
      ...config,
    };
  }

  /**
   * Test chat API endpoints
   */
  async testChatAPI(): Promise<void> {
    // Test sending a message
    await this.testEndpoint({
      name: 'Send Chat Message',
      method: 'POST',
      url: '/chat/send',
      payload: {
        message: 'What is machine learning?',
        sessionId: 'test-session',
      },
      expectedResponse: {
        content: expect.any(String),
        role: 'assistant',
        sources: expect.any(Array),
      },
    });

    // Test getting chat history
    await this.testEndpoint({
      name: 'Get Chat History',
      method: 'GET',
      url: '/chat/history',
      expectedResponse: {
        messages: expect.any(Array),
        total: expect.any(Number),
      },
    });

    // Test clearing chat history
    await this.testEndpoint({
      name: 'Clear Chat History',
      method: 'DELETE',
      url: '/chat/clear',
      expectedResponse: {
        success: true,
      },
    });
  }

  /**
   * Test document API endpoints
   */
  async testDocumentAPI(): Promise<void> {
    // Test getting documents list
    await this.testEndpoint({
      name: 'Get Documents List',
      method: 'GET',
      url: '/documents',
      expectedResponse: {
        documents: expect.any(Array),
        total: expect.any(Number),
      },
    });

    // Test document upload
    await this.testEndpoint({
      name: 'Upload Document',
      method: 'POST',
      url: '/documents/upload',
      payload: new FormData(),
      expectedResponse: {
        id: expect.any(String),
        title: expect.any(String),
        type: expect.any(String),
      },
    });

    // Test document deletion
    await this.testEndpoint({
      name: 'Delete Document',
      method: 'DELETE',
      url: '/documents/test-doc-id',
      expectedResponse: {
        success: true,
      },
    });
  }

  /**
   * Test search API endpoints
   */
  async testSearchAPI(): Promise<void> {
    // Test search functionality
    await this.testEndpoint({
      name: 'Search Documents',
      method: 'POST',
      url: '/search',
      payload: {
        query: 'machine learning',
        filters: {},
        limit: 10,
      },
      expectedResponse: {
        results: expect.any(Array),
        total: expect.any(Number),
        query: 'machine learning',
      },
    });
  }

  /**
   * Test voice API endpoints
   */
  async testVoiceAPI(): Promise<void> {
    // Test speech transcription
    await this.testEndpoint({
      name: 'Transcribe Speech',
      method: 'POST',
      url: '/voice/transcribe',
      payload: new Blob(['mock audio data'], { type: 'audio/wav' }),
      expectedResponse: {
        text: expect.any(String),
        confidence: expect.any(Number),
        language: expect.any(String),
      },
    });

    // Test text-to-speech
    await this.testEndpoint({
      name: 'Synthesize Speech',
      method: 'POST',
      url: '/voice/synthesize',
      payload: {
        text: 'Hello, this is a test.',
        voice: 'default',
        language: 'en-US',
      },
      expectedResponse: {
        audioUrl: expect.any(String),
        duration: expect.any(Number),
      },
    });
  }

  /**
   * Test error handling scenarios
   */
  async testErrorHandling(): Promise<void> {
    // Test network error
    await this.testErrorScenario({
      name: 'Network Error',
      url: '/error/network',
      expectedErrorType: 'NETWORK_ERROR',
    });

    // Test server error
    await this.testErrorScenario({
      name: 'Server Error',
      url: '/error/server',
      expectedErrorType: 'SERVER_ERROR',
    });

    // Test authentication error
    await this.testErrorScenario({
      name: 'Authentication Error',
      url: '/error/auth',
      expectedErrorType: 'AUTHENTICATION_ERROR',
    });
  }

  /**
   * Test API rate limiting
   */
  async testRateLimiting(): Promise<void> {
    const requests = Array.from({ length: 10 }, (_, i) => 
      fetch(`${this.config.baseURL}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `Test message ${i}` }),
      })
    );

    const responses = await Promise.allSettled(requests);
    
    // Check if some requests were rate limited
    const rateLimitedResponses = responses.filter(
      result => result.status === 'fulfilled' && 
      (result.value as Response).status === 429
    );

    // Should have some rate limited responses if rate limiting is working
    expect(rateLimitedResponses.length).toBeGreaterThan(0);
  }

  /**
   * Test API performance
   */
  async testPerformance(): Promise<void> {
    const startTime = Date.now();
    
    await this.testEndpoint({
      name: 'Performance Test',
      method: 'POST',
      url: '/chat/send',
      payload: { message: 'Performance test message' },
      expectedResponse: expect.any(Object),
    });
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    // Response should be under 5 seconds
    expect(responseTime).toBeLessThan(5000);
  }

  /**
   * Test concurrent API requests
   */
  async testConcurrency(): Promise<void> {
    const concurrentRequests = 5;
    const requests = Array.from({ length: concurrentRequests }, (_, i) =>
      fetch(`${this.config.baseURL}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `Concurrent message ${i}` }),
      })
    );

    const responses = await Promise.all(requests);
    
    // All requests should succeed
    responses.forEach((response, index) => {
      expect(response.ok).toBe(true);
    });
  }

  /**
   * Generic endpoint testing utility
   */
  private async testEndpoint(config: {
    name: string;
    method: string;
    url: string;
    payload?: any;
    headers?: Record<string, string>;
    expectedResponse: any;
  }): Promise<void> {
    const { name, method, url, payload, headers = {}, expectedResponse } = config;
    
    const requestOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    if (payload && method !== 'GET') {
      if (payload instanceof FormData || payload instanceof Blob) {
        requestOptions.body = payload;
        delete requestOptions.headers!['Content-Type'];
      } else {
        requestOptions.body = JSON.stringify(payload);
      }
    }

    let response: Response;
    let attempts = 0;

    // Retry logic
    while (attempts < this.config.retries!) {
      try {
        response = await fetch(`${this.config.baseURL}${url}`, requestOptions);
        break;
      } catch (error) {
        attempts++;
        if (attempts >= this.config.retries!) {
          throw new Error(`${name} failed after ${this.config.retries} attempts: ${error}`);
        }
        await new Promise(resolve => setTimeout(resolve, 1000 * attempts));
      }
    }

    expect(response!.ok).toBe(true);

    const responseData = await response!.json();
    expect(responseData).toMatchObject(expectedResponse);

    // Verify the endpoint was called
    expect(this.mockManager.verifyEndpointCalled(url, method)).toBe(true);
  }

  /**
   * Test error scenarios
   */
  private async testErrorScenario(config: {
    name: string;
    url: string;
    method?: string;
    expectedErrorType: string;
  }): Promise<void> {
    const { name, url, method = 'GET', expectedErrorType } = config;

    try {
      await fetch(`${this.config.baseURL}${url}`, { method });
      throw new Error(`${name} should have thrown an error`);
    } catch (error: any) {
      expect(error.type || error.name).toBe(expectedErrorType);
    }
  }
}

/**
 * Utility function to test all API endpoints
 */
export const testAllAPIEndpoints = async (
  mockManager: APIMockManager,
  config?: APITestConfig
): Promise<void> => {
  const tester = new APIIntegrationTester(mockManager, config);

  await tester.testChatAPI();
  await tester.testDocumentAPI();
  await tester.testSearchAPI();
  await tester.testVoiceAPI();
  await tester.testErrorHandling();
};

/**
 * Utility function to test API performance
 */
export const testAPIPerformance = async (
  mockManager: APIMockManager,
  config?: APITestConfig
): Promise<void> => {
  const tester = new APIIntegrationTester(mockManager, config);

  await tester.testPerformance();
  await tester.testConcurrency();
  await tester.testRateLimiting();
};

/**
 * Utility to test WebSocket connections
 */
export const testWebSocketConnection = async (
  url: string,
  timeout = 5000
): Promise<void> => {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    const timeoutId = setTimeout(() => {
      ws.close();
      reject(new Error('WebSocket connection timeout'));
    }, timeout);

    ws.onopen = () => {
      clearTimeout(timeoutId);
      ws.close();
      resolve();
    };

    ws.onerror = (error) => {
      clearTimeout(timeoutId);
      reject(error);
    };
  });
};

/**
 * Utility to test Server-Sent Events
 */
export const testServerSentEvents = async (
  url: string,
  timeout = 5000
): Promise<void> => {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(url);
    const timeoutId = setTimeout(() => {
      eventSource.close();
      reject(new Error('SSE connection timeout'));
    }, timeout);

    eventSource.onopen = () => {
      clearTimeout(timeoutId);
      eventSource.close();
      resolve();
    };

    eventSource.onerror = (error) => {
      clearTimeout(timeoutId);
      eventSource.close();
      reject(error);
    };
  });
};