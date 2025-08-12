/**
 * Comprehensive integration tests for the AI Scholar RAG Chatbot
 * Tests the integration between components, services, and APIs
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

// Import test utilities
import { 
  setupIntegrationTestEnvironment,
  getIntegrationTestEnvironment,
  testAllAPIEndpoints,
  testAPIPerformance,
  testComponentIntegration,
  testUserWorkflow,
  runE2EScenarios,
  commonE2EScenarios,
} from './integration';
import { 
  mockAllAPIEndpoints,
  createMockWebSocket,
  createMockEventSource,
} from './utils/apiMocks';
import { 
  renderWithAllProviders,
  testErrorBoundary,
  testKeyboardNavigation,
  testResponsiveComponent,
  checkAccessibility,
} from './utils';
import { 
  createTestRunner,
  testUtils,
  EnhancedTestRunner,
} from './utils/testRunner';
import { 
  getTestConfig,
  testDataFactories,
  testAssertions,
} from './utils/testConfig';

// Import components for testing
import { ErrorBoundary } from '../components/ErrorBoundary';
import { Header } from '../components/Header';
import { ChatInterface } from '../components/ChatInterface';
import { DocumentManager } from '../components/DocumentManager';
import { VoiceInterface } from '../components/VoiceInterface';

// Import services for testing
import { errorTrackingService } from '../services/errorTrackingService';
import { accessibilityService } from '../services/accessibilityService';

// Set up integration test environment
setupIntegrationTestEnvironment({
  testTimeout: 30000,
  enableRealAPI: false,
  setupDatabase: false,
  mockServices: ['voiceService', 'documentService', 'chatService'],
});

describe('Integration Tests', () => {
  let user: ReturnType<typeof userEvent.setup>;
  let apiMockManager: ReturnType<typeof mockAllAPIEndpoints>;

  beforeAll(async () => {
    // Set up API mocking
    apiMockManager = mockAllAPIEndpoints();
  });

  beforeEach(() => {
    user = userEvent.setup();
  });

  afterAll(async () => {
    if (apiMockManager) {
      apiMockManager.restore();
    }
  });

  describe('API Integration Tests', () => {
    it('should test all API endpoints', async () => {
      const testEnv = getIntegrationTestEnvironment();
      const mockManager = testEnv.getAPIMockManager();
      
      if (mockManager) {
        await testAllAPIEndpoints(mockManager);
      }
    });

    it('should test API performance characteristics', async () => {
      const testEnv = getIntegrationTestEnvironment();
      const mockManager = testEnv.getAPIMockManager();
      
      if (mockManager) {
        await testAPIPerformance(mockManager);
      }
    });

    it('should handle API error scenarios gracefully', async () => {
      // Test network errors
      apiMockManager.mockEndpoint('/chat/send', {
        shouldFail: true,
        error: {
          type: 'NETWORK_ERROR',
          code: 'NETWORK_ERROR',
          message: 'Network connection failed',
          severity: 'high',
          timestamp: new Date(),
          details: {},
        },
      });

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const messageInput = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Test message');
      await user.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/network connection failed/i)).toBeInTheDocument();
      });
    });

    it('should handle slow network conditions', async () => {
      apiMockManager.mockSlowNetwork(2000);

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const messageInput = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Test message');
      await user.click(sendButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/sending/i)).toBeInTheDocument();
      });

      // Should eventually complete
      await waitFor(() => {
        expect(screen.queryByText(/sending/i)).not.toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Component Integration Tests', () => {
    it('should test ErrorBoundary integration', async () => {
      const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
        if (shouldThrow) {
          throw new Error('Integration test error');
        }
        return <div>No error</div>;
      };

      await testErrorBoundary(
        () => renderWithAllProviders(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        ),
        () => {
          // Error is thrown during render
        }
      );
    });

    it('should test Header component integration', async () => {
      await testComponentIntegration(Header, ['basic', 'accessibility', 'responsive']);
    });

    it('should test ChatInterface component integration', async () => {
      await testComponentIntegration(ChatInterface, ['basic', 'accessibility', 'performance']);
    });

    it('should test DocumentManager component integration', async () => {
      await testComponentIntegration(DocumentManager, ['basic', 'accessibility', 'errors']);
    });

    it('should test VoiceInterface component integration', async () => {
      await testComponentIntegration(VoiceInterface, ['basic', 'accessibility', 'performance']);
    });
  });

  describe('User Workflow Integration Tests', () => {
    it('should test complete chat workflow', async () => {
      await testUserWorkflow([
        {
          component: ChatInterface,
          actions: [
            { type: 'wait', target: 'textbox', description: 'Wait for chat input' },
            { type: 'type', target: 'textbox', value: 'What is machine learning?', description: 'Type question' },
            { type: 'click', target: 'Send', description: 'Send message' },
            { type: 'wait', target: 'machine learning', description: 'Wait for response', timeout: 10000 },
          ],
        },
      ]);
    });

    it('should test document upload workflow', async () => {
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await testUserWorkflow([
        {
          component: DocumentManager,
          actions: [
            { type: 'click', target: 'Upload', description: 'Click upload button' },
            { type: 'upload', target: 'file input', value: testFile, description: 'Upload file' },
            { type: 'wait', target: 'test.pdf', description: 'Wait for file to appear', timeout: 10000 },
          ],
        },
      ]);
    });

    it('should test voice interaction workflow', async () => {
      await testUserWorkflow([
        {
          component: VoiceInterface,
          actions: [
            { type: 'click', target: 'microphone', description: 'Start voice input' },
            { type: 'wait', target: 'listening', description: 'Wait for voice recognition' },
            { type: 'wait', target: 'transcription', description: 'Wait for transcription', timeout: 10000 },
          ],
        },
      ]);
    });
  });

  describe('End-to-End Scenario Tests', () => {
    it('should run complete chat workflow scenario', async () => {
      await runE2EScenarios([commonE2EScenarios.chatWorkflow]);
    });

    it('should run document upload workflow scenario', async () => {
      await runE2EScenarios([commonE2EScenarios.documentUploadWorkflow]);
    });

    it('should run search workflow scenario', async () => {
      await runE2EScenarios([commonE2EScenarios.searchWorkflow]);
    });

    it('should run voice interaction workflow scenario', async () => {
      await runE2EScenarios([commonE2EScenarios.voiceInteractionWorkflow]);
    });

    it('should run error handling workflow scenario', async () => {
      await runE2EScenarios([commonE2EScenarios.errorHandlingWorkflow]);
    });

    it('should run multiple scenarios in parallel', async () => {
      await runE2EScenarios([
        commonE2EScenarios.chatWorkflow,
        commonE2EScenarios.searchWorkflow,
        commonE2EScenarios.errorHandlingWorkflow,
      ], { parallel: true, stopOnFailure: false });
    });
  });

  describe('Accessibility Integration Tests', () => {
    it('should test keyboard navigation across components', async () => {
      const { container } = renderWithAllProviders(
        <div>
          <Header 
            onToggleSidebar={() => {}}
            currentView="chat"
            user={{ id: '1', name: 'Test User', email: 'test@example.com', role: 'user' }}
          />
          <ChatInterface />
        </div>
      );

      await testKeyboardNavigation(container, [
        'button:Toggle sidebar',
        'button:Notifications',
        'button:Accessibility settings',
        'button:General settings',
        'textbox',
        'button:Send',
      ]);
    });

    it('should test screen reader compatibility', async () => {
      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      await checkAccessibility(container);
    });

    it('should test high contrast mode compatibility', async () => {
      const { container } = renderWithAllProviders(
        <div style={{ filter: 'contrast(150%)' }}>
          <ChatInterface />
        </div>
      );

      // Verify components are still visible and functional
      expect(screen.getByRole('textbox')).toBeVisible();
      expect(screen.getByRole('button', { name: /send/i })).toBeVisible();
    });

    it('should test reduced motion preferences', async () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: (query: string) => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: () => {},
          removeListener: () => {},
          addEventListener: () => {},
          removeEventListener: () => {},
          dispatchEvent: () => {},
        }),
      });

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      // Verify animations are disabled or reduced
      const animatedElements = container.querySelectorAll('.animate-pulse, .animate-spin');
      animatedElements.forEach(element => {
        const styles = window.getComputedStyle(element);
        expect(styles.animationDuration).toBe('0s');
      });
    });
  });

  describe('Responsive Design Integration Tests', () => {
    it('should test responsive behavior across different viewports', async () => {
      const viewports = [
        { width: 320, height: 568, name: 'Mobile Portrait' },
        { width: 568, height: 320, name: 'Mobile Landscape' },
        { width: 768, height: 1024, name: 'Tablet Portrait' },
        { width: 1024, height: 768, name: 'Tablet Landscape' },
        { width: 1920, height: 1080, name: 'Desktop' },
      ];

      await testResponsiveComponent(
        () => renderWithAllProviders(<ChatInterface />),
        viewports
      );
    });

    it('should test touch interactions on mobile devices', async () => {
      // Mock touch events
      const mockTouchStart = new TouchEvent('touchstart', {
        touches: [{ clientX: 100, clientY: 100 } as Touch],
      });
      const mockTouchEnd = new TouchEvent('touchend', {
        changedTouches: [{ clientX: 100, clientY: 100 } as Touch],
      });

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const sendButton = screen.getByRole('button', { name: /send/i });
      
      fireEvent(sendButton, mockTouchStart);
      fireEvent(sendButton, mockTouchEnd);

      // Verify touch interaction works
      expect(sendButton).toHaveClass('active');
    });
  });

  describe('Performance Integration Tests', () => {
    it('should test component rendering performance', async () => {
      const startTime = performance.now();

      renderWithAllProviders(
        <div>
          <Header 
            onToggleSidebar={() => {}}
            currentView="chat"
            user={{ id: '1', name: 'Test User', email: 'test@example.com', role: 'user' }}
          />
          <ChatInterface />
          <DocumentManager />
        </div>
      );

      const renderTime = performance.now() - startTime;
      expect(renderTime).toBeLessThan(1000); // Should render within 1 second
    });

    it('should test memory usage during interactions', async () => {
      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;

      // Perform multiple interactions
      const messageInput = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send/i });

      for (let i = 0; i < 10; i++) {
        await user.clear(messageInput);
        await user.type(messageInput, `Test message ${i}`);
        await user.click(sendButton);
        await waitFor(() => {
          expect(screen.getByText(`Test message ${i}`)).toBeInTheDocument();
        });
      }

      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be reasonable (less than 10MB)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    });

    it('should test bundle size impact', async () => {
      // This would typically be tested with build tools
      // For now, we'll test that components load efficiently
      const loadStart = performance.now();

      await import('../components/ChatInterface');
      await import('../components/DocumentManager');
      await import('../components/VoiceInterface');

      const loadTime = performance.now() - loadStart;
      expect(loadTime).toBeLessThan(500); // Should load within 500ms
    });
  });

  describe('Real-time Features Integration Tests', () => {
    it('should test WebSocket integration', async () => {
      const { mockWebSocket, simulateMessage, simulateOpen } = createMockWebSocket();

      // Simulate WebSocket connection
      simulateOpen();

      // Simulate receiving a message
      simulateMessage({
        type: 'chat_response',
        content: 'Real-time response',
        timestamp: Date.now(),
      });

      expect(mockWebSocket.send).toHaveBeenCalled();
    });

    it('should test Server-Sent Events integration', async () => {
      const { mockEventSource, simulateMessage, simulateOpen } = createMockEventSource();

      // Simulate SSE connection
      simulateOpen();

      // Simulate receiving an event
      simulateMessage({
        type: 'status_update',
        data: 'Processing complete',
      });

      expect(mockEventSource.addEventListener).toHaveBeenCalled();
    });
  });

  describe('Error Recovery Integration Tests', () => {
    it('should test automatic error recovery', async () => {
      let shouldFail = true;
      
      // Mock API to fail initially, then succeed
      apiMockManager.mockEndpoint('/chat/send', {
        response: () => {
          if (shouldFail) {
            shouldFail = false;
            throw new Error('Temporary failure');
          }
          return { content: 'Recovery successful', role: 'assistant' };
        },
      });

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const messageInput = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Test recovery');
      await user.click(sendButton);

      // Should show error initially
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText('Recovery successful')).toBeInTheDocument();
      });
    });

    it('should test graceful degradation', async () => {
      // Disable voice features
      Object.defineProperty(navigator, 'mediaDevices', {
        value: undefined,
        writable: true,
      });

      const { container } = renderWithAllProviders(
        <VoiceInterface />
      );

      // Should show fallback UI
      expect(screen.getByText(/voice features are not supported/i)).toBeInTheDocument();
      expect(screen.getByText(/please use a modern browser/i)).toBeInTheDocument();
    });
  });

  describe('Data Persistence Integration Tests', () => {
    it('should test localStorage integration', async () => {
      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const messageInput = screen.getByRole('textbox');
      await user.type(messageInput, 'Persistent message');

      // Verify data is saved to localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith(
        expect.stringContaining('chat'),
        expect.stringContaining('Persistent message')
      );
    });

    it('should test sessionStorage integration', async () => {
      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      // Trigger session data storage
      fireEvent(window, new Event('beforeunload'));

      // Verify session data is saved
      expect(sessionStorage.setItem).toHaveBeenCalled();
    });

    it('should test IndexedDB integration', async () => {
      const { container } = renderWithAllProviders(
        <DocumentManager />
      );

      const uploadInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await user.upload(uploadInput, testFile);

      // Verify IndexedDB operations
      expect(window.indexedDB.open).toHaveBeenCalled();
    });
  });

  describe('Security Integration Tests', () => {
    it('should test XSS prevention', async () => {
      const maliciousInput = '<script>alert("XSS")</script>';

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const messageInput = screen.getByRole('textbox');
      await user.type(messageInput, maliciousInput);

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      // Verify script is not executed
      expect(container.querySelector('script')).toBeNull();
      expect(screen.getByText(maliciousInput)).toBeInTheDocument(); // Should be displayed as text
    });

    it('should test CSRF protection', async () => {
      // Mock CSRF token
      const csrfToken = 'test-csrf-token';
      document.head.innerHTML = `<meta name="csrf-token" content="${csrfToken}">`;

      const { container } = renderWithAllProviders(
        <ChatInterface />
      );

      const messageInput = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(messageInput, 'Test CSRF');
      await user.click(sendButton);

      // Verify CSRF token is included in requests
      expect(apiMockManager.getCallHistory()).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            headers: expect.objectContaining({
              'X-CSRF-Token': csrfToken,
            }),
          }),
        ])
      );
    });
  });
});