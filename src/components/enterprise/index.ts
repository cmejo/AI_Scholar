/**
 * Enterprise Components Index
 * Centralized exports for all enterprise components and utilities
 */

// Main Enterprise Components
export { default as EnterpriseAnalyticsDashboard } from './EnterpriseAnalyticsDashboard';
export { default as SecurityDashboard } from './SecurityDashboard';
export { default as WorkflowManager } from './WorkflowManager';
export { default as IntegrationHub } from './IntegrationHub';

// Authentication and User Management
export { default as UserManagement } from './UserManagement';
export { default as SessionManagement } from './SessionManagement';
export { default as EnterpriseAuthGuard, withEnterpriseAuth, usePermissionGate } from './EnterpriseAuthGuard';

// Error Boundaries
export { EnterpriseErrorBoundary } from './EnterpriseErrorBoundary';

// Performance Monitoring
export { EnterprisePerformanceMonitor } from './EnterprisePerformanceMonitor';

// Code Splitting Utilities
export {
  createMonitoredEnterpriseComponent,
  createEnterpriseComponent,
  EnterprisePerformanceTracker,
  EnterpriseComponentPreloader,
  initializeEnterpriseCodeSplitting
} from '../../utils/enterpriseCodeSplitting';

// Performance Integration
export {
  enterprisePerformanceIntegration,
  useEnterprisePerformanceMonitoring
} from '../../utils/enterprisePerformanceIntegration';

// Re-export common types that enterprise components might need
export type { User } from '../../types/auth';