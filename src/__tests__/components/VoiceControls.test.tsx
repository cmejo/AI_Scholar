import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceControls from '../../components/VoiceControls';
import { useVoice } from '../../hooks/useVoice';

// Mock the useVoice hook
jest.mock('../../hooks/useVoice');

const mockUseVoice = useVoice as jest.MockedFunction<typeof useVoice>;

describe('VoiceControls', () => {
  const mockProps = {
    onVoiceInput: jest.fn(),
    voiceEnabled: true,
    onToggleVoice: jest.fn(),
  };

  const mockVoiceState = {
    isListening: false,
    isSpeaking: false,
    currentlySpeaking: null,
    transcriptionInProgress: false,
    error: null,
    permissions: {
      microphone: 'granted' as const,
      speaker: true,
    },
    isSupported: true,
  };

  const mockVoiceActions = {
    voiceState: mockVoiceState,
    startListening: jest.fn(),
    stopListening: jest.fn(),
    speak: jest.fn(),
    stopSpeaking: jest.fn(),
    updateSettings: jest.fn(),
    getSettings: jest.fn(),
    clearError: jest.fn(),
    requestPermissions: jest.fn(),
    testVoice: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseVoice.mockReturnValue(mockVoiceActions);
  });

  it('should render voice controls when voice is enabled', () => {
    render(<VoiceControls {...mockProps} />);

    expect(screen.getByTitle('Disable voice features')).toBeInTheDocument();
    expect(screen.getByTitle('Click to start voice input')).toBeInTheDocument();
  });

  it('should not render when voice is disabled', () => {
    render(<VoiceControls {...mockProps} voiceEnabled={false} />);

    expect(screen.queryByTitle('Disable voice features')).not.toBeInTheDocument();
  });

  it('should toggle voice when toggle button is clicked', () => {
    render(<VoiceControls {...mockProps} />);

    const toggleButton = screen.getByTitle('Disable voice features');
    fireEvent.click(toggleButton);

    expect(mockProps.onToggleVoice).toHaveBeenCalled();
  });

  it('should start listening when microphone button is clicked', async () => {
    const mockTranscript = 'Hello world';
    mockVoiceActions.startListening.mockResolvedValue(mockTranscript);

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Click to start voice input');
    fireEvent.click(micButton);

    await waitFor(() => {
      expect(mockVoiceActions.startListening).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(mockProps.onVoiceInput).toHaveBeenCalledWith(mockTranscript);
    });
  });

  it('should stop listening when microphone button is clicked while recording', async () => {
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        isListening: true,
      },
    });

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Click to stop recording');
    fireEvent.click(micButton);

    expect(mockVoiceActions.stopListening).toHaveBeenCalled();
  });

  it('should show processing indicator during transcription', () => {
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        transcriptionInProgress: true,
      },
    });

    render(<VoiceControls {...mockProps} />);

    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('should display error message when there is an error', () => {
    const errorMessage = 'Microphone not available';
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        error: errorMessage,
      },
    });

    render(<VoiceControls {...mockProps} />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('should clear error when close button is clicked', () => {
    const errorMessage = 'Test error';
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        error: errorMessage,
      },
    });

    render(<VoiceControls {...mockProps} />);

    const closeButton = screen.getByTitle('Clear error');
    fireEvent.click(closeButton);

    expect(mockVoiceActions.clearError).toHaveBeenCalled();
  });

  it('should show disabled state when voice is not supported', () => {
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        isSupported: false,
      },
    });

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Voice input not supported in this browser');
    expect(micButton).toBeDisabled();
  });

  it('should request permissions when microphone is denied', async () => {
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        permissions: {
          ...mockVoiceState.permissions,
          microphone: 'denied',
        },
      },
    });

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Click to enable microphone permissions');
    fireEvent.click(micButton);

    await waitFor(() => {
      expect(mockVoiceActions.requestPermissions).toHaveBeenCalled();
    });
  });

  it('should handle voice input errors gracefully', async () => {
    const mockError = new Error('Voice input failed');
    mockVoiceActions.startListening.mockRejectedValue(mockError);

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Click to start voice input');
    fireEvent.click(micButton);

    await waitFor(() => {
      expect(mockVoiceActions.startListening).toHaveBeenCalled();
    });

    // Should not call onVoiceInput when there's an error
    expect(mockProps.onVoiceInput).not.toHaveBeenCalled();
  });

  it('should show pulsing animation when recording', () => {
    mockUseVoice.mockReturnValue({
      ...mockVoiceActions,
      voiceState: {
        ...mockVoiceState,
        isListening: true,
      },
    });

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Click to stop recording');
    expect(micButton).toHaveClass('animate-pulse');
  });

  it('should not call onVoiceInput with empty transcript', async () => {
    mockVoiceActions.startListening.mockResolvedValue('   '); // Empty/whitespace transcript

    render(<VoiceControls {...mockProps} />);

    const micButton = screen.getByTitle('Click to start voice input');
    fireEvent.click(micButton);

    await waitFor(() => {
      expect(mockVoiceActions.startListening).toHaveBeenCalled();
    });

    expect(mockProps.onVoiceInput).not.toHaveBeenCalled();
  });
});