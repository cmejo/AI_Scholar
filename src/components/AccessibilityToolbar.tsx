import React, { useState, useEffect } from 'react';
import {
  Eye,
  EyeOff,
  Type,
  Contrast,
  Zap,
  ZapOff,
  Volume2,
  VolumeX,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Monitor,
  Palette
} from 'lucide-react';
import { accessibilityService, AccessibilityPreferences } from '../services/accessibilityService';

interface AccessibilityToolbarProps {
  className?: string;
}

export const AccessibilityToolbar: React.FC<AccessibilityToolbarProps> = ({
  className = ''
}) => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(
    accessibilityService.getPreferences()
  );
  const [isExpanded, setIsExpanded] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const updatePreferences = () => {
      setPreferences(accessibilityService.getPreferences());
    };

    // Listen for preference changes
    const interval = setInterval(updatePreferences, 1000);
    return () => clearInterval(interval);
  }, []);

  const togglePreference = <K extends keyof AccessibilityPreferences>(
    key: K,
    value: AccessibilityPreferences[K]
  ) => {
    accessibilityService.updatePreference(key, value);
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const cycleFontSize = () => {
    const sizes: Array<AccessibilityPreferences['fontSize']> = ['small', 'medium', 'large', 'xlarge'];
    const currentIndex = sizes.indexOf(preferences.fontSize);
    const nextSize = sizes[currentIndex < sizes.length - 1 ? currentIndex + 1 : 0];
    togglePreference('fontSize', nextSize);
  };

  const cycleColorBlindnessSupport = () => {
    const types: Array<AccessibilityPreferences['colorBlindnessSupport']> = 
      ['none', 'protanopia', 'deuteranopia', 'tritanopia'];
    const currentIndex = types.indexOf(preferences.colorBlindnessSupport);
    const nextType = types[currentIndex < types.length - 1 ? currentIndex + 1 : 0];
    togglePreference('colorBlindnessSupport', nextType);
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed top-4 right-4 z-50 bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full shadow-lg transition-colors focus-ring"
        aria-label="Show accessibility toolbar"
      >
        <Eye size={20} />
      </button>
    );
  }

  return (
    <div
      className={`accessibility-toolbar fixed top-4 right-4 z-50 bg-gray-800 border border-gray-700 rounded-lg shadow-xl ${className}`}
      role="toolbar"
      aria-label="Accessibility controls"
    >
      {/* Toolbar Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <Eye className="text-blue-400" size={16} />
          <span className="text-sm font-medium text-white">Accessibility</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-700 rounded transition-colors focus-ring"
            aria-label={`${isExpanded ? 'Collapse' : 'Expand'} accessibility toolbar`}
            aria-expanded={isExpanded}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          
          <button
            onClick={() => setIsVisible(false)}
            className="p-1 hover:bg-gray-700 rounded transition-colors focus-ring"
            aria-label="Hide accessibility toolbar"
          >
            <EyeOff size={16} />
          </button>
        </div>
      </div>

      {/* Quick Controls (Always Visible) */}
      <div className="p-3 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          {/* High Contrast Toggle */}
          <button
            onClick={() => togglePreference('highContrastMode', !preferences.highContrastMode)}
            className={`flex items-center space-x-2 p-2 rounded text-xs transition-colors focus-ring ${
              preferences.highContrastMode
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            aria-label={`High contrast mode ${preferences.highContrastMode ? 'enabled' : 'disabled'}`}
            aria-pressed={preferences.highContrastMode}
          >
            <Contrast size={14} />
            <span>Contrast</span>
          </button>

          {/* Font Size Cycle */}
          <button
            onClick={cycleFontSize}
            className="flex items-center space-x-2 p-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded text-xs transition-colors focus-ring"
            aria-label={`Current font size: ${preferences.fontSize}. Click to cycle`}
          >
            <Type size={14} />
            <span className="capitalize">{preferences.fontSize}</span>
          </button>

          {/* Reduced Motion Toggle */}
          <button
            onClick={() => togglePreference('reducedMotion', !preferences.reducedMotion)}
            className={`flex items-center space-x-2 p-2 rounded text-xs transition-colors focus-ring ${
              preferences.reducedMotion
                ? 'bg-orange-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            aria-label={`Reduced motion ${preferences.reducedMotion ? 'enabled' : 'disabled'}`}
            aria-pressed={preferences.reducedMotion}
          >
            {preferences.reducedMotion ? <ZapOff size={14} /> : <Zap size={14} />}
            <span>Motion</span>
          </button>

          {/* Voice Announcements Toggle */}
          <button
            onClick={() => togglePreference('voiceAnnouncements', !preferences.voiceAnnouncements)}
            className={`flex items-center space-x-2 p-2 rounded text-xs transition-colors focus-ring ${
              preferences.voiceAnnouncements
                ? 'bg-green-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            aria-label={`Voice announcements ${preferences.voiceAnnouncements ? 'enabled' : 'disabled'}`}
            aria-pressed={preferences.voiceAnnouncements}
          >
            {preferences.voiceAnnouncements ? <Volume2 size={14} /> : <VolumeX size={14} />}
            <span>Voice</span>
          </button>
        </div>
      </div>

      {/* Extended Controls */}
      {isExpanded && (
        <div className="border-t border-gray-700 p-3 space-y-3">
          {/* Screen Reader Support */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Screen Reader</span>
            <button
              onClick={() => togglePreference('screenReaderEnabled', !preferences.screenReaderEnabled)}
              className={`w-8 h-4 rounded-full transition-colors ${
                preferences.screenReaderEnabled ? 'bg-blue-600' : 'bg-gray-600'
              }`}
              aria-label={`Screen reader support ${preferences.screenReaderEnabled ? 'enabled' : 'disabled'}`}
              role="switch"
              aria-checked={preferences.screenReaderEnabled}
            >
              <div className={`w-3 h-3 bg-white rounded-full transition-transform ${
                preferences.screenReaderEnabled ? 'translate-x-4' : 'translate-x-0.5'
              }`} />
            </button>
          </div>

          {/* Keyboard Navigation Only */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Keyboard Only</span>
            <button
              onClick={() => togglePreference('keyboardNavigationOnly', !preferences.keyboardNavigationOnly)}
              className={`w-8 h-4 rounded-full transition-colors ${
                preferences.keyboardNavigationOnly ? 'bg-blue-600' : 'bg-gray-600'
              }`}
              aria-label={`Keyboard navigation only ${preferences.keyboardNavigationOnly ? 'enabled' : 'disabled'}`}
              role="switch"
              aria-checked={preferences.keyboardNavigationOnly}
            >
              <div className={`w-3 h-3 bg-white rounded-full transition-transform ${
                preferences.keyboardNavigationOnly ? 'translate-x-4' : 'translate-x-0.5'
              }`} />
            </button>
          </div>

          {/* Focus Indicators */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Focus Indicators</span>
            <button
              onClick={() => togglePreference('focusIndicators', !preferences.focusIndicators)}
              className={`w-8 h-4 rounded-full transition-colors ${
                preferences.focusIndicators ? 'bg-blue-600' : 'bg-gray-600'
              }`}
              aria-label={`Focus indicators ${preferences.focusIndicators ? 'enabled' : 'disabled'}`}
              role="switch"
              aria-checked={preferences.focusIndicators}
            >
              <div className={`w-3 h-3 bg-white rounded-full transition-transform ${
                preferences.focusIndicators ? 'translate-x-4' : 'translate-x-0.5'
              }`} />
            </button>
          </div>

          {/* Color Blindness Support */}
          <div className="space-y-2">
            <span className="text-xs text-gray-300">Color Blindness</span>
            <button
              onClick={cycleColorBlindnessSupport}
              className="w-full flex items-center justify-between p-2 bg-gray-700 hover:bg-gray-600 rounded text-xs transition-colors focus-ring"
              aria-label={`Color blindness support: ${preferences.colorBlindnessSupport}. Click to cycle`}
            >
              <div className="flex items-center space-x-2">
                <Palette size={14} />
                <span className="capitalize">
                  {preferences.colorBlindnessSupport === 'none' ? 'None' : preferences.colorBlindnessSupport}
                </span>
              </div>
              <ChevronDown size={12} />
            </button>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-700">
            <button
              onClick={() => accessibilityService.showKeyboardShortcuts()}
              className="flex items-center space-x-2 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors focus-ring"
              aria-label="Show keyboard shortcuts help"
            >
              <HelpCircle size={14} />
              <span>Help</span>
            </button>
            
            <button
              onClick={() => accessibilityService.enhanceSemanticStructure()}
              className="flex items-center space-x-2 p-2 bg-green-600 hover:bg-green-700 text-white rounded text-xs transition-colors focus-ring"
              aria-label="Enhance page accessibility"
            >
              <Monitor size={14} />
              <span>Enhance</span>
            </button>
          </div>
        </div>
      )}

      {/* Status Indicator */}
      <div className="px-3 py-2 border-t border-gray-700 bg-gray-900/50">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">Status:</span>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${
              preferences.screenReaderEnabled || preferences.highContrastMode || preferences.keyboardNavigationOnly
                ? 'bg-green-400'
                : 'bg-yellow-400'
            }`} />
            <span className="text-gray-300">
              {preferences.screenReaderEnabled || preferences.highContrastMode || preferences.keyboardNavigationOnly
                ? 'Enhanced'
                : 'Standard'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessibilityToolbar;