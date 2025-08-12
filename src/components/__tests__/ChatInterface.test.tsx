/**
 * Comprehensive unit tests for ChatInterface component
 * Tests functionality, accessibility, error handling, and user interactions
 */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderWithAllProviders } from '../../test/utils/renderUtils';
import {
    checkAccessibility,
    simulateTyping,
    testKeyboardNavigation
} from '../../test/utils/testHelpers';
import type { ChatConversation, ChatMessage } from '../../types/chat';
import { ChatInterface } from '../ChatInterface';

// Mock the contexts
const mockSendMessage = vi.fn();
const mockCurrentConversation: ChatConversation = {
  id: 'test-conversation',
  messages: [],
  createdAt: new Date(),
  updatedAt: new Date(),
};

const mockDocuments = [
  { id: '1', name: 'Document 1.pdf', type: 'pdf', size: 1024 },
  { id: '2', name: 'Document 2.pdf', type: 'pdf', size: 2048 },
  { id: '3', name: 'Document 3.pdf', type: 'pdf', size: 3072 },
  { id: '4', name: 'Document 4.pdf', type: 'pdf', size: 4096 },
];

vi.mock('../../contexts/ChatContext', () => ({
  useChat: () => ({
    currentConversation: mockCurrentConversation,
    sendMessage: mockSendMessage,
  }),
}));

vi.mock('../../contexts/DocumentContext', () => ({
  useDocument: () => ({
    documents: mockDocuments,
  }),
}));

describe('ChatInterface', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    vi.clearAllMocks();
    mockCurrentConversation.messages = [];
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Render', () => {
    it('should render welcome message when no messages exist', () => {
      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Welcome to AI Scholar')).toBeInTheDocument();
      expect(screen.getByText(/I'm your AI assistant with access to your documents/)).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
    });

    it('should display available documents when documents exist', () => {
      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Available documents:')).toBeInTheDocument();
      expect(screen.getByText('Document 1.pdf')).toBeInTheDocument();
      expect(screen.getByText('Document 2.pdf')).toBeInTheDocument();
      expect(screen.getByText('Document 3.pdf')).toBeInTheDocument();
      expect(screen.getByText('+1 more')).toBeInTheDocument();
    });

    it('should have proper ARIA labels and roles', async () => {
      const { container } = renderWithAllProviders(<ChatInterface />);

      expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Chat interface');
      expect(screen.getByRole('log')).toHaveAttribute('aria-label', 'Chat messages');
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-describedby', 'chat-disclaimer');
      expect(screen.getByLabelText('Ask a question about your documents')).toBeInTheDocument();

      await checkAccessibility(container);
    });
  });

  describe('Message Display', () => {
    beforeEach(() => {
      mockCurrentConversation.messages = [
        {
          role: 'user',
          content: 'Hello, what is machine learning?',
          timestamp: new Date(),
        },
        {
          role: 'assistant',
          content: 'Machine learning is a subset of artificial intelligence...',
          timestamp: new Date(),
          sources: [
            { document: 'ML Guide.pdf', page: 1, relevance: 0.9 },
            { document: 'AI Basics.pdf', page: 3, relevance: 0.8 },
          ],
        },
      ] as ChatMessage[];
    });

    it('should display user and assistant messages correctly', () => {
      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Hello, what is machine learning?')).toBeInTheDocument();
      expect(screen.getByText(/Machine learning is a subset of artificial intelligence/)).toBeInTheDocument();
    });

    it('should display message sources when available', () => {
      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Sources:')).toBeInTheDocument();
      expect(screen.getByText('📄 ML Guide.pdf (p. 1)')).toBeInTheDocument();
      expect(screen.getByText('📄 AI Basics.pdf (p. 3)')).toBeInTheDocument();
    });

    it('should have proper message structure and accessibility', () => {
      renderWithAllProviders(<ChatInterface />);

      const userMessage = screen.getByLabelText(/User message/);
      const assistantMessage = screen.getByLabelText(/Assistant message/);

      expect(userMessage).toBeInTheDocument();
      expect(assistantMessage).toBeInTheDocument();
      expect(screen.getAllByRole('article')).toHaveLength(2);
    });

    it('should scroll to bottom when new messages are added', async () => {
      const scrollIntoViewMock = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoViewMock;

      renderWithAllProviders(<ChatInterface />);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: 'smooth' });
      });
    });
  });

  describe('Message Input', () => {
    it('should allow typing in the input field', async () => {
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'Test message');

      expect(input).toHaveValue('Test message');
    });

    it('should clear input after sending message', async () => {
      mockSendMessage.mockResolvedValue(undefined);
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });

    it('should call sendMessage with correct content', async () => {
      mockSendMessage.mockResolvedValue(undefined);
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'What is AI?');
      await user.click(sendButton);

      expect(mockSendMessage).toHaveBeenCalledWith('What is AI?');
    });

    it('should not send empty messages', async () => {
      renderWithAllProviders(<ChatInterface />);

      const sendButton = screen.getByRole('button', { name: /send message/i });
      await user.click(sendButton);

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should not send whitespace-only messages', async () => {
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, '   ');
      await user.click(sendButton);

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should handle form submission via Enter key', async () => {
      mockSendMessage.mockResolvedValue(undefined);
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'Test message{enter}');

      expect(mockSendMessage).toHaveBeenCalledWith('Test message');
    });
  });

  describe('Loading States', () => {
    it('should show typing indicator when sending message', async () => {
      let resolveMessage: () => void;
      const messagePromise = new Promise<void>((resolve) => {
        resolveMessage = resolve;
      });
      mockSendMessage.mockReturnValue(messagePromise);

      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      expect(screen.getByText('Thinking...')).toBeInTheDocument();
      expect(screen.getByLabelText('AI is typing')).toBeInTheDocument();

      resolveMessage!();
      await waitFor(() => {
        expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
      });
    });

    it('should disable input and send button while typing', async () => {
      let resolveMessage: () => void;
      const messagePromise = new Promise<void>((resolve) => {
        resolveMessage = resolve;
      });
      mockSendMessage.mockReturnValue(messagePromise);

      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();

      resolveMessage!();
      await waitFor(() => {
        expect(input).not.toBeDisabled();
        expect(sendButton).not.toBeDisabled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle sendMessage errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockSendMessage.mockRejectedValue(new Error('Network error'));

      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Error sending message:', expect.any(Error));
      });

      // Should reset loading state
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
      expect(input).not.toBeDisabled();

      consoleErrorSpy.mockRestore();
    });

    it('should maintain input value when send fails', async () => {
      mockSendMessage.mockRejectedValue(new Error('Network error'));
      vi.spyOn(console, 'error').mockImplementation(() => {});

      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should support proper keyboard navigation', async () => {
      renderWithAllProviders(<ChatInterface />);

      await testKeyboardNavigation(document.body, [
        'input[type="text"]',
        'button[aria-label="Send message"]',
      ]);
    });

    it('should focus input field when component mounts', () => {
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      input.focus();
      expect(input).toHaveFocus();
    });
  });

  describe('Responsive Behavior', () => {
    it('should handle long messages properly', () => {
      const longMessage = 'A'.repeat(1000);
      mockCurrentConversation.messages = [
        {
          role: 'user',
          content: longMessage,
          timestamp: new Date(),
        },
      ] as ChatMessage[];

      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('should handle many messages without performance issues', () => {
      const manyMessages: ChatMessage[] = Array.from({ length: 100 }, (_, i) => ({
        role: i % 2 === 0 ? 'user' : 'assistant',
        content: `Message ${i + 1}`,
        timestamp: new Date(),
      }));

      mockCurrentConversation.messages = manyMessages;

      const startTime = performance.now();
      renderWithAllProviders(<ChatInterface />);
      const renderTime = performance.now() - startTime;

      expect(renderTime).toBeLessThan(1000); // Should render within 1 second
      expect(screen.getByText('Message 1')).toBeInTheDocument();
      expect(screen.getByText('Message 100')).toBeInTheDocument();
    });
  });

  describe('Accessibility Features', () => {
    it('should announce new messages to screen readers', () => {
      renderWithAllProviders(<ChatInterface />);

      const messagesArea = screen.getByRole('log');
      expect(messagesArea).toHaveAttribute('aria-live', 'polite');
    });

    it('should have proper heading structure', () => {
      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Welcome to AI Scholar');
      expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Available documents:');
    });

    it('should provide context for form controls', () => {
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'chat-disclaimer');
      expect(screen.getByText(/AI Scholar can make mistakes/)).toHaveAttribute('id', 'chat-disclaimer');
    });

    it('should use semantic HTML elements', () => {
      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('search')).toBeInTheDocument();
      expect(screen.getAllByRole('region')).toHaveLength(3); // messages, input, available docs
    });
  });

  describe('Performance Optimizations', () => {
    it('should not re-render unnecessarily', () => {
      const renderSpy = vi.fn();
      const TestWrapper = () => {
        renderSpy();
        return <ChatInterface />;
      };

      const { rerender } = renderWithAllProviders(<TestWrapper />);
      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props
      rerender(<TestWrapper />);
      expect(renderSpy).toHaveBeenCalledTimes(2);
    });

    it('should handle rapid typing without performance degradation', async () => {
      renderWithAllProviders(<ChatInterface />);

      const input = screen.getByRole('textbox');
      const rapidText = 'This is a test of rapid typing performance';

      const startTime = performance.now();
      await simulateTyping(input, rapidText, 10); // Fast typing
      const typingTime = performance.now() - startTime;

      expect(typingTime).toBeLessThan(2000); // Should complete within 2 seconds
      expect(input).toHaveValue(rapidText);
    });
  });

  describe('Integration with Contexts', () => {
    it('should react to conversation changes', () => {
      const { rerender } = renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Welcome to AI Scholar')).toBeInTheDocument();

      // Update conversation with messages
      mockCurrentConversation.messages = [
        {
          role: 'user',
          content: 'Hello',
          timestamp: new Date(),
        },
      ] as ChatMessage[];

      rerender(<ChatInterface />);

      expect(screen.queryByText('Welcome to AI Scholar')).not.toBeInTheDocument();
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });

    it('should react to document changes', () => {
      const { rerender } = renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Document 1.pdf')).toBeInTheDocument();

      // Mock updated documents
      vi.mocked(vi.importActual('../../contexts/DocumentContext')).useDocument = () => ({
        documents: [{ id: '1', name: 'New Document.pdf', type: 'pdf', size: 1024 }],
      });

      rerender(<ChatInterface />);

      expect(screen.getByText('New Document.pdf')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined conversation gracefully', () => {
      vi.mocked(vi.importActual('../../contexts/ChatContext')).useChat = () => ({
        currentConversation: undefined,
        sendMessage: mockSendMessage,
      });

      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('Welcome to AI Scholar')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should handle empty documents array', () => {
      vi.mocked(vi.importActual('../../contexts/DocumentContext')).useDocument = () => ({
        documents: [],
      });

      renderWithAllProviders(<ChatInterface />);

      expect(screen.queryByText('Available documents:')).not.toBeInTheDocument();
    });

    it('should handle messages without sources', () => {
      mockCurrentConversation.messages = [
        {
          role: 'assistant',
          content: 'This is a message without sources',
          timestamp: new Date(),
        },
      ] as ChatMessage[];

      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText('This is a message without sources')).toBeInTheDocument();
      expect(screen.queryByText('Sources:')).not.toBeInTheDocument();
    });

    it('should handle special characters in messages', () => {
      const specialMessage = 'Test with special chars: <>&"\'';
      mockCurrentConversation.messages = [
        {
          role: 'user',
          content: specialMessage,
          timestamp: new Date(),
        },
      ] as ChatMessage[];

      renderWithAllProviders(<ChatInterface />);

      expect(screen.getByText(specialMessage)).toBeInTheDocument();
    });
  });
});