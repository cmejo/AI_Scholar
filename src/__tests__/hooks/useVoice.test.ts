import { renderHook, act } from '@testing-library/react';
import { useVoice } from '../../hooks/useVoice';
import { voiceService } from '../../services/voiceService';

// Mock the voice service
jest.mock('../../services/voiceService', () => ({
  voiceService: {
    isSupported: jest.fn(),
    getIsListening: jest.fn(),
    isSpeaking: jest.fn(),
    startListening: jest.fn(),
    stopListening: jest.fn(),
    speak: jest.fn(),
    stopSpeaking: jest.fn(),
    updateSettings: jest.fn(),
    getSettings: jest.fn(),
    cleanTextForSpeech: jest.fn(),
    testVoice: jest.fn(),
  },
}));

// Mock browser APIs
const mockSpeechRecognition = {
  start: jest.fn(),
  stop: jest.fn(),
  onresult: null,
  onerror: null,
  onend: null,
};

const mockSpeechSynthesis = {
  speak: jest.fn(),
  cancel: jest.fn(),
  speaking: false,
  getVoices: jest.fn(() => []),
};

// Mock navigator APIs
Object.defineProperty(global.navigator, 'permissions', {
  value: {
    query: jest.fn(),
  },
  writable: true,
});

Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: jest.fn(),
  },
  writable: true,
});

Object.defineProperty(global.window, 'speechSynthesis', {
  value: mockSpeechSynthesis,
  writable: true,
});

Object.defineProperty(global.window, 'SpeechRecognition', {
  value: jest.fn(() => mockSpeechRecognition),
  writable: true,
});

describe('useVoice hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementations
    (voiceService.isSupported as jest.Mock).mockReturnValue(true);
    (voiceService.getIsListening as jest.Mock).mockReturnValue(false);
    (voiceService.isSpeaking as jest.Mock).mockReturnValue(false);
    (voiceService.getSettings as jest.Mock).mockReturnValue({
      enabled: false,
      autoListen: false,
      language: 'en-US',
      voice: 'default',
      rate: 1,
      pitch: 1,
      volume: 1,
    });
    
    (navigator.permissions.query as jest.Mock).mockResolvedValue({
      state: 'prompt',
      onchange: null,
    });
  });

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useVoice());

    expect(result.current.voiceState).toEqual({
      isListening: false,
      isSpeaking: false,
      currentlySpeaking: null,
      transcriptionInProgress: false,
      error: null,
      permissions: {
        microphone: 'prompt',
        speaker: true,
      },
      isSupported: true,
    });
  });

  it('should handle unsupported browser', () => {
    (voiceService.isSupported as jest.Mock).mockReturnValue(false);

    const { result } = renderHook(() => useVoice());

    expect(result.current.voiceState.isSupported).toBe(false);
  });

  it('should start listening successfully', async () => {
    const mockTranscript = 'Hello world';
    (voiceService.startListening as jest.Mock).mockResolvedValue(mockTranscript);

    const { result } = renderHook(() => useVoice());

    let transcript: string;
    await act(async () => {
      transcript = await result.current.startListening();
    });

    expect(transcript!).toBe(mockTranscript);
    expect(voiceService.startListening).toHaveBeenCalled();
  });

  it('should handle listening errors', async () => {
    const mockError = new Error('Microphone not available');
    (voiceService.startListening as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useVoice());

    await act(async () => {
      try {
        await result.current.startListening();
      } catch (error) {
        expect(error).toBe(mockError);
      }
    });

    expect(result.current.voiceState.error).toBe('Microphone not available');
  });

  it('should stop listening', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.stopListening();
    });

    expect(voiceService.stopListening).toHaveBeenCalled();
  });

  it('should speak text successfully', async () => {
    const mockText = 'Hello world';
    (voiceService.speak as jest.Mock).mockResolvedValue(undefined);
    (voiceService.cleanTextForSpeech as jest.Mock).mockReturnValue(mockText);

    const { result } = renderHook(() => useVoice());

    await act(async () => {
      await result.current.speak(mockText);
    });

    expect(voiceService.cleanTextForSpeech).toHaveBeenCalledWith(mockText);
    expect(voiceService.speak).toHaveBeenCalledWith(mockText);
  });

  it('should handle speech synthesis errors', async () => {
    const mockError = new Error('Speech synthesis failed');
    (voiceService.speak as jest.Mock).mockRejectedValue(mockError);
    (voiceService.cleanTextForSpeech as jest.Mock).mockReturnValue('test');

    const { result } = renderHook(() => useVoice());

    await act(async () => {
      try {
        await result.current.speak('test');
      } catch (error) {
        expect(error).toBe(mockError);
      }
    });

    expect(result.current.voiceState.error).toBe('Speech synthesis failed');
  });

  it('should stop speaking', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.stopSpeaking();
    });

    expect(voiceService.stopSpeaking).toHaveBeenCalled();
  });

  it('should update settings', () => {
    const { result } = renderHook(() => useVoice());
    const newSettings = { rate: 1.5, pitch: 0.8 };

    act(() => {
      result.current.updateSettings(newSettings);
    });

    expect(voiceService.updateSettings).toHaveBeenCalledWith(newSettings);
  });

  it('should get settings', () => {
    const mockSettings = {
      enabled: true,
      autoListen: true,
      language: 'en-GB',
      voice: 'test-voice',
      rate: 1.2,
      pitch: 0.9,
      volume: 0.8,
    };
    (voiceService.getSettings as jest.Mock).mockReturnValue(mockSettings);

    const { result } = renderHook(() => useVoice());

    const settings = result.current.getSettings();
    expect(settings).toEqual(mockSettings);
  });

  it('should clear errors', () => {
    const { result } = renderHook(() => useVoice());

    // Set an error first
    act(() => {
      result.current.voiceState.error = 'Test error';
    });

    act(() => {
      result.current.clearError();
    });

    expect(result.current.voiceState.error).toBeNull();
  });

  it('should request microphone permissions', async () => {
    const mockStream = {
      getTracks: jest.fn(() => [{ stop: jest.fn() }]),
    };
    (navigator.mediaDevices.getUserMedia as jest.Mock).mockResolvedValue(mockStream);

    const { result } = renderHook(() => useVoice());

    let permissionGranted: boolean;
    await act(async () => {
      permissionGranted = await result.current.requestPermissions();
    });

    expect(permissionGranted!).toBe(true);
    expect(result.current.voiceState.permissions.microphone).toBe('granted');
  });

  it('should handle denied microphone permissions', async () => {
    const mockError = { name: 'NotAllowedError' };
    (navigator.mediaDevices.getUserMedia as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useVoice());

    let permissionGranted: boolean;
    await act(async () => {
      permissionGranted = await result.current.requestPermissions();
    });

    expect(permissionGranted!).toBe(false);
    expect(result.current.voiceState.permissions.microphone).toBe('denied');
  });

  it('should test voice functionality', async () => {
    (voiceService.testVoice as jest.Mock).mockResolvedValue(true);

    const { result } = renderHook(() => useVoice());

    let testResult: boolean;
    await act(async () => {
      testResult = await result.current.testVoice();
    });

    expect(testResult!).toBe(true);
    expect(voiceService.testVoice).toHaveBeenCalled();
  });

  it('should handle voice test failures', async () => {
    (voiceService.testVoice as jest.Mock).mockRejectedValue(new Error('Test failed'));

    const { result } = renderHook(() => useVoice());

    let testResult: boolean;
    await act(async () => {
      testResult = await result.current.testVoice();
    });

    expect(testResult!).toBe(false);
    expect(result.current.voiceState.error).toBe('Voice test failed. Please check your audio settings.');
  });
});