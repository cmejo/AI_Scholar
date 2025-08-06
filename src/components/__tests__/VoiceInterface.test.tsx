import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import VoiceInterface from '../VoiceInterface';
import voiceService from '../../services/voiceService';

// Mock the voice service
vi.mock('../../services/voiceService', () => ({
  default: {
    isVoiceSupported: vi.fn(),
    isSpeechRecognitionSupported: vi.fn(),
    isTextToSpeechSupported: vi.fn(),
    getAvailableVoices: vi.fn(),
    startSpeechRecognition: vi.fn(),
    stopSpeechRecognition: vi.fn(),
    speechToText: vi.fn(),
    textToSpeech: vi.fn(),
    onSpeechResult: vi.fn(),
    onSpeechError: vi.fn(),
    cleanup: vi.fn(),
  }
}));

// Mock Web Speech API
const mockSpeechRecognition = {
  start: vi.fn(),
  stop: vi.fn(),
  abort: vi.fn(),
  continuous: false,
  interimResults: false,
  lang: 'en-US',
  maxAlternatives: 1,
  onresult: null,
  onerror: null,
  onstart: null,
  onend: null,
};

const mockSpeechSynthesis = {
  speak: vi.fn(),
  cancel: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  getVoices: vi.fn(() => [
    { name: 'Test Voice 1', lang: 'en-US', voiceURI: 'test1' },
    { name: 'Test Voice 2', lang: 'en-GB', voiceURI: 'test2' },
  ]),
  speaking: false,
  pending: false,
  paused: false,
};

// Mock navigator.mediaDevices
const mockMediaDevices = {
  getUserMedia: vi.fn(() => 
    Promise.resolve({
      getTracks: () => [{ stop: vi.fn() }]
    })
  ),
};

Object.defineProperty(global, 'SpeechRecognition', {
  writable: true,
  value: vi.fn(() => mockSpeechRecognition),
});

Object.defineProperty(global, 'webkitSpeechRecognition', {
  writable: true,
  value: vi.fn(() => mockSpeechRecognition),
});

Object.defineProperty(global, 'speechSynthesis', {
  writable: true,
  value: mockSpeechSynthesis,
});

Object.defineProperty(global.navigator, 'mediaDevices', {
  writable: true,
  value: mockMediaDevices,
});

// Mock AudioContext
global.AudioContext = vi.fn(() => ({
  createBufferSource: vi.fn(),
  createBiquadFilter: vi.fn(),
  decodeAudioData: vi.fn(),
  close: vi.fn(),
  state: 'running',
}));

global.webkitAudioContext = global.AudioContext;

// Mock OfflineAudioContext
global.OfflineAudioContext = vi.fn(() => ({
  createBufferSource: vi.fn(),
  createBiquadFilter: vi.fn(),
  startRendering: vi.fn(() => Promise.resolve({})),
  destination: {},
}));

describe('VoiceInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (voiceService.isVoiceSupported as any).mockReturnValue(true);
    (voiceService.isSpeechRecognitionSupported as any).mockReturnValue(true);
    (voiceService.isTextToSpeechSupported as any).mockReturnValue(true);
    (voiceService.getAvailableVoices as any).mockReturnValue([
      { name: 'Test Voice 1', lang: 'en-US' },
      { name: 'Test Voice 2', lang: 'en-GB' },
    ]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders voice interface when supported', () => {
    render(<VoiceInterface />);
    
    expect(screen.getByRole('button', { name: /start listening/i })).toBeInTheDocument();
    expect(screen.getByText(/click to start voice input/i)).toBeInTheDocument();
  });

  it('shows unsupported message when voice features are not available', () => {
    (voiceService.isVoiceSupported as any).mockReturnValue(false);
    
    render(<VoiceInterface />);
    
    expect(screen.getByText(/voice features are not supported/i)).toBeInTheDocument();
    expect(screen.getByText(/please use a modern browser/i)).toBeInTheDocument();
  });

  it('starts listening when microphone button is clicked', async () => {
    render(<VoiceInterface />);
    
    const micButton = screen.getByRole('button', { name: /start listening/i });
    fireEvent.click(micButton);
    
    await waitFor(() => {
      expect(voiceService.startSpeechRecognition).toHaveBeenCalledWith({
        continuous: true,
        interimResults: true,
        language: 'en-US'
      });
    });
  });

  it('stops listening when microphone button is clicked while listening', async () => {
    render(<VoiceInterface />);
    
    const micButton = screen.getByRole('button', { name: /start listening/i });
    
    // Start listening
    fireEvent.click(micButton);
    await waitFor(() => {
      expect(voiceService.startSpeechRecognition).toHaveBeenCalled();
    });
    
    // Stop listening
    fireEvent.click(micButton);
    expect(voiceService.stopSpeechRecognition).toHaveBeenCalled();
  });

  it('displays transcription results', async () => {
    const mockTranscription = {
      text: 'Hello world',
      confidence: 0.95,
      language: 'en-US',
      timestamp: Date.now()
    };

    const onTranscription = vi.fn();
    render(<VoiceInterface onTranscription={onTranscription} />);
    
    // Simulate speech result
    const speechResultCallback = (voiceService.onSpeechResult as any).mock.calls[0][0];
    speechResultCallback(mockTranscription);
    
    await waitFor(() => {
      expect(screen.getByText('Hello world')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 95%')).toBeInTheDocument();
    });
  });

  it('displays error messages', async () => {
    const onError = vi.fn();
    render(<VoiceInterface onError={onError} />);
    
    // Simulate speech error
    const speechErrorCallback = (voiceService.onSpeechError as any).mock.calls[0][0];
    speechErrorCallback('Microphone not available');
    
    await waitFor(() => {
      expect(screen.getByText('Microphone not available')).toBeInTheDocument();
    });
    
    expect(onError).toHaveBeenCalledWith('Microphone not available');
  });

  it('updates voice configuration', async () => {
    render(<VoiceInterface />);
    
    const languageSelect = screen.getByDisplayValue('English (US)');
    fireEvent.change(languageSelect, { target: { value: 'es-ES' } });
    
    await waitFor(() => {
      expect(languageSelect).toHaveValue('es-ES');
    });
  });

  it('adjusts speech rate', async () => {
    render(<VoiceInterface />);
    
    const rateSlider = screen.getByDisplayValue('1');
    fireEvent.change(rateSlider, { target: { value: '1.5' } });
    
    await waitFor(() => {
      expect(screen.getByText('1.5x')).toBeInTheDocument();
    });
  });

  it('tests microphone permission', async () => {
    render(<VoiceInterface />);
    
    const testMicButton = screen.getByText('Test Microphone');
    fireEvent.click(testMicButton);
    
    await waitFor(() => {
      expect(mockMediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true });
    });
  });

  it('tests speaker functionality', async () => {
    render(<VoiceInterface />);
    
    const testSpeakerButton = screen.getByText('Test Speaker');
    fireEvent.click(testSpeakerButton);
    
    await waitFor(() => {
      expect(voiceService.textToSpeech).toHaveBeenCalledWith(
        'Voice interface is working correctly.',
        expect.any(Object)
      );
    });
  });

  it('handles voice selection', async () => {
    render(<VoiceInterface />);
    
    const voiceSelect = screen.getByDisplayValue('Default');
    fireEvent.change(voiceSelect, { target: { value: 'Test Voice 1' } });
    
    await waitFor(() => {
      expect(voiceSelect).toHaveValue('Test Voice 1');
    });
  });

  it('dismisses error messages', async () => {
    const onError = vi.fn();
    render(<VoiceInterface onError={onError} />);
    
    // Simulate error
    const speechErrorCallback = (voiceService.onSpeechError as any).mock.calls[0][0];
    speechErrorCallback('Test error');
    
    await waitFor(() => {
      expect(screen.getByText('Test error')).toBeInTheDocument();
    });
    
    // Dismiss error
    const dismissButton = screen.getByRole('button', { name: /dismiss error/i });
    fireEvent.click(dismissButton);
    
    await waitFor(() => {
      expect(screen.queryByText('Test error')).not.toBeInTheDocument();
    });
  });

  it('auto-starts listening when autoStart is true', async () => {
    render(<VoiceInterface autoStart={true} />);
    
    await waitFor(() => {
      expect(voiceService.startSpeechRecognition).toHaveBeenCalled();
    });
  });

  it('uses custom language when provided', async () => {
    render(<VoiceInterface language="fr-FR" />);
    
    const micButton = screen.getByRole('button', { name: /start listening/i });
    fireEvent.click(micButton);
    
    await waitFor(() => {
      expect(voiceService.startSpeechRecognition).toHaveBeenCalledWith({
        continuous: true,
        interimResults: true,
        language: 'fr-FR'
      });
    });
  });

  it('cleans up resources on unmount', () => {
    const { unmount } = render(<VoiceInterface />);
    
    unmount();
    
    expect(voiceService.cleanup).toHaveBeenCalled();
  });

  it('handles processing state correctly', async () => {
    render(<VoiceInterface />);
    
    const micButton = screen.getByRole('button', { name: /start listening/i });
    fireEvent.click(micButton);
    
    // Should show processing state initially
    await waitFor(() => {
      expect(screen.getByText(/listening/i)).toBeInTheDocument();
    });
  });

  it('handles volume adjustment', async () => {
    render(<VoiceInterface />);
    
    const volumeSlider = screen.getByDisplayValue('1');
    fireEvent.change(volumeSlider, { target: { value: '0.8' } });
    
    await waitFor(() => {
      expect(screen.getByText('80%')).toBeInTheDocument();
    });
  });
});