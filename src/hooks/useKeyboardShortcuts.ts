import { useEffect, useCallback } from 'react';

interface KeyboardShortcuts {
  onVoiceToggle?: () => void;
  onVoiceStart?: () => void;
  onVoiceStop?: () => void;
  onModeSwitch?: (mode: string) => void;
  onSettingsOpen?: () => void;
  onFocusInput?: () => void;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcuts) => {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in input fields
    if (
      event.target instanceof HTMLInputElement ||
      event.target instanceof HTMLTextAreaElement ||
      event.target instanceof HTMLSelectElement ||
      (event.target as HTMLElement)?.contentEditable === 'true'
    ) {
      return;
    }

    const { key, ctrlKey, metaKey, altKey, shiftKey } = event;
    const isModifierPressed = ctrlKey || metaKey;

    // Voice shortcuts
    if (key === ' ' && !isModifierPressed && !altKey && !shiftKey) {
      // Spacebar to start/stop voice input
      event.preventDefault();
      if (shortcuts.onVoiceStart) {
        shortcuts.onVoiceStart();
      }
      return;
    }

    if (key === 'Escape') {
      // Escape to stop voice input
      event.preventDefault();
      if (shortcuts.onVoiceStop) {
        shortcuts.onVoiceStop();
      }
      return;
    }

    // Voice toggle with Ctrl/Cmd + M
    if ((key === 'm' || key === 'M') && isModifierPressed && !altKey && !shiftKey) {
      event.preventDefault();
      if (shortcuts.onVoiceToggle) {
        shortcuts.onVoiceToggle();
      }
      return;
    }

    // Mode switching with Alt + number keys
    if (altKey && !isModifierPressed && !shiftKey) {
      const modeMap: { [key: string]: string } = {
        '1': 'standard',
        '2': 'streaming',
        '3': 'chain_of_thought',
        '4': 'fact_checked',
        '5': 'voice',
      };

      if (modeMap[key] && shortcuts.onModeSwitch) {
        event.preventDefault();
        shortcuts.onModeSwitch(modeMap[key]);
        return;
      }
    }

    // Settings with Ctrl/Cmd + ,
    if (key === ',' && isModifierPressed && !altKey && !shiftKey) {
      event.preventDefault();
      if (shortcuts.onSettingsOpen) {
        shortcuts.onSettingsOpen();
      }
      return;
    }

    // Focus input with Ctrl/Cmd + /
    if (key === '/' && isModifierPressed && !altKey && !shiftKey) {
      event.preventDefault();
      if (shortcuts.onFocusInput) {
        shortcuts.onFocusInput();
      }
      return;
    }
  }, [shortcuts]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Return help text for shortcuts
  const getShortcutsHelp = useCallback(() => {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const modKey = isMac ? '⌘' : 'Ctrl';

    return [
      { key: 'Space', description: 'Start/stop voice input' },
      { key: 'Escape', description: 'Stop voice input' },
      { key: `${modKey} + M`, description: 'Toggle voice features' },
      { key: 'Alt + 1-5', description: 'Switch chat modes' },
      { key: `${modKey} + ,`, description: 'Open settings' },
      { key: `${modKey} + /`, description: 'Focus chat input' },
    ];
  }, []);

  return { getShortcutsHelp };
};

// Accessibility announcements
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

// Focus management
export const manageFocus = {
  trapFocus: (container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  },

  restoreFocus: (previousElement: HTMLElement | null) => {
    if (previousElement && typeof previousElement.focus === 'function') {
      previousElement.focus();
    }
  },

  saveFocus: (): HTMLElement | null => {
    return document.activeElement as HTMLElement;
  }
};