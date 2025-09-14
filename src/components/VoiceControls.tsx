import React, { useState, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, AlertCircle } from 'lucide-react';
import { useVoice } from '../hooks/useVoice';
import VoiceErrorBoundary from './VoiceErrorBoundary';
import VoiceStatusIndicator from './VoiceStatusIndicator';
import { retryVoiceOperation } from '../utils/retryMechanism';
import '../styles/animations.css';

interface VoiceControlsProps {
  onVoiceInput: (transcript: string) => void;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  className?: string;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  onVoiceInput,
  voiceEnabled,
  onToggleVoice,
  className = '',
}) => {
  const {
    voiceState,
    startListening,
    stopListening,
    clearError,
    requestPermissions,
  } = useVoice();

  const [isRecording, setIsRecording] = useState(false);

  const [successState, setSuccessState] = useState(false);

  const handleMicrophoneClick = useCallback(async () => {
    if (!voiceState.isSupported) {
      return;
    }

    if (voiceState.permissions.microphone === 'denied') {
      await requestPermissions();
      return;
    }

    if (voiceState.permissions.microphone === 'prompt') {
      const granted = await requestPermissions();
      if (!granted) return;
    }

    if (isRecording) {
      stopListening();
      setIsRecording(false);
    } else {
      try {
        setIsRecording(true);
        
        const transcript = await retryVoiceOperation(
          () => startListening(),
          'recognition'
        );
        
        if (transcript.trim()) {
          // Show success state briefly
          setSuccessState(true);
          setTimeout(() => setSuccessState(false), 1000);
          
          onVoiceInput(transcript);
        }
      } catch (error) {
        console.error('Voice input failed after retries:', error);
        // Error will be handled by the error boundary
      } finally {
        setIsRecording(false);
      }
    }
  }, [
    voiceState.isSupported,
    voiceState.permissions.microphone,
    isRecording,
    startListening,
    stopListening,
    requestPermissions,
    onVoiceInput,
  ]);

  const getMicrophoneButtonState = () => {
    if (!voiceState.isSupported) {
      return {
        icon: MicOff,
        className: 'bg-gray-600 cursor-not-allowed voice-disabled voice-state-transition',
        title: 'Voice input not supported in this browser',
        disabled: true,
      };
    }

    if (voiceState.permissions.microphone === 'denied') {
      return {
        icon: MicOff,
        className: 'bg-red-600 hover:bg-red-700 voice-state-transition permission-prompt voice-button-hover',
        title: 'Click to enable microphone permissions',
        disabled: false,
      };
    }

    if (voiceState.transcriptionInProgress) {
      return {
        icon: Mic,
        className: 'bg-yellow-600 hover:bg-yellow-700 voice-processing voice-state-transition',
        title: 'Processing speech...',
        disabled: true,
      };
    }

    if (isRecording || voiceState.isListening) {
      return {
        icon: Mic,
        className: 'bg-red-600 hover:bg-red-700 voice-recording voice-state-transition',
        title: 'Click to stop recording',
        disabled: false,
      };
    }

    return {
      icon: Mic,
      className: 'bg-purple-600 hover:bg-purple-700 voice-state-transition voice-button-hover',
      title: 'Click to start voice input',
      disabled: false,
    };
  };

  const micButtonState = getMicrophoneButtonState();

  if (!voiceEnabled) {
    return null;
  }

  return (
    <VoiceErrorBoundary>
      <div className={`flex items-center space-x-2 ${className}`}>
        {/* Voice Toggle Button */}
        <button
          onClick={onToggleVoice}
          className={`p-2 rounded-lg transition-all duration-200 hover:scale-105 ${
            voiceEnabled 
              ? 'bg-purple-600 hover:bg-purple-700 animate-fade-in' 
              : 'bg-gray-700 hover:bg-gray-600'
          }`}
          title={voiceEnabled ? 'Disable voice features' : 'Enable voice features'}
        >
          {voiceEnabled ? (
            <Volume2 className="w-4 h-4 text-white" />
          ) : (
            <VolumeX className="w-4 h-4 text-gray-400" />
          )}
        </button>

        {/* Microphone Button */}
        <button
          onClick={handleMicrophoneClick}
          disabled={micButtonState.disabled}
          className={`p-2 rounded-lg ${micButtonState.className} ${
            successState ? 'voice-success' : ''
          } ${isRecording ? 'voice-button-active' : ''}`}
          title={micButtonState.title}
        >
          <micButtonState.icon className="w-4 h-4 text-white" />
        </button>

        {/* Enhanced Voice Status Indicator */}
        <VoiceStatusIndicator
          isListening={voiceState.isListening || isRecording}
          isSpeaking={voiceState.isSpeaking}
          isProcessing={voiceState.transcriptionInProgress}
          isConnected={navigator.onLine}
        />

        {/* Enhanced Error Display */}
        {voiceState.error && (
          <div className="flex items-center space-x-1 text-sm text-red-400 error-bounce">
            <AlertCircle className="w-4 h-4 animate-pulse-recording" />
            <span className="max-w-xs truncate">{voiceState.error}</span>
            <button
              onClick={clearError}
              className="text-red-300 hover:text-red-200 ml-1 transition-colors duration-200 hover:scale-110"
              title="Clear error"
            >
              ×
            </button>
          </div>
        )}
      </div>
    </VoiceErrorBoundary>
  );
};

export default VoiceControls;