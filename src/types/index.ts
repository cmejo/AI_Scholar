// Global type definitions for the enterprise RAG system

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer' | 'analyst';
  permissions: Permission[];
  preferences: UserPreferences;
  createdAt: Date;
  lastLogin: Date;
}

export interface Permission {
  resource: string;
  actions: ('read' | 'write' | 'delete' | 'admin')[];
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  defaultModel: string;
  responseLength: 'concise' | 'detailed' | 'comprehensive';
  enableVoice: boolean;
  enableNotifications: boolean;
  customDashboard: DashboardConfig;
}

export interface DashboardConfig {
  widgets: DashboardWidget[];
  layout: 'grid' | 'list' | 'cards';
  refreshInterval: number;
}

export interface DashboardWidget {
  id: string;
  type: 'analytics' | 'recent_queries' | 'document_stats' | 'knowledge_graph' | 'trends';
  position: { x: number; y: number; width: number; height: number };
  config: Record<string, any>;
}

export interface MultiModalDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'video' | 'audio' | 'code' | 'structured';
  content: {
    text: string;
    images: ImageContent[];
    tables: TableContent[];
    code: CodeContent[];
    metadata: DocumentMetadata;
  };
  processing: {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    extractedElements: ExtractedElement[];
    ocrResults?: OCRResult[];
  };
}

export interface ImageContent {
  id: string;
  url: string;
  caption?: string;
  extractedText: string;
  objects: DetectedObject[];
  charts?: ChartData[];
}

export interface TableContent {
  id: string;
  headers: string[];
  rows: string[][];
  caption?: string;
  structure: TableStructure;
}

export interface CodeContent {
  id: string;
  language: string;
  code: string;
  documentation?: string;
  functions: FunctionDefinition[];
}

export interface ExtractedElement {
  type: 'text' | 'image' | 'table' | 'chart' | 'code' | 'formula';
  content: any;
  position: { page: number; x: number; y: number; width: number; height: number };
  confidence: number;
}

export interface ConversationMemory {
  id: string;
  userId: string;
  shortTermMemory: MemoryItem[];
  longTermMemory: MemoryItem[];
  contextSummary: string;
  preferences: ConversationPreferences;
  lastUpdated: Date;
}

export interface MemoryItem {
  id: string;
  type: 'fact' | 'preference' | 'context' | 'relationship';
  content: string;
  importance: number;
  timestamp: Date;
  source: string;
  verified: boolean;
}

export interface AnalyticsData {
  queries: QueryAnalytics[];
  documents: DocumentAnalytics[];
  users: UserAnalytics[];
  performance: PerformanceMetrics;
  trends: TrendData[];
}

export interface QueryAnalytics {
  id: string;
  query: string;
  userId: string;
  timestamp: Date;
  responseTime: number;
  satisfaction: number;
  intent: string;
  documentsUsed: string[];
  success: boolean;
}

export interface SecurityAuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  timestamp: Date;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  details: Record<string, any>;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  triggers: WorkflowTrigger[];
  actions: WorkflowAction[];
  conditions: WorkflowCondition[];
  status: 'active' | 'inactive' | 'draft';
}

export interface Integration {
  id: string;
  type: 'slack' | 'teams' | 'email' | 'api' | 'webhook' | 'sso';
  name: string;
  config: IntegrationConfig;
  status: 'active' | 'inactive' | 'error';
  lastSync: Date;
}

// Additional type definitions for all features...
export interface VoiceConfig {
  enabled: boolean;
  language: string;
  voice: string;
  speed: number;
  pitch: number;
}

export interface BiasDetectionResult {
  detected: boolean;
  type: 'gender' | 'racial' | 'political' | 'cultural' | 'other';
  confidence: number;
  explanation: string;
  suggestions: string[];
}

export interface CitationFormat {
  style: 'apa' | 'mla' | 'chicago' | 'ieee' | 'harvard';
  citation: string;
  bibliography: string;
}