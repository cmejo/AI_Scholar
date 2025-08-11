// Global type definitions for the enterprise RAG system

// Re-export all types from sub-modules
export * from './api';
export * from './ui';

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
  config: Record<string, unknown>;
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
  content: unknown;
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
  details: Record<string, unknown>;
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

// Missing type definitions
export interface DocumentMetadata {
  title: string;
  author: string;
  createdAt: Date;
  modifiedAt: Date;
  tags: string[];
  language: string;
  wordCount: number;
  pageCount: number;
}

export interface DetectedObject {
  id: string;
  type: string;
  confidence: number;
  boundingBox: { x: number; y: number; width: number; height: number };
  label: string;
}

export interface ChartData {
  type: 'bar' | 'line' | 'pie' | 'scatter';
  data: unknown[];
  title?: string;
  axes?: { x: string; y: string };
}

export interface TableStructure {
  hasHeaders: boolean;
  columnTypes: string[];
  relationships: string[];
}

export interface FunctionDefinition {
  name: string;
  parameters: Parameter[];
  returnType: string;
  documentation: string;
}

export interface Parameter {
  name: string;
  type: string;
  optional: boolean;
  description: string;
}

export interface OCRResult {
  text: string;
  confidence: number;
  boundingBox: { x: number; y: number; width: number; height: number };
}

export interface ConversationPreferences {
  responseStyle: 'concise' | 'balanced' | 'detailed';
  topicInterests: TopicInterest[];
  preferredSources: string[];
  languageLevel: 'beginner' | 'intermediate' | 'advanced';
}

export interface TopicInterest {
  topic: string;
  interest: number; // 0-1 scale
}

export interface DocumentAnalytics {
  id: string;
  name: string;
  views: number;
  queries: number;
  lastAccessed: Date;
  averageRelevance: number;
  totalReferences?: number;
  averageSatisfaction?: number;
  lastUsed?: Date;
  topQueries?: string[];
}

export interface UserAnalytics {
  id: string;
  name: string;
  totalQueries: number;
  averageSessionTime: number;
  lastActive: Date;
  topTopics: string[];
  averageResponseTime?: number;
  averageSatisfaction?: number;
}

export interface PerformanceMetrics {
  averageResponseTime: number;
  successRate: number;
  errorRate: number;
  throughput: number;
  memoryUsage: number;
  cpuUsage: number;
  totalQueries?: number;
  averageSatisfaction?: number;
}

export interface TrendData {
  period: string;
  metric: string;
  value: number;
  change: number;
  type?: string;
  data?: unknown;
  trend?: unknown;
}

export interface WorkflowTrigger {
  type: 'schedule' | 'event' | 'webhook' | 'document_upload';
  config: Record<string, unknown>;
}

export interface WorkflowAction {
  type: 'email' | 'notification' | 'api_call' | 'data_export' | 'auto_tag' | 'send_notification' | 'generate_summary' | 'update_metadata' | 'create_backup' | 'generate_report' | 'check_freshness';
  config: Record<string, unknown>;
}

export interface WorkflowCondition {
  field: string;
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than';
  value: unknown;
  type?: string;
}

export interface IntegrationConfig {
  apiKey?: string;
  webhookUrl?: string;
  credentials?: Record<string, string>;
  settings?: Record<string, unknown>;
}