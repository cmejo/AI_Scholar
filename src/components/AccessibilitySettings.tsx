import React, { useState, useEffect } from 'react';
import { 
  Eye, 
  Type, 
  Contrast, 
  Zap, 
  ZapOff, 
  Keyboard, 
  Volume2, 
  Focus,
  Palette,
  Settings,
  X,
  HelpCircle
} from 'lucide-react';
import { accessibilityService, AccessibilityPreferences } from '../services/accessibilityService';

interface AccessibilitySettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AccessibilitySettings: React.FC<AccessibilitySettingsProps> = ({
  isOpen,
  onClose
}) => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(
    accessibilityService.getPreferences()
  );
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      accessibilityService.saveFocus();
      accessibilityService.announce('Accessibility settings opened');
    } else {
      setIsVisible(false);
      accessibilityService.restoreFocus();
    }
  }, [isOpen]);

  const updatePreference = <K extends keyof AccessibilityPreferences>(
    key: K,
    value: AccessibilityPreferences[K]
  ) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    accessibilityService.updatePreference(key, value);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose();
    }
  };

  if (!isVisible) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="accessibility-title"
      onKeyDown={handleKeyDown}
    >
      <div
        className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Settings className="text-blue-400" size={24} />
            <h2 id="accessibility-title" className="text-xl font-semibold text-white">
              Accessibility Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close accessibility settings"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Quick Actions */}
          <section>
            <h3 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
              <Zap className="text-yellow-400" size={20} />
              <span>Quick Actions</span>
            </h3>
            
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => accessibilityService.showKeyboardShortcuts()}
                className="flex items-center space-x-2 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors focus-ring"
                aria-label="Show keyboard shortcuts help"
              >
                <HelpCircle className="text-blue-400" size={16} />
                <span className="text-sm">Keyboard Help</span>
              </button>
              
              <button
                onClick={() => {
                  const currentSize = preferences.fontSize;
                  const sizes: Array<AccessibilityPreferences['fontSize']> = ['small', 'medium', 'large', 'xlarge'];
                  const currentIndex = sizes.indexOf(currentSize);
                  const nextSize = sizes[currentIndex < sizes.length - 1 ? currentIndex + 1 : 0];
                  updatePreference('fontSize', nextSize);
                }}
                className="flex items-center space-x-2 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors focus-ring"
                aria-label={`Current font size: ${preferences.fontSize}. Click to cycle to next size`}
              >
                <Type className="text-green-400" size={16} />
                <span className="text-sm">Cycle Font Size</span>
              </button>
              
              <button
                onClick={() => updatePreference('highContrastMode', !preferences.highContrastMode)}
                className="flex items-center space-x-2 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors focus-ring"
                aria-label={`Toggle high contrast mode. Currently ${preferences.highContrastMode ? 'enabled' : 'disabled'}`}
              >
                <Contrast className="text-yellow-400" size={16} />
                <span className="text-sm">Toggle Contrast</span>
              </button>
              
              <button
                onClick={() => updatePreference('reducedMotion', !preferences.reducedMotion)}
                className="flex items-center space-x-2 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-600/50 transition-colors focus-ring"
                aria-label={`Toggle reduced motion. Currently ${preferences.reducedMotion ? 'enabled' : 'disabled'}`}
              >
                <ZapOff className="text-orange-400" size={16} />
                <span className="text-sm">Toggle Motion</span>
              </button>
            </div>
          </section>
          {/* Vision Settings */}
          <section>
            <h3 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
              <Eye className="text-purple-400" size={20} />
              <span>Vision</span>
            </h3>
            
            <div className="space-y-4">
              {/* High Contrast Mode */}
              <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Contrast className="text-yellow-400" size={20} />
                  <div>
                    <div className="text-white font-medium">High Contrast Mode</div>
                    <div className="text-gray-400 text-sm">Increase contrast for better visibility</div>
                  </div>
                </div>
                <button
                  onClick={() => updatePreference('highContrastMode', !preferences.highContrastMode)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    preferences.highContrastMode ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  aria-label={`High contrast mode ${preferences.highContrastMode ? 'enabled' : 'disabled'}`}
                  role="switch"
                  aria-checked={preferences.highContrastMode}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    preferences.highContrastMode ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Font Size */}
              <div className="p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3 mb-3">
                  <Type className="text-green-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Font Size</div>
                    <div className="text-gray-400 text-sm">Adjust text size for better readability</div>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {(['small', 'medium', 'large', 'xlarge'] as const).map((size) => (
                    <button
                      key={size}
                      onClick={() => updatePreference('fontSize', size)}
                      className={`p-2 rounded-lg text-sm font-medium transition-colors ${
                        preferences.fontSize === size
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                      }`}
                      aria-label={`Set font size to ${size}`}
                    >
                      {size.charAt(0).toUpperCase() + size.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Color Blindness Support */}
              <div className="p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3 mb-3">
                  <Palette className="text-pink-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Color Blindness Support</div>
                    <div className="text-gray-400 text-sm">Adjust colors for color vision deficiency</div>
                  </div>
                </div>
                <select
                  value={preferences.colorBlindnessSupport}
                  onChange={(e) => updatePreference('colorBlindnessSupport', e.target.value as 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia')}
                  className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white"
                  aria-label="Color blindness support type"
                >
                  <option value="none">None</option>
                  <option value="protanopia">Protanopia (Red-blind)</option>
                  <option value="deuteranopia">Deuteranopia (Green-blind)</option>
                  <option value="tritanopia">Tritanopia (Blue-blind)</option>
                </select>
              </div>
            </div>
          </section>

          {/* Motor Settings */}
          <section>
            <h3 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
              <Keyboard className="text-blue-400" size={20} />
              <span>Motor & Navigation</span>
            </h3>
            
            <div className="space-y-4">
              {/* Reduced Motion */}
              <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <ZapOff className="text-orange-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Reduced Motion</div>
                    <div className="text-gray-400 text-sm">Minimize animations and transitions</div>
                  </div>
                </div>
                <button
                  onClick={() => updatePreference('reducedMotion', !preferences.reducedMotion)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    preferences.reducedMotion ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  aria-label={`Reduced motion ${preferences.reducedMotion ? 'enabled' : 'disabled'}`}
                  role="switch"
                  aria-checked={preferences.reducedMotion}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    preferences.reducedMotion ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Enhanced Focus Indicators */}
              <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Focus className="text-cyan-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Enhanced Focus Indicators</div>
                    <div className="text-gray-400 text-sm">Show clear focus outlines for keyboard navigation</div>
                  </div>
                </div>
                <button
                  onClick={() => updatePreference('focusIndicators', !preferences.focusIndicators)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    preferences.focusIndicators ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  aria-label={`Focus indicators ${preferences.focusIndicators ? 'enabled' : 'disabled'}`}
                  role="switch"
                  aria-checked={preferences.focusIndicators}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    preferences.focusIndicators ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Keyboard Navigation Only */}
              <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Keyboard className="text-indigo-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Keyboard Navigation Only</div>
                    <div className="text-gray-400 text-sm">Optimize interface for keyboard-only navigation</div>
                  </div>
                </div>
                <button
                  onClick={() => updatePreference('keyboardNavigationOnly', !preferences.keyboardNavigationOnly)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    preferences.keyboardNavigationOnly ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  aria-label={`Keyboard navigation only ${preferences.keyboardNavigationOnly ? 'enabled' : 'disabled'}`}
                  role="switch"
                  aria-checked={preferences.keyboardNavigationOnly}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    preferences.keyboardNavigationOnly ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            </div>
          </section>

          {/* Audio Settings */}
          <section>
            <h3 className="text-lg font-medium text-white mb-4 flex items-center space-x-2">
              <Volume2 className="text-green-400" size={20} />
              <span>Audio & Screen Reader</span>
            </h3>
            
            <div className="space-y-4">
              {/* Screen Reader Support */}
              <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Eye className="text-purple-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Screen Reader Support</div>
                    <div className="text-gray-400 text-sm">Enable enhanced screen reader compatibility</div>
                  </div>
                </div>
                <button
                  onClick={() => updatePreference('screenReaderEnabled', !preferences.screenReaderEnabled)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    preferences.screenReaderEnabled ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  aria-label={`Screen reader support ${preferences.screenReaderEnabled ? 'enabled' : 'disabled'}`}
                  role="switch"
                  aria-checked={preferences.screenReaderEnabled}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    preferences.screenReaderEnabled ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Voice Announcements */}
              <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Volume2 className="text-green-400" size={20} />
                  <div>
                    <div className="text-white font-medium">Voice Announcements</div>
                    <div className="text-gray-400 text-sm">Announce important changes and updates</div>
                  </div>
                </div>
                <button
                  onClick={() => updatePreference('voiceAnnouncements', !preferences.voiceAnnouncements)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    preferences.voiceAnnouncements ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  aria-label={`Voice announcements ${preferences.voiceAnnouncements ? 'enabled' : 'disabled'}`}
                  role="switch"
                  aria-checked={preferences.voiceAnnouncements}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    preferences.voiceAnnouncements ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-700 flex justify-between items-center">
          <div className="text-sm text-gray-400">
            Settings are automatically saved
          </div>
          <button
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};