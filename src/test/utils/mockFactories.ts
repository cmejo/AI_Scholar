/**
 * Type-safe mock factories for common testing patterns
 */

import { vi, type MockedFunction } from 'vitest';
import type {
    APIError,
    ErrorSeverity,
    ErrorType,
    FormError,
    StandardError
} from '../../types/api';
import type {
    ChatMessage,
    ChatResponse,
    DocumentMetadata,
    SearchResult
} from '../../types/ui';
import type {
    SpeechRecognitionResult,
    TextToSpeechOptions,
    VoiceConfig
} from '../../types/voice';

/**
 * Mock factory for API errors with proper TypeScript interfaces
 */
export const createMockAPIError = (
  overrides: Partial<APIError> = {}
): APIError => ({
  type: 'NETWORK_ERROR',
  code: 'NETWORK_ERROR',
  message: 'Mock API error',
  severity: 'medium' as ErrorSeverity,
  timestamp: new Date(),
  details: {},
  ...overrides,
});

/**
 * Mock factory for standard errors
 */
export const createMockStandardError = (
  overrides: Partial<StandardError> = {}
): StandardError => ({
  id: `error_${Date.now()}_mock`,
  type: 'COMPONENT_ERROR' as ErrorType,
  code: 'COMPONENT_ERROR',
  message: 'Mock standard error',
  severity: 'medium' as ErrorSeverity,
  timestamp: new Date(),
  recoverable: true,
  retryable: false,
  userMessage: 'A mock error occurred',
  details: {},
  ...overrides,
});

/**
 * Mock factory for form errors
 */
export const createMockFormError = (
  overrides: Partial<FormError> = {}
): FormError => ({
  field: 'mockField',
  message: 'Mock form error',
  code: 'MOCK_ERROR',
  value: 'mockValue',
  ...overrides,
});

/**
 * Mock factory for voice configuration
 */
export const createMockVoiceConfig = (
  overrides: Partial<VoiceConfig> = {}
): VoiceConfig => ({
  language: 'en-US',
  voice: 'default',
  rate: 1.0,
  pitch: 1.0,
  volume: 1.0,
  continuous: true,
  interimResults: true,
  maxAlternatives: 1,
  ...overrides,
});

/**
 * Mock factory for speech recognition results
 */
export const createMockSpeechResult = (
  overrides: Partial<SpeechRecognitionResult> = {}
): SpeechRecognitionResult => ({
  text: 'Mock speech recognition result',
  confidence: 0.95,
  language: 'en-US',
  timestamp: Date.now(),
  isFinal: true,
  alternatives: [],
  ...overrides,
});

/**
 * Mock factory for text-to-speech options
 */
export const createMockTTSOptions = (
  overrides: Partial<TextToSpeechOptions> = {}
): TextToSpeechOptions => ({
  voice: 'default',
  rate: 1.0,
  pitch: 1.0,
  volume: 1.0,
  language: 'en-US',
  ...overrides,
});

/**
 * Mock factory for chat messages
 */
export const createMockChatMessage = (
  overrides: Partial<ChatMessage> = {}
): ChatMessage => ({
  id: `msg_${Date.now()}_mock`,
  content: 'Mock chat message',
  role: 'user',
  timestamp: new Date(),
  metadata: {},
  ...overrides,
});

/**
 * Mock factory for chat responses
 */
export const createMockChatResponse = (
  overrides: Partial<ChatResponse> = {}
): ChatResponse => ({
  id: `response_${Date.now()}_mock`,
  content: 'Mock chat response',
  role: 'assistant',
  timestamp: new Date(),
  sources: [],
  confidence: 0.9,
  processingTime: 1500,
  metadata: {},
  ...overrides,
});

/**
 * Mock factory for document metadata
 */
export const createMockDocumentMetadata = (
  overrides: Partial<DocumentMetadata> = {}
): DocumentMetadata => ({
  id: `doc_${Date.now()}_mock`,
  title: 'Mock Document',
  author: 'Mock Author',
  type: 'pdf',
  size: 1024000,
  uploadDate: new Date(),
  lastModified: new Date(),
  tags: ['mock', 'test'],
  summary: 'Mock document summary',
  ...overrides,
});

/**
 * Mock factory for search results
 */
export const createMockSearchResult = (
  overrides: Partial<SearchResult> = {}
): SearchResult => ({
  id: `result_${Date.now()}_mock`,
  title: 'Mock Search Result',
  content: 'Mock search result content',
  score: 0.85,
  source: 'mock-source.pdf',
  metadata: createMockDocumentMetadata(),
  highlights: ['mock highlight'],
  ...overrides,
});

/**
 * Mock factory for fetch responses
 */
export const createMockFetchResponse = <T = any>(
  data: T,
  options: {
    status?: number;
    statusText?: string;
    headers?: Record<string, string>;
  } = {}
): Response => {
  const { status = 200, statusText = 'OK', headers = {} } = options;
  
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: new Headers(headers),
    json: vi.fn().mockResolvedValue(data),
    text: vi.fn().mockResolvedValue(JSON.stringify(data)),
    blob: vi.fn().mockResolvedValue(new Blob([JSON.stringify(data)])),
    arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(0)),
    clone: vi.fn().mockReturnThis(),
  } as unknown as Response;
};

/**
 * Mock factory for Web Speech API SpeechRecognition
 */
export const createMockSpeechRecognition = () => {
  const mockRecognition = {
    start: vi.fn(),
    stop: vi.fn(),
    abort: vi.fn(),
    continuous: false,
    interimResults: false,
    lang: 'en-US',
    maxAlternatives: 1,
    onresult: null as ((event: any) => void) | null,
    onerror: null as ((event: any) => void) | null,
    onstart: null as ((event: any) => void) | null,
    onend: null as ((event: any) => void) | null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };

  return mockRecognition;
};

/**
 * Mock factory for Web Speech API SpeechSynthesis
 */
export const createMockSpeechSynthesis = () => {
  const mockSynthesis = {
    speak: vi.fn(),
    cancel: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    getVoices: vi.fn(() => [
      { name: 'Test Voice 1', lang: 'en-US', voiceURI: 'test1', default: true },
      { name: 'Test Voice 2', lang: 'en-GB', voiceURI: 'test2', default: false },
    ]),
    speaking: false,
    pending: false,
    paused: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };

  return mockSynthesis;
};

/**
 * Mock factory for MediaDevices
 */
export const createMockMediaDevices = () => ({
  getUserMedia: vi.fn(() => 
    Promise.resolve({
      getTracks: () => [{ stop: vi.fn() }],
      getAudioTracks: () => [{ stop: vi.fn() }],
      getVideoTracks: () => [],
      active: true,
      id: 'mock-stream-id',
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })
  ),
  enumerateDevices: vi.fn(() => 
    Promise.resolve([
      { deviceId: 'mock-audio-input', kind: 'audioinput', label: 'Mock Microphone' },
      { deviceId: 'mock-audio-output', kind: 'audiooutput', label: 'Mock Speaker' },
    ])
  ),
});

/**
 * Mock factory for AudioContext
 */
export const createMockAudioContext = () => ({
  createBufferSource: vi.fn(() => ({
    connect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
  })),
  createBiquadFilter: vi.fn(() => ({
    connect: vi.fn(),
    frequency: { value: 0 },
    Q: { value: 0 },
    gain: { value: 0 },
  })),
  createAnalyser: vi.fn(() => ({
    connect: vi.fn(),
    getByteFrequencyData: vi.fn(),
    getByteTimeDomainData: vi.fn(),
    fftSize: 2048,
    frequencyBinCount: 1024,
  })),
  decodeAudioData: vi.fn(() => Promise.resolve({})),
  close: vi.fn(() => Promise.resolve()),
  state: 'running',
  sampleRate: 44100,
  destination: {},
});

/**
 * Type-safe mock function creator
 */
export const createMockFunction = <T extends (...args: any[]) => any>(
  implementation?: T
): MockedFunction<T> => {
  return vi.fn(implementation) as MockedFunction<T>;
};

/**
 * Mock factory for localStorage
 */
export const createMockStorage = () => {
  const storage = new Map<string, string>();
  
  return {
    getItem: vi.fn((key: string) => storage.get(key) || null),
    setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
    removeItem: vi.fn((key: string) => storage.delete(key)),
    clear: vi.fn(() => storage.clear()),
    length: 0,
    key: vi.fn((index: number) => Array.from(storage.keys())[index] || null),
  };
};

/**
 * Mock factory for IntersectionObserver
 */
export const createMockIntersectionObserver = () => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '0px',
  thresholds: [0],
});

/**
 * Mock factory for ResizeObserver
 */
export const createMockResizeObserver = () => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
});

/**
 * Advanced mock factories for complex scenarios
 */

/**
 * Mock factory for React components with proper TypeScript support
 */
export const createMockComponent = <P extends Record<string, any>>(
  displayName: string,
  defaultProps?: Partial<P>
): React.ComponentType<P> => {
  const MockComponent = vi.fn().mockImplementation((props: P) => {
    return React.createElement('div', {
      'data-testid': `mock-${displayName.toLowerCase()}`,
      'data-props': JSON.stringify({ ...defaultProps, ...props }),
    }, `Mock ${displayName}`);
  });

  MockComponent.displayName = `Mock${displayName}`;
  return MockComponent as React.ComponentType<P>;
};

/**
 * Mock factory for React hooks with state management
 */
export const createMockHook = <T, P extends any[]>(
  initialValue: T,
  implementation?: (...args: P) => T
): {
  hook: MockedFunction<(...args: P) => T>;
  setValue: (value: T) => void;
  getValue: () => T;
  reset: () => void;
} => {
  let currentValue = initialValue;
  
  const hook = vi.fn().mockImplementation((...args: P) => {
    if (implementation) {
      currentValue = implementation(...args);
    }
    return currentValue;
  });

  return {
    hook,
    setValue: (value: T) => {
      currentValue = value;
      hook.mockReturnValue(value);
    },
    getValue: () => currentValue,
    reset: () => {
      currentValue = initialValue;
      hook.mockClear();
      hook.mockReturnValue(initialValue);
    },
  };
};

/**
 * Mock factory for async operations with controllable timing
 */
export const createMockAsyncOperation = <T>(
  result: T,
  options: {
    delay?: number;
    shouldFail?: boolean;
    error?: Error;
  } = {}
): {
  operation: MockedFunction<() => Promise<T>>;
  resolve: () => void;
  reject: (error?: Error) => void;
  pending: boolean;
} => {
  const { delay = 0, shouldFail = false, error = new Error('Mock error') } = options;
  let resolveFn: (value: T) => void;
  let rejectFn: (error: Error) => void;
  let pending = false;

  const operation = vi.fn().mockImplementation(() => {
    pending = true;
    return new Promise<T>((resolve, reject) => {
      resolveFn = (value: T) => {
        pending = false;
        resolve(value);
      };
      rejectFn = (err: Error) => {
        pending = false;
        reject(err);
      };

      if (delay > 0) {
        setTimeout(() => {
          if (shouldFail) {
            rejectFn(error);
          } else {
            resolveFn(result);
          }
        }, delay);
      } else {
        if (shouldFail) {
          rejectFn(error);
        } else {
          resolveFn(result);
        }
      }
    });
  });

  return {
    operation,
    resolve: () => resolveFn?.(result),
    reject: (err = error) => rejectFn?.(err),
    pending,
  };
};

/**
 * Mock factory for event emitters
 */
export const createMockEventEmitter = <T extends Record<string, any[]>>(): {
  emitter: {
    on: MockedFunction<(event: keyof T, listener: (...args: any[]) => void) => void>;
    off: MockedFunction<(event: keyof T, listener: (...args: any[]) => void) => void>;
    emit: MockedFunction<(event: keyof T, ...args: any[]) => void>;
    once: MockedFunction<(event: keyof T, listener: (...args: any[]) => void) => void>;
    removeAllListeners: MockedFunction<(event?: keyof T) => void>;
  };
  emit: (event: keyof T, ...args: T[keyof T]) => void;
  getListeners: (event: keyof T) => ((...args: any[]) => void)[];
} => {
  const listeners = new Map<keyof T, Set<(...args: any[]) => void>>();

  const on = vi.fn((event: keyof T, listener: (...args: any[]) => void) => {
    if (!listeners.has(event)) {
      listeners.set(event, new Set());
    }
    listeners.get(event)!.add(listener);
  });

  const off = vi.fn((event: keyof T, listener: (...args: any[]) => void) => {
    listeners.get(event)?.delete(listener);
  });

  const emit = vi.fn((event: keyof T, ...args: any[]) => {
    listeners.get(event)?.forEach(listener => listener(...args));
  });

  const once = vi.fn((event: keyof T, listener: (...args: any[]) => void) => {
    const onceListener = (...args: any[]) => {
      listener(...args);
      off(event, onceListener);
    };
    on(event, onceListener);
  });

  const removeAllListeners = vi.fn((event?: keyof T) => {
    if (event) {
      listeners.delete(event);
    } else {
      listeners.clear();
    }
  });

  return {
    emitter: {
      on,
      off,
      emit,
      once,
      removeAllListeners,
    },
    emit: (event: keyof T, ...args: T[keyof T]) => {
      listeners.get(event)?.forEach(listener => listener(...args));
    },
    getListeners: (event: keyof T) => Array.from(listeners.get(event) || []),
  };
};

/**
 * Mock factory for file system operations
 */
export const createMockFileSystem = (): {
  readFile: MockedFunction<(path: string) => Promise<string>>;
  writeFile: MockedFunction<(path: string, content: string) => Promise<void>>;
  deleteFile: MockedFunction<(path: string) => Promise<void>>;
  exists: MockedFunction<(path: string) => Promise<boolean>>;
  files: Map<string, string>;
  reset: () => void;
} => {
  const files = new Map<string, string>();

  const readFile = vi.fn().mockImplementation(async (path: string) => {
    if (!files.has(path)) {
      throw new Error(`File not found: ${path}`);
    }
    return files.get(path)!;
  });

  const writeFile = vi.fn().mockImplementation(async (path: string, content: string) => {
    files.set(path, content);
  });

  const deleteFile = vi.fn().mockImplementation(async (path: string) => {
    if (!files.has(path)) {
      throw new Error(`File not found: ${path}`);
    }
    files.delete(path);
  });

  const exists = vi.fn().mockImplementation(async (path: string) => {
    return files.has(path);
  });

  return {
    readFile,
    writeFile,
    deleteFile,
    exists,
    files,
    reset: () => {
      files.clear();
      readFile.mockClear();
      writeFile.mockClear();
      deleteFile.mockClear();
      exists.mockClear();
    },
  };
};

/**
 * Mock factory for database operations
 */
export const createMockDatabase = <T extends Record<string, any>>(): {
  find: MockedFunction<(query: Partial<T>) => Promise<T[]>>;
  findOne: MockedFunction<(query: Partial<T>) => Promise<T | null>>;
  create: MockedFunction<(data: Omit<T, 'id'>) => Promise<T>>;
  update: MockedFunction<(id: string, data: Partial<T>) => Promise<T>>;
  delete: MockedFunction<(id: string) => Promise<void>>;
  data: Map<string, T>;
  reset: () => void;
} => {
  const data = new Map<string, T>();
  let idCounter = 1;

  const find = vi.fn().mockImplementation(async (query: Partial<T>) => {
    const results: T[] = [];
    for (const item of data.values()) {
      const matches = Object.entries(query).every(([key, value]) => 
        item[key] === value
      );
      if (matches) {
        results.push(item);
      }
    }
    return results;
  });

  const findOne = vi.fn().mockImplementation(async (query: Partial<T>) => {
    const results = await find(query);
    return results[0] || null;
  });

  const create = vi.fn().mockImplementation(async (itemData: Omit<T, 'id'>) => {
    const id = `mock_id_${idCounter++}`;
    const item = { ...itemData, id } as T;
    data.set(id, item);
    return item;
  });

  const update = vi.fn().mockImplementation(async (id: string, updateData: Partial<T>) => {
    const existing = data.get(id);
    if (!existing) {
      throw new Error(`Item not found: ${id}`);
    }
    const updated = { ...existing, ...updateData };
    data.set(id, updated);
    return updated;
  });

  const deleteItem = vi.fn().mockImplementation(async (id: string) => {
    if (!data.has(id)) {
      throw new Error(`Item not found: ${id}`);
    }
    data.delete(id);
  });

  return {
    find,
    findOne,
    create,
    update,
    delete: deleteItem,
    data,
    reset: () => {
      data.clear();
      idCounter = 1;
      find.mockClear();
      findOne.mockClear();
      create.mockClear();
      update.mockClear();
      deleteItem.mockClear();
    },
  };
};

/**
 * Mock factory for performance monitoring
 */
export const createMockPerformanceMonitor = (): {
  mark: MockedFunction<(name: string) => void>;
  measure: MockedFunction<(name: string, startMark?: string, endMark?: string) => number>;
  getEntries: MockedFunction<() => PerformanceEntry[]>;
  clearMarks: MockedFunction<(name?: string) => void>;
  clearMeasures: MockedFunction<(name?: string) => void>;
  marks: Map<string, number>;
  measures: Map<string, number>;
  reset: () => void;
} => {
  const marks = new Map<string, number>();
  const measures = new Map<string, number>();

  const mark = vi.fn().mockImplementation((name: string) => {
    marks.set(name, performance.now());
  });

  const measure = vi.fn().mockImplementation((name: string, startMark?: string, endMark?: string) => {
    const startTime = startMark ? marks.get(startMark) || 0 : 0;
    const endTime = endMark ? marks.get(endMark) || performance.now() : performance.now();
    const duration = endTime - startTime;
    measures.set(name, duration);
    return duration;
  });

  const getEntries = vi.fn().mockImplementation(() => {
    const entries: PerformanceEntry[] = [];
    
    marks.forEach((startTime, name) => {
      entries.push({
        name,
        entryType: 'mark',
        startTime,
        duration: 0,
        toJSON: () => ({ name, entryType: 'mark', startTime, duration: 0 }),
      });
    });

    measures.forEach((duration, name) => {
      entries.push({
        name,
        entryType: 'measure',
        startTime: 0,
        duration,
        toJSON: () => ({ name, entryType: 'measure', startTime: 0, duration }),
      });
    });

    return entries;
  });

  const clearMarks = vi.fn().mockImplementation((name?: string) => {
    if (name) {
      marks.delete(name);
    } else {
      marks.clear();
    }
  });

  const clearMeasures = vi.fn().mockImplementation((name?: string) => {
    if (name) {
      measures.delete(name);
    } else {
      measures.clear();
    }
  });

  return {
    mark,
    measure,
    getEntries,
    clearMarks,
    clearMeasures,
    marks,
    measures,
    reset: () => {
      marks.clear();
      measures.clear();
      mark.mockClear();
      measure.mockClear();
      getEntries.mockClear();
      clearMarks.mockClear();
      clearMeasures.mockClear();
    },
  };
};