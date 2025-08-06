/**
 * Voice Service for Speech-to-Text and Text-to-Speech functionality
 * Supports Web Speech API with fallback to server-side processing
 */

export interface VoiceConfig {
  language: string;
  voice?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

export interface TranscriptionResult {
  text: string;
  confidence: number;
  language: string;
  timestamp: number;
}

export interface AudioProcessingResult {
  processedAudio: Blob;
  noiseReduced: boolean;
  qualityEnhanced: boolean;
}

export interface SpeechRecognitionOptions {
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  language?: string;
}

class VoiceService {
  private recognition: SpeechRecognition | null = null;
  private synthesis: SpeechSynthesis | null = null;
  private isListening = false;
  private audioContext: AudioContext | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private recordedChunks: Blob[] = [];

  constructor() {
    this.initializeWebSpeechAPI();
    this.initializeAudioContext();
  }

  /**
   * Initialize Web Speech API if available
   */
  private initializeWebSpeechAPI(): void {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
    }

    if ('speechSynthesis' in window) {
      this.synthesis = window.speechSynthesis;
    }
  }

  /**
   * Initialize Audio Context for audio processing
   */
  private initializeAudioContext(): void {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (error) {
      console.warn('Audio Context not supported:', error);
    }
  }

  /**
   * Start speech recognition
   */
  async startSpeechRecognition(options: SpeechRecognitionOptions = {}): Promise<void> {
    if (!this.recognition) {
      throw new Error('Speech recognition not supported');
    }

    if (this.isListening) {
      return;
    }

    // Configure recognition
    this.recognition.continuous = options.continuous ?? true;
    this.recognition.interimResults = options.interimResults ?? true;
    this.recognition.maxAlternatives = options.maxAlternatives ?? 1;
    this.recognition.lang = options.language ?? 'en-US';

    this.isListening = true;
    this.recognition.start();
  }

  /**
   * Stop speech recognition
   */
  stopSpeechRecognition(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  /**
   * Convert speech to text using Web Speech API
   */
  async speechToText(options: SpeechRecognitionOptions = {}): Promise<TranscriptionResult> {
    return new Promise((resolve, reject) => {
      if (!this.recognition) {
        // Fallback to server-side processing
        this.speechToTextServerSide(options).then(resolve).catch(reject);
        return;
      }

      // Configure recognition
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = options.maxAlternatives ?? 1;
      this.recognition.lang = options.language ?? 'en-US';

      this.recognition.onresult = (event) => {
        const result = event.results[0];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence;

        resolve({
          text: transcript,
          confidence: confidence,
          language: options.language ?? 'en-US',
          timestamp: Date.now()
        });
      };

      this.recognition.onerror = (event) => {
        reject(new Error(`Speech recognition error: ${event.error}`));
      };

      this.recognition.start();
    });
  }

  /**
   * Server-side speech to text processing with enhanced features
   */
  private async speechToTextServerSide(options: SpeechRecognitionOptions): Promise<TranscriptionResult> {
    try {
      // Record audio for server processing
      const audioBlob = await this.recordAudio(5000); // 5 second recording
      
      // Process audio for noise reduction if supported
      const processedAudio = await this.processAudio(audioBlob);
      
      const formData = new FormData();
      formData.append('audio', processedAudio.processedAudio);
      formData.append('language', options.language ?? 'en-US');
      formData.append('real_time', 'false'); // Batch processing

      const response = await fetch('/api/voice/speech-to-text', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Server-side speech recognition failed');
      }

      const result = await response.json();
      
      return {
        text: result.text,
        confidence: result.confidence,
        language: result.language,
        timestamp: result.timestamp || Date.now()
      };
    } catch (error) {
      throw new Error(`Server-side speech recognition error: ${error.message}`);
    }
  }

  /**
   * Convert text to speech
   */
  async textToSpeech(text: string, config: VoiceConfig = {}): Promise<void> {
    if (!this.synthesis) {
      // Fallback to server-side TTS
      return this.textToSpeechServerSide(text, config);
    }

    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Configure voice settings
      utterance.lang = config.language ?? 'en-US';
      utterance.rate = config.rate ?? 1;
      utterance.pitch = config.pitch ?? 1;
      utterance.volume = config.volume ?? 1;

      // Set voice if specified
      if (config.voice) {
        const voices = this.synthesis!.getVoices();
        const selectedVoice = voices.find(voice => voice.name === config.voice);
        if (selectedVoice) {
          utterance.voice = selectedVoice;
        }
      }

      utterance.onend = () => resolve();
      utterance.onerror = (event) => reject(new Error(`TTS error: ${event.error}`));

      this.synthesis!.speak(utterance);
    });
  }

  /**
   * Server-side text to speech with enhanced voice options
   */
  private async textToSpeechServerSide(text: string, config: VoiceConfig): Promise<void> {
    try {
      const response = await fetch('/api/voice/text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          text, 
          config: {
            ...config,
            language: config.language || 'en-US'
          }
        })
      });

      if (!response.ok) {
        throw new Error('Server-side TTS failed');
      }

      const audioBlob = await response.blob();
      await this.playAudio(audioBlob);
    } catch (error) {
      throw new Error(`Server-side TTS error: ${error.message}`);
    }
  }

  /**
   * Get available voice profiles from server
   */
  async getAvailableVoiceProfiles(language?: string): Promise<any[]> {
    try {
      const url = language 
        ? `/api/voice/available-voices?language=${language}`
        : '/api/voice/available-voices';
        
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Failed to get voice profiles');
      }
      
      const data = await response.json();
      return data.voices || [];
    } catch (error) {
      console.warn('Failed to get server voice profiles:', error);
      return this.getAvailableVoices(); // Fallback to local voices
    }
  }

  /**
   * Start streaming speech recognition session
   */
  async startStreamingSession(language: string = 'en-US'): Promise<string> {
    try {
      const response = await fetch('/api/voice/streaming/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ language })
      });

      if (!response.ok) {
        throw new Error('Failed to start streaming session');
      }

      const data = await response.json();
      return data.session_id;
    } catch (error) {
      throw new Error(`Failed to start streaming session: ${error.message}`);
    }
  }

  /**
   * Process streaming audio chunk
   */
  async processStreamingChunk(sessionId: string, audioChunk: Blob): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('audio_chunk', audioChunk);

      const response = await fetch('/api/voice/streaming/process', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to process streaming chunk');
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to process streaming chunk: ${error.message}`);
    }
  }

  /**
   * Stop streaming session and get final results
   */
  async stopStreamingSession(sessionId: string): Promise<any> {
    try {
      const response = await fetch('/api/voice/streaming/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error('Failed to stop streaming session');
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to stop streaming session: ${error.message}`);
    }
  }

  /**
   * Get streaming session results
   */
  async getStreamingResults(sessionId: string): Promise<any> {
    try {
      const response = await fetch(`/api/voice/streaming/results/${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to get streaming results');
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to get streaming results: ${error.message}`);
    }
  }

  /**
   * Get available voices
   */
  getAvailableVoices(): SpeechSynthesisVoice[] {
    if (!this.synthesis) {
      return [];
    }
    return this.synthesis.getVoices();
  }

  /**
   * Record audio for processing
   */
  private async recordAudio(duration: number): Promise<Blob> {
    return new Promise(async (resolve, reject) => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        this.recordedChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            this.recordedChunks.push(event.data);
          }
        };

        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.recordedChunks, { type: 'audio/webm' });
          stream.getTracks().forEach(track => track.stop());
          resolve(audioBlob);
        };

        this.mediaRecorder.start();
        setTimeout(() => {
          if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
          }
        }, duration);
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Play audio blob
   */
  private async playAudio(audioBlob: Blob): Promise<void> {
    return new Promise((resolve, reject) => {
      const audio = new Audio();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      audio.src = audioUrl;
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        resolve();
      };
      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        reject(new Error('Audio playback failed'));
      };
      
      audio.play();
    });
  }

  /**
   * Process audio for noise reduction and quality enhancement
   */
  async processAudio(audioBlob: Blob): Promise<AudioProcessingResult> {
    if (!this.audioContext) {
      return {
        processedAudio: audioBlob,
        noiseReduced: false,
        qualityEnhanced: false
      };
    }

    try {
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      
      // Apply noise reduction and quality enhancement
      const processedBuffer = await this.applyAudioFilters(audioBuffer);
      const processedBlob = await this.audioBufferToBlob(processedBuffer);

      return {
        processedAudio: processedBlob,
        noiseReduced: true,
        qualityEnhanced: true
      };
    } catch (error) {
      console.warn('Audio processing failed:', error);
      return {
        processedAudio: audioBlob,
        noiseReduced: false,
        qualityEnhanced: false
      };
    }
  }

  /**
   * Apply audio filters for noise reduction
   */
  private async applyAudioFilters(audioBuffer: AudioBuffer): Promise<AudioBuffer> {
    const offlineContext = new OfflineAudioContext(
      audioBuffer.numberOfChannels,
      audioBuffer.length,
      audioBuffer.sampleRate
    );

    const source = offlineContext.createBufferSource();
    source.buffer = audioBuffer;

    // High-pass filter for noise reduction
    const highPassFilter = offlineContext.createBiquadFilter();
    highPassFilter.type = 'highpass';
    highPassFilter.frequency.value = 80; // Remove low-frequency noise

    // Low-pass filter for quality enhancement
    const lowPassFilter = offlineContext.createBiquadFilter();
    lowPassFilter.type = 'lowpass';
    lowPassFilter.frequency.value = 8000; // Remove high-frequency noise

    // Connect filters
    source.connect(highPassFilter);
    highPassFilter.connect(lowPassFilter);
    lowPassFilter.connect(offlineContext.destination);

    source.start();
    return await offlineContext.startRendering();
  }

  /**
   * Convert AudioBuffer to Blob
   */
  private async audioBufferToBlob(audioBuffer: AudioBuffer): Promise<Blob> {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const length = audioBuffer.length * numberOfChannels * 2;
    const buffer = new ArrayBuffer(length);
    const view = new DataView(buffer);
    
    let offset = 0;
    for (let i = 0; i < audioBuffer.length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[i]));
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
        offset += 2;
      }
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }

  /**
   * Check if voice features are supported
   */
  isVoiceSupported(): boolean {
    return !!(this.recognition || this.synthesis);
  }

  /**
   * Check if speech recognition is supported
   */
  isSpeechRecognitionSupported(): boolean {
    return !!this.recognition;
  }

  /**
   * Check if text-to-speech is supported
   */
  isTextToSpeechSupported(): boolean {
    return !!this.synthesis;
  }

  /**
   * Set up event listeners for speech recognition
   */
  onSpeechResult(callback: (result: TranscriptionResult) => void): void {
    if (!this.recognition) return;

    this.recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence;

        callback({
          text: transcript,
          confidence: confidence,
          language: this.recognition!.lang,
          timestamp: Date.now()
        });
      }
    };
  }

  /**
   * Set up error handling for speech recognition
   */
  onSpeechError(callback: (error: string) => void): void {
    if (!this.recognition) return;

    this.recognition.onerror = (event) => {
      callback(event.error);
    };
  }

  /**
   * Clean up resources
   */
  cleanup(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
    
    if (this.synthesis) {
      this.synthesis.cancel();
    }
    
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
    
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }
  }
}

export default new VoiceService();