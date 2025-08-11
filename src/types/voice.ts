/**
 * Type definitions for voice navigation and voice services
 */

// Voice Navigation Types
export interface NavigationParameters {
  query?: string;
  documentId?: string;
  section?: string;
  page?: number;
  filter?: string;
  sortBy?: string;
  view?: 'list' | 'grid' | 'detail';
}

export interface NavigationCommand {
  destination: string;
  action: 'navigate' | 'open' | 'show' | 'close' | 'toggle';
  parameters?: NavigationParameters;
}

export interface VoiceShortcut {
  id: string;
  phrase: string;
  action: () => void | Promise<void>;
  description: string;
  category: 'navigation' | 'research' | 'document' | 'system';
  enabled: boolean;
}

export interface AccessibilitySettings {
  fontSize?: number;
  highContrast?: boolean;
  screenReader?: boolean;
  voiceSpeed?: number;
  keyboardNavigation?: boolean;
}

export interface AccessibilityFeature {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  settings: AccessibilitySettings;
}

// Voice Recognition Types
export interface SpeechRecognitionResult {
  text: string;
  confidence: number;
  language: string;
  timestamp?: number;
  isFinal: boolean;
}

export interface VoiceCommand {
  command: string;
  context?: string;
  confidence: number;
  timestamp: number;
}

export interface VoiceProcessingResult {
  recognized: boolean;
  command?: VoiceCommand;
  error?: string;
  suggestions?: string[];
}

// Speech Synthesis Types
export interface SpeechSynthesisOptions {
  voice?: SpeechSynthesisVoice;
  rate?: number;
  pitch?: number;
  volume?: number;
  lang?: string;
}

export interface VoiceSettings {
  enabled: boolean;
  language: string;
  voice?: string;
  rate: number;
  pitch: number;
  volume: number;
  autoSpeak: boolean;
}

// Event Types
export interface VoiceNavigationEvent {
  type: 'navigation' | 'command' | 'error' | 'recognition';
  data: NavigationCommand | VoiceCommand | Error | SpeechRecognitionResult;
  timestamp: number;
}

export type VoiceEventListener = (event: VoiceNavigationEvent) => void;

// Browser Speech Recognition Types (extending native types)
export interface ExtendedSpeechRecognition extends SpeechRecognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  serviceURI: string;
  grammars: SpeechGrammarList;
}

export interface ExtendedSpeechRecognitionEvent extends SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
  interpretation: unknown;
  emma: Document;
}