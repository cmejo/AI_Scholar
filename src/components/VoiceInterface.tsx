import React, { useState, useEffect, useRef, useCallback } from 'react';
import voiceService, { VoiceConfig, TranscriptionResult } from '../services/voiceService';

interface VoiceInterfaceProps {
  onTranscription?: (result: TranscriptionResult) => void;
  onError?: (error: string) => void;
  className?: string;
  autoStart?: boolean;
  language?: string;
}

interface VoiceState {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  currentTranscription: string;
  confidence: number;
  error: string | null;
  isSupported: boolean;
}

const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  onTranscription,
  onError,
  className = '',
  autoStart = false,
  language = 'en-US'
}) => {
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
    currentTranscription: '',
    confidence: 0,
    error: null,
    isSupported: false
  });

  const [voiceConfig, setVoiceConfig] = useState<VoiceConfig>({
    language: language,
    rate: 1,
    pitch: 1,
    volume: 1
  });

  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const transcriptionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const recognitionRef = useRef<boolean>(false);

  // Initialize voice service and check support
  useEffect(() => {
    const initializeVoice = async () => {
      const isSupported = voiceService.isVoiceSupported();
      setVoiceState(prev => ({ ...prev, isSupported }));

      if (isSupported) {
        // Get available voices
        const voices = voiceService.getAvailableVoices();
        setAvailableVoices(voices);

        // Set up event listeners
        voiceService.onSpeechResult(handleSpeechResult);
        voiceService.onSpeechError(handleSpeechError);

        // Auto-start if requested
        if (autoStart) {
          startListening();
        }
      }
    };

    initializeVoice();

    // Cleanup on unmount
    return () => {
      voiceService.cleanup();
      if (transcriptionTimeoutRef.current) {
        clearTimeout(transcriptionTimeoutRef.current);
      }
    };
  }, [autoStart]);

  // Handle speech recognition results
  const handleSpeechResult = useCallback((result: TranscriptionResult) => {
    setVoiceState(prev => ({
      ...prev,
      currentTranscription: result.text,
      confidence: result.confidence,
      isProcessing: false
    }));

    // Clear previous timeout
    if (transcriptionTimeoutRef.current) {
      clearTimeout(transcriptionTimeoutRef.current);
    }

    // Set timeout to finalize transcription
    transcriptionTimeoutRef.current = setTimeout(() => {
      if (onTranscription) {
        onTranscription(result);
      }
    }, 1000); // Wait 1 second for more speech

  }, [onTranscription]);

  // Handle speech recognition errors
  const handleSpeechError = useCallback((error: string) => {
    setVoiceState(prev => ({
      ...prev,
      error,
      isListening: false,
      isProcessing: false
    }));

    if (onError) {
      onError(error);
    }
  }, [onError]);

  // Start listening for speech
  const startListening = useCallback(async () => {
    if (!voiceState.isSupported || voiceState.isListening) {
      return;
    }

    try {
      setVoiceState(prev => ({
        ...prev,
        isListening: true,
        isProcessing: true,
        error: null,
        currentTranscription: ''
      }));

      await voiceService.startSpeechRecognition({
        continuous: true,
        interimResults: true,
        language: voiceConfig.language
      });

      recognitionRef.current = true;
    } catch (error) {
      handleSpeechError(error instanceof Error ? error.message : 'Failed to start listening');
    }
  }, [voiceState.isSupported, voiceState.isListening, voiceConfig.language]);

  // Stop listening for speech
  const stopListening = useCallback(() => {
    if (!voiceState.isListening) {
      return;
    }

    voiceService.stopSpeechRecognition();
    recognitionRef.current = false;

    setVoiceState(prev => ({
      ...prev,
      isListening: false,
      isProcessing: false
    }));

    // Clear transcription timeout
    if (transcriptionTimeoutRef.current) {
      clearTimeout(transcriptionTimeoutRef.current);
      transcriptionTimeoutRef.current = null;
    }
  }, [voiceState.isListening]);

  // Toggle listening state
  const toggleListening = useCallback(() => {
    if (voiceState.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [voiceState.isListening, startListening, stopListening]);

  // Speak text using TTS
  const speakText = useCallback(async (text: string) => {
    if (!voiceState.isSupported || voiceState.isSpeaking) {
      return;
    }

    try {
      setVoiceState(prev => ({ ...prev, isSpeaking: true, error: null }));
      
      await voiceService.textToSpeech(text, voiceConfig);
      
      setVoiceState(prev => ({ ...prev, isSpeaking: false }));
    } catch (error) {
      setVoiceState(prev => ({
        ...prev,
        isSpeaking: false,
        error: error instanceof Error ? error.message : 'Failed to speak text'
      }));
    }
  }, [voiceState.isSupported, voiceState.isSpeaking, voiceConfig]);

  // Update voice configuration
  const updateVoiceConfig = useCallback((updates: Partial<VoiceConfig>) => {
    setVoiceConfig(prev => ({ ...prev, ...updates }));
  }, []);

  // Get microphone permission status
  const getMicrophonePermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      return false;
    }
  }, []);

  // Request microphone permission
  const requestMicrophonePermission = useCallback(async () => {
    const hasPermission = await getMicrophonePermission();
    if (!hasPermission) {
      setVoiceState(prev => ({
        ...prev,
        error: 'Microphone permission required for voice input'
      }));
    }
    return hasPermission;
  }, [getMicrophonePermission]);

  if (!voiceState.isSupported) {
    return (
      <div className={`voice-interface voice-interface--unsupported ${className}`}>
        <div className="voice-interface__message">
          <p>Voice features are not supported in this browser.</p>
          <p>Please use a modern browser with Web Speech API support.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`voice-interface ${className}`}>
      {/* Main Voice Controls */}
      <div className="voice-interface__controls">
        <button
          className={`voice-interface__mic-button ${
            voiceState.isListening ? 'voice-interface__mic-button--active' : ''
          } ${voiceState.isProcessing ? 'voice-interface__mic-button--processing' : ''}`}
          onClick={toggleListening}
          disabled={voiceState.isProcessing}
          aria-label={voiceState.isListening ? 'Stop listening' : 'Start listening'}
        >
          <div className="voice-interface__mic-icon">
            {voiceState.isListening ? (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            )}
          </div>
          {voiceState.isProcessing && (
            <div className="voice-interface__processing-indicator">
              <div className="voice-interface__spinner"></div>
            </div>
          )}
        </button>

        <div className="voice-interface__status">
          {voiceState.isListening && (
            <span className="voice-interface__status-text voice-interface__status-text--listening">
              Listening...
            </span>
          )}
          {voiceState.isProcessing && !voiceState.isListening && (
            <span className="voice-interface__status-text voice-interface__status-text--processing">
              Processing...
            </span>
          )}
          {voiceState.isSpeaking && (
            <span className="voice-interface__status-text voice-interface__status-text--speaking">
              Speaking...
            </span>
          )}
          {!voiceState.isListening && !voiceState.isProcessing && !voiceState.isSpeaking && (
            <span className="voice-interface__status-text">
              Click to start voice input
            </span>
          )}
        </div>
      </div>

      {/* Current Transcription */}
      {voiceState.currentTranscription && (
        <div className="voice-interface__transcription">
          <div className="voice-interface__transcription-text">
            {voiceState.currentTranscription}
          </div>
          {voiceState.confidence > 0 && (
            <div className="voice-interface__confidence">
              Confidence: {Math.round(voiceState.confidence * 100)}%
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {voiceState.error && (
        <div className="voice-interface__error">
          <div className="voice-interface__error-message">
            {voiceState.error}
          </div>
          <button
            className="voice-interface__error-dismiss"
            onClick={() => setVoiceState(prev => ({ ...prev, error: null }))}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Voice Configuration */}
      <div className="voice-interface__config">
        <div className="voice-interface__config-section">
          <label className="voice-interface__config-label">
            Language:
            <select
              value={voiceConfig.language}
              onChange={(e) => updateVoiceConfig({ language: e.target.value })}
              className="voice-interface__config-select"
            >
              <option value="en-US">English (US)</option>
              <option value="en-GB">English (UK)</option>
              <option value="es-ES">Spanish</option>
              <option value="fr-FR">French</option>
              <option value="de-DE">German</option>
              <option value="it-IT">Italian</option>
              <option value="pt-BR">Portuguese (Brazil)</option>
              <option value="ja-JP">Japanese</option>
              <option value="ko-KR">Korean</option>
              <option value="zh-CN">Chinese (Simplified)</option>
            </select>
          </label>
        </div>

        {availableVoices.length > 0 && (
          <div className="voice-interface__config-section">
            <label className="voice-interface__config-label">
              Voice:
              <select
                value={voiceConfig.voice || ''}
                onChange={(e) => updateVoiceConfig({ voice: e.target.value })}
                className="voice-interface__config-select"
              >
                <option value="">Default</option>
                {availableVoices.map((voice) => (
                  <option key={voice.name} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}

        <div className="voice-interface__config-section">
          <label className="voice-interface__config-label">
            Speech Rate:
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={voiceConfig.rate || 1}
              onChange={(e) => updateVoiceConfig({ rate: parseFloat(e.target.value) })}
              className="voice-interface__config-range"
            />
            <span className="voice-interface__config-value">
              {voiceConfig.rate?.toFixed(1)}x
            </span>
          </label>
        </div>

        <div className="voice-interface__config-section">
          <label className="voice-interface__config-label">
            Volume:
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={voiceConfig.volume || 1}
              onChange={(e) => updateVoiceConfig({ volume: parseFloat(e.target.value) })}
              className="voice-interface__config-range"
            />
            <span className="voice-interface__config-value">
              {Math.round((voiceConfig.volume || 1) * 100)}%
            </span>
          </label>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="voice-interface__actions">
        <button
          className="voice-interface__action-button"
          onClick={() => requestMicrophonePermission()}
          disabled={voiceState.isProcessing}
        >
          Test Microphone
        </button>
        
        <button
          className="voice-interface__action-button"
          onClick={() => speakText('Voice interface is working correctly.')}
          disabled={voiceState.isSpeaking || voiceState.isProcessing}
        >
          Test Speaker
        </button>
      </div>
    </div>
  );
};

export default VoiceInterface;