import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatModeSelector from '../../components/ChatModeSelector';
import { ChatSettings } from '../../types/chat';

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('ChatModeSelector', () => {
  const mockSettings: ChatSettings = {
    mode: 'standard',
    temperature: 0.7,
    maxTokens: 2000,
    enableMemory: true,
    enableFactChecking: false,
    enableChainOfThought: false,
    voiceSettings: {
      enabled: false,
      autoListen: false,
      language: 'en-US',
      voice: 'default',
      rate: 1,
      pitch: 1,
      volume: 1,
    },
  };

  const mockProps = {
    currentMode: 'standard' as const,
    onModeChange: jest.fn(),
    settings: mockSettings,
    onSettingsChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  it('should render all available modes', () => {
    render(<ChatModeSelector {...mockProps} />);

    expect(screen.getByText('Standard')).toBeInTheDocument();
    expect(screen.getByText('Streaming')).toBeInTheDocument();
    expect(screen.getByText('Chain of Thought')).toBeInTheDocument();
    expect(screen.getByText('Fact Checked')).toBeInTheDocument();
    expect(screen.getByText('Voice')).toBeInTheDocument();
  });

  it('should highlight the current mode', () => {
    render(<ChatModeSelector {...mockProps} currentMode="chain_of_thought" />);

    const chainOfThoughtButton = screen.getByText('Chain of Thought').closest('button');
    expect(chainOfThoughtButton).toHaveClass('bg-purple-600');
  });

  it('should call onModeChange when a mode is selected', () => {
    render(<ChatModeSelector {...mockProps} />);

    const streamingButton = screen.getByText('Streaming');
    fireEvent.click(streamingButton);

    expect(mockProps.onModeChange).toHaveBeenCalledWith('streaming');
    expect(mockProps.onSettingsChange).toHaveBeenCalledWith({ mode: 'streaming' });
  });

  it('should show current mode description', () => {
    render(<ChatModeSelector {...mockProps} />);

    expect(screen.getByText('Mode:')).toBeInTheDocument();
    expect(screen.getByText('Standard')).toBeInTheDocument();
    expect(screen.getByText('Regular chat with AI assistant')).toBeInTheDocument();
  });

  it('should open settings panel when settings button is clicked', () => {
    render(<ChatModeSelector {...mockProps} />);

    const settingsButton = screen.getByTitle('Chat settings');
    fireEvent.click(settingsButton);

    expect(screen.getByText('Chat Settings')).toBeInTheDocument();
  });

  it('should update temperature setting', () => {
    render(<ChatModeSelector {...mockProps} />);

    // Open settings
    const settingsButton = screen.getByTitle('Chat settings');
    fireEvent.click(settingsButton);

    // Find and change temperature slider
    const temperatureSlider = screen.getByDisplayValue('0.7');
    fireEvent.change(temperatureSlider, { target: { value: '1.2' } });

    expect(mockProps.onSettingsChange).toHaveBeenCalledWith({ temperature: 1.2 });
  });

  it('should update max tokens setting', () => {
    render(<ChatModeSelector {...mockProps} />);

    // Open settings
    const settingsButton = screen.getByTitle('Chat settings');
    fireEvent.click(settingsButton);

    // Find and change max tokens slider
    const maxTokensSlider = screen.getByDisplayValue('2000');
    fireEvent.change(maxTokensSlider, { target: { value: '3000' } });

    expect(mockProps.onSettingsChange).toHaveBeenCalledWith({ maxTokens: 3000 });
  });

  it('should toggle feature settings', () => {
    render(<ChatModeSelector {...mockProps} />);

    // Open settings
    const settingsButton = screen.getByTitle('Chat settings');
    fireEvent.click(settingsButton);

    // Toggle memory setting
    const memoryCheckbox = screen.getByLabelText('Enable Memory');
    fireEvent.click(memoryCheckbox);

    expect(mockProps.onSettingsChange).toHaveBeenCalledWith({ enableMemory: false });
  });

  it('should close settings panel', () => {
    render(<ChatModeSelector {...mockProps} />);

    // Open settings
    const settingsButton = screen.getByTitle('Chat settings');
    fireEvent.click(settingsButton);

    expect(screen.getByText('Chat Settings')).toBeInTheDocument();

    // Close settings
    const closeButton = screen.getByText('Close Settings');
    fireEvent.click(closeButton);

    expect(screen.queryByText('Chat Settings')).not.toBeInTheDocument();
  });

  it('should load settings from localStorage on mount', () => {
    const savedSettings = JSON.stringify({
      ...mockSettings,
      temperature: 1.5,
      enableMemory: false,
    });
    mockLocalStorage.getItem.mockReturnValue(savedSettings);

    render(<ChatModeSelector {...mockProps} />);

    expect(mockProps.onSettingsChange).toHaveBeenCalledWith({
      ...mockSettings,
      temperature: 1.5,
      enableMemory: false,
    });
  });

  it('should save settings to localStorage when they change', () => {
    const { rerender } = render(<ChatModeSelector {...mockProps} />);

    const newSettings = { ...mockSettings, temperature: 1.2 };
    rerender(<ChatModeSelector {...mockProps} settings={newSettings} />);

    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'chatSettings',
      JSON.stringify(newSettings)
    );
  });

  it('should handle localStorage parsing errors gracefully', () => {
    mockLocalStorage.getItem.mockReturnValue('invalid json');
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(<ChatModeSelector {...mockProps} />);

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to load chat settings:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  it('should show voice settings button', () => {
    render(<ChatModeSelector {...mockProps} />);

    expect(screen.getByTitle('Voice settings')).toBeInTheDocument();
  });

  it('should show keyboard shortcuts help', () => {
    render(<ChatModeSelector {...mockProps} />);

    expect(screen.getByTitle('Keyboard shortcuts')).toBeInTheDocument();
  });

  it('should display mode tooltips on hover', () => {
    render(<ChatModeSelector {...mockProps} />);

    const chainOfThoughtButton = screen.getByText('Chain of Thought').closest('button');
    expect(chainOfThoughtButton).toHaveAttribute('title', 'See AI reasoning process');
  });

  it('should handle disabled modes', () => {
    // This test would require modifying the component to accept disabled modes
    // For now, all modes are enabled by default
    render(<ChatModeSelector {...mockProps} />);

    const buttons = screen.getAllByRole('button');
    const modeButtons = buttons.filter(button => 
      button.textContent?.includes('Standard') ||
      button.textContent?.includes('Streaming') ||
      button.textContent?.includes('Chain of Thought') ||
      button.textContent?.includes('Fact Checked') ||
      button.textContent?.includes('Voice')
    );

    modeButtons.forEach(button => {
      expect(button).not.toBeDisabled();
    });
  });
});