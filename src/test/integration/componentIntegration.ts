/**
 * Component integration testing utilities
 */

import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { expect } from 'vitest';
import { APIMockManager } from '../utils/apiMocks';
import { renderWithProviders } from '../utils/renderUtils';

/**
 * Interface for component integration test configuration
 */
interface ComponentIntegrationConfig {
  mockAPI?: boolean;
  mockServices?: Record<string, any>;
  providers?: any;
  timeout?: number;
}

/**
 * Component integration test utilities
 */
export class ComponentIntegrationTester {
  private apiMockManager?: APIMockManager;
  private config: ComponentIntegrationConfig;

  constructor(config: ComponentIntegrationConfig = {}) {
    this.config = {
      mockAPI: true,
      timeout: 10000,
      ...config,
    };

    if (this.config.mockAPI) {
      this.apiMockManager = new APIMockManager();
      this.apiMockManager
        .mockChatEndpoints()
        .mockDocumentEndpoints()
        .mockSearchEndpoints()
        .mockVoiceEndpoints();
    }
  }

  /**
   * Test chat interface integration
   */
  async testChatInterface(ChatComponent: React.ComponentType<any>): Promise<void> {
    const user = userEvent.setup();
    const { container } = renderWithProviders(
      React.createElement(ChatComponent),
      { mockServices: this.config.mockServices }
    );

    // Test initial render
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();

    // Test sending a message
    const messageInput = screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(messageInput, 'What is machine learning?');
    await user.click(sendButton);

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText(/machine learning/i)).toBeInTheDocument();
    }, { timeout: this.config.timeout });

    // Verify API was called
    if (this.apiMockManager) {
      expect(this.apiMockManager.verifyEndpointCalled('/chat/send', 'POST')).toBe(true);
    }
  }

  /**
   * Test document upload integration
   */
  async testDocumentUpload(UploadComponent: React.ComponentType<any>): Promise<void> {
    const user = userEvent.setup();
    const { container } = renderWithProviders(
      React.createElement(UploadComponent),
      { mockServices: this.config.mockServices }
    );

    // Test file upload
    const fileInput = screen.getByLabelText(/upload/i) as HTMLInputElement;
    const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await user.upload(fileInput, testFile);

    // Wait for upload to complete
    await waitFor(() => {
      expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument();
    }, { timeout: this.config.timeout });

    // Verify API was called
    if (this.apiMockManager) {
      expect(this.apiMockManager.verifyEndpointCalled('/documents/upload', 'POST')).toBe(true);
    }
  }

  /**
   * Test search functionality integration
   */
  async testSearchFunctionality(SearchComponent: React.ComponentType<any>): Promise<void> {
    const user = userEvent.setup();
    const { container } = renderWithProviders(
      React.createElement(SearchComponent),
      { mockServices: this.config.mockServices }
    );

    // Test search input
    const searchInput = screen.getByRole('searchbox');
    const searchButton = screen.getByRole('button', { name: /search/i });

    await user.type(searchInput, 'neural networks');
    await user.click(searchButton);

    // Wait for search results
    await waitFor(() => {
      expect(screen.getByText(/search results/i)).toBeInTheDocument();
    }, { timeout: this.config.timeout });

    // Verify search results are displayed
    const results = screen.getAllByTestId(/search-result/i);
    expect(results.length).toBeGreaterThan(0);

    // Verify API was called
    if (this.apiMockManager) {
      expect(this.apiMockManager.verifyEndpointCalled('/search', 'POST')).toBe(true);
    }
  }

  /**
   * Test voice interface integration
   */
  async testVoiceInterface(VoiceComponent: React.ComponentType<any>): Promise<void> {
    const user = userEvent.setup();
    const { container } = renderWithProviders(
      React.createElement(VoiceComponent),
      { mockServices: this.config.mockServices }
    );

    // Test microphone button
    const micButton = screen.getByRole('button', { name: /microphone/i });
    await user.click(micButton);

    // Wait for voice recognition to start
    await waitFor(() => {
      expect(screen.getByText(/listening/i)).toBeInTheDocument();
    });

    // Simulate speech recognition result
    const mockSpeechEvent = new CustomEvent('speechresult', {
      detail: { text: 'Hello world', confidence: 0.95 }
    });
    window.dispatchEvent(mockSpeechEvent);

    // Wait for transcription to appear
    await waitFor(() => {
      expect(screen.getByText(/hello world/i)).toBeInTheDocument();
    });
  }

  /**
   * Test error handling integration
   */
  async testErrorHandling(Component: React.ComponentType<any>): Promise<void> {
    // Mock API to return errors
    if (this.apiMockManager) {
      this.apiMockManager.mockErrors();
    }

    const user = userEvent.setup();
    const { container } = renderWithProviders(
      React.createElement(Component),
      { mockServices: this.config.mockServices }
    );

    // Trigger an action that should cause an error
    const triggerButton = screen.getByRole('button', { name: /trigger error/i });
    await user.click(triggerButton);

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(/error occurred/i)).toBeInTheDocument();
    });

    // Test error dismissal
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    await user.click(dismissButton);

    await waitFor(() => {
      expect(screen.queryByText(/error occurred/i)).not.toBeInTheDocument();
    });
  }

  /**
   * Test responsive behavior
   */
  async testResponsiveBehavior(Component: React.ComponentType<any>): Promise<void> {
    const viewports = [
      { width: 320, height: 568, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' },
    ];

    for (const viewport of viewports) {
      // Mock window dimensions
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: viewport.width,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: viewport.height,
      });

      // Trigger resize event
      window.dispatchEvent(new Event('resize'));

      const { container } = renderWithProviders(
        React.createElement(Component),
        { mockServices: this.config.mockServices }
      );

      // Wait for responsive changes
      await waitFor(() => {
        expect(container).toBeInTheDocument();
      });

      // Test viewport-specific behavior
      if (viewport.width < 768) {
        // Mobile-specific tests
        expect(screen.queryByTestId('mobile-menu')).toBeInTheDocument();
      } else {
        // Desktop-specific tests
        expect(screen.queryByTestId('desktop-sidebar')).toBeInTheDocument();
      }
    }
  }

  /**
   * Test accessibility compliance
   */
  async testAccessibility(Component: React.ComponentType<any>): Promise<void> {
    const { container } = renderWithProviders(
      React.createElement(Component),
      { mockServices: this.config.mockServices }
    );

    // Test keyboard navigation
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    // Test Tab navigation
    for (let i = 0; i < focusableElements.length; i++) {
      const element = focusableElements[i] as HTMLElement;
      element.focus();
      
      await waitFor(() => {
        expect(document.activeElement).toBe(element);
      });
    }

    // Test ARIA attributes
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
      const hasAccessibleName = 
        button.getAttribute('aria-label') ||
        button.getAttribute('aria-labelledby') ||
        button.textContent?.trim();
      
      expect(hasAccessibleName).toBeTruthy();
    });

    // Test form labels
    const inputs = container.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      const hasLabel = 
        input.getAttribute('aria-label') ||
        input.getAttribute('aria-labelledby') ||
        container.querySelector(`label[for="${input.id}"]`) ||
        input.closest('label');
      
      if (input.getAttribute('type') !== 'hidden') {
        expect(hasLabel).toBeTruthy();
      }
    });
  }

  /**
   * Test performance characteristics
   */
  async testPerformance(Component: React.ComponentType<any>): Promise<void> {
    const startTime = performance.now();
    
    const { container } = renderWithProviders(
      React.createElement(Component),
      { mockServices: this.config.mockServices }
    );

    const renderTime = performance.now() - startTime;
    
    // Component should render within reasonable time
    expect(renderTime).toBeLessThan(1000); // 1 second

    // Test re-render performance
    const reRenderStart = performance.now();
    
    // Trigger a re-render
    fireEvent.click(screen.getByRole('button', { name: /refresh/i }));
    
    const reRenderTime = performance.now() - reRenderStart;
    expect(reRenderTime).toBeLessThan(500); // 500ms
  }

  /**
   * Test data flow integration
   */
  async testDataFlow(Component: React.ComponentType<any>): Promise<void> {
    const user = userEvent.setup();
    const { container } = renderWithProviders(
      React.createElement(Component),
      { mockServices: this.config.mockServices }
    );

    // Test data loading
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });

    // Test data updates
    const updateButton = screen.getByRole('button', { name: /update/i });
    await user.click(updateButton);

    await waitFor(() => {
      expect(screen.getByText(/updated/i)).toBeInTheDocument();
    });

    // Test data persistence
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/saved/i)).toBeInTheDocument();
    });
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    if (this.apiMockManager) {
      this.apiMockManager.restore();
    }
  }
}

/**
 * Utility function to test component integration
 */
export const testComponentIntegration = async (
  Component: React.ComponentType<any>,
  tests: string[] = ['basic', 'accessibility', 'performance'],
  config?: ComponentIntegrationConfig
): Promise<void> => {
  const tester = new ComponentIntegrationTester(config);

  try {
    if (tests.includes('basic')) {
      // Run basic integration tests based on component type
      // This would need to be customized based on the actual component
    }

    if (tests.includes('accessibility')) {
      await tester.testAccessibility(Component);
    }

    if (tests.includes('performance')) {
      await tester.testPerformance(Component);
    }

    if (tests.includes('responsive')) {
      await tester.testResponsiveBehavior(Component);
    }

    if (tests.includes('errors')) {
      await tester.testErrorHandling(Component);
    }
  } finally {
    tester.cleanup();
  }
};

/**
 * Utility to test user workflows end-to-end
 */
export const testUserWorkflow = async (
  workflow: Array<{
    component: React.ComponentType<any>;
    actions: Array<{
      type: 'click' | 'type' | 'upload' | 'wait';
      target: string;
      value?: any;
      timeout?: number;
    }>;
  }>,
  config?: ComponentIntegrationConfig
): Promise<void> => {
  const tester = new ComponentIntegrationTester(config);
  const user = userEvent.setup();

  try {
    for (const step of workflow) {
      const { container } = renderWithProviders(
        React.createElement(step.component),
        { mockServices: config?.mockServices }
      );

      for (const action of step.actions) {
        switch (action.type) {
          case 'click':
            const clickTarget = screen.getByRole('button', { name: new RegExp(action.target, 'i') });
            await user.click(clickTarget);
            break;

          case 'type':
            const typeTarget = screen.getByRole('textbox');
            await user.type(typeTarget, action.value);
            break;

          case 'upload':
            const uploadTarget = screen.getByLabelText(new RegExp(action.target, 'i')) as HTMLInputElement;
            await user.upload(uploadTarget, action.value);
            break;

          case 'wait':
            await waitFor(() => {
              expect(screen.getByText(new RegExp(action.target, 'i'))).toBeInTheDocument();
            }, { timeout: action.timeout || 5000 });
            break;
        }
      }
    }
  } finally {
    tester.cleanup();
  }
};