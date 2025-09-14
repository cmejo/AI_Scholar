import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import VoiceControls from '../components/VoiceControls';
import VoiceStatusIndicator from '../components/VoiceStatusIndicator';
import SpeakerButton from '../components/SpeakerButton';
import { vi } from 'vitest';

// Mock the useVoice hook
vi.mock('../hooks/useVoice', () => ({
  useVoice: () => ({
    voiceState: {
      isSupported: true,
      isListening: false,
      isSpeaking: false,
      transcriptionInProgress: false,
      error: null,
      permissions: {
        microphone: 'granted',
        speaker: true,
      },
      currentlySpeaking: null,
    },
    startListening: vi.fn(),
    stopListening: vi.fn(),
    speak: vi.fn(),
    stopSpeaking: vi.fn(),
    clearError: vi.fn(),
    requestPermissions: vi.fn(),
  }),
}));

describe('Voice Interface Animations', () => {
  it('should render VoiceControls with animation classes', () => {
    const mockOnVoiceInput = vi.fn();
    const mockOnToggleVoice = vi.fn();

    render(
      <VoiceControls
        onVoiceInput={mockOnVoiceInput}
        voiceEnabled={true}
        onToggleVoice={mockOnToggleVoice}
      />
    );

    // Check if animation classes are present in the DOM
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    // Check for transition classes
    const micButton = buttons.find(button => 
      button.className.includes('voice-state-transition')
    );
    expect(micButton).toBeDefined();
  });

  it('should render VoiceStatusIndicator with proper animation states', () => {
    render(
      <VoiceStatusIndicator
        isListening={true}
        isSpeaking={false}
        isProcessing={false}
        isConnected={true}
      />
    );

    // Should show listening state with animations
    expect(screen.getByText('Listening...')).toBeInTheDocument();
  });

  it('should render SpeakerButton with hover animations', () => {
    render(
      <SpeakerButton
        text="Test message"
        messageId="test-1"
      />
    );

    const speakerButton = screen.getByRole('button');
    expect(speakerButton).toBeInTheDocument();
    expect(speakerButton.className).toContain('voice-state-transition');
  });

  it('should handle processing state animations', () => {
    render(
      <VoiceStatusIndicator
        isListening={false}
        isSpeaking={false}
        isProcessing={true}
        isConnected={true}
      />
    );

    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('should handle speaking state animations', () => {
    render(
      <VoiceStatusIndicator
        isListening={false}
        isSpeaking={true}
        isProcessing={false}
        isConnected={true}
      />
    );

    expect(screen.getByText('Speaking...')).toBeInTheDocument();
  });
});