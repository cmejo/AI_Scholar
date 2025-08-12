import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { accessibilityService } from '../../services/accessibilityService';
import type { HeaderProps } from '../../types/ui';
import { Header } from '../Header';

// Mock the accessibility service
vi.mock('../../services/accessibilityService', () => ({
  accessibilityService: {
    announce: vi.fn(),
  },
}));

// Mock the AccessibilitySettings component
vi.mock('../AccessibilitySettings', () => ({
  AccessibilitySettings: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
    isOpen ? (
      <div data-testid="accessibility-settings-modal">
        <button onClick={onClose}>Close Settings</button>
      </div>
    ) : null
  ),
}));

const defaultProps: HeaderProps = {
  onToggleSidebar: vi.fn(),
  currentView: 'chat',
  user: {
    id: 'user-1',
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'researcher',
  },
};

describe('Header', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render header with correct structure', () => {
      render(<Header {...defaultProps} />);

      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();
      expect(header).toHaveAttribute('aria-label', 'Main navigation header');
    });

    it('should render sidebar toggle button', () => {
      render(<Header {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: /toggle sidebar/i });
      expect(toggleButton).toBeInTheDocument();
      expect(toggleButton).toHaveAttribute('aria-label', 'Toggle sidebar navigation');
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
      expect(toggleButton).toHaveAttribute('aria-controls', 'main-sidebar');
    });

    it('should render main heading with correct title', () => {
      render(<Header {...defaultProps} />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveTextContent('Enhanced RAG Chat');
      expect(heading).toHaveAttribute('id', 'main-heading');
    });

    it('should render user navigation', () => {
      render(<Header {...defaultProps} />);

      const userNav = screen.getByRole('navigation', { name: /user actions/i });
      expect(userNav).toBeInTheDocument();
    });
  });

  describe('View-specific Content', () => {
    const viewTestCases = [
      { view: 'chat' as const, title: 'Enhanced RAG Chat', iconClass: 'text-purple-400' },
      { view: 'documents' as const, title: 'Smart Document Manager', iconClass: 'text-emerald-400' },
      { view: 'analytics' as const, title: 'Enterprise Analytics', iconClass: 'text-blue-400' },
      { view: 'security' as const, title: 'Security Dashboard', iconClass: 'text-red-400' },
      { view: 'workflows' as const, title: 'Workflow Manager', iconClass: 'text-yellow-400' },
      { view: 'integrations' as const, title: 'Integration Hub', iconClass: 'text-indigo-400' },
    ];

    viewTestCases.forEach(({ view, title }) => {
      it(`should display correct title for ${view} view`, () => {
        render(<Header {...defaultProps} currentView={view} />);

        expect(screen.getByText(title)).toBeInTheDocument();
      });
    });

    it('should default to chat view for unknown view', () => {
      render(<Header {...defaultProps} currentView={'unknown' as any} />);

      expect(screen.getByText('AI Scholar Enterprise')).toBeInTheDocument();
    });
  });

  describe('User Information', () => {
    it('should display user information when user is provided', () => {
      render(<Header {...defaultProps} />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('researcher')).toBeInTheDocument();
    });

    it('should have proper ARIA labels for user information', () => {
      render(<Header {...defaultProps} />);

      const userGroup = screen.getByRole('group', { name: /user information/i });
      expect(userGroup).toBeInTheDocument();

      const userName = screen.getByLabelText(/user: john doe/i);
      expect(userName).toBeInTheDocument();

      const userRole = screen.getByLabelText(/role: researcher/i);
      expect(userRole).toBeInTheDocument();
    });

    it('should not display user information when user is not provided', () => {
      render(<Header {...defaultProps} user={undefined} />);

      expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
      expect(screen.queryByRole('group', { name: /user information/i })).not.toBeInTheDocument();
    });

    it('should display user avatar with proper styling', () => {
      render(<Header {...defaultProps} />);

      const avatar = screen.getByRole('group', { name: /user information/i }).querySelector('div');
      expect(avatar).toHaveClass('w-8', 'h-8', 'bg-gradient-to-br', 'from-purple-600', 'to-emerald-600');
    });
  });

  describe('System Status', () => {
    it('should display system status indicator', () => {
      render(<Header {...defaultProps} />);

      const statusIndicator = screen.getByRole('status', { name: /system status/i });
      expect(statusIndicator).toBeInTheDocument();
      expect(statusIndicator).toHaveAttribute('aria-live', 'polite');
    });

    it('should show operational status message', () => {
      render(<Header {...defaultProps} />);

      expect(screen.getByText('All Systems Operational')).toBeInTheDocument();
    });

    it('should have animated status dot', () => {
      render(<Header {...defaultProps} />);

      const statusDot = screen.getByRole('status').querySelector('.animate-pulse');
      expect(statusDot).toBeInTheDocument();
      expect(statusDot).toHaveClass('w-2', 'h-2', 'bg-emerald-400', 'rounded-full');
    });
  });

  describe('Notifications', () => {
    it('should render notifications button with badge', () => {
      render(<Header {...defaultProps} />);

      const notificationButton = screen.getByRole('button', { name: /notifications \(3 unread\)/i });
      expect(notificationButton).toBeInTheDocument();
    });

    it('should display notification count badge', () => {
      render(<Header {...defaultProps} />);

      const badge = screen.getByLabelText(/3 unread notifications/i);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('3');
    });

    it('should announce when notifications are opened', async () => {
      render(<Header {...defaultProps} />);

      const notificationButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(notificationButton);

      expect(accessibilityService.announce).toHaveBeenCalledWith(
        'Notifications panel opened',
        'polite'
      );
    });
  });

  describe('Accessibility Settings', () => {
    it('should render accessibility settings button', () => {
      render(<Header {...defaultProps} />);

      const accessibilityButton = screen.getByRole('button', { name: /open accessibility settings/i });
      expect(accessibilityButton).toBeInTheDocument();
      expect(accessibilityButton).toHaveAttribute('title', 'Accessibility settings and options');
    });

    it('should open accessibility settings modal when button is clicked', async () => {
      render(<Header {...defaultProps} />);

      const accessibilityButton = screen.getByRole('button', { name: /open accessibility settings/i });
      await user.click(accessibilityButton);

      expect(screen.getByTestId('accessibility-settings-modal')).toBeInTheDocument();
    });

    it('should announce when accessibility settings are opened', async () => {
      render(<Header {...defaultProps} />);

      const accessibilityButton = screen.getByRole('button', { name: /open accessibility settings/i });
      await user.click(accessibilityButton);

      expect(accessibilityService.announce).toHaveBeenCalledWith(
        'Accessibility settings opened',
        'polite'
      );
    });

    it('should close accessibility settings modal', async () => {
      render(<Header {...defaultProps} />);

      // Open modal
      const accessibilityButton = screen.getByRole('button', { name: /open accessibility settings/i });
      await user.click(accessibilityButton);

      expect(screen.getByTestId('accessibility-settings-modal')).toBeInTheDocument();

      // Close modal
      const closeButton = screen.getByText('Close Settings');
      await user.click(closeButton);

      expect(screen.queryByTestId('accessibility-settings-modal')).not.toBeInTheDocument();
    });

    it('should announce when accessibility settings are closed', async () => {
      render(<Header {...defaultProps} />);

      // Open modal
      const accessibilityButton = screen.getByRole('button', { name: /open accessibility settings/i });
      await user.click(accessibilityButton);

      // Close modal
      const closeButton = screen.getByText('Close Settings');
      await user.click(closeButton);

      expect(accessibilityService.announce).toHaveBeenCalledWith(
        'Accessibility settings closed',
        'polite'
      );
    });
  });

  describe('General Settings', () => {
    it('should render general settings button', () => {
      render(<Header {...defaultProps} />);

      const settingsButton = screen.getByRole('button', { name: /open general settings/i });
      expect(settingsButton).toBeInTheDocument();
      expect(settingsButton).toHaveAttribute('title', 'Application settings');
    });

    it('should announce when general settings are opened', async () => {
      render(<Header {...defaultProps} />);

      const settingsButton = screen.getByRole('button', { name: /open general settings/i });
      await user.click(settingsButton);

      expect(accessibilityService.announce).toHaveBeenCalledWith(
        'Settings panel opened',
        'polite'
      );
    });
  });

  describe('Sidebar Toggle', () => {
    it('should call onToggleSidebar when toggle button is clicked', async () => {
      const onToggleSidebar = vi.fn();
      render(<Header {...defaultProps} onToggleSidebar={onToggleSidebar} />);

      const toggleButton = screen.getByRole('button', { name: /toggle sidebar/i });
      await user.click(toggleButton);

      expect(onToggleSidebar).toHaveBeenCalledTimes(1);
    });

    it('should have proper keyboard navigation for toggle button', async () => {
      const onToggleSidebar = vi.fn();
      render(<Header {...defaultProps} onToggleSidebar={onToggleSidebar} />);

      const toggleButton = screen.getByRole('button', { name: /toggle sidebar/i });
      
      // Focus the button
      toggleButton.focus();
      expect(document.activeElement).toBe(toggleButton);

      // Press Enter
      await user.keyboard('{Enter}');
      expect(onToggleSidebar).toHaveBeenCalledTimes(1);

      // Press Space
      await user.keyboard(' ');
      expect(onToggleSidebar).toHaveBeenCalledTimes(2);
    });
  });

  describe('Accessibility Compliance', () => {
    it('should have proper ARIA landmarks', () => {
      render(<Header {...defaultProps} />);

      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation', { name: /user actions/i })).toBeInTheDocument();
    });

    it('should have proper heading hierarchy', () => {
      render(<Header {...defaultProps} />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
    });

    it('should have focus management for interactive elements', () => {
      render(<Header {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeFocusable();
        expect(button).toHaveClass('focus-ring');
      });
    });

    it('should have proper ARIA labels for all interactive elements', () => {
      render(<Header {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName();
      });
    });

    it('should use aria-hidden appropriately for decorative elements', () => {
      render(<Header {...defaultProps} />);

      // Icons should be hidden from screen readers
      const header = screen.getByRole('banner');
      const hiddenElements = header.querySelectorAll('[aria-hidden="true"]');
      expect(hiddenElements.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Behavior', () => {
    it('should hide user details on small screens', () => {
      render(<Header {...defaultProps} />);

      const userDetails = screen.getByText('John Doe').parentElement;
      expect(userDetails).toHaveClass('hidden', 'md:block');
    });

    it('should hide system status on small screens', () => {
      render(<Header {...defaultProps} />);

      const systemStatus = screen.getByRole('status');
      expect(systemStatus).toHaveClass('hidden', 'sm:flex');
    });
  });

  describe('Theme and Styling', () => {
    it('should have proper dark theme styling', () => {
      render(<Header {...defaultProps} />);

      const header = screen.getByRole('banner');
      expect(header).toHaveClass('bg-gray-800', 'border-b', 'border-gray-700');
    });

    it('should have hover effects on interactive elements', () => {
      render(<Header {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('hover:bg-gray-700');
      });
    });

    it('should have proper transition effects', () => {
      render(<Header {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('transition-colors');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle missing user gracefully', () => {
      expect(() => {
        render(<Header {...defaultProps} user={undefined} />);
      }).not.toThrow();
    });

    it('should handle invalid currentView gracefully', () => {
      expect(() => {
        render(<Header {...defaultProps} currentView={'invalid' as any} />);
      }).not.toThrow();
    });

    it('should handle missing onToggleSidebar gracefully', () => {
      expect(() => {
        render(<Header {...defaultProps} onToggleSidebar={undefined as any} />);
      }).not.toThrow();
    });
  });

  describe('Performance', () => {
    it('should not cause unnecessary re-renders', () => {
      const { rerender } = render(<Header {...defaultProps} />);

      // Re-render with same props
      rerender(<Header {...defaultProps} />);

      // Component should render without issues
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should handle rapid state changes', async () => {
      render(<Header {...defaultProps} />);

      const accessibilityButton = screen.getByRole('button', { name: /open accessibility settings/i });

      // Rapidly open and close settings
      await user.click(accessibilityButton);
      const closeButton = screen.getByText('Close Settings');
      await user.click(closeButton);
      await user.click(accessibilityButton);

      expect(screen.getByTestId('accessibility-settings-modal')).toBeInTheDocument();
    });
  });
});