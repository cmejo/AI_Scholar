import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MobileCard } from '../MobileCard';
import { MobileButton } from '../MobileButton';
import { MobileInput } from '../MobileInput';
import { MobileGrid, MobileGridItem } from '../MobileGrid';
import { Search } from 'lucide-react';

describe('Mobile Components', () => {
  describe('MobileCard', () => {
    it('renders children correctly', () => {
      render(
        <MobileCard>
          <div>Test Content</div>
        </MobileCard>
      );
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('handles click events when interactive', () => {
      const handleClick = vi.fn();
      render(
        <MobileCard onClick={handleClick} interactive>
          <div>Clickable Card</div>
        </MobileCard>
      );
      
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies correct variant classes', () => {
      const { container } = render(
        <MobileCard variant="elevated">
          <div>Elevated Card</div>
        </MobileCard>
      );
      
      expect(container.firstChild).toHaveClass('shadow-lg');
    });
  });

  describe('MobileButton', () => {
    it('renders with correct text', () => {
      render(<MobileButton>Click Me</MobileButton>);
      expect(screen.getByRole('button')).toHaveTextContent('Click Me');
    });

    it('handles click events', () => {
      const handleClick = vi.fn();
      render(<MobileButton onClick={handleClick}>Click Me</MobileButton>);
      
      fireEvent.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('shows loading state', () => {
      render(<MobileButton loading>Loading Button</MobileButton>);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('renders with icon', () => {
      render(
        <MobileButton icon={Search}>
          Search
        </MobileButton>
      );
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Search');
    });
  });

  describe('MobileInput', () => {
    it('renders with placeholder', () => {
      render(<MobileInput placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('handles value changes', () => {
      const handleChange = vi.fn();
      render(<MobileInput value="" onChange={handleChange} />);
      
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'test' } });
      expect(handleChange).toHaveBeenCalledWith('test');
    });

    it('shows error state', () => {
      render(<MobileInput error="This field is required" />);
      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });

    it('renders as textarea when multiline', () => {
      render(<MobileInput multiline placeholder="Enter text" />);
      expect(screen.getByRole('textbox')).toBeInstanceOf(HTMLTextAreaElement);
    });
  });

  describe('MobileGrid', () => {
    it('renders grid with items', () => {
      render(
        <MobileGrid columns={2}>
          <MobileGridItem>Item 1</MobileGridItem>
          <MobileGridItem>Item 2</MobileGridItem>
        </MobileGrid>
      );
      
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });

    it('applies correct column classes', () => {
      const { container } = render(
        <MobileGrid columns={3}>
          <MobileGridItem>Item</MobileGridItem>
        </MobileGrid>
      );
      
      expect(container.firstChild).toHaveClass('grid-cols-1');
    });
  });
});