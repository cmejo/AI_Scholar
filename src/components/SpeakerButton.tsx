import React, { useState, useCallback } from 'react';
import { Volume2, VolumeX, Square } from 'lucide-react';
import { useVoice } from '../hooks/useVoice';

interface SpeakerButtonProps {
  text: string;
  messageId: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const SpeakerButton: React.FC<SpeakerButtonProps> = ({
  text,
  messageId,
  className = '',
  size = 'sm',
}) => {
  const { voiceState, speak, stopSpeaking } = useVoice();
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sizeClasses = {
    sm: 'w-4 h-4 p-1',
    md: 'w-5 h-5 p-1.5',
    lg: 'w-6 h-6 p-2',
  };

  const [isSuccess, setIsSuccess] = useState(false);

  const handleSpeakClick = useCallback(async () => {
    if (!voiceState.permissions.speaker) {
      setError('Speech synthesis not available');
      return;
    }

    if (isPlaying) {
      stopSpeaking();
      setIsPlaying(false);
      return;
    }

    try {
      setError(null);
      setIsPlaying(true);
      await speak(text);
      
      // Show success state briefly
      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 800);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Speech failed';
      setError(errorMessage);
      console.error('Text-to-speech error:', err);
    } finally {
      setIsPlaying(false);
    }
  }, [text, speak, stopSpeaking, isPlaying, voiceState.permissions.speaker]);

  // Update playing state based on voice service state
  React.useEffect(() => {
    const isCurrentlyPlaying = voiceState.isSpeaking && voiceState.currentlySpeaking === text;
    setIsPlaying(isCurrentlyPlaying);
  }, [voiceState.isSpeaking, voiceState.currentlySpeaking, text]);

  if (!voiceState.permissions.speaker) {
    return null;
  }

  const getButtonContent = () => {
    if (isSuccess) {
      return {
        icon: Volume2,
        title: 'Speech completed',
        className: 'text-green-400 animate-success-bounce',
      };
    }

    if (isPlaying) {
      return {
        icon: Square,
        title: 'Stop speaking',
        className: 'text-red-400 hover:text-red-300 animate-pulse-recording',
      };
    }

    if (error) {
      return {
        icon: VolumeX,
        title: `Speech error: ${error}`,
        className: 'text-gray-500 hover:text-gray-400 error-bounce',
      };
    }

    return {
      icon: Volume2,
      title: 'Speak this message',
      className: 'text-gray-400 hover:text-white voice-button-hover',
    };
  };

  const buttonContent = getButtonContent();

  return (
    <button
      onClick={handleSpeakClick}
      className={`
        ${sizeClasses[size]} 
        ${buttonContent.className} 
        voice-state-transition rounded 
        ${className}
        ${isPlaying ? 'voice-button-active' : ''}
      `}
      title={buttonContent.title}
      disabled={!voiceState.permissions.speaker}
    >
      <buttonContent.icon className="w-full h-full" />
    </button>
  );
};

export default SpeakerButton;