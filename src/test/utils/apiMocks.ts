/**
 * Comprehensive API mocking utilities for testing
 * Provides realistic API responses and error scenarios
 */

import { vi, type MockedFunction } from 'vitest';
import type { APIError, StandardError } from '../../types/api';

export interface MockEndpointConfig {
  response?: any;
  responseType?: 'json' | 'text' | 'blob' | 'arrayBuffer';
  delay?: number;
  shouldFail?: boolean;
  error?: APIError | StandardError;
  method?: string;
  requiresAuth?: boolean;
  headers?: Record<string, string>;
}

export interface APIMockManager {
  mockEndpoint: (endpoint: string, config: MockEndpointConfig) => void;
  mockStreamingEndpoint: (endpoint: string, chunks: string[]) => void;
  mockNetworkFailure: (endpoint: string) => void;
  mockSlowNetwork: (delay: number) => void;
  reset: () => void;
  restore: () => void;
  getCallHistory: (endpoint?: string) => any[];
}

export const mockAllAPIEndpoints = (): APIMockManager => {
  const originalFetch = global.fetch;
  const callHistory: Array<{ endpoint: string; options: any; timestamp: number }> = [];
  const endpointMocks = new Map<string, MockEndpointConfig>();
  let globalDelay = 0;

  const mockFetch: MockedFunction<typeof fetch> = vi.fn().mockImplementation(
    async (url: string | Request, options?: RequestInit) => {
      const endpoint = typeof url === 'string' ? url : url.url;
      const method = options?.method || 'GET';

      // Record call history
      callHistory.push({
        endpoint,
        options: { method, ...options },
        timestamp: Date.now(),
      });

      // Apply global delay if set
      if (globalDelay > 0) {
        await new Promise(resolve => setTimeout(resolve, globalDelay));
      }

      // Find matching mock configuration
      const mockConfig = endpointMocks.get(endpoint) || endpointMocks.get('*');
      
      if (!mockConfig) {
        throw new Error(`Unmocked endpoint: ${endpoint}`);
      }

      // Check method if specified
      if (mockConfig.method && mockConfig.method !== method) {
        throw new Error(`Method mismatch for ${endpoint}: expected ${mockConfig.method}, got ${method}`);
      }

      // Check authentication if required
      if (mockConfig.requiresAuth) {
        const authHeader = options?.headers?.['Authorization'] || 
                          (options?.headers as any)?.authorization;
        if (!authHeader) {
          return createErrorResponse(401, {
            type: 'UNAUTHORIZED',
            code: 'UNAUTHORIZED',
            message: 'Authentication required',
            severity: 'medium',
            timestamp: new Date(),
            details: {},
          });
        }
      }

      // Apply endpoint-specific delay
      if (mockConfig.delay) {
        await new Promise(resolve => setTimeout(resolve, mockConfig.delay));
      }

      // Handle failure scenarios
      if (mockConfig.shouldFail && mockConfig.error) {
        return createErrorResponse(getStatusFromError(mockConfig.error), mockConfig.error);
      }

      // Handle successful responses
      const response = typeof mockConfig.response === 'function' 
        ? mockConfig.response() 
        : mockConfig.response;

      return createSuccessResponse(response, mockConfig);
    }
  );

  global.fetch = mockFetch;

  const createSuccessResponse = (data: any, config: MockEndpointConfig): Response => {
    const headers = new Headers({
      'Content-Type': getContentType(config.responseType || 'json'),
      ...config.headers,
    });

    let body: any;
    switch (config.responseType) {
      case 'text':
        body = typeof data === 'string' ? data : JSON.stringify(data);
        break;
      case 'blob':
        body = data instanceof Blob ? data : new Blob([data]);
        break;
      case 'arrayBuffer':
        body = data instanceof ArrayBuffer ? data : new ArrayBuffer(0);
        break;
      case 'json':
      default:
        body = JSON.stringify(data);
        break;
    }

    return new Response(body, {
      status: 200,
      statusText: 'OK',
      headers,
    });
  };

  const createErrorResponse = (status: number, error: APIError | StandardError): Response => {
    const headers = new Headers({
      'Content-Type': 'application/json',
    });

    // Add rate limiting headers if applicable
    if (error.type === 'RATE_LIMIT_EXCEEDED' && error.details?.retry_after) {
      headers.set('Retry-After', error.details.retry_after.toString());
    }

    return new Response(JSON.stringify({ error }), {
      status,
      statusText: getStatusText(status),
      headers,
    });
  };

  const getContentType = (responseType: string): string => {
    switch (responseType) {
      case 'text':
        return 'text/plain';
      case 'blob':
        return 'application/octet-stream';
      case 'arrayBuffer':
        return 'application/octet-stream';
      case 'json':
      default:
        return 'application/json';
    }
  };

  const getStatusFromError = (error: APIError | StandardError): number => {
    switch (error.type) {
      case 'UNAUTHORIZED':
        return 401;
      case 'FORBIDDEN':
        return 403;
      case 'NOT_FOUND':
        return 404;
      case 'VALIDATION_ERROR':
        return 400;
      case 'RATE_LIMIT_EXCEEDED':
        return 429;
      case 'FILE_TOO_LARGE':
        return 413;
      case 'INTERNAL_SERVER_ERROR':
        return 500;
      case 'SERVICE_UNAVAILABLE':
        return 503;
      default:
        return 500;
    }
  };

  const getStatusText = (status: number): string => {
    const statusTexts: Record<number, string> = {
      200: 'OK',
      400: 'Bad Request',
      401: 'Unauthorized',
      403: 'Forbidden',
      404: 'Not Found',
      413: 'Payload Too Large',
      429: 'Too Many Requests',
      500: 'Internal Server Error',
      503: 'Service Unavailable',
    };
    return statusTexts[status] || 'Unknown';
  };

  return {
    mockEndpoint: (endpoint: string, config: MockEndpointConfig) => {
      endpointMocks.set(endpoint, config);
    },

    mockStreamingEndpoint: (endpoint: string, chunks: string[]) => {
      endpointMocks.set(endpoint, {
        response: () => {
          const stream = new ReadableStream({
            start(controller) {
              chunks.forEach((chunk, index) => {
                setTimeout(() => {
                  controller.enqueue(new TextEncoder().encode(chunk));
                  if (index === chunks.length - 1) {
                    controller.close();
                  }
                }, index * 100);
              });
            },
          });

          return new Response(stream, {
            headers: {
              'Content-Type': 'text/stream',
              'Transfer-Encoding': 'chunked',
            },
          });
        },
      });
    },

    mockNetworkFailure: (endpoint: string) => {
      endpointMocks.set(endpoint, {
        response: () => {
          throw new Error('Network error: Failed to fetch');
        },
      });
    },

    mockSlowNetwork: (delay: number) => {
      globalDelay = delay;
    },

    reset: () => {
      endpointMocks.clear();
      callHistory.length = 0;
      globalDelay = 0;
      mockFetch.mockClear();
    },

    restore: () => {
      global.fetch = originalFetch;
      endpointMocks.clear();
      callHistory.length = 0;
    },

    getCallHistory: (endpoint?: string) => {
      if (endpoint) {
        return callHistory.filter(call => call.endpoint.includes(endpoint));
      }
      return [...callHistory];
    },
  };
};

/**
 * Mock WebSocket for testing real-time features
 */
export const createMockWebSocket = () => {
  const mockWS = {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: WebSocket.CONNECTING,
    url: 'ws://localhost:3000/ws',
    protocol: '',
    extensions: '',
    bufferedAmount: 0,
    binaryType: 'blob' as BinaryType,
    onopen: null as ((event: Event) => void) | null,
    onclose: null as ((event: CloseEvent) => void) | null,
    onmessage: null as ((event: MessageEvent) => void) | null,
    onerror: null as ((event: Event) => void) | null,
    dispatchEvent: vi.fn(),
    CONNECTING: WebSocket.CONNECTING,
    OPEN: WebSocket.OPEN,
    CLOSING: WebSocket.CLOSING,
    CLOSED: WebSocket.CLOSED,
  };

  const originalWebSocket = global.WebSocket;
  global.WebSocket = vi.fn(() => mockWS) as any;

  const simulateOpen = () => {
    mockWS.readyState = WebSocket.OPEN;
    const event = new Event('open');
    if (mockWS.onopen) mockWS.onopen(event);
    mockWS.dispatchEvent(event);
  };

  const simulateMessage = (data: any) => {
    const event = new MessageEvent('message', { 
      data: typeof data === 'string' ? data : JSON.stringify(data) 
    });
    if (mockWS.onmessage) mockWS.onmessage(event);
    mockWS.dispatchEvent(event);
  };

  const simulateClose = (code = 1000, reason = 'Normal closure') => {
    mockWS.readyState = WebSocket.CLOSED;
    const event = new CloseEvent('close', { code, reason });
    if (mockWS.onclose) mockWS.onclose(event);
    mockWS.dispatchEvent(event);
  };

  const simulateError = () => {
    const event = new Event('error');
    if (mockWS.onerror) mockWS.onerror(event);
    mockWS.dispatchEvent(event);
  };

  const restore = () => {
    global.WebSocket = originalWebSocket;
  };

  return {
    mockWebSocket: mockWS,
    simulateOpen,
    simulateMessage,
    simulateClose,
    simulateError,
    restore,
  };
};

/**
 * Mock EventSource for testing Server-Sent Events
 */
export const createMockEventSource = () => {
  const mockES = {
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    close: vi.fn(),
    readyState: EventSource.CONNECTING,
    url: 'http://localhost:3000/events',
    withCredentials: false,
    onopen: null as ((event: Event) => void) | null,
    onmessage: null as ((event: MessageEvent) => void) | null,
    onerror: null as ((event: Event) => void) | null,
    dispatchEvent: vi.fn(),
    CONNECTING: EventSource.CONNECTING,
    OPEN: EventSource.OPEN,
    CLOSED: EventSource.CLOSED,
  };

  const originalEventSource = global.EventSource;
  global.EventSource = vi.fn(() => mockES) as any;

  const simulateOpen = () => {
    mockES.readyState = EventSource.OPEN;
    const event = new Event('open');
    if (mockES.onopen) mockES.onopen(event);
    mockES.dispatchEvent(event);
  };

  const simulateMessage = (eventData: { type?: string; data: string; id?: string }) => {
    const event = new MessageEvent('message', {
      data: eventData.data,
      lastEventId: eventData.id || '',
      type: eventData.type || 'message',
    });
    if (mockES.onmessage) mockES.onmessage(event);
    mockES.dispatchEvent(event);
  };

  const simulateError = () => {
    const event = new Event('error');
    if (mockES.onerror) mockES.onerror(event);
    mockES.dispatchEvent(event);
  };

  const simulateClose = () => {
    mockES.readyState = EventSource.CLOSED;
    mockES.close();
  };

  const restore = () => {
    global.EventSource = originalEventSource;
  };

  return {
    mockEventSource: mockES,
    simulateOpen,
    simulateMessage,
    simulateError,
    simulateClose,
    restore,
  };
};

/**
 * Create mock service responses for common scenarios
 */
export const createMockServiceResponses = () => {
  return {
    chat: {
      sendMessage: {
        content: 'This is a mock AI response to your question.',
        role: 'assistant' as const,
        sources: [
          { document: 'guide.pdf', page: 1, relevance: 0.95 },
          { document: 'manual.pdf', page: 3, relevance: 0.87 },
        ],
        timestamp: new Date(),
      },
      
      streamingResponse: [
        'This is ',
        'a streaming ',
        'response from ',
        'the AI assistant. ',
        'It demonstrates ',
        'real-time text ',
        'generation.',
      ],
    },

    documents: {
      upload: {
        id: 'doc-123',
        name: 'test-document.pdf',
        size: 1024000,
        type: 'application/pdf',
        status: 'processing' as const,
        uploadedAt: new Date(),
      },

      processingStatus: {
        id: 'doc-123',
        status: 'ready' as const,
        progress: 100,
        processed_pages: 15,
        total_pages: 15,
        processing_time: 5000,
        metadata: {
          title: 'Test Document',
          author: 'Test Author',
          created_date: '2023-01-01',
        },
      },

      list: [
        {
          id: 'doc-1',
          name: 'document1.pdf',
          size: 1024000,
          type: 'application/pdf',
          status: 'ready',
          uploadedAt: new Date('2023-01-01'),
        },
        {
          id: 'doc-2',
          name: 'document2.pdf',
          size: 2048000,
          type: 'application/pdf',
          status: 'ready',
          uploadedAt: new Date('2023-01-02'),
        },
      ],
    },

    search: {
      results: {
        results: [
          {
            document: 'guide.pdf',
            page: 1,
            content: 'Machine learning is a method of data analysis...',
            relevance: 0.95,
            metadata: { section: 'Introduction' },
          },
          {
            document: 'manual.pdf',
            page: 5,
            content: 'Deep learning networks use multiple layers...',
            relevance: 0.89,
            metadata: { section: 'Advanced Topics' },
          },
        ],
        total: 2,
        query_time: 150,
        facets: {
          document_type: { pdf: 2 },
          section: { Introduction: 1, 'Advanced Topics': 1 },
        },
      },
    },

    voice: {
      transcription: {
        text: 'What is artificial intelligence and how does it work?',
        confidence: 0.95,
        language: 'en-US',
        duration: 4.2,
        words: [
          { word: 'What', start: 0.0, end: 0.3, confidence: 0.98 },
          { word: 'is', start: 0.3, end: 0.5, confidence: 0.99 },
          { word: 'artificial', start: 0.5, end: 1.2, confidence: 0.96 },
          { word: 'intelligence', start: 1.2, end: 2.0, confidence: 0.94 },
        ],
      },

      synthesis: new ArrayBuffer(8192), // Mock audio data
    },

    analytics: {
      dashboard: {
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
          response_time_p95: 1200,
          response_time_p99: 2500,
        },
        user_engagement: {
          daily_active_users: 320,
          session_duration_avg: 1800,
          messages_per_session: 8.5,
          bounce_rate: 0.15,
        },
      },

      events: {
        success: true,
        event_id: 'event-123',
        processed_at: new Date(),
      },
    },

    errors: {
      common: [
        {
          type: 'NETWORK_ERROR',
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to server',
          severity: 'high' as const,
          timestamp: new Date(),
          details: { endpoint: '/api/chat/send', status: 0 },
        },
        {
          type: 'VALIDATION_ERROR',
          code: 'VALIDATION_ERROR',
          message: 'Invalid input data',
          severity: 'medium' as const,
          timestamp: new Date(),
          details: {
            errors: [
              { field: 'message', message: 'Message cannot be empty' },
            ],
          },
        },
        {
          type: 'RATE_LIMIT_EXCEEDED',
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests',
          severity: 'medium' as const,
          timestamp: new Date(),
          details: { retry_after: 60, limit: 100, window: 3600 },
        },
      ],
    },
  };
};

/**
 * Utility to create realistic test data
 */
export const createTestData = {
  user: (overrides: Partial<any> = {}) => ({
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user',
    created_at: new Date('2023-01-01'),
    last_login: new Date(),
    preferences: {
      theme: 'dark',
      language: 'en',
      notifications: true,
    },
    ...overrides,
  }),

  conversation: (overrides: Partial<any> = {}) => ({
    id: 'conv-123',
    title: 'Test Conversation',
    created_at: new Date(),
    updated_at: new Date(),
    message_count: 5,
    user_id: 'user-123',
    ...overrides,
  }),

  message: (overrides: Partial<any> = {}) => ({
    id: 'msg-123',
    conversation_id: 'conv-123',
    role: 'user',
    content: 'Test message content',
    timestamp: new Date(),
    metadata: {},
    ...overrides,
  }),

  document: (overrides: Partial<any> = {}) => ({
    id: 'doc-123',
    name: 'test-document.pdf',
    original_name: 'test-document.pdf',
    size: 1024000,
    type: 'application/pdf',
    status: 'ready',
    uploaded_at: new Date(),
    processed_at: new Date(),
    user_id: 'user-123',
    metadata: {
      pages: 10,
      title: 'Test Document',
      author: 'Test Author',
    },
    ...overrides,
  }),
};