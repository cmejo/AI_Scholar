import { useState, useEffect, useCallback, useRef } from 'react';
import { voiceService } from '../services/voiceService';
import { VoiceSettings } from '../types/chat';
import { 
  getBrowserInfo, 
  getVoiceCompatibilityMessage, 
  checkMicrophonePermissions 
} from '../utils/browserCompatibility';

interface VoiceState {
  isListening: boolean;
  isSpeaking: boolean;
  currentlySpeaking: string | null;
  transcriptionInProgress: boolean;
  error: string | null;
  permissions: {
    microphone: 'granted' | 'denied' | 'prompt';
    speaker: boolean;
  };
  isSupported: boolean;
}

interface UseVoiceReturn {
  voiceState: VoiceState;
  startListening: () => Promise<string>;
  stopListening: () => void;
  speak: (text: string) => Promise<void>;
  stopSpeaking: () => void;
  updateSettings: (settings: Partial<VoiceSettings>) => void;
  getSettings: () => VoiceSettings;
  clearError: () => void;
  requestPermissions: () => Promise<boolean>;
  testVoice: () => Promise<boolean>;
}

export const useVoice = (): UseVoiceReturn => {
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isListening: false,
    isSpeaking: false,
    currentlySpeaking: null,
    transcriptionInProgress: false,
    error: null,
    permissions: {
      microphone: 'prompt',
      speaker: true,
    },
    isSupported: false,
  });

  const currentSpeechRef = useRef<string | null>(null);

  // Initialize voice service and check support
  useEffect(() => {
    const initializeVoice = async () => {
      const browserInfo = getBrowserInfo();
      const isSupported = voiceService.isSupported();
      const compatibilityMessage = getVoiceCompatibilityMessage(browserInfo);
      
      setVoiceState(prev => ({
        ...prev,
        isSupported,
        permissions: {
          ...prev.permissions,
          speaker: browserInfo.capabilities.speechSynthesis,
        },
        error: compatibilityMessage
      }));

      // Check microphone permissions if supported
      if (isSupported && browserInfo.capabilities.permissions) {
        try {
          const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
          setVoiceState(prev => ({
            ...prev,
            permissions: {
              ...prev.permissions,
              microphone: permission.state as 'granted' | 'denied' | 'prompt',
            }
          }));

          // Listen for permission changes
          permission.onchange = () => {
            setVoiceState(prev => ({
              ...prev,
              permissions: {
                ...prev.permissions,
                microphone: permission.state as 'granted' | 'denied' | 'prompt',
              }
            }));
          };
        } catch (error) {
          console.warn('Could not check microphone permissions:', error);
        }
      }
    };

    initializeVoice();
  }, []);

  // Monitor voice service state
  useEffect(() => {
    const checkVoiceState = () => {
      setVoiceState(prev => ({
        ...prev,
        isListening: voiceService.getIsListening(),
        isSpeaking: voiceService.isSpeaking(),
      }));
    };

    const interval = setInterval(checkVoiceState, 100);
    return () => clearInterval(interval);
  }, []);

  const startListening = useCallback(async (): Promise<string> => {
    if (!voiceState.isSupported) {
      throw new Error('Speech recognition is not supported in this browser');
    }

    setVoiceState(prev => ({ ...prev, error: null, transcriptionInProgress: true }));

    try {
      const transcript = await voiceService.startListening();
      setVoiceState(prev => ({ 
        ...prev, 
        transcriptionInProgress: false,
        isListening: false 
      }));
      return transcript;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Speech recognition failed';
      setVoiceState(prev => ({ 
        ...prev, 
        error: errorMessage,
        transcriptionInProgress: false,
        isListening: false 
      }));
      throw error;
    }
  }, [voiceState.isSupported]);

  const stopListening = useCallback(() => {
    voiceService.stopListening();
    setVoiceState(prev => ({ 
      ...prev, 
      isListening: false,
      transcriptionInProgress: false 
    }));
  }, []);

  const speak = useCallback(async (text: string): Promise<void> => {
    if (!voiceState.permissions.speaker) {
      throw new Error('Speech synthesis is not available');
    }

    // Stop any current speech
    if (currentSpeechRef.current) {
      voiceService.stopSpeaking();
    }

    currentSpeechRef.current = text;
    setVoiceState(prev => ({ 
      ...prev, 
      currentlySpeaking: text,
      isSpeaking: true,
      error: null 
    }));

    try {
      const cleanText = voiceService.cleanTextForSpeech(text);
      await voiceService.speak(cleanText);
      
      // Only clear if this is still the current speech
      if (currentSpeechRef.current === text) {
        setVoiceState(prev => ({ 
          ...prev, 
          currentlySpeaking: null,
          isSpeaking: false 
        }));
        currentSpeechRef.current = null;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Speech synthesis failed';
      setVoiceState(prev => ({ 
        ...prev, 
        error: errorMessage,
        currentlySpeaking: null,
        isSpeaking: false 
      }));
      currentSpeechRef.current = null;
      throw error;
    }
  }, [voiceState.permissions.speaker]);

  const stopSpeaking = useCallback(() => {
    voiceService.stopSpeaking();
    setVoiceState(prev => ({ 
      ...prev, 
      currentlySpeaking: null,
      isSpeaking: false 
    }));
    currentSpeechRef.current = null;
  }, []);

  const updateSettings = useCallback((settings: Partial<VoiceSettings>) => {
    voiceService.updateSettings(settings);
  }, []);

  const getSettings = useCallback(() => {
    return voiceService.getSettings();
  }, []);

  const clearError = useCallback(() => {
    setVoiceState(prev => ({ ...prev, error: null }));
  }, []);

  const requestPermissions = useCallback(async (): Promise<boolean> => {
    try {
      const permissionResult = await checkMicrophonePermissions();
      
      if (permissionResult.granted) {
        setVoiceState(prev => ({
          ...prev,
          permissions: {
            ...prev.permissions,
            microphone: 'granted',
          },
          error: null
        }));
        return true;
      } else {
        setVoiceState(prev => ({
          ...prev,
          permissions: {
            ...prev.permissions,
            microphone: 'denied',
          },
          error: permissionResult.error || 'Microphone access denied.'
        }));
        return false;
      }
    } catch (error) {
      setVoiceState(prev => ({
        ...prev,
        permissions: {
          ...prev.permissions,
          microphone: 'denied',
        },
        error: 'Failed to request microphone permissions.'
      }));
      return false;
    }
  }, []);

  const testVoice = useCallback(async (): Promise<boolean> => {
    try {
      await voiceService.testVoice();
      return true;
    } catch (error) {
      setVoiceState(prev => ({
        ...prev,
        error: 'Voice test failed. Please check your audio settings.'
      }));
      return false;
    }
  }, []);

  return {
    voiceState,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    updateSettings,
    getSettings,
    clearError,
    requestPermissions,
    testVoice,
  };
};