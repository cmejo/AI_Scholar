// API-related type definitions

export interface APIResponse<T = unknown> {
  data: T;
  success: boolean;
  message?: string;
  error?: APIError;
  timestamp: Date;
}

// Enhanced API Error Types
export interface APIError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: Date;
  stack?: string;
  requestId?: string;
  type: APIErrorType;
  statusCode?: number;
  severity: ErrorSeverity;
}

export enum APIErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND_ERROR = 'NOT_FOUND_ERROR',
  RATE_LIMIT_ERROR = 'RATE_LIMIT_ERROR',
  SERVER_ERROR = 'SERVER_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

// Validation Error Details
export interface ValidationErrorDetails extends Record<string, unknown> {
  field: string;
  message: string;
  code: string;
  value?: unknown;
}

// Network Error Details
export interface NetworkErrorDetails extends Record<string, unknown> {
  url: string;
  method: string;
  status?: number;
  statusText?: string;
  timeout?: boolean;
}

// Authentication Error Details
export interface AuthenticationErrorDetails extends Record<string, unknown> {
  reason: 'expired_token' | 'invalid_token' | 'missing_token' | 'invalid_credentials';
  redirectUrl?: string;
}

// Authorization Error Details
export interface AuthorizationErrorDetails extends Record<string, unknown> {
  resource: string;
  action: string;
  requiredPermissions: string[];
  userPermissions: string[];
}

// Server Error Details
export interface ServerErrorDetails extends Record<string, unknown> {
  errorId: string;
  service: string;
  operation: string;
  context?: Record<string, unknown>;
}

// Missing type definitions
export interface DocumentMetadata {
  title?: string;
  author?: string;
  createdAt?: Date;
  modifiedAt?: Date;
  size?: number;
  type?: string;
  tags?: string[];
  description?: string;
}

export interface ImageContent {
  id: string;
  url: string;
  alt?: string;
  caption?: string;
  width?: number;
  height?: number;
}

export interface TableContent {
  id: string;
  headers: string[];
  rows: (string | number | boolean)[][];
  caption?: string;
}

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface PerformanceMetrics {
  responseTime: number;
  throughput: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export interface QueryParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
  filters?: Record<string, unknown>;
}

export interface FetchOptions extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

// Chart and Visualization Types
export interface ChartInstance {
  id: string;
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'area' | 'radar';
  data: ChartDataset[];
  options: ChartOptions;
  canvas: HTMLCanvasElement;
  destroy: () => void;
  update: (data?: ChartDataset[]) => void;
  resize: () => void;
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    title?: {
      display?: boolean;
      text?: string;
    };
  };
  scales?: {
    x?: ScaleOptions;
    y?: ScaleOptions;
  };
}

export interface ScaleOptions {
  display?: boolean;
  title?: {
    display?: boolean;
    text?: string;
  };
  min?: number;
  max?: number;
  beginAtZero?: boolean;
}

export interface ChartStats {
  totalDataPoints: number;
  averageValue: number;
  minValue: number;
  maxValue: number;
  lastUpdated: Date;
}

// Workflow Types
export interface WorkflowContext {
  documentId?: string;
  userId?: string;
  timestamp: Date;
  metadata: Record<string, unknown>;
  variables: Record<string, unknown>;
}

export interface WorkflowExecutionResult {
  success: boolean;
  result?: unknown;
  error?: string;
  executionTime: number;
  logs: WorkflowLog[];
}

export interface WorkflowLog {
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: Date;
  context?: Record<string, unknown>;
}

export interface WorkflowJob {
  id: string;
  workflowId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  progress: number;
  result?: WorkflowExecutionResult;
  context: WorkflowContext;
}

// Document Types
export interface DocumentUpload {
  id: string;
  name: string;
  type: string;
  size: number;
  content: string | ArrayBuffer;
  metadata: DocumentMetadata;
  uploadedAt: Date;
  uploadedBy: string;
}

export interface DocumentProcessingResult {
  documentId: string;
  success: boolean;
  extractedText?: string;
  extractedImages?: ImageContent[];
  extractedTables?: TableContent[];
  metadata?: DocumentMetadata;
  processingTime: number;
  errors?: string[];
}

// Notification Types
export interface NotificationConfig {
  type: 'email' | 'slack' | 'webhook' | 'in-app';
  recipients: string[];
  template?: string;
  subject?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  retryPolicy?: {
    maxRetries: number;
    retryDelay: number;
  };
}

export interface NotificationResult {
  id: string;
  success: boolean;
  sentAt: Date;
  recipients: NotificationRecipient[];
  error?: string;
}

export interface NotificationRecipient {
  address: string;
  status: 'sent' | 'failed' | 'pending';
  error?: string;
}

// Report Types
export interface ReportConfig {
  type: 'daily' | 'weekly' | 'monthly' | 'custom';
  format: 'pdf' | 'html' | 'json' | 'csv';
  sections: ReportSection[];
  recipients?: string[];
  schedule?: CronExpression;
}

export interface ReportSection {
  id: string;
  title: string;
  type: 'chart' | 'table' | 'text' | 'metrics';
  data: unknown;
  config?: Record<string, unknown>;
}

export interface GeneratedReport {
  id: string;
  type: ReportConfig['type'];
  generatedAt: Date;
  data: ReportData;
  metadata: ReportMetadata;
}

export interface ReportData {
  summary: ReportSummary;
  sections: ReportSection[];
  charts: ChartData[];
  tables: TableData[];
}

export interface ReportSummary {
  totalDocuments: number;
  totalQueries: number;
  averageResponseTime: number;
  successRate: number;
  topTopics: string[];
  period: {
    start: Date;
    end: Date;
  };
}

export interface ReportMetadata {
  generatedBy: string;
  version: string;
  format: string;
  size: number;
  checksum?: string;
}

export interface TableData {
  headers: string[];
  rows: (string | number | boolean)[][];
  caption?: string;
  summary?: string;
}

export interface CronExpression {
  minute: string;
  hour: string;
  dayOfMonth: string;
  month: string;
  dayOfWeek: string;
}

// Health and Analytics Types
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: ServiceHealth[];
  uptime: number;
  version: string;
  timestamp: Date;
}

export interface ServiceHealth {
  name: string;
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  lastCheck: Date;
  error?: string;
}

export interface AnalyticsMetrics {
  totalUsers: number;
  activeUsers: number;
  totalQueries: number;
  averageResponseTime: number;
  errorRate: number;
  topQueries: QueryFrequency[];
  userEngagement: EngagementMetrics;
  systemPerformance: PerformanceMetrics;
}

export interface QueryFrequency {
  query: string;
  count: number;
  averageResponseTime: number;
  successRate: number;
}

export interface EngagementMetrics {
  averageSessionDuration: number;
  queriesPerSession: number;
  returnUserRate: number;
  satisfactionScore: number;
}

// Incident Management Types
export interface IncidentTimeline {
  id: string;
  incidentId: string;
  timestamp: Date;
  event: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  user?: string;
  metadata?: Record<string, unknown>;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolved' | 'closed';
  createdAt: Date;
  resolvedAt?: Date;
  assignedTo?: string;
  timeline: IncidentTimeline[];
  affectedServices: string[];
}