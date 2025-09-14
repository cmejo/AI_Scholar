import React, { useState, useEffect } from 'react';
import { 
  Accessibility, Eye, EyeOff, Type, Contrast, Volume2, 
  VolumeX, MousePointer, Keyboard, RotateCcw, X, Settings
} from 'lucide-react';

interface AccessibilitySettings {
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
  focusIndicators: boolean;
  colorBlindMode: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';
  fontSize: number;
  soundEnabled: boolean;
  cursorSize: 'normal' | 'large' | 'extra-large';
}

interface AccessibilityToolbarProps {
  isVisible: boolean;
  onToggle: () => void;
  position?: 'left' | 'right';
}

export const AccessibilityToolbar: React.FC<AccessibilityToolbarProps> = ({
  isVisible,
  onToggle,
  position = 'left'
}) => {
  const [settings, setSettings] = useState<AccessibilitySettings>({
    highContrast: false,
    largeText: false,
    reducedMotion: false,
    screenReader: false,
    keyboardNavigation: true,
    focusIndicators: true,
    colorBlindMode: 'none',
    fontSize: 16,
    soundEnabled: true,
    cursorSize: 'normal'
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [announcements, setAnnouncements] = useState<string[]>([]);

  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibility-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('Failed to load accessibility settings:', error);
      }
    }
  }, []);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));
    applyAccessibilitySettings(settings);
  }, [settings]);

  // Apply accessibility settings to the document
  const applyAccessibilitySettings = (newSettings: AccessibilitySettings) => {
    const root = document.documentElement;
    
    // High contrast
    if (newSettings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Large text
    if (newSettings.largeText) {
      root.style.fontSize = `${Math.max(newSettings.fontSize, 18)}px`;
    } else {
      root.style.fontSize = `${newSettings.fontSize}px`;
    }

    // Reduced motion
    if (newSettings.reducedMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }

    // Focus indicators
    if (newSettings.focusIndicators) {
      root.classList.add('enhanced-focus');
    } else {
      root.classList.remove('enhanced-focus');
    }

    // Color blind mode
    root.className = root.className.replace(/colorblind-\w+/g, '');
    if (newSettings.colorBlindMode !== 'none') {
      root.classList.add(`colorblind-${newSettings.colorBlindMode}`);
    }

    // Cursor size
    root.className = root.className.replace(/cursor-\w+/g, '');
    if (newSettings.cursorSize !== 'normal') {
      root.classList.add(`cursor-${newSettings.cursorSize}`);
    }
  };

  // Screen reader announcements
  const announceToScreenReader = (message: string) => {
    if (!settings.screenReader) return;

    setAnnouncements(prev => [...prev, message]);
    
    // Create live region for screen reader
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.textContent = message;
    document.body.appendChild(liveRegion);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(liveRegion);
    }, 1000);

    // Play sound if enabled
    if (settings.soundEnabled) {
      playNotificationSound();
    }
  };

  const playNotificationSound = () => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  };

  const updateSetting = <K extends keyof AccessibilitySettings>(
    key: K, 
    value: AccessibilitySettings[K],
    announcement?: string
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    if (announcement) {
      announceToScreenReader(announcement);
    }
  };

  const resetSettings = () => {
    const defaultSettings: AccessibilitySettings = {
      highContrast: false,
      largeText: false,
      reducedMotion: false,
      screenReader: false,
      keyboardNavigation: true,
      focusIndicators: true,
      colorBlindMode: 'none',
      fontSize: 16,
      soundEnabled: true,
      cursorSize: 'normal'
    };
    setSettings(defaultSettings);
    announceToScreenReader('Accessibility settings reset to defaults');
  };

  if (!isVisible) return null;

  return (
    <>
      {/* Accessibility Toolbar */}
      <div
        style={{
          position: 'fixed',
          [position]: '20px',
          top: '50%',
          transform: 'translateY(-50%)',
          background: 'rgba(0, 0, 0, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '12px',
          padding: '16px',
          width: isExpanded ? '280px' : '60px',
          color: 'white',
          fontSize: '14px',
          zIndex: 1000,
          transition: 'width 0.3s ease, opacity 0.3s ease',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)'
        }}
        role="toolbar"
        aria-label="Accessibility controls"
      >
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: isExpanded ? '16px' : '0'
        }}>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'none',
              border: 'none',
              color: '#10b981',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'background 0.2s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
            onMouseOut={(e) => e.currentTarget.style.background = 'none'}
            aria-label={isExpanded ? 'Collapse accessibility toolbar' : 'Expand accessibility toolbar'}
            aria-expanded={isExpanded}
          >
            <Accessibility style={{ width: '20px', height: '20px' }} />
            {isExpanded && <span style={{ fontWeight: 'bold' }}>Accessibility</span>}
          </button>
          
          {isExpanded && (
            <button
              onClick={onToggle}
              style={{
                background: 'none',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '4px'
              }}
              onMouseOver={(e) => e.currentTarget.style.color = '#ef4444'}
              onMouseOut={(e) => e.currentTarget.style.color = '#9ca3af'}
              aria-label="Close accessibility toolbar"
            >
              <X style={{ width: '16px', height: '16px' }} />
            </button>
          )}
        </div>

        {/* Controls */}
        {isExpanded && (
          <div style={{ display: 'grid', gap: '12px' }}>
            {/* High Contrast */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Contrast style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                <span>High Contrast</span>
              </div>
              <button
                onClick={() => updateSetting('highContrast', !settings.highContrast, 
                  `High contrast ${!settings.highContrast ? 'enabled' : 'disabled'}`)}
                style={{
                  background: settings.highContrast ? '#10b981' : 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '12px',
                  width: '40px',
                  height: '20px',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                aria-label={`High contrast ${settings.highContrast ? 'enabled' : 'disabled'}`}
                role="switch"
                aria-checked={settings.highContrast}
              >
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: 'white',
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '2px',
                  left: settings.highContrast ? '22px' : '2px',
                  transition: 'left 0.2s ease'
                }} />
              </button>
            </div>

            {/* Large Text */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Type style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                <span>Large Text</span>
              </div>
              <button
                onClick={() => updateSetting('largeText', !settings.largeText,
                  `Large text ${!settings.largeText ? 'enabled' : 'disabled'}`)}
                style={{
                  background: settings.largeText ? '#10b981' : 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '12px',
                  width: '40px',
                  height: '20px',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                aria-label={`Large text ${settings.largeText ? 'enabled' : 'disabled'}`}
                role="switch"
                aria-checked={settings.largeText}
              >
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: 'white',
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '2px',
                  left: settings.largeText ? '22px' : '2px',
                  transition: 'left 0.2s ease'
                }} />
              </button>
            </div>

            {/* Font Size Slider */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '12px', color: '#9ca3af' }}>
                Font Size: {settings.fontSize}px
              </label>
              <input
                type="range"
                min="12"
                max="24"
                value={settings.fontSize}
                onChange={(e) => updateSetting('fontSize', parseInt(e.target.value))}
                style={{
                  width: '100%',
                  height: '4px',
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '2px',
                  outline: 'none',
                  cursor: 'pointer'
                }}
                aria-label="Font size"
              />
            </div>

            {/* Reduced Motion */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MousePointer style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                <span>Reduced Motion</span>
              </div>
              <button
                onClick={() => updateSetting('reducedMotion', !settings.reducedMotion,
                  `Reduced motion ${!settings.reducedMotion ? 'enabled' : 'disabled'}`)}
                style={{
                  background: settings.reducedMotion ? '#10b981' : 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '12px',
                  width: '40px',
                  height: '20px',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                aria-label={`Reduced motion ${settings.reducedMotion ? 'enabled' : 'disabled'}`}
                role="switch"
                aria-checked={settings.reducedMotion}
              >
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: 'white',
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '2px',
                  left: settings.reducedMotion ? '22px' : '2px',
                  transition: 'left 0.2s ease'
                }} />
              </button>
            </div>

            {/* Screen Reader */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Volume2 style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                <span>Screen Reader</span>
              </div>
              <button
                onClick={() => updateSetting('screenReader', !settings.screenReader,
                  `Screen reader announcements ${!settings.screenReader ? 'enabled' : 'disabled'}`)}
                style={{
                  background: settings.screenReader ? '#10b981' : 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '12px',
                  width: '40px',
                  height: '20px',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                aria-label={`Screen reader ${settings.screenReader ? 'enabled' : 'disabled'}`}
                role="switch"
                aria-checked={settings.screenReader}
              >
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: 'white',
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '2px',
                  left: settings.screenReader ? '22px' : '2px',
                  transition: 'left 0.2s ease'
                }} />
              </button>
            </div>

            {/* Color Blind Mode */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '12px', color: '#9ca3af' }}>
                Color Blind Support
              </label>
              <select
                value={settings.colorBlindMode}
                onChange={(e) => updateSetting('colorBlindMode', e.target.value as any,
                  `Color blind mode set to ${e.target.value === 'none' ? 'none' : e.target.value}`)}
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '6px',
                  padding: '8px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none'
                }}
                aria-label="Color blind support mode"
              >
                <option value="none" style={{ background: '#374151' }}>None</option>
                <option value="protanopia" style={{ background: '#374151' }}>Protanopia (Red-blind)</option>
                <option value="deuteranopia" style={{ background: '#374151' }}>Deuteranopia (Green-blind)</option>
                <option value="tritanopia" style={{ background: '#374151' }}>Tritanopia (Blue-blind)</option>
              </select>
            </div>

            {/* Reset Button */}
            <button
              onClick={resetSettings}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '6px',
                padding: '8px',
                color: '#ef4444',
                cursor: 'pointer',
                fontSize: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'background 0.2s ease'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.3)'}
              onMouseOut={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
              aria-label="Reset accessibility settings to defaults"
            >
              <RotateCcw style={{ width: '14px', height: '14px' }} />
              Reset Settings
            </button>
          </div>
        )}
      </div>

      {/* Screen Reader Live Region */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        style={{
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: 0,
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          border: 0
        }}
      >
        {announcements[announcements.length - 1]}
      </div>

      {/* CSS for accessibility features */}
      <style>{`
        .high-contrast {
          filter: contrast(150%) brightness(120%);
        }
        
        .reduced-motion * {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
        
        .enhanced-focus *:focus {
          outline: 3px solid #10b981 !important;
          outline-offset: 2px !important;
        }
        
        .colorblind-protanopia {
          filter: url(#protanopia-filter);
        }
        
        .colorblind-deuteranopia {
          filter: url(#deuteranopia-filter);
        }
        
        .colorblind-tritanopia {
          filter: url(#tritanopia-filter);
        }
        
        .cursor-large * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path d="M2 2l8 20 4-8 8-4z" fill="white" stroke="black" stroke-width="2"/></svg>') 2 2, auto !important;
        }
        
        .cursor-extra-large * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><path d="M3 3l12 30 6-12 12-6z" fill="white" stroke="black" stroke-width="3"/></svg>') 3 3, auto !important;
        }
        
        .sr-only {
          position: absolute !important;
          width: 1px !important;
          height: 1px !important;
          padding: 0 !important;
          margin: -1px !important;
          overflow: hidden !important;
          clip: rect(0, 0, 0, 0) !important;
          white-space: nowrap !important;
          border: 0 !important;
        }
      `}</style>
    </>
  );
};