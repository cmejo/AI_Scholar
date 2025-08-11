/**
 * Type definitions for speech recognition and processing
 */

// Speech Recognition Result Types
export interface SpeechRecognitionResultData {
  text: string;
  confidence: number;
  language: string;
  timestamp: number;
  isFinal: boolean;
  alternatives?: SpeechAlternative[];
}

export interface SpeechAlternative {
  transcript: string;
  confidence: number;
}

// Speech Recognition Event Types
export interface SpeechRecognitionEventData {
  results: SpeechRecognitionResultList;
  resultIndex: number;
  interpretation?: unknown;
  emma?: Document;
}

// Voice Processing Types
export interface VoiceProcessingOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  serviceURI?: string;
}

export interface VoiceCommandResult {
  recognized: boolean;
  command?: string;
  confidence: number;
  parameters?: Record<string, unknown>;
  error?: string;
  suggestions?: string[];
}

// Audio Processing Types
export interface AudioProcessingConfig {
  sampleRate: number;
  channels: number;
  bitDepth: number;
  format: 'wav' | 'mp3' | 'ogg' | 'webm';
}

export interface AudioBuffer {
  data: Float32Array;
  sampleRate: number;
  channels: number;
  duration: number;
}

export interface AudioAnalysis {
  volume: number;
  frequency: number;
  quality: 'poor' | 'fair' | 'good' | 'excellent';
  noiseLevel: number;
  speechDetected: boolean;
}

// Voice Session Types
export interface VoiceSession {
  id: string;
  startTime: Date;
  endTime?: Date;
  language: string;
  commands: VoiceCommand[];
  status: 'active' | 'paused' | 'ended';
  settings: VoiceSessionSettings;
}

export interface VoiceCommand {
  id: string;
  timestamp: Date;
  text: string;
  confidence: number;
  processed: boolean;
  result?: VoiceCommandResult;
  error?: string;
}

export interface VoiceSessionSettings {
  language: string;
  continuous: boolean;
  interimResults: boolean;
  noiseReduction: boolean;
  echoCancellation: boolean;
  autoGainControl: boolean;
}

// Speech Synthesis Types
export interface SpeechSynthesisConfig {
  voice?: SpeechSynthesisVoice;
  rate: number;
  pitch: number;
  volume: number;
  language: string;
}

export interface TextToSpeechRequest {
  text: string;
  config: SpeechSynthesisConfig;
  priority: 'low' | 'normal' | 'high';
}

export interface TextToSpeechResult {
  success: boolean;
  audioUrl?: string;
  duration?: number;
  error?: string;
}

// Voice Navigation Types
export interface VoiceNavigationCommand {
  action: NavigationAction;
  target?: string;
  parameters?: NavigationParameters;
  confidence: number;
}

export type NavigationAction = 
  | 'go_to'
  | 'search'
  | 'open'
  | 'close'
  | 'scroll'
  | 'click'
  | 'back'
  | 'forward'
  | 'refresh'
  | 'help';

export interface NavigationParameters {
  query?: string;
  direction?: 'up' | 'down' | 'left' | 'right';
  amount?: number;
  element?: string;
  [key: string]: unknown;
}

// Voice Feedback Types
export interface VoiceFeedback {
  type: 'confirmation' | 'error' | 'information' | 'warning';
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  autoSpeak: boolean;
  config?: SpeechSynthesisConfig;
}

export interface VoiceFeedbackQueue {
  items: VoiceFeedback[];
  currentItem?: VoiceFeedback;
  isPlaying: boolean;
  isPaused: boolean;
}

// Voice Analytics Types
export interface VoiceAnalytics {
  sessionId: string;
  totalCommands: number;
  successfulCommands: number;
  averageConfidence: number;
  mostUsedCommands: CommandFrequency[];
  errorRate: number;
  sessionDuration: number;
  languageDistribution: LanguageUsage[];
}

export interface CommandFrequency {
  command: string;
  count: number;
  averageConfidence: number;
  successRate: number;
}

export interface LanguageUsage {
  language: string;
  count: number;
  percentage: number;
}

// Voice Training Types
export interface VoiceTrainingData {
  userId: string;
  samples: VoiceSample[];
  adaptationLevel: number;
  lastTraining: Date;
  improvements: TrainingImprovement[];
}

export interface VoiceSample {
  id: string;
  text: string;
  audioData: ArrayBuffer;
  quality: number;
  timestamp: Date;
  verified: boolean;
}

export interface TrainingImprovement {
  metric: 'accuracy' | 'confidence' | 'speed' | 'noise_handling';
  before: number;
  after: number;
  improvement: number;
  date: Date;
}

// Voice Error Types
export interface VoiceError {
  code: VoiceErrorCode;
  message: string;
  details?: Record<string, unknown>;
  timestamp: Date;
  recoverable: boolean;
  suggestions?: string[];
}

export type VoiceErrorCode = 
  | 'MICROPHONE_ACCESS_DENIED'
  | 'MICROPHONE_NOT_FOUND'
  | 'SPEECH_RECOGNITION_FAILED'
  | 'NETWORK_ERROR'
  | 'LANGUAGE_NOT_SUPPORTED'
  | 'AUDIO_PROCESSING_ERROR'
  | 'COMMAND_NOT_RECOGNIZED'
  | 'SYNTHESIS_FAILED'
  | 'TIMEOUT'
  | 'UNKNOWN_ERROR';

// Voice Accessibility Types
export interface VoiceAccessibilityFeatures {
  screenReaderCompatible: boolean;
  keyboardShortcuts: KeyboardShortcut[];
  visualIndicators: VisualIndicator[];
  hapticFeedback: boolean;
  customCommands: CustomCommand[];
}

export interface KeyboardShortcut {
  key: string;
  modifiers: string[];
  action: string;
  description: string;
}

export interface VisualIndicator {
  type: 'listening' | 'processing' | 'speaking' | 'error';
  element: string;
  style: Record<string, string>;
  animation?: string;
}

export interface CustomCommand {
  id: string;
  phrase: string;
  action: string;
  parameters?: Record<string, unknown>;
  enabled: boolean;
  userDefined: boolean;
}