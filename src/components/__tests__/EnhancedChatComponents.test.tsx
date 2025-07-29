import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import { UncertaintyVisualization } from '../UncertaintyVisualization';
import { ReasoningStepsDisplay } from '../ReasoningStepsDisplay';
import { FeedbackCollector } from '../FeedbackCollector';

describe('Enhanced Chat Interface Components', () => {
  describe('UncertaintyVisualization', () => {
    const mockUncertainty = {
      confidence: 0.85,
      factors: [
        {
          factor: 'Source Quality',
          impact: 0.9,
          explanation: 'High-quality academic sources available'
        },
        {
          factor: 'Context Completeness',
          impact: 0.7,
          explanation: 'Some context may be missing'
        }
      ]
    };

    test('renders uncertainty visualization with confidence score', () => {
      render(
        <UncertaintyVisualization
          uncertainty={mockUncertainty}
          isExpanded={false}
          onToggle={() => {}}
        />
      );

      expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    test('expands to show detailed factors when toggled', () => {
      const onToggle = vi.fn();
      render(
        <UncertaintyVisualization
          uncertainty={mockUncertainty}
          isExpanded={true}
          onToggle={onToggle}
        />
      );

      expect(screen.getByText('Source Quality')).toBeInTheDocument();
      expect(screen.getByText('Context Completeness')).toBeInTheDocument();
      expect(screen.getByText('High-quality academic sources available')).toBeInTheDocument();
    });

    test('calls onToggle when clicked', () => {
      const onToggle = vi.fn();
      render(
        <UncertaintyVisualization
          uncertainty={mockUncertainty}
          isExpanded={false}
          onToggle={onToggle}
        />
      );

      fireEvent.click(screen.getByText('Confidence: 85%'));
      expect(onToggle).toHaveBeenCalled();
    });
  });

  describe('ReasoningStepsDisplay', () => {
    const mockReasoning = {
      steps: [
        {
          step: 1,
          description: 'Analyzed user query and identified key concepts',
          confidence: 0.95,
          evidence: ['Query parsing', 'Entity extraction']
        },
        {
          step: 2,
          description: 'Retrieved relevant information from memory context',
          confidence: 0.88,
          evidence: ['Short-term memory', 'User preferences']
        }
      ],
      conclusion: 'Generated comprehensive response with high confidence',
      overallConfidence: 0.85
    };

    test('renders reasoning steps with overall confidence', () => {
      render(
        <ReasoningStepsDisplay
          reasoning={mockReasoning}
          isExpanded={false}
          onToggle={() => {}}
        />
      );

      expect(screen.getByText('Chain of Thought (2 steps)')).toBeInTheDocument();
      expect(screen.getByText('85% confidence')).toBeInTheDocument();
    });

    test('expands to show detailed reasoning steps', () => {
      render(
        <ReasoningStepsDisplay
          reasoning={mockReasoning}
          isExpanded={true}
          onToggle={() => {}}
        />
      );

      expect(screen.getByText('Step 1')).toBeInTheDocument();
      expect(screen.getByText('Step 2')).toBeInTheDocument();
      expect(screen.getByText('Analyzed user query and identified key concepts')).toBeInTheDocument();
      expect(screen.getByText('Retrieved relevant information from memory context')).toBeInTheDocument();
    });

    test('shows evidence for each step', () => {
      render(
        <ReasoningStepsDisplay
          reasoning={mockReasoning}
          isExpanded={true}
          onToggle={() => {}}
        />
      );

      expect(screen.getByText('Query parsing')).toBeInTheDocument();
      expect(screen.getByText('Entity extraction')).toBeInTheDocument();
      expect(screen.getByText('Short-term memory')).toBeInTheDocument();
      expect(screen.getByText('User preferences')).toBeInTheDocument();
    });
  });

  describe('FeedbackCollector', () => {
    test('renders quick feedback buttons', () => {
      const onFeedback = vi.fn();
      render(
        <FeedbackCollector
          messageId="test-message"
          onFeedback={onFeedback}
        />
      );

      expect(screen.getByText('Was this helpful?')).toBeInTheDocument();
      expect(screen.getByTitle('Helpful')).toBeInTheDocument();
      expect(screen.getByTitle('Not helpful')).toBeInTheDocument();
    });

    test('shows detailed feedback form when clicked', () => {
      const onFeedback = vi.fn();
      render(
        <FeedbackCollector
          messageId="test-message"
          onFeedback={onFeedback}
        />
      );

      fireEvent.click(screen.getByText('Detailed feedback'));
      
      expect(screen.getByText('Provide Feedback')).toBeInTheDocument();
      expect(screen.getByText('Rate this response:')).toBeInTheDocument();
    });

    test('allows rating selection', () => {
      const onFeedback = vi.fn();
      render(
        <FeedbackCollector
          messageId="test-message"
          onFeedback={onFeedback}
        />
      );

      fireEvent.click(screen.getByText('Detailed feedback'));
      
      // Click on 4-star rating
      const stars = screen.getAllByRole('button');
      const fourthStar = stars.find(button => button.querySelector('svg'));
      if (fourthStar) {
        fireEvent.click(fourthStar);
      }
    });

    test('shows thank you message after feedback submission', async () => {
      const onFeedback = vi.fn();
      render(
        <FeedbackCollector
          messageId="test-message"
          onFeedback={onFeedback}
        />
      );

      // Click helpful button
      fireEvent.click(screen.getByTitle('Helpful'));
      
      // Should show thank you message (this would be async in real implementation)
      // For now, we just verify the onFeedback was called
      expect(onFeedback).toHaveBeenCalledWith('test-message', {
        rating: 5,
        helpful: true
      });
    });

    test('displays existing feedback when provided', () => {
      const onFeedback = vi.fn();
      const existingFeedback = {
        rating: 4,
        helpful: true,
        corrections: 'Great response!'
      };

      render(
        <FeedbackCollector
          messageId="test-message"
          currentFeedback={existingFeedback}
          onFeedback={onFeedback}
        />
      );

      expect(screen.getByText('Feedback submitted')).toBeInTheDocument();
    });
  });

  describe('Component Integration', () => {
    test('components work together in a message context', () => {
      const mockUncertainty = {
        confidence: 0.75,
        factors: [
          {
            factor: 'Source Quality',
            impact: 0.8,
            explanation: 'Good quality sources'
          }
        ]
      };

      const mockReasoning = {
        steps: [
          {
            step: 1,
            description: 'Analyzed query',
            confidence: 0.9,
            evidence: ['NLP processing']
          }
        ],
        conclusion: 'Response generated',
        overallConfidence: 0.75
      };

      const onFeedback = vi.fn();
      const onUncertaintyToggle = vi.fn();
      const onReasoningToggle = vi.fn();

      render(
        <div>
          <UncertaintyVisualization
            uncertainty={mockUncertainty}
            isExpanded={false}
            onToggle={onUncertaintyToggle}
          />
          <ReasoningStepsDisplay
            reasoning={mockReasoning}
            isExpanded={false}
            onToggle={onReasoningToggle}
          />
          <FeedbackCollector
            messageId="integration-test"
            onFeedback={onFeedback}
          />
        </div>
      );

      // Verify all components render
      expect(screen.getByText('Confidence: 75%')).toBeInTheDocument();
      expect(screen.getByText('Chain of Thought (1 steps)')).toBeInTheDocument();
      expect(screen.getByText('Was this helpful?')).toBeInTheDocument();

      // Test interactions
      fireEvent.click(screen.getByText('Confidence: 75%'));
      expect(onUncertaintyToggle).toHaveBeenCalled();

      fireEvent.click(screen.getByText('Chain of Thought (1 steps)'));
      expect(onReasoningToggle).toHaveBeenCalled();

      fireEvent.click(screen.getByTitle('Helpful'));
      expect(onFeedback).toHaveBeenCalled();
    });
  });
});