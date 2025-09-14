import React, { useState } from 'react';
import { Keyboard, X, Info } from 'lucide-react';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

interface KeyboardShortcutsHelpProps {
  className?: string;
}

export const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { getShortcutsHelp } = useKeyboardShortcuts({});

  const shortcuts = getShortcutsHelp();

  return (
    <>
      {/* Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors ${className}`}
        title="Keyboard shortcuts"
        aria-label="Show keyboard shortcuts"
      >
        <Keyboard className="w-4 h-4" />
      </button>

      {/* Help Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl w-full max-w-md mx-4">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center space-x-2">
                <Keyboard className="w-5 h-5 text-purple-400" />
                <h2 className="text-lg font-medium text-white">Keyboard Shortcuts</h2>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Close shortcuts help"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4">
              <div className="space-y-3">
                {shortcuts.map((shortcut, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">{shortcut.description}</span>
                    <kbd className="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-xs font-mono text-gray-200">
                      {shortcut.key}
                    </kbd>
                  </div>
                ))}
              </div>

              {/* Additional Info */}
              <div className="mt-6 p-3 bg-blue-900/20 border border-blue-800/30 rounded-md">
                <div className="flex items-start space-x-2">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-blue-300">
                    <p className="font-medium mb-1">Voice Features:</p>
                    <ul className="space-y-1 text-blue-200">
                      <li>• Hold Space to start voice input</li>
                      <li>• Press Escape to stop voice input</li>
                      <li>• Voice features require microphone permissions</li>
                      <li>• Works best in Chrome, Edge, or Safari</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Accessibility Info */}
              <div className="mt-4 p-3 bg-green-900/20 border border-green-800/30 rounded-md">
                <div className="flex items-start space-x-2">
                  <Info className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-green-300">
                    <p className="font-medium mb-1">Accessibility:</p>
                    <ul className="space-y-1 text-green-200">
                      <li>• All features are keyboard accessible</li>
                      <li>• Screen reader announcements for voice actions</li>
                      <li>• High contrast mode supported</li>
                      <li>• Focus management for modal dialogs</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end p-4 border-t border-gray-700">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default KeyboardShortcutsHelp;