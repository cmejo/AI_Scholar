import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Settings, Play, Pause } from 'lucide-react';
import { voiceService } from '../services/voiceService';
import { VoiceConfig } from '../types';

interface VoiceInterfaceProps {
  onVoiceQuery: (query: string) => Promise<string>;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  onVoiceQuery,
  enabled,
  onToggle
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [config, setConfig] = useState<VoiceConfig>({
    enabled,
    language: 'en-US',
    voice: 'default',
    speed: 1.0,
    pitch: 1.0
  });
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  useEffect(() => {
    // Load available voices
    const loadVoices = () => {
      const voices = voiceService.getAvailableVoices();
      setAvailableVoices(voices);
    };

    loadVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  useEffect(() => {
    voiceService.configure(config);
  }, [config]);

  const handleStartListening = async () => {
    if (!enabled) return;

    try {
      setIsListening(true);
      setTranscript('');
      
      const result = await voiceService.startListening();
      setTranscript(result);
      
      // Process the voice query
      const response = await onVoiceQuery(result);
      
      // Speak the response
      setIsSpeaking(true);
      await voiceService.speak(response);
      setIsSpeaking(false);
      
    } catch (error) {
      console.error('Voice interaction error:', error);
      setIsListening(false);
      setIsSpeaking(false);
    } finally {
      setIsListening(false);
    }
  };

  const handleStopListening = () => {
    voiceService.stopListening();
    setIsListening(false);
  };

  const handleConfigChange = (key: keyof VoiceConfig, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    
    if (key === 'enabled') {
      onToggle(value);
    }
  };

  const support = voiceService.isSupported();

  if (!support.speechRecognition && !support.speechSynthesis) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 text-center">
        <MicOff className="text-gray-500 mx-auto mb-2" size={24} />
        <p className="text-gray-400 text-sm">Voice features not supported in this browser</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      {/* Voice Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={enabled ? (isListening ? handleStopListening : handleStartListening) : undefined}
            disabled={!enabled || isSpeaking}
            className={`p-3 rounded-full transition-all duration-300 ${
              enabled
                ? isListening
                  ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                  : 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-600 cursor-not-allowed'
            }`}
          >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
          
          <div className="flex flex-col">
            <span className="text-white font-medium">
              {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Voice Assistant'}
            </span>
            <span className="text-gray-400 text-sm">
              {enabled ? 'Click to start voice interaction' : 'Voice disabled'}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleConfigChange('enabled', !enabled)}
            className={`p-2 rounded-lg transition-colors ${
              enabled ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-gray-600 hover:bg-gray-700'
            }`}
          >
            {enabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
          
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>

      {/* Transcript Display */}
      {transcript && (
        <div className="mb-4 p-3 bg-gray-700 rounded-lg">
          <div className="text-sm text-gray-400 mb-1">You said:</div>
          <div className="text-white">{transcript}</div>
        </div>
      )}

      {/* Voice Settings */}
      {showSettings && (
        <div className="border-t border-gray-700 pt-4 space-y-4">
          <h4 className="text-white font-medium">Voice Settings</h4>
          
          {/* Language Selection */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Language</label>
            <select
              value={config.language}
              onChange={(e) => handleConfigChange('language', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="en-US">English (US)</option>
              <option value="en-GB">English (UK)</option>
              <option value="es-ES">Spanish</option>
              <option value="fr-FR">French</option>
              <option value="de-DE">German</option>
              <option value="it-IT">Italian</option>
              <option value="pt-BR">Portuguese</option>
              <option value="ja-JP">Japanese</option>
              <option value="ko-KR">Korean</option>
              <option value="zh-CN">Chinese (Simplified)</option>
            </select>
          </div>

          {/* Voice Selection */}
          {availableVoices.length > 0 && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">Voice</label>
              <select
                value={config.voice}
                onChange={(e) => handleConfigChange('voice', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="default">Default</option>
                {availableVoices
                  .filter(voice => voice.lang.startsWith(config.language.split('-')[0]))
                  .map((voice, index) => (
                    <option key={index} value={voice.name}>
                      {voice.name} ({voice.lang})
                    </option>
                  ))}
              </select>
            </div>
          )}

          {/* Speed Control */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Speech Speed: {config.speed.toFixed(1)}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={config.speed}
              onChange={(e) => handleConfigChange('speed', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Pitch Control */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Pitch: {config.pitch.toFixed(1)}
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={config.pitch}
              onChange={(e) => handleConfigChange('pitch', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Test Voice */}
          <button
            onClick={() => voiceService.speak('This is a test of the voice synthesis system.')}
            disabled={isSpeaking}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            {isSpeaking ? <Pause size={16} /> : <Play size={16} />}
            <span>{isSpeaking ? 'Speaking...' : 'Test Voice'}</span>
          </button>
        </div>
      )}

      {/* Voice Commands Help */}
      {enabled && (
        <div className="mt-4 p-3 bg-gray-700 rounded-lg">
          <div className="text-sm text-gray-400 mb-2">Voice Commands:</div>
          <div className="text-xs text-gray-500 space-y-1">
            <div>• "Search for [topic]" - Search documents</div>
            <div>• "Show analytics" - Open analytics dashboard</div>
            <div>• "Upload document" - Open document upload</div>
            <div>• "Help" - Get assistance</div>
          </div>
        </div>
      )}
    </div>
  );
};