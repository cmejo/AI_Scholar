interface BrowserCapabilities {
  speechRecognition: boolean;
  speechSynthesis: boolean;
  mediaDevices: boolean;
  permissions: boolean;
  webAudio: boolean;
}

interface BrowserInfo {
  name: string;
  version: string;
  isMobile: boolean;
  isIOS: boolean;
  isAndroid: boolean;
  capabilities: BrowserCapabilities;
}

export const detectBrowserCapabilities = (): BrowserCapabilities => {
  const capabilities: BrowserCapabilities = {
    speechRecognition: false,
    speechSynthesis: false,
    mediaDevices: false,
    permissions: false,
    webAudio: false,
  };

  // Check Speech Recognition API
  if (typeof window !== 'undefined') {
    capabilities.speechRecognition = !!(
      window.SpeechRecognition || 
      window.webkitSpeechRecognition
    );

    // Check Speech Synthesis API
    capabilities.speechSynthesis = !!(
      window.speechSynthesis && 
      window.SpeechSynthesisUtterance
    );

    // Check MediaDevices API
    capabilities.mediaDevices = !!(
      navigator.mediaDevices && 
      navigator.mediaDevices.getUserMedia
    );

    // Check Permissions API
    capabilities.permissions = !!(
      navigator.permissions && 
      navigator.permissions.query
    );

    // Check Web Audio API
    capabilities.webAudio = !!(
      window.AudioContext || 
      window.webkitAudioContext
    );
  }

  return capabilities;
};

export const getBrowserInfo = (): BrowserInfo => {
  const userAgent = navigator.userAgent;
  
  // Detect browser name and version
  let browserName = 'Unknown';
  let browserVersion = 'Unknown';
  
  if (userAgent.includes('Chrome')) {
    browserName = 'Chrome';
    const match = userAgent.match(/Chrome\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  } else if (userAgent.includes('Firefox')) {
    browserName = 'Firefox';
    const match = userAgent.match(/Firefox\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
    browserName = 'Safari';
    const match = userAgent.match(/Version\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  } else if (userAgent.includes('Edge')) {
    browserName = 'Edge';
    const match = userAgent.match(/Edge\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  }

  // Detect mobile and platform
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
  const isIOS = /iPad|iPhone|iPod/.test(userAgent);
  const isAndroid = /Android/.test(userAgent);

  return {
    name: browserName,
    version: browserVersion,
    isMobile,
    isIOS,
    isAndroid,
    capabilities: detectBrowserCapabilities(),
  };
};

export const getVoiceCompatibilityMessage = (browserInfo: BrowserInfo): string | null => {
  const { capabilities, name, isMobile, isIOS } = browserInfo;

  if (!capabilities.speechRecognition && !capabilities.speechSynthesis) {
    return `Voice features are not supported in ${name}. Please use Chrome, Edge, or Safari for the best experience.`;
  }

  if (!capabilities.speechRecognition) {
    return `Voice input is not supported in ${name}. Text-to-speech is available, but you won't be able to use voice commands.`;
  }

  if (!capabilities.speechSynthesis) {
    return `Text-to-speech is not supported in ${name}. Voice input is available, but responses won't be spoken aloud.`;
  }

  if (isIOS && isMobile) {
    return `Voice features work on iOS, but may require user interaction to start. Tap the microphone button to begin.`;
  }

  if (isMobile) {
    return `Voice features are available on mobile. Make sure to allow microphone permissions when prompted.`;
  }

  return null; // No compatibility issues
};

export const getRecommendedBrowser = (): string => {
  const browserInfo = getBrowserInfo();
  
  if (browserInfo.capabilities.speechRecognition && browserInfo.capabilities.speechSynthesis) {
    return `${browserInfo.name} supports all voice features.`;
  }

  if (browserInfo.isMobile) {
    if (browserInfo.isIOS) {
      return 'For the best experience on iOS, use Safari.';
    }
    return 'For the best experience on Android, use Chrome.';
  }

  return 'For the best voice experience, we recommend using Chrome or Edge.';
};

export const checkMicrophonePermissions = async (): Promise<{
  granted: boolean;
  error?: string;
}> => {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return {
        granted: false,
        error: 'Microphone access is not supported in this browser.'
      };
    }

    // Try to get microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Clean up the stream
    stream.getTracks().forEach(track => track.stop());
    
    return { granted: true };
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === 'NotAllowedError') {
        return {
          granted: false,
          error: 'Microphone access was denied. Please allow microphone permissions and try again.'
        };
      }
      if (error.name === 'NotFoundError') {
        return {
          granted: false,
          error: 'No microphone found. Please connect a microphone and try again.'
        };
      }
      if (error.name === 'NotSupportedError') {
        return {
          granted: false,
          error: 'Microphone access is not supported in this browser.'
        };
      }
    }
    
    return {
      granted: false,
      error: 'Failed to access microphone. Please check your browser settings.'
    };
  }
};

export const testSpeechSynthesis = (): Promise<boolean> => {
  return new Promise((resolve) => {
    if (!window.speechSynthesis) {
      resolve(false);
      return;
    }

    try {
      const utterance = new SpeechSynthesisUtterance('');
      utterance.volume = 0; // Silent test
      
      utterance.onend = () => resolve(true);
      utterance.onerror = () => resolve(false);
      
      // Timeout after 1 second
      setTimeout(() => resolve(false), 1000);
      
      window.speechSynthesis.speak(utterance);
    } catch (error) {
      resolve(false);
    }
  });
};

// Extend Window interface for TypeScript
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
    AudioContext: typeof AudioContext;
    webkitAudioContext: typeof AudioContext;
  }
}