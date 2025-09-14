import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../../App';

// Mock the voice service
jest.mock('../../services/voiceService', () => ({
  voiceService: {
    isSupported: jest.fn(() => true),
    getIsListening: jest.fn(() => false),
    isSpeaking: jest.fn(() => false),
    startListening: jest.fn(),
    stopListening: jest.fn(),
    speak: jest.fn(),
    stopSpeaking: jest.fn(),
    updateSettings: jest.fn(),
    getSettings: jest.fn(() => ({
      enabled: true,
      autoListen: false,
      language: 'en-US',
      voice: 'default',
      rate: 1,
      pitch: 1,
      volume: 1,
    })),
    cleanTextForSpeech: jest.fn((text) => text),
    testVoice: jest.fn(),
  },
}));

// Mock browser APIs
const mockSpeechSynthesis = {
  speak: jest.fn(),
  cancel: jest.fn(),
  speaking: false,
  getVoices: jest.fn(() => [
    { name: 'Test Voice 1', lang: 'en-US' },
    { name: 'Test Voice 2', lang: 'en-GB' },
  ]),
};

Object.defineProperty(global.window, 'speechSynthesis', {
  value: mockSpeechSynthesis,
  writable: true,
});

Object.defineProperty(global.navigator, 'permissions', {
  value: {
    query: jest.fn(() => Promise.resolve({ state: 'granted', onchange: null })),
  },
  writable: true,
});

Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: jest.fn(() => Promise.resolve({
      getTracks: () => [{ stop: jest.fn() }],
    })),
  },
  writable: true,
});

// Mock fetch for chat API
global.fetch = jest.fn();

describe('Voice Workflow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful chat API response
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        response: 'This is a test response from the AI assistant.',
      }),
    });
  });

  it('should complete full voice input to message workflow', async () => {
    const { voiceService } = require('../../services/voiceService');
    voiceService.startListening.mockResolvedValue('Hello, how are you?');

    render(<App />);

    // Enable voice features
    const voiceToggle = screen.getByTitle('Enable voice features');
    fireEvent.click(voiceToggle);

    // Wait for voice controls to appear
    await waitFor(() => {
      expect(screen.getByTitle('Click to start voice input')).toBeInTheDocument();
    });

    // Start voice input
    const micButton = screen.getByTitle('Click to start voice input');
    fireEvent.click(micButton);

    // Wait for voice input to complete and message to be sent
    await waitFor(() => {
      expect(voiceService.startListening).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
    });

    // Verify API call was made
    expect(global.fetch).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: expect.stringContaining('Hello, how are you?'),
    }));
  });

  it('should handle voice input errors gracefully', async () => {
    const { voiceService } = require('../../services/voiceService');
    voiceService.startListening.mockRejectedValue(new Error('Microphone not available'));

    render(<App />);

    // Enable voice features
    const voiceToggle = screen.getByTitle('Enable voice features');
    fireEvent.click(voiceToggle);

    await waitFor(() => {
      expect(screen.getByTitle('Click to start voice input')).toBeInTheDocument();
    });

    // Try to start voice input
    const micButton = screen.getByTitle('Click to start voice input');
    fireEvent.click(micButton);

    await waitFor(() => {
      expect(voiceService.startListening).toHaveBeenCalled();
    });

    // Should not send a message when voice input fails
    expect(screen.queryByText('Microphone not available')).not.toBeInTheDocument();
  });

  it('should switch chat modes and preserve conversation', async () => {
    render(<App />);

    // Send a regular message first
    const input = screen.getByPlaceholderText('Ask me anything about research...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });

    // Switch to Chain of Thought mode
    const chainOfThoughtButton = screen.getByText('Chain of Thought');
    fireEvent.click(chainOfThoughtButton);

    // Verify mode switched and conversation is preserved
    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(chainOfThoughtButton.closest('button')).toHaveClass('bg-purple-600');
  });

  it('should handle text-to-speech for AI responses', async () => {
    const { voiceService } = require('../../services/voiceService');
    voiceService.speak.mockResolvedValue(undefined);

    render(<App />);

    // Send a message to get a response
    const input = screen.getByPlaceholderText('Ask me anything about research...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(sendButton);

    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument();
    });

    // Find and click the speaker button for the AI response
    const speakerButtons = screen.getAllByTitle('Speak this message');
    expect(speakerButtons.length).toBeGreaterThan(0);

    fireEvent.click(speakerButtons[0]);

    await waitFor(() => {
      expect(voiceService.speak).toHaveBeenCalledWith('This is a test response from the AI assistant.');
    });
  });

  it('should open and configure voice settings', async () => {
    render(<App />);

    // Open voice settings
    const voiceSettingsButton = screen.getByTitle('Voice settings');
    fireEvent.click(voiceSettingsButton);

    await waitFor(() => {
      expect(screen.getByText('Voice Settings')).toBeInTheDocument();
    });

    // Enable voice features
    const enableVoiceCheckbox = screen.getByLabelText('Enable Voice Features');
    fireEvent.click(enableVoiceCheckbox);

    // Change speech rate
    const rateSlider = screen.getByDisplayValue('1');
    fireEvent.change(rateSlider, { target: { value: '1.5' } });

    // Close settings
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    expect(screen.queryByText('Voice Settings')).not.toBeInTheDocument();
  });

  it('should show chain of thought reasoning in appropriate mode', async () => {
    render(<App />);

    // Switch to Chain of Thought mode
    const chainOfThoughtButton = screen.getByText('Chain of Thought');
    fireEvent.click(chainOfThoughtButton);

    // Send a message
    const input = screen.getByPlaceholderText('Ask me anything about research...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Explain quantum physics' } });
    fireEvent.click(sendButton);

    // Wait for response with reasoning
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument();
    });

    // Should show chain of thought component
    await waitFor(() => {
      expect(screen.getByText(/Chain of Thought/)).toBeInTheDocument();
    });
  });

  it('should show citations in fact-checked mode', async () => {
    render(<App />);

    // Switch to Fact Checked mode
    const factCheckedButton = screen.getByText('Fact Checked');
    fireEvent.click(factCheckedButton);

    // Send a message
    const input = screen.getByPlaceholderText('Ask me anything about research...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'What is the capital of France?' } });
    fireEvent.click(sendButton);

    // Wait for response with citations
    await waitFor(() => {
      expect(screen.getByText('This is a test response from the AI assistant.')).toBeInTheDocument();
    });

    // Should show sources section
    await waitFor(() => {
      expect(screen.getByText(/Sources/)).toBeInTheDocument();
    });
  });

  it('should handle keyboard shortcuts for voice control', async () => {
    const { voiceService } = require('../../services/voiceService');
    voiceService.startListening.mockResolvedValue('Voice shortcut test');

    render(<App />);

    // Enable voice features first
    const voiceToggle = screen.getByTitle('Enable voice features');
    fireEvent.click(voiceToggle);

    await waitFor(() => {
      expect(screen.getByTitle('Click to start voice input')).toBeInTheDocument();
    });

    // Simulate spacebar press for voice input
    fireEvent.keyDown(document, { key: ' ', code: 'Space' });

    await waitFor(() => {
      expect(voiceService.startListening).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('Voice shortcut test')).toBeInTheDocument();
    });
  });

  it('should handle mode switching via keyboard shortcuts', async () => {
    render(<App />);

    // Switch to streaming mode with Alt+2
    fireEvent.keyDown(document, { key: '2', altKey: true });

    await waitFor(() => {
      const streamingButton = screen.getByText('Streaming');
      expect(streamingButton.closest('button')).toHaveClass('bg-purple-600');
    });
  });

  it('should persist settings across sessions', async () => {
    const mockLocalStorage = {
      getItem: jest.fn(),
      setItem: jest.fn(),
    };

    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
    });

    // Mock saved settings
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify({
      mode: 'chain_of_thought',
      temperature: 1.2,
      enableMemory: false,
    }));

    render(<App />);

    // Should load saved settings
    await waitFor(() => {
      const chainOfThoughtButton = screen.getByText('Chain of Thought');
      expect(chainOfThoughtButton.closest('button')).toHaveClass('bg-purple-600');
    });
  });

  it('should handle network errors gracefully', async () => {
    // Mock network error
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<App />);

    // Send a message
    const input = screen.getByPlaceholderText('Ask me anything about research...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/encountered an error/)).toBeInTheDocument();
    });
  });

  it('should show loading state during voice processing', async () => {
    const { voiceService } = require('../../services/voiceService');
    
    // Mock delayed voice recognition
    voiceService.startListening.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve('Delayed response'), 100))
    );

    render(<App />);

    // Enable voice features
    const voiceToggle = screen.getByTitle('Enable voice features');
    fireEvent.click(voiceToggle);

    await waitFor(() => {
      expect(screen.getByTitle('Click to start voice input')).toBeInTheDocument();
    });

    // Start voice input
    const micButton = screen.getByTitle('Click to start voice input');
    fireEvent.click(micButton);

    // Should show processing indicator
    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Delayed response')).toBeInTheDocument();
    });
  });
});