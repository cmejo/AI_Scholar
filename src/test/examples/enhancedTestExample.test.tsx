/**
 * Example test file demonstrating enhanced test utilities and mocking capabilities
 * This file serves as a reference for how to use the improved testing framework
 */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import enhanced test utilities
import {
    APIMockManager,
    createMockAsyncOperation,
    createMockComponent,
    createMockHook,
    createTestRunner,
    renderWithAllProviders,
    setupTest,
    testAssertions,
    testDataFactories,
    testUtils
} from '../utils';

// Import types for type-safe testing
import type {
    ChatResponse,
    StandardError
} from '../../types/api';

// Example component for testing
const ExampleChatComponent: React.FC<{
  onSendMessage?: (message: string) => Promise<ChatResponse>;
  onError?: (error: StandardError) => void;
}> = ({ onSendMessage, onError }) => {
  const [message, setMessage] = React.useState('');
  const [response, setResponse] = React.useState<ChatResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<StandardError | null>(null);

  const handleSend = async () => {
    if (!message.trim() || !onSendMessage) return;

    setLoading(true);
    setError(null);

    try {
      const result = await onSendMessage(message);
      setResponse(result);
      setMessage('');
    } catch (err) {
      const standardError = err as StandardError;
      setError(standardError);
      onError?.(standardError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="chat-component">
      <div>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          aria-label="Chat message input"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !message.trim()}
          aria-label="Send message"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>

      {error && (
        <div role="alert" data-testid="error-message">
          Error: {error.userMessage || error.message}
          <button
            onClick={() => setError(null)}
            aria-label="Dismiss error"
          >
            Dismiss
          </button>
        </div>
      )}

      {response && (
        <div data-testid="chat-response">
          <p>{response.content}</p>
          <small>Confidence: {response.confidence}</small>
        </div>
      )}
    </div>
  );
};

// Example service for testing
class ExampleChatService {
  async sendMessage(message: string): Promise<ChatResponse> {
    const response = await fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw testDataFactories.createStandardError({
        message: 'Failed to send message',
        userMessage: 'Unable to send your message. Please try again.',
      });
    }

    return response.json();
  }
}

describe('Enhanced Test Utilities Examples', () => {
  let testRunner: ReturnType<typeof createTestRunner>;
  let apiMockManager: APIMockManager;
  let chatService: ExampleChatService;

  beforeEach(() => {
    // Set up enhanced test environment
    const testSetup = setupTest('integration');
    testRunner = testSetup.runner;

    // Set up API mocking
    apiMockManager = new APIMockManager();
    chatService = new ExampleChatService();
  });

  describe('Component Testing with Enhanced Utilities', () => {
    it('should test component with comprehensive checks', async () => {
      // Use the enhanced test runner for comprehensive component testing
      testRunner.createComponentTest({
        name: 'ExampleChatComponent - Comprehensive Test',
        component: ExampleChatComponent,
        props: {
          onSendMessage: vi.fn().mockResolvedValue(
            testDataFactories.createChatResponse({
              content: 'Test response',
              confidence: 0.95,
            })
          ),
          onError: vi.fn(),
        },
        testAccessibility: true,
        testPerformance: true,
        testResponsive: true,
      });
    });

    it('should test component with mock factories', async () => {
      const mockOnSendMessage = vi.fn();
      const mockOnError = vi.fn();

      // Create mock response using factory
      const mockResponse = testDataFactories.createChatResponse({
        content: 'Mock response from factory',
        confidence: 0.9,
        processingTime: 1200,
      });

      mockOnSendMessage.mockResolvedValue(mockResponse);

      const { container } = renderWithAllProviders(
        <ExampleChatComponent
          onSendMessage={mockOnSendMessage}
          onError={mockOnError}
        />
      );

      const user = userEvent.setup();
      const input = screen.getByLabelText('Chat message input');
      const sendButton = screen.getByLabelText('Send message');

      // Test user interaction
      await user.type(input, 'Test message');
      await user.click(sendButton);

      // Wait for response
      await waitFor(() => {
        expect(screen.getByTestId('chat-response')).toBeInTheDocument();
      });

      // Verify mock was called with correct parameters
      expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
      expect(screen.getByText('Mock response from factory')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 0.9')).toBeInTheDocument();

      // Test accessibility
      await testAssertions.assertKeyboardAccessible(container);
    });

    it('should test error handling with type-safe mocks', async () => {
      const mockOnSendMessage = vi.fn();
      const mockOnError = vi.fn();

      // Create mock error using factory
      const mockError = testDataFactories.createStandardError({
        type: 'NETWORK_ERROR',
        message: 'Network connection failed',
        userMessage: 'Unable to connect to the server. Please try again.',
        severity: 'high',
        recoverable: false,
        retryable: true,
      });

      mockOnSendMessage.mockRejectedValue(mockError);

      renderWithAllProviders(
        <ExampleChatComponent
          onSendMessage={mockOnSendMessage}
          onError={mockOnError}
        />
      );

      const user = userEvent.setup();
      const input = screen.getByLabelText('Chat message input');
      const sendButton = screen.getByLabelText('Send message');

      // Trigger error
      await user.type(input, 'Test message');
      await user.click(sendButton);

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Verify error handling
      expect(mockOnError).toHaveBeenCalledWith(mockError);
      expect(screen.getByText(/Unable to connect to the server/)).toBeInTheDocument();

      // Test error dismissal
      const dismissButton = screen.getByLabelText('Dismiss error');
      await user.click(dismissButton);

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('API Testing with Enhanced Mocking', () => {
    it('should test API with typed responses', async () => {
      // Set up typed API mock
      const mockResponse = testDataFactories.createChatResponse({
        content: 'API response',
        confidence: 0.85,
      });

      apiMockManager.mockEndpoint('/api/chat/send', {
        method: 'POST',
        response: mockResponse,
        delay: 100,
      });

      // Test the service
      const result = await chatService.sendMessage('Test message');

      expect(result).toEqual(mockResponse);
      expect(apiMockManager.verifyEndpointCalled('/api/chat/send', 'POST')).toBe(true);
    });

    it('should test API error scenarios', async () => {
      // Set up error mock
      const mockError = testDataFactories.createAPIError({
        type: 'SERVER_ERROR',
        message: 'Internal server error',
        severity: 'high',
      });

      apiMockManager.mockEndpoint('/api/chat/send', {
        method: 'POST',
        shouldFail: true,
        error: mockError,
        status: 500,
      });

      // Test error handling
      await expect(chatService.sendMessage('Test message')).rejects.toThrow();
    });

    it('should test API performance', async () => {
      testRunner.createAPITest({
        name: 'Chat API Performance Test',
        endpoint: '/api/chat/send',
        method: 'POST',
        payload: { message: 'Performance test' },
        expectedResponse: testDataFactories.createChatResponse(),
        testPerformance: true,
        timeout: 5000,
      });
    });
  });

  describe('Advanced Mock Patterns', () => {
    it('should use controllable async operations', async () => {
      const { operation, resolve, reject, pending } = createMockAsyncOperation(
        testDataFactories.createChatResponse(),
        { delay: 1000 }
      );

      const mockOnSendMessage = operation;

      renderWithAllProviders(
        <ExampleChatComponent onSendMessage={mockOnSendMessage} />
      );

      const user = userEvent.setup();
      const input = screen.getByLabelText('Chat message input');
      const sendButton = screen.getByLabelText('Send message');

      // Start async operation
      await user.type(input, 'Test message');
      await user.click(sendButton);

      // Verify loading state
      expect(screen.getByText('Sending...')).toBeInTheDocument();

      // Manually resolve the operation
      resolve();

      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
      });
    });

    it('should use mock hooks for state management', async () => {
      const { hook: useMockState, setValue, getValue } = createMockHook(
        { messages: [], loading: false },
        (initialState) => {
          const [state, setState] = React.useState(initialState);
          return { state, setState };
        }
      );

      // Test hook behavior
      expect(getValue()).toEqual({ messages: [], loading: false });

      setValue({ messages: ['test'], loading: true });
      expect(getValue()).toEqual({ messages: ['test'], loading: true });
    });

    it('should use mock components for isolation', async () => {
      const MockButton = createMockComponent<{ onClick: () => void; children: React.ReactNode }>('Button');
      
      const TestComponent = () => (
        <MockButton onClick={() => console.log('clicked')}>
          Click me
        </MockButton>
      );

      const { container } = renderWithAllProviders(<TestComponent />);

      expect(screen.getByTestId('mock-button')).toBeInTheDocument();
      expect(MockButton).toHaveBeenCalledWith(
        expect.objectContaining({
          onClick: expect.any(Function),
          children: 'Click me',
        }),
        expect.any(Object)
      );
    });
  });

  describe('Integration Testing Patterns', () => {
    it('should test complete user workflow', async () => {
      testRunner.createIntegrationTest({
        name: 'Complete Chat Workflow',
        scenario: 'User sends message and receives response',
        steps: [
          {
            action: 'render',
            assertion: () => {
              expect(screen.getByTestId('chat-component')).toBeInTheDocument();
            },
          },
          {
            action: 'type',
            target: 'Chat message input',
            value: 'Hello, AI!',
          },
          {
            action: 'click',
            target: 'Send message',
          },
          {
            action: 'wait',
            target: 'chat-response',
            timeout: 5000,
          },
          {
            action: 'verify',
            assertion: (result) => {
              expect(result).toBeInTheDocument();
            },
          },
        ],
        testData: {
          mockResponse: testDataFactories.createChatResponse({
            content: 'Hello! How can I help you?',
          }),
        },
      });
    });
  });

  describe('Performance and Accessibility Testing', () => {
    it('should measure and assert performance metrics', async () => {
      const startTime = performance.now();

      renderWithAllProviders(
        <ExampleChatComponent
          onSendMessage={vi.fn().mockResolvedValue(testDataFactories.createChatResponse())}
        />
      );

      const renderTime = performance.now() - startTime;

      // Use enhanced assertions
      testAssertions.assertRenderTime(renderTime, 1000);

      // Check memory usage if available
      if ((performance as any).memory) {
        const memoryUsage = (performance as any).memory.usedJSHeapSize;
        testAssertions.assertMemoryUsage(memoryUsage, 50 * 1024 * 1024); // 50MB
      }
    });

    it('should test accessibility compliance', async () => {
      const { container } = renderWithAllProviders(
        <ExampleChatComponent
          onSendMessage={vi.fn().mockResolvedValue(testDataFactories.createChatResponse())}
        />
      );

      // Test keyboard accessibility
      testAssertions.assertKeyboardAccessible(container);

      // Test ARIA compliance
      const input = screen.getByLabelText('Chat message input');
      expect(input).toHaveAttribute('aria-label');

      const button = screen.getByLabelText('Send message');
      expect(button).toHaveAttribute('aria-label');

      // Test error announcements
      const mockOnSendMessage = vi.fn().mockRejectedValue(
        testDataFactories.createStandardError({
          userMessage: 'Test error message',
        })
      );

      renderWithAllProviders(
        <ExampleChatComponent onSendMessage={mockOnSendMessage} />
      );

      const user = userEvent.setup();
      await user.type(screen.getByLabelText('Chat message input'), 'Test');
      await user.click(screen.getByLabelText('Send message'));

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent('Test error message');
      });
    });
  });

  describe('Test Report Generation', () => {
    it('should generate comprehensive test reports', async () => {
      // Run several tests to collect metrics
      const { container } = renderWithAllProviders(
        <ExampleChatComponent
          onSendMessage={vi.fn().mockResolvedValue(testDataFactories.createChatResponse())}
        />
      );

      // Generate report
      const report = testRunner.generateTestReport();

      expect(report).toHaveProperty('performance');
      expect(report).toHaveProperty('accessibility');
      expect(report).toHaveProperty('summary');

      expect(report.summary).toHaveProperty('totalPerformanceTests');
      expect(report.summary).toHaveProperty('averageRenderTime');
      expect(report.summary).toHaveProperty('totalAccessibilityTests');
      expect(report.summary).toHaveProperty('totalViolations');

      console.log('Test Report:', JSON.stringify(report, null, 2));
    });
  });
});

// Example of using the quick test utilities
describe('Quick Test Utilities Examples', () => {
  it('should use quick component test utility', () => {
    testUtils.testComponent(ExampleChatComponent, {
      onSendMessage: vi.fn().mockResolvedValue(testDataFactories.createChatResponse()),
    });
  });

  it('should use quick API test utility', () => {
    testUtils.testAPI('/api/chat/send', {
      method: 'POST',
      payload: { message: 'Test' },
      expectedResponse: testDataFactories.createChatResponse(),
    });
  });

  it('should use quick integration test utility', () => {
    testUtils.testIntegration('Chat Workflow', [
      { action: 'type', target: 'input', value: 'Hello' },
      { action: 'click', target: 'Send' },
      { action: 'wait', target: 'response' },
    ]);
  });
});