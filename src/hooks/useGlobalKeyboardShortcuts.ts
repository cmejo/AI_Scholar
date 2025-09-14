import { useEffect } from 'react';

interface KeyboardShortcut {
  key: string;
  altKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  action: () => void;
  description: string;
}

interface UseGlobalKeyboardShortcutsProps {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

export const useGlobalKeyboardShortcuts = ({ 
  shortcuts, 
  enabled = true 
}: UseGlobalKeyboardShortcutsProps) => {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const matchingShortcut = shortcuts.find(shortcut => {
        return (
          shortcut.key.toLowerCase() === event.key.toLowerCase() &&
          !!shortcut.altKey === event.altKey &&
          !!shortcut.ctrlKey === event.ctrlKey &&
          !!shortcut.shiftKey === event.shiftKey
        );
      });

      if (matchingShortcut) {
        event.preventDefault();
        matchingShortcut.action();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, enabled]);

  return { shortcuts };
};

// Global navigation shortcuts
export const createNavigationShortcuts = (navigate: (view: string) => void) => [
  {
    key: '1',
    altKey: true,
    action: () => navigate('chat'),
    description: 'Navigate to Chat (Alt+1)'
  },
  {
    key: '2',
    altKey: true,
    action: () => navigate('documents'),
    description: 'Navigate to Documents (Alt+2)'
  },
  {
    key: '3',
    altKey: true,
    action: () => navigate('analytics'),
    description: 'Navigate to Analytics (Alt+3)'
  },
  {
    key: '4',
    altKey: true,
    action: () => navigate('settings'),
    description: 'Navigate to Settings (Alt+4)'
  },
  {
    key: '5',
    altKey: true,
    action: () => navigate('help'),
    description: 'Navigate to Help (Alt+5)'
  },
  {
    key: '6',
    altKey: true,
    action: () => navigate('about'),
    description: 'Navigate to About (Alt+6)'
  }
];