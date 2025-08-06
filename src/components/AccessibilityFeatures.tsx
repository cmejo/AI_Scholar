import React, { useEffect, useState } from 'react';
import { 
  Eye, 
  Keyboard, 
  Volume2, 
  Navigation, 
  Monitor,
  Smartphone,
  MousePointer,
  HelpCircle,
  AlertTriangle,
  CheckCircle,
  Info,
  X
} from 'lucide-react';
import { accessibilityService } from '../services/accessibilityService';
import ColorBlindnessFilters from './ColorBlindnessFilters';
import AccessibilityValidator from './AccessibilityValidator';

interface AccessibilityFeaturesProps {
  children: React.ReactNode;
}

export const AccessibilityFeatures: React.FC<AccessibilityFeaturesProps> = ({ children }) => {
  const [isKeyboardUser, setIsKeyboardUser] = useState(false);
  const [announcements, setAnnouncements] = useState<string[]>([]);

  useEffect(() => {
    // Initialize accessibility features
    accessibilityService.announce('Accessibility features initialized', 'polite');

    // Track keyboard usage
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        setIsKeyboardUser(true);
        document.body.classList.add('keyboard-navigation');
      }
    };

    const handleMouseDown = () => {
      setIsKeyboardUser(false);
      document.body.classList.remove('keyboard-navigation');
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  return (
    <div className="accessibility-wrapper">
      {/* Color Blindness Filters */}
      <ColorBlindnessFilters />
      
      {/* Skip Links */}
      <div className="skip-links" role="navigation" aria-label="Skip navigation">
        <a 
          href="#main-content" 
          className="skip-link"
          onClick={(e) => {
            e.preventDefault();
            const target = document.getElementById('main-content');
            if (target) {
              target.focus();
              target.scrollIntoView({ behavior: 'smooth' });
              accessibilityService.announce('Skipped to main content');
            }
          }}
        >
          Skip to main content
        </a>
        <a 
          href="#main-sidebar" 
          className="skip-link"
          onClick={(e) => {
            e.preventDefault();
            const target = document.getElementById('main-sidebar');
            if (target) {
              target.focus();
              target.scrollIntoView({ behavior: 'smooth' });
              accessibilityService.announce('Skipped to navigation');
            }
          }}
        >
          Skip to navigation
        </a>
        <a 
          href="#chat-input" 
          className="skip-link"
          onClick={(e) => {
            e.preventDefault();
            const target = document.getElementById('chat-input');
            if (target) {
              target.focus();
              accessibilityService.announce('Skipped to search input');
            }
          }}
        >
          Skip to search
        </a>
        <button 
          className="skip-link"
          onClick={() => {
            const settingsButton = document.querySelector('[aria-label*="accessibility"]') as HTMLElement;
            if (settingsButton) {
              settingsButton.click();
              accessibilityService.announce('Opened accessibility settings');
            }
          }}
        >
          Skip to accessibility settings
        </button>
      </div>

      {/* Keyboard Navigation Indicator */}
      {isKeyboardUser && (
        <div 
          className="keyboard-navigation-indicator"
          role="status"
          aria-live="polite"
          aria-label="Keyboard navigation active"
        >
          <div className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <Keyboard size={16} />
            <span className="text-sm font-medium">
              Keyboard navigation active - Use Tab to navigate, Enter to select, Escape to close
            </span>
          </div>
        </div>
      )}

      {/* Live Region for Announcements */}
      <div
        id="accessibility-announcements"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        role="status"
      >
        {announcements.map((announcement, index) => (
          <div key={index}>{announcement}</div>
        ))}
      </div>

      {/* Assertive Live Region for Important Announcements */}
      <div
        id="accessibility-alerts"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        role="alert"
      />

      {/* Main Content */}
      {children}

      {/* Accessibility Status Panel */}
      <AccessibilityStatusPanel />
    </div>
  );
};

const AccessibilityStatusPanel: React.FC = () => {
  const [preferences, setPreferences] = useState(accessibilityService.getPreferences());
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updatePreferences = () => {
      setPreferences(accessibilityService.getPreferences());
    };

    // Listen for preference changes
    const interval = setInterval(updatePreferences, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
    accessibilityService.announce(
      `Accessibility status panel ${!isVisible ? 'opened' : 'closed'}`,
      'polite'
    );
  };

  return (
    <div className="accessibility-status-panel">
      <button
        onClick={toggleVisibility}
        className="accessibility-status-toggle"
        aria-label={`${isVisible ? 'Hide' : 'Show'} accessibility status panel`}
        aria-expanded={isVisible}
        aria-controls="accessibility-status-content"
      >
        <Eye size={16} />
        <span className="sr-only">Accessibility Status</span>
      </button>

      {isVisible && (
        <div
          id="accessibility-status-content"
          className="accessibility-status-content"
          role="region"
          aria-labelledby="accessibility-status-heading"
        >
          <h3 id="accessibility-status-heading" className="text-sm font-medium mb-2">
            Accessibility Status
          </h3>
          
          <div className="space-y-2 text-xs">
            <div className="flex items-center space-x-2">
              {preferences.screenReaderEnabled ? (
                <CheckCircle className="text-green-400" size={12} />
              ) : (
                <AlertTriangle className="text-yellow-400" size={12} />
              )}
              <span>Screen Reader: {preferences.screenReaderEnabled ? 'Enabled' : 'Disabled'}</span>
            </div>
            
            <div className="flex items-center space-x-2">
              {preferences.highContrastMode ? (
                <CheckCircle className="text-green-400" size={12} />
              ) : (
                <Info className="text-blue-400" size={12} />
              )}
              <span>High Contrast: {preferences.highContrastMode ? 'Enabled' : 'Disabled'}</span>
            </div>
            
            <div className="flex items-center space-x-2">
              {preferences.keyboardNavigationOnly ? (
                <CheckCircle className="text-green-400" size={12} />
              ) : (
                <Info className="text-blue-400" size={12} />
              )}
              <span>Keyboard Only: {preferences.keyboardNavigationOnly ? 'Enabled' : 'Disabled'}</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <Info className="text-blue-400" size={12} />
              <span>Font Size: {preferences.fontSize}</span>
            </div>
            
            <div className="flex items-center space-x-2">
              {preferences.reducedMotion ? (
                <CheckCircle className="text-green-400" size={12} />
              ) : (
                <Info className="text-blue-400" size={12} />
              )}
              <span>Reduced Motion: {preferences.reducedMotion ? 'Enabled' : 'Disabled'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Accessibility Helper Components
export const AccessibleButton: React.FC<{
  children: React.ReactNode;
  onClick: () => void;
  ariaLabel: string;
  ariaDescribedBy?: string;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
}> = ({ 
  children, 
  onClick, 
  ariaLabel, 
  ariaDescribedBy, 
  disabled = false, 
  variant = 'primary',
  size = 'medium'
}) => {
  const baseClasses = 'focus-ring transition-colors font-medium rounded-lg';
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-600',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white disabled:bg-gray-800',
    danger: 'bg-red-600 hover:bg-red-700 text-white disabled:bg-gray-600'
  };
  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm min-h-[32px]',
    medium: 'px-4 py-2 text-base min-h-[40px]',
    large: 'px-6 py-3 text-lg min-h-[48px]'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
    >
      {children}
    </button>
  );
};

export const AccessibleInput: React.FC<{
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  helpText?: string;
}> = ({
  id,
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  required = false,
  disabled = false,
  error,
  helpText
}) => {
  const helpId = helpText ? `${id}-help` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(' ') || undefined;

  return (
    <div className="space-y-1">
      <label 
        htmlFor={id}
        className="block text-sm font-medium text-gray-300"
      >
        {label}
        {required && <span className="text-red-400 ml-1" aria-label="required">*</span>}
      </label>
      
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        aria-describedby={describedBy}
        aria-invalid={error ? 'true' : 'false'}
        className={`
          w-full px-3 py-2 bg-gray-700 border rounded-lg text-white placeholder-gray-400
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
          ${error ? 'border-red-500' : 'border-gray-600'}
        `}
      />
      
      {helpText && (
        <p id={helpId} className="text-xs text-gray-400">
          {helpText}
        </p>
      )}
      
      {error && (
        <p id={errorId} className="text-xs text-red-400" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

export const AccessibleHeading: React.FC<{
  level: 1 | 2 | 3 | 4 | 5 | 6;
  children: React.ReactNode;
  id?: string;
  className?: string;
}> = ({ level, children, id, className = '' }) => {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
  const defaultClasses = {
    1: 'text-3xl font-bold',
    2: 'text-2xl font-semibold',
    3: 'text-xl font-semibold',
    4: 'text-lg font-medium',
    5: 'text-base font-medium',
    6: 'text-sm font-medium'
  };

  return (
    <Tag 
      id={id}
      className={`${defaultClasses[level]} ${className}`}
      role="heading"
      aria-level={level}
    >
      {children}
    </Tag>
  );
};

export const AccessibleList: React.FC<{
  items: Array<{
    id: string;
    content: React.ReactNode;
    onClick?: () => void;
    ariaLabel?: string;
  }>;
  ordered?: boolean;
  ariaLabel?: string;
}> = ({ items, ordered = false, ariaLabel }) => {
  const ListTag = ordered ? 'ol' : 'ul';

  return (
    <ListTag 
      role="list"
      aria-label={ariaLabel}
      className="space-y-1"
    >
      {items.map((item) => (
        <li 
          key={item.id}
          role="listitem"
          className={item.onClick ? 'cursor-pointer hover:bg-gray-700 rounded p-2 transition-colors' : ''}
          onClick={item.onClick}
          aria-label={item.ariaLabel}
          tabIndex={item.onClick ? 0 : undefined}
          onKeyDown={item.onClick ? (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              item.onClick!();
            }
          } : undefined}
        >
          {item.content}
        </li>
      ))}
    </ListTag>
  );
};

export const AccessibleModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'small' | 'medium' | 'large';
}> = ({ isOpen, onClose, title, children, size = 'medium' }) => {
  const [trapCleanup, setTrapCleanup] = useState<(() => void) | null>(null);

  useEffect(() => {
    if (isOpen) {
      accessibilityService.saveFocus();
      accessibilityService.announce(`Modal opened: ${title}`, 'assertive');
      
      // Set up focus trap
      const modalElement = document.querySelector('[role="dialog"]') as HTMLElement;
      if (modalElement) {
        const cleanup = accessibilityService.trapFocus(modalElement);
        setTrapCleanup(() => cleanup);
      }
    } else {
      accessibilityService.restoreFocus();
      if (trapCleanup) {
        trapCleanup();
        setTrapCleanup(null);
      }
    }

    return () => {
      if (trapCleanup) {
        trapCleanup();
      }
    };
  }, [isOpen, title, trapCleanup]);

  if (!isOpen) return null;

  const sizeClasses = {
    small: 'max-w-md',
    medium: 'max-w-2xl',
    large: 'max-w-4xl'
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className={`bg-gray-800 rounded-lg ${sizeClasses[size]} w-full max-h-[90vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-700 flex items-center justify-between">
          <AccessibleHeading level={2} id="modal-title" className="text-white">
            {title}
          </AccessibleHeading>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors focus-ring"
            aria-label={`Close ${title} modal`}
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default AccessibilityFeatures;