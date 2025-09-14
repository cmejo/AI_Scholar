/**
 * Integration Types
 * Type definitions for integration management
 */

export interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'connected' | 'disconnected' | 'error' | 'pending';
  type: 'api' | 'webhook' | 'database' | 'cloud' | 'email' | 'custom';
  lastSync?: Date;
  nextSync?: Date;
  syncStatus: 'success' | 'failed' | 'in_progress' | 'never';
  errorMessage?: string;
  config: IntegrationConfig;
  credentials: {
    type: 'api_key' | 'oauth' | 'basic_auth' | 'certificate';
    masked: boolean;
  };
  metrics: {
    totalRequests: number;
    successRate: number;
    averageResponseTime: number;
    lastRequest?: Date;
  };
}

export interface IntegrationConfig {
  endpoint?: string;
  apiKey?: string;
  credentials?: Record<string, string>;
  settings: Record<string, any>;
  syncInterval?: number;
}

export interface IntegrationStats {
  totalIntegrations: number;
  connectedIntegrations: number;
  failedIntegrations: number;
  pendingIntegrations: number;
  totalSyncs: number;
  successfulSyncs: number;
  failedSyncs: number;
}

export interface SyncStatus {
  id: string;
  integrationId: string;
  integrationName: string;
  status: 'success' | 'failed' | 'in_progress' | 'pending' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  recordsProcessed: number;
  recordsTotal: number;
  errorCount: number;
  errorMessage?: string;
  syncType: 'full' | 'incremental' | 'manual';
  triggeredBy: string;
  dataSize: number;
  throughput: number;
  conflicts: number;
  conflictResolution: 'auto' | 'manual' | 'skip';
}

export interface SyncMetrics {
  totalSyncs: number;
  successfulSyncs: number;
  failedSyncs: number;
  averageDuration: number;
  averageThroughput: number;
  totalDataSynced: number;
  lastSyncTime?: Date;
  nextScheduledSync?: Date;
  successRate: number;
}

export interface SyncError {
  id: string;
  syncId: string;
  timestamp: Date;
  errorType: 'connection' | 'authentication' | 'data_validation' | 'rate_limit' | 'timeout';
  message: string;
  details?: Record<string, any>;
  resolved: boolean;
}

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: Date;
  responseTime: number;
  details: {
    connectivity: boolean;
    authentication: boolean;
    permissions: boolean;
    dataAccess: boolean;
  };
  errors?: string[];
}

export interface APIKey {
  id: string;
  name: string;
  description: string;
  service: string;
  type: 'api_key' | 'oauth_token' | 'certificate' | 'secret';
  value: string;
  masked: boolean;
  status: 'active' | 'expired' | 'revoked' | 'pending';
  createdAt: Date;
  expiresAt?: Date;
  lastUsed?: Date;
  usageCount: number;
  permissions: string[];
  environment: 'development' | 'staging' | 'production';
  rotationSchedule?: {
    enabled: boolean;
    intervalDays: number;
    nextRotation?: Date;
  };
}

export interface ConnectionConfig {
  id?: string;
  name: string;
  type: 'api' | 'webhook' | 'database' | 'oauth' | 'custom';
  endpoint: string;
  method?: string;
  headers: Record<string, string>;
  authentication: {
    type: 'none' | 'api_key' | 'bearer_token' | 'basic_auth' | 'oauth2';
    credentials: Record<string, string>;
  };
  timeout: number;
  retries: number;
  validateSsl: boolean;
}

export interface IntegrationCatalogItem {
  id: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  icon: string;
  type: Integration['type'];
  features: string[];
  pricing: 'free' | 'paid' | 'freemium';
  documentation: string;
  setupComplexity: 'easy' | 'medium' | 'advanced';
  popularity: number;
  rating: number;
  reviews: number;
  tags: string[];
}

export interface IntegrationTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  type: Integration['type'];
  configTemplate: Partial<IntegrationConfig>;
  requiredFields: string[];
  optionalFields: string[];
  validationRules: Record<string, any>;
  instructions: string[];
}