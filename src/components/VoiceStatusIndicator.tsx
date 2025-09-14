import React from 'react';
import { Mic, Volume2, Wifi, WifiOff } from 'lucide-react';
import '../styles/animations.css';

interface VoiceStatusIndicatorProps {
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  isConnected: boolean;
  className?: string;
}

export const VoiceStatusIndicator: React.FC<VoiceStatusIndicatorProps> = ({
  isListening,
  isSpeaking,
  isProcessing,
  isConnected,
  className = '',
}) => {
  const getStatusContent = () => {
    if (!isConnected) {
      return {
        icon: WifiOff,
        text: 'Offline',
        className: 'text-red-400',
        animation: 'animate-pulse-recording',
        waveType: 'error',
      };
    }

    if (isListening) {
      return {
        icon: Mic,
        text: 'Listening...',
        className: 'text-red-400',
        animation: 'voice-recording status-indicator',
        showWave: true,
        waveType: 'listening',
      };
    }

    if (isProcessing) {
      return {
        icon: Mic,
        text: 'Processing...',
        className: 'text-yellow-400',
        animation: 'animate-voice-processing status-indicator',
        showWave: true,
        waveType: 'processing',
      };
    }

    if (isSpeaking) {
      return {
        icon: Volume2,
        text: 'Speaking...',
        className: 'text-blue-400',
        animation: 'animate-pulse-recording status-indicator',
        showWave: true,
        waveType: 'speaking',
      };
    }

    return null;
  };

  const status = getStatusContent();

  if (!status) {
    return null;
  }

  const IconComponent = status.icon;

  return (
    <div className={`flex items-center space-x-2 voice-state-transition ${className}`}>
      {/* Status Icon with Enhanced Animation */}
      <div className={`${status.animation} ${status.className} voice-state-transition`}>
        <IconComponent className="w-4 h-4" />
      </div>

      {/* Enhanced Voice Wave Animation */}
      {status.showWave && (
        <div className={`voice-wave ${status.waveType || ''} animate-fade-in`}>
          <div className="voice-wave-bar h-1"></div>
          <div className="voice-wave-bar h-2"></div>
          <div className="voice-wave-bar h-3"></div>
          <div className="voice-wave-bar h-4"></div>
          <div className="voice-wave-bar h-3"></div>
          <div className="voice-wave-bar h-2"></div>
          <div className="voice-wave-bar h-1"></div>
        </div>
      )}

      {/* Status Text with Fade Animation */}
      <span className={`text-sm font-medium ${status.className} animate-fade-in`}>
        {status.text}
      </span>
    </div>
  );
};

export default VoiceStatusIndicator;