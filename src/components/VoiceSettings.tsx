import React, { useState, useEffect, useCallback } from 'react';
import { Settings, Volume2, Mic, TestTube, Check, X } from 'lucide-react';
import { VoiceSettings as VoiceSettingsType } from '../types/chat';
import { useVoice } from '../hooks/useVoice';

interface VoiceSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export const VoiceSettings: React.FC<VoiceSettingsProps> = ({
  isOpen,
  onClose,
  className = '',
}) => {
  const { updateSettings, getSettings, testVoice, voiceState } = useVoice();
  const [settings, setSettings] = useState<VoiceSettingsType>(getSettings());
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [isTestingVoice, setIsTestingVoice] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis?.getVoices() || [];
      setAvailableVoices(voices);
    };

    loadVoices();
    
    // Some browsers load voices asynchronously
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  // Update local settings when voice settings change
  useEffect(() => {
    setSettings(getSettings());
  }, [getSettings]);

  const handleSettingChange = useCallback((key: keyof VoiceSettingsType, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    updateSettings(newSettings);
  }, [settings, updateSettings]);

  const handleTestVoice = useCallback(async () => {
    setIsTestingVoice(true);
    setTestResult(null);

    try {
      const success = await testVoice();
      setTestResult(success ? 'success' : 'error');
    } catch (error) {
      setTestResult('error');
    } finally {
      setIsTestingVoice(false);
    }

    // Clear test result after 3 seconds
    setTimeout(() => setTestResult(null), 3000);
  }, [testVoice]);

  const getLanguageOptions = () => [
    { code: 'en-US', name: 'English (US)' },
    { code: 'en-GB', name: 'English (UK)' },
    { code: 'es-ES', name: 'Spanish (Spain)' },
    { code: 'es-MX', name: 'Spanish (Mexico)' },
    { code: 'fr-FR', name: 'French (France)' },
    { code: 'de-DE', name: 'German (Germany)' },
    { code: 'it-IT', name: 'Italian (Italy)' },
    { code: 'pt-BR', name: 'Portuguese (Brazil)' },
    { code: 'ja-JP', name: 'Japanese (Japan)' },
    { code: 'ko-KR', name: 'Korean (Korea)' },
    { code: 'zh-CN', name: 'Chinese (Simplified)' },
  ];

  if (!isOpen) return null;

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 ${className}`}>
      <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-medium text-white">Voice Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Voice Enable Toggle */}
          <div className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.enabled}
                onChange={(e) => handleSettingChange('enabled', e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-300">Enable Voice Features</span>
            </label>
          </div>

          {settings.enabled && (
            <>
              {/* Auto Listen */}
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.autoListen}
                    onChange={(e) => handleSettingChange('autoListen', e.target.checked)}
                    className="rounded bg-gray-700 border-gray-600 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm text-gray-300">Auto-listen after responses</span>
                </label>
              </div>

              {/* Language Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  <Mic className="w-4 h-4 inline mr-1" />
                  Speech Recognition Language
                </label>
                <select
                  value={settings.language}
                  onChange={(e) => handleSettingChange('language', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {getLanguageOptions().map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Voice Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  <Volume2 className="w-4 h-4 inline mr-1" />
                  Text-to-Speech Voice
                </label>
                <select
                  value={settings.voice}
                  onChange={(e) => handleSettingChange('voice', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="default">Default System Voice</option>
                  {availableVoices.map((voice, index) => (
                    <option key={index} value={voice.name}>
                      {voice.name} ({voice.lang})
                    </option>
                  ))}
                </select>
              </div>

              {/* Speech Rate */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Speech Rate: {settings.rate.toFixed(1)}x
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={settings.rate}
                  onChange={(e) => handleSettingChange('rate', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Slow</span>
                  <span>Normal</span>
                  <span>Fast</span>
                </div>
              </div>

              {/* Speech Pitch */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Speech Pitch: {settings.pitch.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={settings.pitch}
                  onChange={(e) => handleSettingChange('pitch', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Low</span>
                  <span>Normal</span>
                  <span>High</span>
                </div>
              </div>

              {/* Speech Volume */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Speech Volume: {Math.round(settings.volume * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.volume}
                  onChange={(e) => handleSettingChange('volume', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              {/* Test Voice Button */}
              <div className="space-y-2">
                <button
                  onClick={handleTestVoice}
                  disabled={isTestingVoice || !voiceState.permissions.speaker}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-md transition-colors"
                >
                  {isTestingVoice ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Testing...</span>
                    </>
                  ) : (
                    <>
                      <TestTube className="w-4 h-4" />
                      <span>Test Voice Settings</span>
                    </>
                  )}
                </button>

                {/* Test Result */}
                {testResult && (
                  <div className={`flex items-center space-x-2 text-sm ${
                    testResult === 'success' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {testResult === 'success' ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <X className="w-4 h-4" />
                    )}
                    <span>
                      {testResult === 'success' 
                        ? 'Voice test successful!' 
                        : 'Voice test failed. Check your audio settings.'
                      }
                    </span>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Voice Status Info */}
          <div className="bg-gray-900/50 rounded-md p-3 space-y-2">
            <h4 className="text-sm font-medium text-gray-300">Voice Status</h4>
            <div className="space-y-1 text-xs text-gray-400">
              <div className="flex justify-between">
                <span>Speech Recognition:</span>
                <span className={voiceState.isSupported ? 'text-green-400' : 'text-red-400'}>
                  {voiceState.isSupported ? 'Supported' : 'Not Supported'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Text-to-Speech:</span>
                <span className={voiceState.permissions.speaker ? 'text-green-400' : 'text-red-400'}>
                  {voiceState.permissions.speaker ? 'Available' : 'Not Available'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Microphone:</span>
                <span className={
                  voiceState.permissions.microphone === 'granted' ? 'text-green-400' :
                  voiceState.permissions.microphone === 'denied' ? 'text-red-400' : 'text-yellow-400'
                }>
                  {voiceState.permissions.microphone === 'granted' ? 'Granted' :
                   voiceState.permissions.microphone === 'denied' ? 'Denied' : 'Not Requested'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-2 p-4 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceSettings;