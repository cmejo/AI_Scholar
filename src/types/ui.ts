// UI and React component type definitions

import type { ReactNode } from 'react';

// Base UI Types
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  id?: string;
  'data-testid'?: string;
}

// User Interface Types
export interface UserInfo {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer' | 'analyst';
  avatar?: string;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: boolean;
  accessibility: AccessibilitySettings;
}

export interface AccessibilitySettings {
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
  reducedMotion: boolean;
}

// Navigation Types
export type ViewType = 'chat' | 'documents' | 'analytics' | 'security' | 'workflows' | 'integrations';

export interface NavigationItem {
  id: ViewType;
  label: string;
  icon: string;
  path: string;
  badge?: number;
  disabled?: boolean;
}

// Header Component Types
export interface HeaderProps extends BaseComponentProps {
  onToggleSidebar: () => void;
  currentView: string;
  user?: UserInfo;
}

// Sidebar Component Types
export interface SidebarProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: string;
  onViewChange: (view: ViewType) => void;
  user?: UserInfo;
  voiceEnabled: boolean;
  onToggleVoice: (enabled: boolean) => void;
}

// Mobile Layout Types
export interface MobileLayoutProps extends BaseComponentProps {
  currentView: string;
  onViewChange: (view: string) => void;
  user?: UserInfo;
  voiceEnabled: boolean;
  onToggleVoice: (enabled: boolean) => void;
}

export interface MobileHeaderProps extends BaseComponentProps {
  currentView: string;
  user?: UserInfo;
  onToggleNav: () => void;
  voiceEnabled: boolean;
  onToggleVoice: (enabled: boolean) => void;
}

export interface MobileNavigationProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: string;
  onViewChange: (view: string) => void;
  user?: UserInfo;
}

// Form and Input Types
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface FormFieldProps extends BaseComponentProps {
  label?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
}

export interface SelectProps extends FormFieldProps {
  value: string;
  onValueChange: (value: string) => void;
  options?: SelectOption[];
  placeholder?: string;
}

// Chat Interface Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  sources?: DocumentSource[];
  reasoning?: ReasoningStep[];
  uncertainty?: UncertaintyInfo;
  feedback?: MessageFeedback;
  metadata?: MessageMetadata;
}

export interface DocumentSource {
  id: string;
  name: string;
  type: string;
  relevance: number;
  excerpt: string;
  page?: number;
  url?: string;
}

export interface ReasoningStep {
  step: number;
  description: string;
  confidence: number;
  evidence: string[];
  reasoning: string;
}

export interface UncertaintyInfo {
  overall: number;
  factors: UncertaintyFactor[];
  explanation: string;
  suggestions: string[];
}

export interface UncertaintyFactor {
  factor: string;
  impact: number;
  description: string;
}

export interface MessageFeedback {
  rating?: 'positive' | 'negative';
  aspects?: FeedbackAspect[];
  comment?: string;
  timestamp: Date;
  userId: string;
}

export interface FeedbackAspect {
  aspect: 'accuracy' | 'relevance' | 'completeness' | 'clarity';
  rating: number; // 1-5 scale
}

export interface MessageMetadata {
  model: string;
  responseTime: number;
  tokensUsed: number;
  cost?: number;
  version: string;
}

// Visualization Types
export interface VisualizationProps extends BaseComponentProps {
  data: VisualizationData;
  type: VisualizationType;
  config?: VisualizationConfig;
  onInteraction?: (event: VisualizationEvent) => void;
}

export interface VisualizationData {
  datasets: DatasetInfo[];
  metadata: VisualizationMetadata;
}

export interface DatasetInfo {
  id: string;
  name: string;
  data: DataPoint[];
  type: 'numeric' | 'categorical' | 'temporal' | 'geospatial';
}

export interface DataPoint {
  x: number | string | Date;
  y: number | string;
  label?: string;
  metadata?: Record<string, unknown>;
}

export type VisualizationType = 
  | 'bar' 
  | 'line' 
  | 'pie' 
  | 'scatter' 
  | 'heatmap' 
  | 'network' 
  | 'treemap' 
  | 'sankey';

export interface VisualizationConfig {
  title?: string;
  subtitle?: string;
  theme: 'light' | 'dark';
  interactive: boolean;
  responsive: boolean;
  animations: boolean;
  legend: LegendConfig;
  axes?: AxesConfig;
  colors?: string[];
}

export interface LegendConfig {
  show: boolean;
  position: 'top' | 'bottom' | 'left' | 'right';
  align: 'start' | 'center' | 'end';
}

export interface AxesConfig {
  x: AxisConfig;
  y: AxisConfig;
}

export interface AxisConfig {
  title?: string;
  show: boolean;
  grid: boolean;
  scale: 'linear' | 'log' | 'time' | 'category';
}

export interface VisualizationMetadata {
  createdAt: Date;
  updatedAt: Date;
  version: string;
  source: string;
  description?: string;
}

export interface VisualizationEvent {
  type: 'click' | 'hover' | 'select' | 'zoom' | 'pan';
  data: DataPoint | DataPoint[];
  coordinates?: { x: number; y: number };
  metadata?: Record<string, unknown>;
}

// Analytics Dashboard Types
export interface DashboardProps extends BaseComponentProps {
  userId?: string;
  timeRange?: TimeRange;
  onExport?: (data: ExportData) => void;
}

export interface TimeRange {
  start: Date;
  end: Date;
  preset?: 'today' | 'week' | 'month' | 'quarter' | 'year' | 'custom';
}

export interface ExportData {
  format: 'pdf' | 'csv' | 'json' | 'xlsx';
  data: unknown;
  filename: string;
  timestamp: Date;
}

export interface AnalyticsDashboardData {
  overview: OverviewMetrics;
  queries: QueryAnalytics[];
  documents: DocumentAnalytics[];
  users: UserAnalytics[];
  performance: PerformanceMetrics;
  trends: TrendAnalysis[];
}

export interface OverviewMetrics {
  totalQueries: number;
  totalUsers: number;
  totalDocuments: number;
  averageResponseTime: number;
  successRate: number;
  satisfactionScore: number;
}

export interface QueryAnalytics {
  id: string;
  query: string;
  count: number;
  averageResponseTime: number;
  successRate: number;
  timestamp: Date;
}

export interface DocumentAnalytics {
  id: string;
  name: string;
  accessCount: number;
  lastAccessed: Date;
  relevanceScore: number;
}

export interface UserAnalytics {
  id: string;
  name: string;
  queryCount: number;
  lastActive: Date;
  satisfactionScore: number;
}

export interface PerformanceMetrics {
  responseTime: number;
  throughput: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
}

export interface TrendAnalysis {
  metric: string;
  period: 'hour' | 'day' | 'week' | 'month';
  data: TrendDataPoint[];
  change: number;
  direction: 'up' | 'down' | 'stable';
}

export interface TrendDataPoint {
  timestamp: Date;
  value: number;
  label?: string;
}

// Security Dashboard Types
export interface SecurityDashboardProps extends BaseComponentProps {
  filters?: SecurityFilters;
  onFilterChange?: (filters: SecurityFilters) => void;
}

export interface SecurityFilters {
  action?: string;
  success?: boolean;
  timeRange?: TimeRange;
  userId?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

export interface SecurityEvent {
  id: string;
  timestamp: Date;
  action: string;
  userId: string;
  resource: string;
  success: boolean;
  ipAddress: string;
  userAgent: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  details: Record<string, unknown>;
}

// Voice Interface Types
export interface VoiceInterfaceProps extends BaseComponentProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  onVoiceQuery: (query: string) => Promise<string>;
  language?: string;
  voice?: string;
}

export interface VoiceNavigationProps extends BaseComponentProps {
  features: AccessibilityFeature[];
  onFeatureToggle: (featureId: string, enabled: boolean) => void;
  onSettingChange: (featureId: string, setting: string, value: unknown) => void;
}

export interface AccessibilityFeature {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  settings: AccessibilityFeatureSetting[];
}

export interface AccessibilityFeatureSetting {
  key: string;
  label: string;
  type: 'boolean' | 'number' | 'string' | 'select';
  value: unknown;
  options?: SelectOption[];
  min?: number;
  max?: number;
}

// Enhanced Error Handling Types
export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  retryCount: number;
}

export interface ErrorBoundaryProps extends BaseComponentProps {
  fallback?: ReactNode | ((error: Error, errorInfo: React.ErrorInfo, retry: () => void) => ReactNode);
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  maxRetries?: number;
  resetOnPropsChange?: boolean;
  resetKeys?: Array<string | number>;
  isolate?: boolean;
}

// Error Context Types
export interface ErrorContext {
  component?: string;
  feature?: string;
  operation?: string;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, unknown>;
}

// Error Handler Hook Types
export interface ErrorHandlerOptions {
  enableNotifications?: boolean;
  enableReporting?: boolean;
  context?: string;
  onError?: (error: StandardError) => void;
}

export interface ErrorHandlerReturn {
  handleError: (error: unknown, context?: string) => StandardError;
  reportError: (error: Error, context?: Record<string, unknown>) => void;
  clearErrors: () => void;
  errorCount: number;
}

// Standardized Error Interface
export interface StandardError {
  id: string;
  type: ErrorType;
  code: string;
  message: string;
  severity: ErrorSeverity;
  timestamp: Date;
  stack?: string;
  context?: ErrorContext;
  details?: Record<string, unknown>;
  userMessage: string;
  recoverable: boolean;
  retryable: boolean;
}

export enum ErrorType {
  COMPONENT_ERROR = 'COMPONENT_ERROR',
  API_ERROR = 'API_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
  NOT_FOUND_ERROR = 'NOT_FOUND_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  RATE_LIMIT_ERROR = 'RATE_LIMIT_ERROR',
  SERVER_ERROR = 'SERVER_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

// Error Notification Types
export interface ErrorNotification {
  id: string;
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  duration?: number;
  actions?: ErrorNotificationAction[];
  dismissible: boolean;
}

export interface ErrorNotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

// Form Error Types
export interface FormError {
  field: string;
  message: string;
  code: string;
  value?: unknown;
}

// Import error detail types from API types
export type {
    AuthenticationErrorDetails,
    AuthorizationErrorDetails, NetworkErrorDetails, ServerErrorDetails, ValidationErrorDetails
} from './api';

export interface FormErrorState {
  errors: Record<string, FormError>;
  hasErrors: boolean;
  isValid: boolean;
}

// Async Error Handler Types
export interface AsyncErrorHandlerReturn<T> {
  execute: (asyncFn: () => Promise<T>) => Promise<T | null>;
  loading: boolean;
  error: StandardError | null;
  clearError: () => void;
}

// Retry Handler Types
export interface RetryHandlerOptions {
  maxRetries?: number;
  retryDelay?: number;
  backoffMultiplier?: number;
  retryCondition?: (error: StandardError) => boolean;
}

export interface RetryHandlerReturn<T> {
  executeWithRetry: (asyncFn: () => Promise<T>) => Promise<T>;
  retryCount: number;
  isRetrying: boolean;
}

// Feedback Types
export interface FeedbackFormProps extends BaseComponentProps {
  messageId?: string;
  onSubmit: (feedback: FeedbackSubmission) => void;
  initialFeedback?: MessageFeedback;
}

export interface FeedbackSubmission {
  type: 'rating' | 'correction' | 'suggestion' | 'bug_report';
  rating?: 'positive' | 'negative';
  aspects?: FeedbackAspect[];
  comment?: string;
  severity?: 'low' | 'medium' | 'high';
  category?: string;
  metadata?: Record<string, unknown>;
}

// Knowledge Graph Types
export interface KnowledgeGraphProps extends BaseComponentProps {
  documents: KnowledgeGraphDocument[];
  selectedNodes?: string[];
  onNodeSelect?: (nodeId: string) => void;
  onEdgeSelect?: (edgeId: string) => void;
  layout?: 'force' | 'hierarchical' | 'circular';
}

export interface KnowledgeGraphDocument {
  id: string;
  name: string;
  type: string;
  content: string;
  relationships: DocumentRelationship[];
  metadata: Record<string, unknown>;
}

export interface DocumentRelationship {
  id: string;
  sourceId: string;
  targetId: string;
  type: 'references' | 'similar_to' | 'contradicts' | 'extends' | 'summarizes';
  strength: number;
  description?: string;
}