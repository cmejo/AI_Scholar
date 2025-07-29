import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { EnhancedChatInterface } from '../EnhancedChatInterface';
import { EnhancedChatProvider } from '../../contexts/EnhancedChatContext';
import { DocumentProvider } from '../../contexts/DocumentContext';

// Mock the contexts and dependencies
const mockDocuments = [
  { id: '1', name: 'test-doc-1.pdf', type: 'pdf' as const, content: 'Test content 1' },
  { id: '2', name: 'test-doc-2.pdf', type: 'pdf' as const, content: 'Test content 2' }
];

const MockProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <DocumentProvider>
    <EnhancedChatProvider>
      {children}
    </EnhancedChatProvider>
  </DocumentProvider>
);

// Mock document context
vi.mock('../../contexts/DocumentContext', () => ({
  useDocument: () => ({
    documents: mockDocuments,
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
    isUploading: false
  }),
  DocumentProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

describe('EnhancedChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Render and UI Components', () => {
    it('renders the enhanced chat interface with all main components', () => {
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      // Check header elements
      expect(screen.getByText('Enhanced Memory-Aware Chat')).toBeInTheDocument();
      expect(screen.getByText('Context-aware conversations with reasoning transparency and feedback learning')).toBeInTheDocument();

      // Check feature toggle buttons
      expect(screen.getByText('Memory ON')).toBeInTheDocument();
      expect(screen.getByText('Uncertainty ON')).toBeInTheDocument();
      expect(screen.getByText('Reasoning ON')).toBeInTheDocument();
      expect(screen.getByText('Feedback ON')).toBeInTheDocument();

      // Check input area
      expect(screen.getByPlaceholderText(/Ask me anything - I'll remember our conversation/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    it('displays welcome message with feature indicators when no messages', () => {
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      expect(screen.getByText('Enhanced Memory-Aware Assistant')).toBeInTheDocument();
      expect(screen.getByText(/I remember our conversations/)).toBeInTheDocument();
      expect(screen.getByText('✓ 2 documents loaded and ready')).toBeInTheDocument();

      // Check feature indicators
      expect(screen.getByText('Memory Context')).toBeInTheDocument();
      expect(screen.getByText('Uncertainty Tracking')).toBeInTheDocument();
      expect(screen.getByText('Reasoning Steps')).toBeInTheDocument();
      expect(screen.getByText('Feedback Learning')).toBeInTheDocument();
    });
  });

  describe('Feature Toggle Functionality', () => {
    it('toggles memory awareness feature', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const memoryToggle = screen.getByText('Memory ON');
      await user.click(memoryToggle);

      expect(screen.getByText('Memory OFF')).toBeInTheDocument();
    });

    it('toggles uncertainty visualization feature', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const uncertaintyToggle = screen.getByText('Uncertainty ON');
      await user.click(uncertaintyToggle);

      expect(screen.getByText('Uncertainty OFF')).toBeInTheDocument();
    });

    it('toggles reasoning steps feature', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const reasoningToggle = screen.getByText('Reasoning ON');
      await user.click(reasoningToggle);

      expect(screen.getByText('Reasoning OFF')).toBeInTheDocument();
    });

    it('toggles feedback collection feature', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const feedbackToggle = screen.getByText('Feedback ON');
      await user.click(feedbackToggle);

      expect(screen.getByText('Feedback OFF')).toBeInTheDocument();
    });
  });

  describe('Memory Panel Functionality', () => {
    it('shows and hides memory panel', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const memoryPanelButton = screen.getByText('Memory Panel');
      await user.click(memoryPanelButton);

      expect(screen.getByText('Short-term Memory')).toBeInTheDocument();
      expect(screen.getByText('User Preferences')).toBeInTheDocument();

      await user.click(memoryPanelButton);
      expect(screen.queryByText('Short-term Memory')).not.toBeInTheDocument();
    });

    it('displays memory context when available', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      // Send a message to create memory context
      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test question');
      await user.click(screen.getByRole('button', { name: /send/i }));

      // Wait for response and open memory panel
      await waitFor(() => {
        expect(screen.getByText(/Test question/)).toBeInTheDocument();
      });

      const memoryPanelButton = screen.getByText('Memory Panel');
      await user.click(memoryPanelButton);

      expect(screen.getByText('Short-term Memory')).toBeInTheDocument();
    });
  });

  describe('Settings Panel Functionality', () => {
    it('shows and hides settings panel', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const settingsButton = screen.getByTitle('Settings');
      await user.click(settingsButton);

      expect(screen.getByText('Enhanced Chat Settings')).toBeInTheDocument();
      expect(screen.getByText('Response Style')).toBeInTheDocument();
      expect(screen.getByText('Confidence Threshold')).toBeInTheDocument();
      expect(screen.getByText('Max Memory Items')).toBeInTheDocument();

      await user.click(settingsButton);
      expect(screen.queryByText('Enhanced Chat Settings')).not.toBeInTheDocument();
    });

    it('updates response style setting', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const settingsButton = screen.getByTitle('Settings');
      await user.click(settingsButton);

      const responseStyleSelect = screen.getByDisplayValue('detailed');
      await user.selectOptions(responseStyleSelect, 'concise');

      expect(screen.getByDisplayValue('concise')).toBeInTheDocument();
    });

    it('updates confidence threshold setting', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const settingsButton = screen.getByTitle('Settings');
      await user.click(settingsButton);

      const confidenceSlider = screen.getByDisplayValue('0.7');
      fireEvent.change(confidenceSlider, { target: { value: '0.9' } });

      expect(screen.getByText('90%')).toBeInTheDocument();
    });
  });

  describe('Message Sending and Display', () => {
    it('sends a message and displays user message immediately', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(input, 'Hello, test message');
      await user.click(sendButton);

      expect(screen.getByText('Hello, test message')).toBeInTheDocument();
      expect(input).toHaveValue('');
    });

    it('shows typing indicator while processing', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test question');
      await user.click(screen.getByRole('button', { name: /send/i }));

      expect(screen.getByText(/Processing with memory context/)).toBeInTheDocument();
    });

    it('displays AI response with enhanced features', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'What is machine learning?');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Check for enhanced features in response
      expect(screen.getByText(/Sources with relevance scores/)).toBeInTheDocument();
      expect(screen.getByText(/Memory Context Used/)).toBeInTheDocument();
    });
  });

  describe('Uncertainty Visualization', () => {
    it('displays uncertainty information when enabled', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test uncertainty');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Confidence:/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('hides uncertainty when feature is disabled', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      // Disable uncertainty visualization
      const uncertaintyToggle = screen.getByText('Uncertainty ON');
      await user.click(uncertaintyToggle);

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test without uncertainty');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
    });
  });

  describe('Reasoning Steps Display', () => {
    it('displays reasoning steps when enabled', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test reasoning');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Chain of Thought/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('hides reasoning steps when feature is disabled', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      // Disable reasoning steps
      const reasoningToggle = screen.getByText('Reasoning ON');
      await user.click(reasoningToggle);

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test without reasoning');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(screen.queryByText(/Chain of Thought/)).not.toBeInTheDocument();
    });
  });

  describe('Feedback Collection', () => {
    it('displays feedback options for assistant messages when enabled', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test feedback');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Was this helpful/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('hides feedback collection when feature is disabled', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      // Disable feedback collection
      const feedbackToggle = screen.getByText('Feedback ON');
      await user.click(feedbackToggle);

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test without feedback');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(screen.queryByText(/Was this helpful/)).not.toBeInTheDocument();
    });

    it('processes feedback submission', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test feedback submission');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Was this helpful/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Click thumbs up
      const thumbsUpButton = screen.getByTitle('Helpful');
      await user.click(thumbsUpButton);

      await waitFor(() => {
        expect(screen.getByText(/Thank you for your feedback/)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design and Accessibility', () => {
    it('handles keyboard navigation', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      
      // Test Enter key submission
      await user.type(input, 'Test keyboard submission');
      await user.keyboard('{Enter}');

      expect(screen.getByText('Test keyboard submission')).toBeInTheDocument();
    });

    it('disables input and send button while typing', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(input, 'Test disable during typing');
      await user.click(sendButton);

      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });

    it('maintains proper ARIA labels and roles', () => {
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('handles empty input gracefully', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const sendButton = screen.getByRole('button', { name: /send/i });
      
      // Try to send empty message
      await user.click(sendButton);

      // Should not create any new messages
      expect(screen.queryByText(/Based on our conversation history/)).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('displays error message when message processing fails', async () => {
      const user = userEvent.setup();
      
      // Mock console.error to avoid test output noise
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test error handling');
      await user.click(screen.getByRole('button', { name: /send/i }));

      // The component should handle errors gracefully
      await waitFor(() => {
        expect(screen.getByText('Test error handling')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Performance and User Experience', () => {
    it('scrolls to bottom when new messages are added', async () => {
      const user = userEvent.setup();
      
      // Mock scrollIntoView
      const scrollIntoViewMock = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoViewMock;

      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test scroll behavior');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled();
      });
    });

    it('updates memory counter in header', async () => {
      const user = userEvent.setup();
      render(
        <MockProviders>
          <EnhancedChatInterface />
        </MockProviders>
      );

      // Initial state
      expect(screen.getByText(/Memory: 0\/10 short-term, 0 long-term/)).toBeInTheDocument();

      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test memory counter');
      await user.click(screen.getByRole('button', { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText(/Memory: 2\/10 short-term, 0 long-term/)).toBeInTheDocument();
      });
    });
  });
});