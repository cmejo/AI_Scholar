import React, { useState, useCallback, useEffect } from 'react';
import { MessageCircle, Zap, Brain, CheckCircle, Mic, Settings } from 'lucide-react';
import { ChatMode, ChatSettings } from '../types/chat';
import VoiceSettings from './VoiceSettings';
import KeyboardShortcutsHelp from './KeyboardShortcutsHelp';
import '../styles/animations.css';

interface ChatModeSelectorProps {
  currentMode: ChatMode['id'];
  onModeChange: (mode: ChatMode['id']) => void;
  settings: ChatSettings;
  onSettingsChange: (settings: Partial<ChatSettings>) => void;
  className?: string;
}

const availableModes: ChatMode[] = [
  {
    id: 'standard',
    name: 'Standard',
    description: 'Regular chat with AI assistant',
    icon: 'MessageCircle',
    enabled: true,
  },
  {
    id: 'streaming',
    name: 'Streaming',
    description: 'Real-time response streaming',
    icon: 'Zap',
    enabled: true,
  },
  {
    id: 'chain_of_thought',
    name: 'Chain of Thought',
    description: 'See AI reasoning process',
    icon: 'Brain',
    enabled: true,
  },
  {
    id: 'fact_checked',
    name: 'Fact Checked',
    description: 'Responses with citations',
    icon: 'CheckCircle',
    enabled: true,
  },
  {
    id: 'voice',
    name: 'Voice',
    description: 'Voice-optimized responses',
    icon: 'Mic',
    enabled: true,
  },
];

const iconMap = {
  MessageCircle,
  Zap,
  Brain,
  CheckCircle,
  Mic,
};

export const ChatModeSelector: React.FC<ChatModeSelectorProps> = ({
  currentMode,
  onModeChange,
  settings,
  onSettingsChange,
  className = '',
}) => {
  const [showSettings, setShowSettings] = useState(false);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('chatSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        onSettingsChange(parsed);
      } catch (error) {
        console.error('Failed to load chat settings:', error);
      }
    }
  }, [onSettingsChange]);

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('chatSettings', JSON.stringify(settings));
  }, [settings]);

  const handleModeChange = useCallback((mode: ChatMode['id']) => {
    onModeChange(mode);
    onSettingsChange({ mode });
  }, [onModeChange, onSettingsChange]);

  const handleSettingChange = useCallback((key: keyof ChatSettings, value: any) => {
    onSettingsChange({ [key]: value });
  }, [onSettingsChange]);

  const getModeIcon = (iconName: string) => {
    const IconComponent = iconMap[iconName as keyof typeof iconMap];
    return IconComponent || MessageCircle;
  };

  const currentModeData = availableModes.find(mode => mode.id === currentMode) || availableModes[0];

  return (
    <div className={`relative ${className}`}>
      {/* Mode Selector Buttons */}
      <div className="flex items-center space-x-1 bg-gray-800 rounded-lg p-1">
        {availableModes.map((mode) => {
          const IconComponent = getModeIcon(mode.icon);
          const isActive = currentMode === mode.id;
          
          return (
            <button
              key={mode.id}
              onClick={() => handleModeChange(mode.id)}
              disabled={!mode.enabled}
              className={`
                flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium 
                transition-all duration-200 mode-switch hover:scale-105
                ${isActive 
                  ? 'bg-purple-600 text-white mode-active shadow-lg' 
                  : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }
                ${!mode.enabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              title={mode.description}
            >
              <IconComponent className="w-4 h-4" />
              <span className="hidden sm:inline">{mode.name}</span>
            </button>
          );
        })}
        
        {/* Voice Settings Button */}
        <button
          onClick={() => setShowVoiceSettings(true)}
          className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
          title="Voice settings"
        >
          <Mic className="w-4 h-4" />
        </button>

        {/* Keyboard Shortcuts Help */}
        <KeyboardShortcutsHelp />

        {/* Settings Button */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
          title="Chat settings"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* Current Mode Indicator */}
      <div className="mt-2 text-xs text-gray-400 animate-fade-in">
        Mode: <span className="text-purple-400 font-medium animate-slide-in">{currentModeData.name}</span>
        {currentModeData.description && (
          <span className="ml-2 animate-fade-in">• {currentModeData.description}</span>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-10 p-4 settings-panel-enter">
          <h3 className="text-sm font-medium text-white mb-3">Chat Settings</h3>
          
          {/* Temperature Setting */}
          <div className="mb-4">
            <label className="block text-xs text-gray-400 mb-1">
              Temperature: {settings.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Focused</span>
              <span>Creative</span>
            </div>
          </div>

          {/* Max Tokens Setting */}
          <div className="mb-4">
            <label className="block text-xs text-gray-400 mb-1">
              Max Tokens: {settings.maxTokens}
            </label>
            <input
              type="range"
              min="100"
              max="4000"
              step="100"
              value={settings.maxTokens}
              onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Feature Toggles */}
          <div className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.enableMemory}
                onChange={(e) => handleSettingChange('enableMemory', e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-300">Enable Memory</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.enableFactChecking}
                onChange={(e) => handleSettingChange('enableFactChecking', e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-300">Enable Fact Checking</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.enableChainOfThought}
                onChange={(e) => handleSettingChange('enableChainOfThought', e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-300">Enable Chain of Thought</span>
            </label>
          </div>

          {/* Close Settings */}
          <button
            onClick={() => setShowSettings(false)}
            className="mt-4 w-full px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-md transition-colors"
          >
            Close Settings
          </button>
        </div>
      )}

      {/* Voice Settings Modal */}
      <VoiceSettings
        isOpen={showVoiceSettings}
        onClose={() => setShowVoiceSettings(false)}
      />
    </div>
  );
};

export default ChatModeSelector;