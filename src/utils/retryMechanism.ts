interface RetryOptions {
  maxAttempts: number;
  delay: number;
  backoff: boolean;
  onRetry?: (attempt: number, error: Error) => void;
}

export class RetryableError extends Error {
  constructor(message: string, public isRetryable: boolean = true) {
    super(message);
    this.name = 'RetryableError';
  }
}

export const withRetry = async <T>(
  operation: () => Promise<T>,
  options: Partial<RetryOptions> = {}
): Promise<T> => {
  const {
    maxAttempts = 3,
    delay = 1000,
    backoff = true,
    onRetry
  } = options;

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      // Don't retry if it's the last attempt
      if (attempt === maxAttempts) {
        break;
      }

      // Don't retry if error is not retryable
      if (error instanceof RetryableError && !error.isRetryable) {
        break;
      }

      // Don't retry certain types of errors
      if (isNonRetryableError(error as Error)) {
        break;
      }

      // Call retry callback if provided
      if (onRetry) {
        onRetry(attempt, error as Error);
      }

      // Wait before retrying
      const waitTime = backoff ? delay * Math.pow(2, attempt - 1) : delay;
      await sleep(waitTime);
    }
  }

  throw lastError!;
};

const isNonRetryableError = (error: Error): boolean => {
  const nonRetryableMessages = [
    'not supported',
    'not allowed',
    'permission denied',
    'not found',
    'invalid',
  ];

  return nonRetryableMessages.some(message => 
    error.message.toLowerCase().includes(message)
  );
};

const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Voice-specific retry utilities
export const retryVoiceOperation = async <T>(
  operation: () => Promise<T>,
  operationType: 'recognition' | 'synthesis' | 'permission'
): Promise<T> => {
  const options: RetryOptions = {
    maxAttempts: operationType === 'permission' ? 1 : 3,
    delay: operationType === 'recognition' ? 500 : 1000,
    backoff: true,
    onRetry: (attempt, error) => {
      console.warn(`Voice ${operationType} failed (attempt ${attempt}):`, error.message);
    }
  };

  return withRetry(operation, options);
};

// Network connectivity check
export const checkNetworkConnectivity = (): boolean => {
  return navigator.onLine;
};

// Voice service health check
export const checkVoiceServiceHealth = async (): Promise<{
  speechRecognition: boolean;
  speechSynthesis: boolean;
  microphone: boolean;
}> => {
  const health = {
    speechRecognition: false,
    speechSynthesis: false,
    microphone: false,
  };

  // Check Speech Recognition
  try {
    if (window.SpeechRecognition || window.webkitSpeechRecognition) {
      health.speechRecognition = true;
    }
  } catch (error) {
    console.warn('Speech recognition health check failed:', error);
  }

  // Check Speech Synthesis
  try {
    if (window.speechSynthesis) {
      health.speechSynthesis = true;
    }
  } catch (error) {
    console.warn('Speech synthesis health check failed:', error);
  }

  // Check Microphone
  try {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      // Quick permission check without actually requesting access
      health.microphone = true;
    }
  } catch (error) {
    console.warn('Microphone health check failed:', error);
  }

  return health;
};

// Recovery strategies
export const getRecoveryStrategy = (error: Error): {
  strategy: string;
  action: () => Promise<void>;
  message: string;
} => {
  const errorMessage = error.message.toLowerCase();

  if (errorMessage.includes('microphone') || errorMessage.includes('permission')) {
    return {
      strategy: 'permission',
      action: async () => {
        // Guide user to enable permissions
        window.alert('Please enable microphone permissions in your browser settings and refresh the page.');
      },
      message: 'Microphone permissions need to be enabled'
    };
  }

  if (errorMessage.includes('network') || errorMessage.includes('connection')) {
    return {
      strategy: 'network',
      action: async () => {
        // Wait for network to recover
        await waitForNetwork();
      },
      message: 'Waiting for network connection to recover'
    };
  }

  if (errorMessage.includes('not supported')) {
    return {
      strategy: 'fallback',
      action: async () => {
        // Switch to text-only mode
        console.log('Switching to text-only mode');
      },
      message: 'Voice features not supported, using text-only mode'
    };
  }

  return {
    strategy: 'retry',
    action: async () => {
      // Generic retry after delay
      await sleep(2000);
    },
    message: 'Retrying voice operation'
  };
};

const waitForNetwork = (): Promise<void> => {
  return new Promise((resolve) => {
    if (navigator.onLine) {
      resolve();
      return;
    }

    const handleOnline = () => {
      window.removeEventListener('online', handleOnline);
      resolve();
    };

    window.addEventListener('online', handleOnline);
    
    // Timeout after 30 seconds
    setTimeout(() => {
      window.removeEventListener('online', handleOnline);
      resolve();
    }, 30000);
  });
};