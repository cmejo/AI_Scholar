// Voice Interface Service
import { VoiceConfig } from '../types';

export class VoiceService {
  private recognition: SpeechRecognition | null = null;
  private synthesis: SpeechSynthesis;
  private isListening = false;
  private config: VoiceConfig = {
    enabled: false,
    language: 'en-US',
    voice: 'default',
    speed: 1.0,
    pitch: 1.0
  };

  constructor() {
    this.synthesis = window.speechSynthesis;
    this.initializeSpeechRecognition();
  }

  /**
   * Initialize speech recognition
   */
  private initializeSpeechRecognition(): void {
    if ('webkitSpeechRecognition' in window) {
      this.recognition = new (window as any).webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
      this.recognition = new SpeechRecognition();
    }

    if (this.recognition) {
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = this.config.language;
    }
  }

  /**
   * Configure voice settings
   */
  configure(config: Partial<VoiceConfig>): void {
    this.config = { ...this.config, ...config };
    
    if (this.recognition) {
      this.recognition.lang = this.config.language;
    }
  }

  /**
   * Start listening for voice input
   */
  async startListening(): Promise<string> {
    if (!this.recognition || !this.config.enabled) {
      throw new Error('Speech recognition not available or disabled');
    }

    return new Promise((resolve, reject) => {
      if (!this.recognition) {
        reject(new Error('Speech recognition not initialized'));
        return;
      }

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.isListening = false;
        resolve(transcript);
      };

      this.recognition.onerror = (event) => {
        this.isListening = false;
        reject(new Error(`Speech recognition error: ${event.error}`));
      };

      this.recognition.onend = () => {
        this.isListening = false;
      };

      this.isListening = true;
      this.recognition.start();
    });
  }

  /**
   * Stop listening
   */
  stopListening(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  /**
   * Speak text using text-to-speech
   */
  async speak(text: string): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Configure voice settings
      utterance.rate = this.config.speed;
      utterance.pitch = this.config.pitch;
      utterance.lang = this.config.language;

      // Set voice if specified
      if (this.config.voice !== 'default') {
        const voices = this.synthesis.getVoices();
        const selectedVoice = voices.find(voice => voice.name === this.config.voice);
        if (selectedVoice) {
          utterance.voice = selectedVoice;
        }
      }

      utterance.onend = () => resolve();
      utterance.onerror = (event) => reject(new Error(`Speech synthesis error: ${event.error}`));

      this.synthesis.speak(utterance);
    });
  }

  /**
   * Get available voices
   */
  getAvailableVoices(): SpeechSynthesisVoice[] {
    return this.synthesis.getVoices();
  }

  /**
   * Check if voice features are supported
   */
  isSupported(): {
    speechRecognition: boolean;
    speechSynthesis: boolean;
  } {
    return {
      speechRecognition: !!this.recognition,
      speechSynthesis: 'speechSynthesis' in window
    };
  }

  /**
   * Get current listening status
   */
  getListeningStatus(): boolean {
    return this.isListening;
  }

  /**
   * Process voice command
   */
  async processVoiceCommand(command: string): Promise<{
    action: string;
    parameters: any;
    confidence: number;
  }> {
    const normalizedCommand = command.toLowerCase().trim();
    
    // Command patterns
    const patterns = [
      {
        pattern: /search for (.+)/,
        action: 'search',
        extract: (match: RegExpMatchArray) => ({ query: match[1] })
      },
      {
        pattern: /upload (document|file)/,
        action: 'upload',
        extract: () => ({})
      },
      {
        pattern: /open (.+)/,
        action: 'navigate',
        extract: (match: RegExpMatchArray) => ({ target: match[1] })
      },
      {
        pattern: /show (analytics|dashboard|documents)/,
        action: 'navigate',
        extract: (match: RegExpMatchArray) => ({ target: match[1] })
      },
      {
        pattern: /help|what can you do/,
        action: 'help',
        extract: () => ({})
      }
    ];

    for (const { pattern, action, extract } of patterns) {
      const match = normalizedCommand.match(pattern);
      if (match) {
        return {
          action,
          parameters: extract(match),
          confidence: 0.9
        };
      }
    }

    // Default to search if no pattern matches
    return {
      action: 'search',
      parameters: { query: command },
      confidence: 0.5
    };
  }

  /**
   * Generate voice response for text
   */
  generateVoiceResponse(text: string): string {
    // Optimize text for speech
    let voiceText = text
      .replace(/\n/g, '. ')
      .replace(/\s+/g, ' ')
      .trim();

    // Add pauses for better speech flow
    voiceText = voiceText
      .replace(/\. /g, '. ... ')
      .replace(/\? /g, '? ... ')
      .replace(/! /g, '! ... ');

    // Limit length for voice output
    if (voiceText.length > 500) {
      voiceText = voiceText.substring(0, 497) + '...';
    }

    return voiceText;
  }

  /**
   * Handle voice interaction flow
   */
  async handleVoiceInteraction(
    onTranscript: (text: string) => void,
    onResponse: (text: string) => Promise<string>,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      // Listen for user input
      const transcript = await this.startListening();
      onTranscript(transcript);

      // Process the transcript and get response
      const response = await onResponse(transcript);

      // Speak the response
      const voiceResponse = this.generateVoiceResponse(response);
      await this.speak(voiceResponse);

    } catch (error) {
      onError(error as Error);
    }
  }
}

export const voiceService = new VoiceService();