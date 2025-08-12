/**
 * Test helper utilities for common testing patterns
 */

import type { RenderResult } from '@testing-library/react';
import { act, waitFor } from '@testing-library/react';
import { vi, type MockedFunction } from 'vitest';

/**
 * Wait for a specific condition to be true with timeout
 */
export const waitForCondition = async (
  condition: () => boolean | Promise<boolean>,
  timeout = 5000,
  interval = 100
): Promise<void> => {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const result = await condition();
    if (result) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  throw new Error(`Condition not met within ${timeout}ms`);
};

/**
 * Wait for multiple async operations to complete
 */
export const waitForAll = async (
  promises: Promise<any>[],
  timeout = 10000
): Promise<any[]> => {
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error(`Operations timed out after ${timeout}ms`)), timeout);
  });
  
  return Promise.race([
    Promise.all(promises),
    timeoutPromise
  ]) as Promise<any[]>;
};

/**
 * Simulate user typing with realistic delays
 */
export const simulateTyping = async (
  element: HTMLElement,
  text: string,
  delay = 50
): Promise<void> => {
  for (const char of text) {
    await act(async () => {
      element.focus();
      // Simulate keydown, keypress, input, keyup events
      const keydownEvent = new KeyboardEvent('keydown', { key: char });
      const keypressEvent = new KeyboardEvent('keypress', { key: char });
      const inputEvent = new InputEvent('input', { data: char });
      const keyupEvent = new KeyboardEvent('keyup', { key: char });
      
      element.dispatchEvent(keydownEvent);
      element.dispatchEvent(keypressEvent);
      
      if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
        element.value += char;
      }
      
      element.dispatchEvent(inputEvent);
      element.dispatchEvent(keyupEvent);
      
      await new Promise(resolve => setTimeout(resolve, delay));
    });
  }
};

/**
 * Simulate file upload
 */
export const simulateFileUpload = (
  input: HTMLInputElement,
  files: File[]
): void => {
  Object.defineProperty(input, 'files', {
    value: files,
    writable: false,
  });
  
  const event = new Event('change', { bubbles: true });
  input.dispatchEvent(event);
};

/**
 * Create a mock file for testing
 */
export const createMockFile = (
  name: string,
  content: string,
  type = 'text/plain'
): File => {
  const blob = new Blob([content], { type });
  return new File([blob], name, { type });
};

/**
 * Mock console methods and capture their calls
 */
export const mockConsole = () => {
  const originalConsole = { ...console };
  const consoleMocks = {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    debug: vi.fn(),
  };
  
  Object.assign(console, consoleMocks);
  
  return {
    mocks: consoleMocks,
    restore: () => Object.assign(console, originalConsole),
  };
};

/**
 * Mock Date.now() for consistent timestamps in tests
 */
export const mockDateNow = (timestamp?: number) => {
  const mockTimestamp = timestamp || Date.now();
  const originalDateNow = Date.now;
  
  Date.now = vi.fn(() => mockTimestamp);
  
  return {
    restore: () => {
      Date.now = originalDateNow;
    },
    advance: (ms: number) => {
      (Date.now as MockedFunction<typeof Date.now>).mockReturnValue(mockTimestamp + ms);
    },
  };
};

/**
 * Mock Math.random() for predictable random values
 */
export const mockMathRandom = (values: number[] | number) => {
  const originalRandom = Math.random;
  const valueArray = Array.isArray(values) ? values : [values];
  let index = 0;
  
  Math.random = vi.fn(() => {
    const value = valueArray[index % valueArray.length];
    index++;
    return value;
  });
  
  return {
    restore: () => {
      Math.random = originalRandom;
    },
  };
};

/**
 * Create a promise that can be resolved/rejected externally
 */
export const createControllablePromise = <T = any>() => {
  let resolve: (value: T | PromiseLike<T>) => void;
  let reject: (reason?: any) => void;
  
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  
  return {
    promise,
    resolve: resolve!,
    reject: reject!,
  };
};

/**
 * Flush all pending promises and timers
 */
export const flushPromises = async (): Promise<void> => {
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, 0));
  });
};

/**
 * Mock window.location
 */
export const mockLocation = (url: string) => {
  const originalLocation = window.location;
  
  // Create a mock location object
  const mockLocationObj = new URL(url);
  Object.defineProperty(window, 'location', {
    value: {
      ...mockLocationObj,
      assign: vi.fn(),
      replace: vi.fn(),
      reload: vi.fn(),
    },
    writable: true,
  });
  
  return {
    restore: () => {
      Object.defineProperty(window, 'location', {
        value: originalLocation,
        writable: true,
      });
    },
  };
};

/**
 * Mock window.matchMedia
 */
export const mockMatchMedia = (matches = false) => {
  const originalMatchMedia = window.matchMedia;
  
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
  
  return {
    restore: () => {
      window.matchMedia = originalMatchMedia;
    },
  };
};

/**
 * Mock clipboard API
 */
export const mockClipboard = () => {
  const originalClipboard = navigator.clipboard;
  
  const clipboardMock = {
    writeText: vi.fn(() => Promise.resolve()),
    readText: vi.fn(() => Promise.resolve('mock clipboard text')),
    write: vi.fn(() => Promise.resolve()),
    read: vi.fn(() => Promise.resolve([])),
  };
  
  Object.defineProperty(navigator, 'clipboard', {
    value: clipboardMock,
    writable: true,
  });
  
  return {
    mocks: clipboardMock,
    restore: () => {
      Object.defineProperty(navigator, 'clipboard', {
        value: originalClipboard,
        writable: true,
      });
    },
  };
};

/**
 * Test utility for checking accessibility
 */
export const checkAccessibility = async (container: HTMLElement): Promise<void> => {
  // Check for basic accessibility requirements
  const buttons = container.querySelectorAll('button');
  const inputs = container.querySelectorAll('input, textarea, select');
  const images = container.querySelectorAll('img');
  const links = container.querySelectorAll('a');
  
  // Check buttons have accessible names
  buttons.forEach((button, index) => {
    const hasAccessibleName = 
      button.getAttribute('aria-label') ||
      button.getAttribute('aria-labelledby') ||
      button.textContent?.trim() ||
      button.querySelector('[aria-hidden="false"]')?.textContent?.trim();
    
    if (!hasAccessibleName) {
      throw new Error(`Button at index ${index} lacks an accessible name`);
    }
  });
  
  // Check form inputs have labels
  inputs.forEach((input, index) => {
    const hasLabel = 
      input.getAttribute('aria-label') ||
      input.getAttribute('aria-labelledby') ||
      container.querySelector(`label[for="${input.id}"]`) ||
      input.closest('label');
    
    if (!hasLabel && input.getAttribute('type') !== 'hidden') {
      throw new Error(`Input at index ${index} lacks a label`);
    }
  });
  
  // Check images have alt text
  images.forEach((img, index) => {
    const hasAltText = 
      img.getAttribute('alt') !== null ||
      img.getAttribute('aria-label') ||
      img.getAttribute('aria-labelledby') ||
      img.getAttribute('role') === 'presentation';
    
    if (!hasAltText) {
      throw new Error(`Image at index ${index} lacks alt text`);
    }
  });
  
  // Check links have accessible names
  links.forEach((link, index) => {
    const hasAccessibleName = 
      link.getAttribute('aria-label') ||
      link.getAttribute('aria-labelledby') ||
      link.textContent?.trim();
    
    if (!hasAccessibleName) {
      throw new Error(`Link at index ${index} lacks an accessible name`);
    }
  });
};

/**
 * Utility to test component with different viewport sizes
 */
export const testResponsiveComponent = async (
  renderComponent: () => RenderResult,
  viewports: { width: number; height: number; name: string }[]
): Promise<void> => {
  for (const viewport of viewports) {
    // Mock window dimensions
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: viewport.width,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: viewport.height,
    });
    
    // Trigger resize event
    window.dispatchEvent(new Event('resize'));
    
    // Re-render component
    const { container } = renderComponent();
    
    // Wait for any responsive changes to take effect
    await waitFor(() => {
      // Component should be rendered without errors
      expect(container).toBeInTheDocument();
    });
  }
};

/**
 * Utility to test keyboard navigation
 */
export const testKeyboardNavigation = async (
  container: HTMLElement,
  expectedFocusOrder: string[]
): Promise<void> => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  expect(focusableElements).toHaveLength(expectedFocusOrder.length);
  
  // Test Tab navigation
  for (let i = 0; i < expectedFocusOrder.length; i++) {
    const element = focusableElements[i] as HTMLElement;
    element.focus();
    
    await waitFor(() => {
      expect(document.activeElement).toBe(element);
    });
    
    // Check if element matches expected selector or text content
    const expectedSelector = expectedFocusOrder[i];
    const matches = 
      element.matches(expectedSelector) ||
      element.textContent?.includes(expectedSelector) ||
      element.getAttribute('aria-label')?.includes(expectedSelector);
    
    expect(matches).toBe(true);
  }
};

/**
 * Utility to test error boundaries
 */
export const testErrorBoundary = async (
  renderWithErrorBoundary: () => RenderResult,
  triggerError: () => void
): Promise<void> => {
  const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  
  try {
    const { container } = renderWithErrorBoundary();
    
    // Trigger the error
    await act(async () => {
      triggerError();
    });
    
    // Wait for error boundary to catch the error
    await waitFor(() => {
      expect(container.textContent).toMatch(/something went wrong|error occurred/i);
    });
    
    expect(consoleSpy).toHaveBeenCalled();
  } finally {
    consoleSpy.mockRestore();
  }
};

/**
 * Advanced test utilities for complex scenarios
 */

/**
 * Mock API responses with type safety
 */
export const mockTypedAPIResponse = <T>(
  endpoint: string,
  response: T,
  options: {
    delay?: number;
    status?: number;
    headers?: Record<string, string>;
  } = {}
): MockedFunction<typeof fetch> => {
  const { delay = 0, status = 200, headers = {} } = options;
  
  return vi.fn().mockImplementation(async (url: string) => {
    if (url.includes(endpoint)) {
      if (delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      return {
        ok: status >= 200 && status < 300,
        status,
        statusText: status === 200 ? 'OK' : 'Error',
        headers: new Headers(headers),
        json: () => Promise.resolve(response),
        text: () => Promise.resolve(JSON.stringify(response)),
        blob: () => Promise.resolve(new Blob([JSON.stringify(response)])),
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
        clone: () => mockTypedAPIResponse(endpoint, response, options),
      };
    }
    
    throw new Error(`Unmocked endpoint: ${url}`);
  });
};

/**
 * Mock error responses with proper error types
 */
export const mockAPIError = (
  endpoint: string,
  error: APIError | StandardError,
  options: {
    delay?: number;
    status?: number;
  } = {}
): MockedFunction<typeof fetch> => {
  const { delay = 0, status = 500 } = options;
  
  return vi.fn().mockImplementation(async (url: string) => {
    if (url.includes(endpoint)) {
      if (delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      const errorResponse = {
        ok: false,
        status,
        statusText: 'Error',
        headers: new Headers({ 'Content-Type': 'application/json' }),
        json: () => Promise.resolve({ error }),
        text: () => Promise.resolve(JSON.stringify({ error })),
        blob: () => Promise.resolve(new Blob([JSON.stringify({ error })])),
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
        clone: () => mockAPIError(endpoint, error, options),
      };
      
      throw Object.assign(new Error(error.message), error);
    }
    
    throw new Error(`Unmocked endpoint: ${url}`);
  });
};

/**
 * Create a comprehensive test environment with all necessary mocks
 */
export const createTestEnvironment = (config: {
  mockAPIs?: boolean;
  mockStorage?: boolean;
  mockWebAPIs?: boolean;
  mockMediaDevices?: boolean;
  mockNotifications?: boolean;
} = {}) => {
  const {
    mockAPIs = true,
    mockStorage = true,
    mockWebAPIs = true,
    mockMediaDevices = true,
    mockNotifications = true,
  } = config;

  const mocks: Record<string, any> = {};

  if (mockAPIs) {
    mocks.fetch = vi.fn();
    globalThis.fetch = mocks.fetch;
  }

  if (mockStorage) {
    mocks.localStorage = createMockStorage();
    mocks.sessionStorage = createMockStorage();
    Object.defineProperty(window, 'localStorage', { value: mocks.localStorage });
    Object.defineProperty(window, 'sessionStorage', { value: mocks.sessionStorage });
  }

  if (mockWebAPIs) {
    mocks.intersectionObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }));
    mocks.resizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }));
    mocks.mutationObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      disconnect: vi.fn(),
      takeRecords: vi.fn(() => []),
    }));

    globalThis.IntersectionObserver = mocks.intersectionObserver;
    globalThis.ResizeObserver = mocks.resizeObserver;
    globalThis.MutationObserver = mocks.mutationObserver;
  }

  if (mockMediaDevices) {
    mocks.mediaDevices = {
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
    };

    Object.defineProperty(navigator, 'mediaDevices', { 
      value: mocks.mediaDevices,
      writable: true,
    });
  }

  if (mockNotifications) {
    mocks.notification = vi.fn();
    mocks.notification.permission = 'granted';
    mocks.notification.requestPermission = vi.fn(() => Promise.resolve('granted'));
    Object.defineProperty(window, 'Notification', { value: mocks.notification });
  }

  return {
    mocks,
    cleanup: () => {
      Object.keys(mocks).forEach(key => {
        if (mocks[key].mockRestore) {
          mocks[key].mockRestore();
        }
      });
    },
  };
};

/**
 * Mock form validation with proper error types
 */
export const mockFormValidation = (
  errors: FormError[] = []
): {
  validate: MockedFunction<(data: any) => Promise<{ isValid: boolean; errors: FormError[] }>>;
  reset: () => void;
} => {
  const validate = vi.fn().mockImplementation(async (data: any) => {
    // Simulate validation delay
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const validationErrors = errors.filter(error => {
      const fieldValue = data[error.field];
      return !fieldValue || fieldValue === error.value;
    });

    return {
      isValid: validationErrors.length === 0,
      errors: validationErrors,
    };
  });

  return {
    validate,
    reset: () => validate.mockClear(),
  };
};

/**
 * Mock voice recognition with proper types
 */
export const mockVoiceRecognition = (
  results: SpeechRecognitionResult[] = []
): {
  recognition: any;
  simulateResult: (result: SpeechRecognitionResult) => void;
  simulateError: (error: string) => void;
} => {
  const recognition = {
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

  const simulateResult = (result: SpeechRecognitionResult) => {
    if (recognition.onresult) {
      const event = {
        results: [{
          0: { transcript: result.text, confidence: result.confidence },
          isFinal: result.isFinal,
          length: 1,
        }],
        resultIndex: 0,
      };
      recognition.onresult(event);
    }
  };

  const simulateError = (error: string) => {
    if (recognition.onerror) {
      recognition.onerror({ error });
    }
  };

  // Auto-simulate results if provided
  if (results.length > 0) {
    recognition.start.mockImplementation(() => {
      setTimeout(() => {
        results.forEach(result => simulateResult(result));
      }, 100);
    });
  }

  return {
    recognition,
    simulateResult,
    simulateError,
  };
};

/**
 * Mock drag and drop operations
 */
export const mockDragAndDrop = () => {
  const createDataTransfer = (files: File[] = []) => ({
    files: {
      length: files.length,
      item: (index: number) => files[index] || null,
      [Symbol.iterator]: function* () {
        for (const file of files) {
          yield file;
        }
      },
    },
    types: files.length > 0 ? ['Files'] : [],
    getData: vi.fn(),
    setData: vi.fn(),
    clearData: vi.fn(),
    setDragImage: vi.fn(),
  });

  const simulateDragOver = (element: HTMLElement, files: File[] = []) => {
    const event = new DragEvent('dragover', {
      bubbles: true,
      cancelable: true,
      dataTransfer: createDataTransfer(files) as any,
    });
    element.dispatchEvent(event);
  };

  const simulateDrop = (element: HTMLElement, files: File[] = []) => {
    const event = new DragEvent('drop', {
      bubbles: true,
      cancelable: true,
      dataTransfer: createDataTransfer(files) as any,
    });
    element.dispatchEvent(event);
  };

  return {
    simulateDragOver,
    simulateDrop,
    createDataTransfer,
  };
};

/**
 * Mock WebSocket with proper event handling
 */
export const mockWebSocket = () => {
  const mockWS = {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: WebSocket.OPEN,
    url: 'ws://localhost:3000/ws',
    protocol: '',
    extensions: '',
    bufferedAmount: 0,
    binaryType: 'blob' as BinaryType,
    onopen: null as ((event: Event) => void) | null,
    onclose: null as ((event: CloseEvent) => void) | null,
    onmessage: null as ((event: MessageEvent) => void) | null,
    onerror: null as ((event: Event) => void) | null,
    dispatchEvent: vi.fn(),
    CONNECTING: WebSocket.CONNECTING,
    OPEN: WebSocket.OPEN,
    CLOSING: WebSocket.CLOSING,
    CLOSED: WebSocket.CLOSED,
  };

  const originalWebSocket = globalThis.WebSocket;
  globalThis.WebSocket = vi.fn(() => mockWS) as any;

  const simulateOpen = () => {
    const event = new Event('open');
    if (mockWS.onopen) mockWS.onopen(event);
  };

  const simulateMessage = (data: any) => {
    const event = new MessageEvent('message', { 
      data: typeof data === 'string' ? data : JSON.stringify(data) 
    });
    if (mockWS.onmessage) mockWS.onmessage(event);
  };

  const simulateClose = (code = 1000, reason = 'Normal closure') => {
    mockWS.readyState = WebSocket.CLOSED;
    const event = new CloseEvent('close', { code, reason });
    if (mockWS.onclose) mockWS.onclose(event);
  };

  const simulateError = () => {
    const event = new Event('error');
    if (mockWS.onerror) mockWS.onerror(event);
  };

  const restore = () => {
    globalThis.WebSocket = originalWebSocket;
  };

  return {
    mockWS,
    simulateOpen,
    simulateMessage,
    simulateClose,
    simulateError,
    restore,
  };
};

/**
 * Create a mock storage implementation
 */
const createMockStorage = () => {
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