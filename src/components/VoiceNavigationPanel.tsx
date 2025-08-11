import React, { useEffect, useState } from 'react';
import type { AccessibilityFeature, VoiceShortcut } from '../services/voiceNavigationService';
import voiceNavigationService from '../services/voiceNavigationService';

interface VoiceNavigationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

const VoiceNavigationPanel: React.FC<VoiceNavigationPanelProps> = ({
  isOpen,
  onClose,
  className = ''
}) => {
  const [shortcuts, setShortcuts] = useState<VoiceShortcut[]>([]);
  const [accessibilityFeatures, setAccessibilityFeatures] = useState<AccessibilityFeature[]>([]);
  const [activeTab, setActiveTab] = useState<'shortcuts' | 'accessibility'>('shortcuts');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadShortcuts();
      loadAccessibilityFeatures();
    }
  }, [isOpen]);

  const loadShortcuts = (): void => {
    const availableShortcuts = voiceNavigationService.getAvailableShortcuts();
    setShortcuts(availableShortcuts);
  };

  const loadAccessibilityFeatures = (): void => {
    const features = voiceNavigationService.getAccessibilityFeatures();
    setAccessibilityFeatures(features);
  };

  const handleShortcutToggle = (shortcutId: string, enabled: boolean): void => {
    voiceNavigationService.setShortcutEnabled(shortcutId, enabled);
    loadShortcuts();
  };

  const handleAccessibilityToggle = (featureId: string, enabled: boolean): void => {
    voiceNavigationService.setAccessibilityFeatureEnabled(featureId, enabled);
    loadAccessibilityFeatures();
  };

  const handleAccessibilitySettingChange = (featureId: string, setting: string, value: unknown): void => {
    voiceNavigationService.updateAccessibilityFeatureSettings(featureId, { [setting]: value });
    loadAccessibilityFeatures();
  };

  const filteredShortcuts = shortcuts.filter(shortcut =>
    shortcut.phrase.toLowerCase().includes(searchTerm.toLowerCase()) ||
    shortcut.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    shortcut.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const groupedShortcuts = filteredShortcuts.reduce((groups, shortcut) => {
    const category = shortcut.category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(shortcut);
    return groups;
  }, {} as Record<string, VoiceShortcut[]>);

  if (!isOpen) return null;

  return (
    <div className={`voice-navigation-panel ${className}`}>
      <div className="voice-navigation-panel__overlay" onClick={onClose} />
      
      <div className="voice-navigation-panel__content">
        {/* Header */}
        <div className="voice-navigation-panel__header">
          <h2 className="voice-navigation-panel__title">Voice Navigation Settings</h2>
          <button
            className="voice-navigation-panel__close"
            onClick={onClose}
            aria-label="Close voice navigation panel"
          >
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="voice-navigation-panel__tabs">
          <button
            className={`voice-navigation-panel__tab ${activeTab === 'shortcuts' ? 'voice-navigation-panel__tab--active' : ''}`}
            onClick={() => setActiveTab('shortcuts')}
          >
            Voice Shortcuts
          </button>
          <button
            className={`voice-navigation-panel__tab ${activeTab === 'accessibility' ? 'voice-navigation-panel__tab--active' : ''}`}
            onClick={() => setActiveTab('accessibility')}
          >
            Accessibility
          </button>
        </div>

        {/* Content */}
        <div className="voice-navigation-panel__body">
          {activeTab === 'shortcuts' && (
            <div className="voice-navigation-panel__shortcuts">
              {/* Search */}
              <div className="voice-navigation-panel__search">
                <input
                  type="text"
                  placeholder="Search shortcuts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="voice-navigation-panel__search-input"
                />
              </div>

              {/* Shortcuts by category */}
              {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
                <div key={category} className="voice-navigation-panel__category">
                  <h3 className="voice-navigation-panel__category-title">
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </h3>
                  
                  <div className="voice-navigation-panel__shortcuts-list">
                    {categoryShortcuts.map((shortcut) => (
                      <div key={shortcut.id} className="voice-navigation-panel__shortcut">
                        <div className="voice-navigation-panel__shortcut-info">
                          <div className="voice-navigation-panel__shortcut-phrase">
                            "{shortcut.phrase}"
                          </div>
                          <div className="voice-navigation-panel__shortcut-description">
                            {shortcut.description}
                          </div>
                        </div>
                        
                        <label className="voice-navigation-panel__toggle">
                          <input
                            type="checkbox"
                            checked={shortcut.enabled}
                            onChange={(e) => handleShortcutToggle(shortcut.id, e.target.checked)}
                            className="voice-navigation-panel__toggle-input"
                          />
                          <span className="voice-navigation-panel__toggle-slider"></span>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {filteredShortcuts.length === 0 && (
                <div className="voice-navigation-panel__empty">
                  <p>No shortcuts found matching your search.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'accessibility' && (
            <div className="voice-navigation-panel__accessibility">
              {accessibilityFeatures.map((feature) => (
                <div key={feature.id} className="voice-navigation-panel__feature">
                  <div className="voice-navigation-panel__feature-header">
                    <div className="voice-navigation-panel__feature-info">
                      <h4 className="voice-navigation-panel__feature-name">
                        {feature.name}
                      </h4>
                      <p className="voice-navigation-panel__feature-description">
                        {feature.description}
                      </p>
                    </div>
                    
                    <label className="voice-navigation-panel__toggle">
                      <input
                        type="checkbox"
                        checked={feature.enabled}
                        onChange={(e) => handleAccessibilityToggle(feature.id, e.target.checked)}
                        className="voice-navigation-panel__toggle-input"
                      />
                      <span className="voice-navigation-panel__toggle-slider"></span>
                    </label>
                  </div>

                  {/* Feature-specific settings */}
                  {feature.enabled && (
                    <div className="voice-navigation-panel__feature-settings">
                      {feature.id === 'voice_feedback' && (
                        <>
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Feedback Level:
                              <select
                                value={feature.settings.feedbackLevel}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'feedbackLevel', e.target.value)}
                                className="voice-navigation-panel__setting-select"
                              >
                                <option value="minimal">Minimal</option>
                                <option value="essential">Essential</option>
                                <option value="detailed">Detailed</option>
                                <option value="verbose">Verbose</option>
                              </select>
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Speech Rate:
                              <input
                                type="range"
                                min="0.5"
                                max="2"
                                step="0.1"
                                value={feature.settings.rate}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'rate', parseFloat(e.target.value))}
                                className="voice-navigation-panel__setting-range"
                              />
                              <span className="voice-navigation-panel__setting-value">
                                {feature.settings.rate}x
                              </span>
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Volume:
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={feature.settings.volume}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'volume', parseFloat(e.target.value))}
                                className="voice-navigation-panel__setting-range"
                              />
                              <span className="voice-navigation-panel__setting-value">
                                {Math.round(feature.settings.volume * 100)}%
                              </span>
                            </label>
                          </div>
                        </>
                      )}

                      {feature.id === 'screen_reader' && (
                        <>
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              <input
                                type="checkbox"
                                checked={feature.settings.announceNavigation}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'announceNavigation', e.target.checked)}
                                className="voice-navigation-panel__setting-checkbox"
                              />
                              Announce Navigation
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              <input
                                type="checkbox"
                                checked={feature.settings.announceContent}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'announceContent', e.target.checked)}
                                className="voice-navigation-panel__setting-checkbox"
                              />
                              Announce Content Changes
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              <input
                                type="checkbox"
                                checked={feature.settings.announceActions}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'announceActions', e.target.checked)}
                                className="voice-navigation-panel__setting-checkbox"
                              />
                              Announce Actions
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Verbosity Level:
                              <select
                                value={feature.settings.verbosityLevel}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'verbosityLevel', e.target.value)}
                                className="voice-navigation-panel__setting-select"
                              >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                              </select>
                            </label>
                          </div>
                        </>
                      )}

                      {feature.id === 'high_contrast' && (
                        <>
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Contrast Level:
                              <select
                                value={feature.settings.contrastLevel}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'contrastLevel', e.target.value)}
                                className="voice-navigation-panel__setting-select"
                              >
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="maximum">Maximum</option>
                              </select>
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Color Scheme:
                              <select
                                value={feature.settings.colorScheme}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'colorScheme', e.target.value)}
                                className="voice-navigation-panel__setting-select"
                              >
                                <option value="dark">Dark</option>
                                <option value="light">Light</option>
                                <option value="auto">Auto</option>
                              </select>
                            </label>
                          </div>
                        </>
                      )}

                      {feature.id === 'text_scaling' && (
                        <>
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Scale Factor:
                              <input
                                type="range"
                                min="1"
                                max="2"
                                step="0.1"
                                value={feature.settings.scaleFactor}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'scaleFactor', parseFloat(e.target.value))}
                                className="voice-navigation-panel__setting-range"
                              />
                              <span className="voice-navigation-panel__setting-value">
                                {feature.settings.scaleFactor}x
                              </span>
                            </label>
                          </div>
                          
                          <div className="voice-navigation-panel__setting">
                            <label className="voice-navigation-panel__setting-label">
                              Line Height:
                              <input
                                type="range"
                                min="1"
                                max="2"
                                step="0.1"
                                value={feature.settings.lineHeight}
                                onChange={(e) => handleAccessibilitySettingChange(feature.id, 'lineHeight', parseFloat(e.target.value))}
                                className="voice-navigation-panel__setting-range"
                              />
                              <span className="voice-navigation-panel__setting-value">
                                {feature.settings.lineHeight}
                              </span>
                            </label>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="voice-navigation-panel__footer">
          <div className="voice-navigation-panel__help">
            <p>
              <strong>Quick Start:</strong> Say "help" to hear available commands, 
              or "go to documents" to navigate to the documents page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceNavigationPanel;