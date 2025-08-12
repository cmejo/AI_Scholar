/**
 * Test fixtures and sample data for consistent testing
 */

import type {
    ChatMessage,
    ChatResponse,
    DocumentMetadata,
    FormError,
    SearchResult,
    StandardError
} from '../../types/api';
import type {
    SpeechRecognitionResult,
    VoiceConfig
} from '../../types/voice';

/**
 * Sample chat messages for testing
 */
export const sampleChatMessages: ChatMessage[] = [
  {
    id: 'msg_001',
    content: 'What is machine learning?',
    role: 'user',
    timestamp: new Date('2024-01-15T10:00:00Z'),
    metadata: {
      sessionId: 'session_001',
      userAgent: 'Mozilla/5.0 (Test Browser)',
    },
  },
  {
    id: 'msg_002',
    content: 'Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.',
    role: 'assistant',
    timestamp: new Date('2024-01-15T10:00:05Z'),
    metadata: {
      sessionId: 'session_001',
      model: 'gpt-4',
      processingTime: 1250,
    },
  },
  {
    id: 'msg_003',
    content: 'Can you explain neural networks?',
    role: 'user',
    timestamp: new Date('2024-01-15T10:01:00Z'),
    metadata: {
      sessionId: 'session_001',
      userAgent: 'Mozilla/5.0 (Test Browser)',
    },
  },
];

/**
 * Sample chat responses for testing
 */
export const sampleChatResponses: ChatResponse[] = [
  {
    id: 'response_001',
    content: 'Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information.',
    role: 'assistant',
    timestamp: new Date('2024-01-15T10:01:05Z'),
    sources: [
      {
        id: 'source_001',
        title: 'Introduction to Neural Networks',
        content: 'Neural networks are fundamental to modern AI...',
        score: 0.92,
        source: 'neural_networks_guide.pdf',
        metadata: {
          id: 'doc_001',
          title: 'Neural Networks Guide',
          author: 'Dr. Jane Smith',
          type: 'pdf',
          size: 2048000,
          uploadDate: new Date('2024-01-10T00:00:00Z'),
          lastModified: new Date('2024-01-10T00:00:00Z'),
          tags: ['neural-networks', 'ai', 'machine-learning'],
          summary: 'Comprehensive guide to neural networks',
        },
        highlights: ['neural networks', 'interconnected nodes', 'process information'],
      },
    ],
    confidence: 0.89,
    processingTime: 1850,
    metadata: {
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 500,
    },
  },
];

/**
 * Sample document metadata for testing
 */
export const sampleDocuments: DocumentMetadata[] = [
  {
    id: 'doc_001',
    title: 'Machine Learning Fundamentals',
    author: 'Dr. John Doe',
    type: 'pdf',
    size: 1024000,
    uploadDate: new Date('2024-01-01T00:00:00Z'),
    lastModified: new Date('2024-01-01T00:00:00Z'),
    tags: ['machine-learning', 'fundamentals', 'ai'],
    summary: 'A comprehensive introduction to machine learning concepts and algorithms.',
  },
  {
    id: 'doc_002',
    title: 'Deep Learning with Python',
    author: 'Jane Smith',
    type: 'pdf',
    size: 3072000,
    uploadDate: new Date('2024-01-05T00:00:00Z'),
    lastModified: new Date('2024-01-05T00:00:00Z'),
    tags: ['deep-learning', 'python', 'neural-networks'],
    summary: 'Practical guide to implementing deep learning models using Python.',
  },
  {
    id: 'doc_003',
    title: 'Natural Language Processing',
    author: 'Bob Johnson',
    type: 'docx',
    size: 512000,
    uploadDate: new Date('2024-01-10T00:00:00Z'),
    lastModified: new Date('2024-01-12T00:00:00Z'),
    tags: ['nlp', 'text-processing', 'linguistics'],
    summary: 'Overview of natural language processing techniques and applications.',
  },
];

/**
 * Sample search results for testing
 */
export const sampleSearchResults: SearchResult[] = [
  {
    id: 'result_001',
    title: 'Introduction to Machine Learning',
    content: 'Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.',
    score: 0.95,
    source: 'ml_introduction.pdf',
    metadata: sampleDocuments[0],
    highlights: ['machine learning', 'data analysis', 'artificial intelligence'],
  },
  {
    id: 'result_002',
    title: 'Neural Network Architectures',
    content: 'Neural networks are a series of algorithms that endeavor to recognize underlying relationships in a set of data through a process that mimics the way the human brain operates.',
    score: 0.87,
    source: 'neural_networks.pdf',
    metadata: sampleDocuments[1],
    highlights: ['neural networks', 'algorithms', 'human brain'],
  },
  {
    id: 'result_003',
    title: 'Text Classification with NLP',
    content: 'Natural Language Processing (NLP) enables computers to understand, interpret and manipulate human language. Text classification is a fundamental NLP task.',
    score: 0.82,
    source: 'nlp_guide.docx',
    metadata: sampleDocuments[2],
    highlights: ['Natural Language Processing', 'text classification', 'human language'],
  },
];

/**
 * Sample voice configurations for testing
 */
export const sampleVoiceConfigs: VoiceConfig[] = [
  {
    language: 'en-US',
    voice: 'default',
    rate: 1.0,
    pitch: 1.0,
    volume: 1.0,
    continuous: true,
    interimResults: true,
    maxAlternatives: 1,
  },
  {
    language: 'es-ES',
    voice: 'spanish-female',
    rate: 0.9,
    pitch: 1.1,
    volume: 0.8,
    continuous: false,
    interimResults: false,
    maxAlternatives: 3,
  },
  {
    language: 'fr-FR',
    voice: 'french-male',
    rate: 1.2,
    pitch: 0.9,
    volume: 1.0,
    continuous: true,
    interimResults: true,
    maxAlternatives: 1,
  },
];

/**
 * Sample speech recognition results for testing
 */
export const sampleSpeechResults: SpeechRecognitionResult[] = [
  {
    text: 'Hello, how are you today?',
    confidence: 0.98,
    language: 'en-US',
    timestamp: Date.now(),
    isFinal: true,
    alternatives: [
      { text: 'Hello, how are you today?', confidence: 0.98 },
      { text: 'Hello, how are you to day?', confidence: 0.85 },
    ],
  },
  {
    text: 'What is machine learning?',
    confidence: 0.92,
    language: 'en-US',
    timestamp: Date.now() + 1000,
    isFinal: true,
    alternatives: [
      { text: 'What is machine learning?', confidence: 0.92 },
      { text: 'What is machine learning', confidence: 0.88 },
    ],
  },
  {
    text: 'Can you explain neural networks?',
    confidence: 0.89,
    language: 'en-US',
    timestamp: Date.now() + 2000,
    isFinal: false,
    alternatives: [
      { text: 'Can you explain neural networks?', confidence: 0.89 },
      { text: 'Can you explain neural network?', confidence: 0.82 },
    ],
  },
];

/**
 * Sample error objects for testing
 */
export const sampleErrors: StandardError[] = [
  {
    id: 'error_001',
    type: 'NETWORK_ERROR',
    code: 'NETWORK_ERROR',
    message: 'Failed to fetch data from server',
    severity: 'medium',
    timestamp: new Date('2024-01-15T10:00:00Z'),
    recoverable: false,
    retryable: true,
    userMessage: 'Unable to connect to the server. Please check your internet connection and try again.',
    details: {
      url: 'https://api.example.com/chat',
      method: 'POST',
      status: 0,
    },
  },
  {
    id: 'error_002',
    type: 'VALIDATION_ERROR',
    code: 'VALIDATION_ERROR',
    message: 'Invalid input data',
    severity: 'low',
    timestamp: new Date('2024-01-15T10:01:00Z'),
    recoverable: true,
    retryable: false,
    userMessage: 'Please check your input and try again.',
    details: {
      validationErrors: [
        { field: 'email', message: 'Invalid email format', code: 'INVALID_EMAIL' },
        { field: 'password', message: 'Password too short', code: 'PASSWORD_TOO_SHORT' },
      ],
    },
  },
  {
    id: 'error_003',
    type: 'SERVER_ERROR',
    code: 'INTERNAL_SERVER_ERROR',
    message: 'Internal server error occurred',
    severity: 'high',
    timestamp: new Date('2024-01-15T10:02:00Z'),
    recoverable: false,
    retryable: true,
    userMessage: 'A server error occurred. Our team has been notified.',
    details: {
      statusCode: 500,
      requestId: 'req_12345',
    },
  },
];

/**
 * Sample form errors for testing
 */
export const sampleFormErrors: FormError[] = [
  {
    field: 'email',
    message: 'Please enter a valid email address',
    code: 'INVALID_EMAIL',
    value: 'invalid-email',
  },
  {
    field: 'password',
    message: 'Password must be at least 8 characters long',
    code: 'PASSWORD_TOO_SHORT',
    value: '123',
  },
  {
    field: 'confirmPassword',
    message: 'Passwords do not match',
    code: 'PASSWORD_MISMATCH',
    value: 'different-password',
  },
];

/**
 * Sample user profiles for testing
 */
export const sampleUserProfiles = [
  {
    id: 'user_001',
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'researcher',
    preferences: {
      theme: 'light',
      language: 'en-US',
      notifications: true,
    },
    createdAt: new Date('2024-01-01T00:00:00Z'),
    lastLoginAt: new Date('2024-01-15T09:00:00Z'),
  },
  {
    id: 'user_002',
    name: 'Jane Smith',
    email: 'jane.smith@example.com',
    role: 'student',
    preferences: {
      theme: 'dark',
      language: 'en-US',
      notifications: false,
    },
    createdAt: new Date('2024-01-05T00:00:00Z'),
    lastLoginAt: new Date('2024-01-15T08:30:00Z'),
  },
];

/**
 * Sample API responses for testing
 */
export const sampleAPIResponses = {
  chatSend: {
    success: true,
    data: sampleChatResponses[0],
    timestamp: new Date().toISOString(),
  },
  chatHistory: {
    success: true,
    data: {
      messages: sampleChatMessages,
      total: sampleChatMessages.length,
      page: 1,
      limit: 50,
    },
    timestamp: new Date().toISOString(),
  },
  documentList: {
    success: true,
    data: {
      documents: sampleDocuments,
      total: sampleDocuments.length,
      page: 1,
      limit: 20,
    },
    timestamp: new Date().toISOString(),
  },
  searchResults: {
    success: true,
    data: {
      results: sampleSearchResults,
      total: sampleSearchResults.length,
      query: 'machine learning',
      processingTime: 150,
    },
    timestamp: new Date().toISOString(),
  },
  voiceTranscription: {
    success: true,
    data: sampleSpeechResults[0],
    timestamp: new Date().toISOString(),
  },
};

/**
 * Sample test scenarios for different use cases
 */
export const testScenarios = {
  happyPath: {
    name: 'Happy Path - Normal Operation',
    description: 'All operations succeed with expected responses',
    mockData: sampleAPIResponses,
  },
  networkError: {
    name: 'Network Error Scenario',
    description: 'Network requests fail with connection errors',
    errors: [sampleErrors[0]],
  },
  validationError: {
    name: 'Validation Error Scenario',
    description: 'User input validation fails',
    errors: [sampleErrors[1]],
    formErrors: sampleFormErrors,
  },
  serverError: {
    name: 'Server Error Scenario',
    description: 'Server returns internal errors',
    errors: [sampleErrors[2]],
  },
  slowNetwork: {
    name: 'Slow Network Scenario',
    description: 'Network requests take longer than usual',
    delay: 3000,
    mockData: sampleAPIResponses,
  },
  emptyResults: {
    name: 'Empty Results Scenario',
    description: 'API returns empty results',
    mockData: {
      ...sampleAPIResponses,
      searchResults: {
        success: true,
        data: {
          results: [],
          total: 0,
          query: 'nonexistent query',
          processingTime: 50,
        },
        timestamp: new Date().toISOString(),
      },
    },
  },
};

/**
 * Utility function to get sample data by type
 */
export const getSampleData = <T>(type: string, count?: number): T[] => {
  const dataMap: Record<string, any[]> = {
    chatMessages: sampleChatMessages,
    chatResponses: sampleChatResponses,
    documents: sampleDocuments,
    searchResults: sampleSearchResults,
    voiceConfigs: sampleVoiceConfigs,
    speechResults: sampleSpeechResults,
    errors: sampleErrors,
    formErrors: sampleFormErrors,
    userProfiles: sampleUserProfiles,
  };

  const data = dataMap[type] || [];
  return count ? data.slice(0, count) : data;
};

/**
 * Utility function to create variations of sample data
 */
export const createDataVariations = <T extends Record<string, any>>(
  baseData: T,
  variations: Partial<T>[]
): T[] => {
  return variations.map(variation => ({ ...baseData, ...variation }));
};