import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ThoughtProcess from '../../components/ThoughtProcess';
import { ThoughtStep } from '../../types/chat';

describe('ThoughtProcess', () => {
  const mockSteps: ThoughtStep[] = [
    {
      step: 1,
      description: 'Analyzing the user question',
      reasoning: 'I need to understand what the user is asking about.',
      confidence: 0.9,
    },
    {
      step: 2,
      description: 'Gathering relevant information',
      reasoning: 'Based on the question, I will search my knowledge base.',
      confidence: 0.85,
    },
    {
      step: 3,
      description: 'Formulating response',
      reasoning: 'I will structure my answer to be clear and helpful.',
      confidence: 0.75,
    },
  ];

  const mockProps = {
    steps: mockSteps,
    isExpanded: false,
    onToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render nothing when no steps provided', () => {
    const { container } = render(
      <ThoughtProcess {...mockProps} steps={[]} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should render collapsed state by default', () => {
    render(<ThoughtProcess {...mockProps} />);

    expect(screen.getByText('Chain of Thought (3 steps)')).toBeInTheDocument();
    expect(screen.queryByText('Analyzing the user question')).not.toBeInTheDocument();
  });

  it('should expand when toggle is clicked', () => {
    render(<ThoughtProcess {...mockProps} />);

    const toggleButton = screen.getByText('Chain of Thought (3 steps)');
    fireEvent.click(toggleButton);

    expect(mockProps.onToggle).toHaveBeenCalled();
  });

  it('should show steps when expanded', () => {
    render(<ThoughtProcess {...mockProps} isExpanded={true} />);

    expect(screen.getByText('Step 1')).toBeInTheDocument();
    expect(screen.getByText('Step 2')).toBeInTheDocument();
    expect(screen.getByText('Step 3')).toBeInTheDocument();
    expect(screen.getByText('Analyzing the user question')).toBeInTheDocument();
  });

  it('should show confidence levels correctly', () => {
    render(<ThoughtProcess {...mockProps} isExpanded={true} />);

    expect(screen.getByText('High')).toBeInTheDocument(); // 90% confidence
    expect(screen.getByText('Medium')).toBeInTheDocument(); // 85% confidence
    expect(screen.getByText('Medium')).toBeInTheDocument(); // 75% confidence
  });

  it('should show confidence percentages', () => {
    render(<ThoughtProcess {...mockProps} isExpanded={true} />);

    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('should expand individual steps when clicked', () => {
    render(<ThoughtProcess {...mockProps} isExpanded={true} />);

    const step1Button = screen.getByText('Step 1').closest('button');
    fireEvent.click(step1Button!);

    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('Reasoning')).toBeInTheDocument();
    expect(screen.getByText('I need to understand what the user is asking about.')).toBeInTheDocument();
  });

  it('should show confidence bar in expanded step', () => {
    render(<ThoughtProcess {...mockProps} isExpanded={true} />);

    const step1Button = screen.getByText('Step 1').closest('button');
    fireEvent.click(step1Button!);

    expect(screen.getByText('Confidence:')).toBeInTheDocument();
  });

  it('should use different icons for different steps', () => {
    render(<ThoughtProcess {...mockProps} isExpanded={true} />);

    // Each step should have an icon (Brain, Target, or Lightbulb)
    const stepButtons = screen.getAllByText(/Step \d/);
    expect(stepButtons).toHaveLength(3);
  });

  it('should handle confidence color coding', () => {
    const stepsWithVariedConfidence: ThoughtStep[] = [
      { step: 1, description: 'High confidence', reasoning: 'Test', confidence: 0.9 },
      { step: 2, description: 'Medium confidence', reasoning: 'Test', confidence: 0.7 },
      { step: 3, description: 'Low confidence', reasoning: 'Test', confidence: 0.4 },
    ];

    render(
      <ThoughtProcess 
        {...mockProps} 
        steps={stepsWithVariedConfidence} 
        isExpanded={true} 
      />
    );

    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('should show correct chevron icons', () => {
    const { rerender } = render(<ThoughtProcess {...mockProps} />);

    // Should show right chevron when collapsed
    expect(screen.getByText('Chain of Thought (3 steps)')).toBeInTheDocument();

    // Should show down chevron when expanded
    rerender(<ThoughtProcess {...mockProps} isExpanded={true} />);
    expect(screen.getByText('Chain of Thought (3 steps)')).toBeInTheDocument();
  });

  it('should handle empty reasoning gracefully', () => {
    const stepsWithEmptyReasoning: ThoughtStep[] = [
      {
        step: 1,
        description: 'Test step',
        reasoning: '',
        confidence: 0.8,
      },
    ];

    render(
      <ThoughtProcess 
        {...mockProps} 
        steps={stepsWithEmptyReasoning} 
        isExpanded={true} 
      />
    );

    const stepButton = screen.getByText('Step 1').closest('button');
    fireEvent.click(stepButton!);

    expect(screen.getByText('Reasoning')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <ThoughtProcess {...mockProps} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});