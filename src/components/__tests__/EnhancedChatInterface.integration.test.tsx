import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { EnhancedChatInterface } from '../EnhancedChatInterface';

// Mock the contexts
vi.mock('../../contexts/EnhancedChatContext', () => ({
  useEnhancedChat: () => ({
    conversations: [],
    currentConversation: null,
    createNewConversation: vi.fn(),
    switchConversation: vi.fn(),
    sendMessage: vi.fn(),
    deleteConversation: vi.fn(),
  })
}));

vi.mock('../../contexts/DocumentContext', () => ({
  useDocument: () => ({
    documents: [
      { id: '1', name: 'test-doc.pdf', type: 'pdf', content: 'Test content' },
      { id: '2', name: 'another-doc.pdf', type: 'pdf', content: 'More content' }
    ],
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
    isUploading: false
  })
}));

// Mock the child components with more realistic behavior
vi.mock('../UncertaintyVisualization', () => ({
  UncertaintyVisualization: ({ uncertainty, isExpanded, onToggle }: any) => (
    <div data-testid="uncertainty-visualization">
      <button onClick={onToggle} data-testid="uncertainty-toggle">
        Confidence: {(uncertainty.confidence * 100).toFixed(0)}%
      </button>
      {isExpanded && (
        <div data-testid="uncertainty-details">
          <div>Uncertainty Factors Analysis:</div>
          {uncertainty.factors.map((factor: any, index: number) => (
            <div key={index} data-testid={`uncertainty-factor-${index}`}>
              {factor.factor}: {(factor.impact * 100).toFixed(0)}%
            </div>
          ))}
        </div>
      )}
    </div>
  )
}));

vi.mock('../ReasoningStepsDisplay', () => ({
  ReasoningStepsDisplay: ({ reasoning, isExpanded, onToggle }: any) => (
    <div data-testid="reasoning-steps">
      <button onClick={onToggle} data-testid="reasoning-toggle">
        Chain of Thought ({reasoning.steps.length} steps)
      </button>
      {isExpanded && (
        <div data-testid="reasoning-details">
          <div>Reasoning Process Breakdown:</div>
          {reasoning.steps.map((step: any, index: number) => (
            <div key={index} data-testid={`reasoning-step-${index}`}>
              Step {step.step}: {step.description}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}));

vi.mock('../FeedbackCollector', () => ({
  FeedbackCollector: ({ messageId, onFeedback, currentFeedback }: any) => (
    <div data-testid="feedback-collector">
      {!currentFeedback ? (
        <div>
          <span>Was this helpful?</span>
          <button 
            onClick={() => onFeedback(messageId, { rating: 5, helpful: true })}
            data-testid="thumbs-up"
          >
            👍
          </button>
          <button 
            onClick={() => onFeedback(messageId, { rating: 2, helpful: false })}
            data-testid="thumbs-down"
          >
            👎
          </button>
        </div>
      ) : (
        <div data-testid="feedback-submitted">
          Feedback submitted: {currentFeedback.helpful ? 'Helpful' : 'Not helpful'}
        </div>
      )}
    </div>
  )
}));

describe('EnhancedChatInterface - Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Feature Integration', () => {
    it('integrates all enhanced features in a complete conversation flow', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Verify initial state
      expect(screen.getByText('Enhanced Memory-Aware Assistant')).toBeInTheDocument();
      expect(screen.getByText('Memory ON')).toBeInTheDocument();
      expect(screen.getByText('Uncertainty ON')).toBeInTheDocument();
      expect(screen.getByText('Reasoning ON')).toBeInTheDocument();
      expect(screen.getByText('Feedback ON')).toBeInTheDocument();

      // Send a message
      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'What is artificial intelligence?');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      // Verify user message appears
      expect(screen.getByText('What is artificial intelligence?')).toBeInTheDocument();

      // Wait for AI response
      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify enhanced features are present
      expect(screen.getByTestId('uncertainty-visualization')).toBeInTheDocument();
      expect(screen.getByTestId('reasoning-steps')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-collector')).toBeInTheDocument();

      // Test uncertainty visualization interaction
      const uncertaintyToggle = screen.getByTestId('uncertainty-toggle');
      await user.click(uncertaintyToggle);
      expect(screen.getByTestId('uncertainty-details')).toBeInTheDocument();

      // Test reasoning steps interaction
      const reasoningToggle = screen.getByTestId('reasoning-toggle');
      await user.click(reasoningToggle);
      expect(screen.getByTestId('reasoning-details')).toBeInTheDocument();

      // Test feedback interaction
      const thumbsUp = screen.getByTestId('thumbs-up');
      await user.click(thumbsUp);
      expect(screen.getByTestId('feedback-submitted')).toBeInTheDocument();
      expect(screen.getByText('Feedback submitted: Helpful')).toBeInTheDocument();
    });

    it('maintains memory context across multiple messages', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Send first message
      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Tell me about machine learning');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Check memory counter updated
      expect(screen.getByText(/Memory: 2\/10 short-term, 0 long-term/)).toBeInTheDocument();

      // Send second message
      await user.clear(input);
      await user.type(input, 'What about deep learning?');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      await waitFor(() => {
        expect(screen.getAllByText(/Based on our conversation history/)).toHaveLength(2);
      }, { timeout: 5000 });

      // Check memory counter updated again
      expect(screen.getByText(/Memory: 4\/10 short-term, 0 long-term/)).toBeInTheDocument();
    });

    it('handles feature toggles correctly', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Disable uncertainty visualization
      await user.click(screen.getByText('Uncertainty ON'));
      expect(screen.getByText('Uncertainty OFF')).toBeInTheDocument();

      // Disable reasoning steps
      await user.click(screen.getByText('Reasoning ON'));
      expect(screen.getByText('Reasoning OFF')).toBeInTheDocument();

      // Send a message
      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Test with features disabled');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify disabled features are not present
      expect(screen.queryByTestId('uncertainty-visualization')).not.toBeInTheDocument();
      expect(screen.queryByTestId('reasoning-steps')).not.toBeInTheDocument();
      
      // But feedback should still be present
      expect(screen.getByTestId('feedback-collector')).toBeInTheDocument();
    });
  });

  describe('Memory Panel Integration', () => {
    it('shows and updates memory panel with conversation data', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Open memory panel
      await user.click(screen.getByText('Memory Panel'));
      expect(screen.getByText('Short-term Memory')).toBeInTheDocument();
      expect(screen.getByText('User Preferences')).toBeInTheDocument();
      expect(screen.getByText('No short-term memories yet')).toBeInTheDocument();

      // Send a message to create memory
      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Create some memory');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Check memory panel shows the memory
      expect(screen.queryByText('No short-term memories yet')).not.toBeInTheDocument();
      expect(screen.getByText('Conversation Summary')).toBeInTheDocument();
    });
  });

  describe('Settings Panel Integration', () => {
    it('shows and updates settings correctly', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Open settings panel
      await user.click(screen.getByTitle('Settings'));
      expect(screen.getByText('Enhanced Chat Settings')).toBeInTheDocument();

      // Wait for settings panel to be fully rendered
      await waitFor(() => {
        expect(screen.getByText('Response Style')).toBeInTheDocument();
      });

      // Update response style - find by label text instead
      const responseStyleSelect = screen.getByLabelText(/Response Style/i) || 
                                  screen.getByRole('combobox');
      await user.selectOptions(responseStyleSelect, 'concise');
      expect(responseStyleSelect).toHaveValue('concise');

      // Update confidence threshold
      const confidenceSlider = screen.getByRole('slider');
      fireEvent.change(confidenceSlider, { target: { value: '0.9' } });
      expect(screen.getByText('90%')).toBeInTheDocument();

      // Update max memory items
      const memoryInput = screen.getByRole('spinbutton');
      await user.clear(memoryInput);
      await user.type(memoryInput, '20');
      expect(memoryInput).toHaveValue(20);

      // Check memory counter reflects the change
      expect(screen.getByText(/Memory: 0\/20 short-term, 0 long-term/)).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('handles rapid user interactions gracefully', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      const input = screen.getByPlaceholderText(/Ask me anything/);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      // Send multiple messages quickly
      await user.type(input, 'First message');
      await user.click(sendButton);

      // Input should be cleared and disabled
      expect(input).toHaveValue('');
      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();

      // Wait for response with longer timeout
      await waitFor(() => {
        expect(input).not.toBeDisabled();
        expect(sendButton).not.toBeDisabled();
      }, { timeout: 10000 });
    }, 15000);

    it('maintains UI state consistency during interactions', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Toggle multiple features
      await user.click(screen.getByText('Memory ON'));
      await user.click(screen.getByText('Uncertainty ON'));
      await user.click(screen.getByText('Reasoning ON'));

      expect(screen.getByText('Memory OFF')).toBeInTheDocument();
      expect(screen.getByText('Uncertainty OFF')).toBeInTheDocument();
      expect(screen.getByText('Reasoning OFF')).toBeInTheDocument();

      // Open and close panels
      await user.click(screen.getByText('Memory Panel'));
      expect(screen.getByText('Short-term Memory')).toBeInTheDocument();

      await user.click(screen.getByTitle('Settings'));
      expect(screen.getByText('Enhanced Chat Settings')).toBeInTheDocument();

      // Close panels
      await user.click(screen.getByText('Memory Panel'));
      await user.click(screen.getByTitle('Settings'));

      expect(screen.queryByText('Short-term Memory')).not.toBeInTheDocument();
      expect(screen.queryByText('Enhanced Chat Settings')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('handles empty input gracefully', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      const sendButton = screen.getByRole('button', { name: /send message/i });
      
      // Button should be disabled for empty input
      expect(sendButton).toBeDisabled();

      // Try clicking anyway
      await user.click(sendButton);
      
      // No messages should be created
      expect(screen.queryByText(/Based on our conversation history/)).not.toBeInTheDocument();
    });

    it('handles whitespace-only input correctly', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      const input = screen.getByPlaceholderText(/Ask me anything/);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      // Type only whitespace
      await user.type(input, '   ');
      
      // Button should still be disabled
      expect(sendButton).toBeDisabled();
    });

    it('maintains accessibility during all interactions', async () => {
      const user = userEvent.setup();
      render(<EnhancedChatInterface />);

      // Check initial accessibility
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();

      // Send message and check accessibility is maintained
      const input = screen.getByPlaceholderText(/Ask me anything/);
      await user.type(input, 'Accessibility test');
      await user.click(screen.getByRole('button', { name: /send message/i }));

      await waitFor(() => {
        expect(screen.getByText(/Based on our conversation history/)).toBeInTheDocument();
      }, { timeout: 5000 });

      // All interactive elements should still be accessible
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
      expect(screen.getByTestId('thumbs-up')).toBeInTheDocument();
      expect(screen.getByTestId('thumbs-down')).toBeInTheDocument();
    });
  });
});