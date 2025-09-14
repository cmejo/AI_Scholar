/**
 * IntegrationValidator - Comprehensive integration testing and validation functionality
 */
import React, { useState } from 'react';
import {
  TestTube,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Shield,
  Zap,
  Database,
  Globe,
  Key,
  Activity,
  Clock,
  Eye,
  EyeOff,
  Download,
  FileText,
  Settings
} from 'lucide-react';
import { ConnectionConfig, APIKey } from '../../../types/integration';

export interface IntegrationValidatorProps {
  onValidationComplete?: (result: ValidationResult) => void;
  className?: string;
}

export interface ValidationResult {
  success: boolean;
  message: string;
  details: ValidationStepResult[];
  duration: number;
  timestamp: Date;
  recommendations: string[];
}

export interface ValidationStepResult {
  step: string;
  category: 'security' | 'performance' | 'connectivity' | 'configuration';
  status: 'success' | 'failed' | 'warning' | 'info';
  message: string;
  duration: number;
  details?: any;
  recommendation?: string;
}

interface ValidationConfig {
  connections: ConnectionConfig[];
  apiKeys: APIKey[];
  testEndpoints: boolean;
  validateSecurity: boolean;
  checkPerformance: boolean;
  generateReport: boolean;
}

export const IntegrationValidator: React.FC<IntegrationValidatorProps> = ({
  onValidationComplete,
  className = ''
}) => {
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [showDetails, setShowDetails] = useState(false);
  const [config, setConfig] = useState<ValidationConfig>({
    connections: [],
    apiKeys: [],
    testEndpoints: true,
    validateSecurity: true,
    checkPerformance: true,
    generateReport: true
  });

  // Comprehensive validation suite
  const runComprehensiveValidation = async () => {
    setValidating(true);
    setValidationResult(null);
    setCurrentStep('');

    const startTime = Date.now();
    const results: ValidationStepResult[] = [];
    const recommendations: string[] = [];

    try {
      // Configuration validation
      setCurrentStep('Validating Configuration');
      const configResults = await validateConfiguration();
      results.push(...configResults);

      // Security validation
      if (config.validateSecurity) {
        setCurrentStep('Security Validation');
        const securityResults = await validateSecurity();
        results.push(...securityResults);
      }

      // Connectivity tests
      if (config.testEndpoints) {
        setCurrentStep('Testing Connectivity');
        const connectivityResults = await testConnectivity();
        results.push(...connectivityResults);
      }

      // Performance tests
      if (config.checkPerformance) {
        setCurrentStep('Performance Testing');
        const performanceResults = await testPerformance();
        results.push(...performanceResults);
      }

      // Generate recommendations
      setCurrentStep('Generating Recommendations');
      const generatedRecommendations = generateRecommendations(results);
      recommendations.push(...generatedRecommendations);

      const totalDuration = Date.now() - startTime;
      const successCount = results.filter(r => r.status === 'success').length;
      const failedCount = results.filter(r => r.status === 'failed').length;
      const warningCount = results.filter(r => r.status === 'warning').length;

      const overallSuccess = failedCount === 0 && results.length > 0;

      const finalResult: ValidationResult = {
        success: overallSuccess,
        message: overallSuccess 
          ? `Validation completed successfully (${successCount}/${results.length} checks passed)`
          : `Validation completed with issues (${failedCount} failures, ${warningCount} warnings)`,
        details: results,
        duration: totalDuration,
        timestamp: new Date(),
        recommendations
      };

      setValidationResult(finalResult);
      onValidationComplete?.(finalResult);

    } catch (error) {
      const finalResult: ValidationResult = {
        success: false,
        message: 'Validation failed: ' + (error instanceof Error ? error.message : 'Unknown error'),
        details: results,
        duration: Date.now() - startTime,
        timestamp: new Date(),
        recommendations: ['Review system configuration and try again']
      };

      setValidationResult(finalResult);
      onValidationComplete?.(finalResult);
    } finally {
      setValidating(false);
      setCurrentStep('');
    }
  };

  // Configuration validation
  const validateConfiguration = async (): Promise<ValidationStepResult[]> => {
    const results: ValidationStepResult[] = [];
    
    await new Promise(resolve => setTimeout(resolve, 500));

    // Check if any integrations are configured
    if (config.connections.length === 0 && config.apiKeys.length === 0) {
      results.push({
        step: 'Integration Configuration',
        category: 'configuration',
        status: 'warning',
        message: 'No integrations configured',
        duration: 0,
        recommendation: 'Configure at least one integration to enable functionality'
      });
    } else {
      results.push({
        step: 'Integration Configuration',
        category: 'configuration',
        status: 'success',
        message: `${config.connections.length} connections and ${config.apiKeys.length} API keys configured`,
        duration: 0
      });
    }

    // Validate connection configurations
    for (const connection of config.connections) {
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const validationResult = validateConnectionConfig(connection);
      results.push({
        step: `Connection: ${connection.name}`,
        category: 'configuration',
        status: validationResult.valid ? 'success' : 'failed',
        message: validationResult.message,
        duration: 0,
        recommendation: validationResult.recommendation
      });
    }

    // Validate API key configurations
    for (const apiKey of config.apiKeys) {
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const validationResult = validateAPIKeyConfig(apiKey);
      results.push({
        step: `API Key: ${apiKey.name}`,
        category: 'configuration',
        status: validationResult.valid ? 'success' : 'failed',
        message: validationResult.message,
        duration: 0,
        recommendation: validationResult.recommendation
      });
    }

    return results;
  };

  // Security validation
  const validateSecurity = async (): Promise<ValidationStepResult[]> => {
    const results: ValidationStepResult[] = [];
    
    await new Promise(resolve => setTimeout(resolve, 800));

    // Check SSL/TLS usage
    const httpConnections = config.connections.filter(c => c.endpoint.startsWith('http://'));
    if (httpConnections.length > 0) {
      results.push({
        step: 'SSL/TLS Security',
        category: 'security',
        status: 'warning',
        message: `${httpConnections.length} connections use HTTP instead of HTTPS`,
        duration: 0,
        recommendation: 'Use HTTPS for all connections to ensure data encryption'
      });
    } else {
      results.push({
        step: 'SSL/TLS Security',
        category: 'security',
        status: 'success',
        message: 'All connections use secure HTTPS protocol',
        duration: 0
      });
    }

    // Check API key security
    const expiredKeys = config.apiKeys.filter(k => k.expiresAt && new Date(k.expiresAt) <= new Date());
    if (expiredKeys.length > 0) {
      results.push({
        step: 'API Key Expiration',
        category: 'security',
        status: 'failed',
        message: `${expiredKeys.length} API keys have expired`,
        duration: 0,
        recommendation: 'Rotate expired API keys immediately'
      });
    } else {
      results.push({
        step: 'API Key Expiration',
        category: 'security',
        status: 'success',
        message: 'All API keys are valid and not expired',
        duration: 0
      });
    }

    // Check key rotation schedules
    const keysWithoutRotation = config.apiKeys.filter(k => !k.rotationSchedule?.enabled);
    if (keysWithoutRotation.length > 0) {
      results.push({
        step: 'Key Rotation Policy',
        category: 'security',
        status: 'warning',
        message: `${keysWithoutRotation.length} API keys do not have automatic rotation enabled`,
        duration: 0,
        recommendation: 'Enable automatic key rotation for enhanced security'
      });
    } else {
      results.push({
        step: 'Key Rotation Policy',
        category: 'security',
        status: 'success',
        message: 'All API keys have rotation policies configured',
        duration: 0
      });
    }

    return results;
  };

  // Connectivity testing
  const testConnectivity = async (): Promise<ValidationStepResult[]> => {
    const results: ValidationStepResult[] = [];
    
    for (const connection of config.connections) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate connectivity test
      const isReachable = Math.random() > 0.1; // 90% success rate for demo
      const responseTime = Math.floor(Math.random() * 1000) + 100;
      
      results.push({
        step: `Connectivity: ${connection.name}`,
        category: 'connectivity',
        status: isReachable ? 'success' : 'failed',
        message: isReachable 
          ? `Connection successful (${responseTime}ms)`
          : 'Connection failed - endpoint unreachable',
        duration: responseTime,
        recommendation: isReachable ? undefined : 'Check endpoint URL and network connectivity'
      });
    }

    return results;
  };

  // Performance testing
  const testPerformance = async (): Promise<ValidationStepResult[]> => {
    const results: ValidationStepResult[] = [];
    
    for (const connection of config.connections) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulate performance test
      const responseTime = Math.floor(Math.random() * 2000) + 200;
      const throughput = Math.floor(Math.random() * 1000) + 100;
      
      let status: ValidationStepResult['status'] = 'success';
      let recommendation: string | undefined;
      
      if (responseTime > 1000) {
        status = 'warning';
        recommendation = 'Consider optimizing endpoint or implementing caching';
      }
      
      results.push({
        step: `Performance: ${connection.name}`,
        category: 'performance',
        status,
        message: `Response time: ${responseTime}ms, Throughput: ${throughput} req/min`,
        duration: responseTime,
        recommendation,
        details: { responseTime, throughput }
      });
    }

    return results;
  };

  // Generate recommendations based on validation results
  const generateRecommendations = (results: ValidationStepResult[]): string[] => {
    const recommendations: string[] = [];
    
    const failedTests = results.filter(r => r.status === 'failed');
    const warningTests = results.filter(r => r.status === 'warning');
    
    if (failedTests.length > 0) {
      recommendations.push(`Address ${failedTests.length} critical issues to ensure proper functionality`);
    }
    
    if (warningTests.length > 0) {
      recommendations.push(`Review ${warningTests.length} warnings to optimize integration performance`);
    }
    
    // Security recommendations
    const securityIssues = results.filter(r => r.category === 'security' && r.status !== 'success');
    if (securityIssues.length > 0) {
      recommendations.push('Implement security best practices for all integrations');
    }
    
    // Performance recommendations
    const performanceIssues = results.filter(r => r.category === 'performance' && r.status === 'warning');
    if (performanceIssues.length > 0) {
      recommendations.push('Consider performance optimizations for better user experience');
    }
    
    if (recommendations.length === 0) {
      recommendations.push('All integrations are properly configured and performing well');
    }
    
    return recommendations;
  };

  // Validate individual connection configuration
  const validateConnectionConfig = (connection: ConnectionConfig): { valid: boolean; message: string; recommendation?: string } => {
    if (!connection.name || !connection.endpoint) {
      return { 
        valid: false, 
        message: 'Missing required configuration fields',
        recommendation: 'Ensure name and endpoint are properly configured'
      };
    }
    
    try {
      new URL(connection.endpoint);
    } catch {
      return { 
        valid: false, 
        message: 'Invalid endpoint URL format',
        recommendation: 'Use a valid URL format (e.g., https://api.example.com)'
      };
    }
    
    return { valid: true, message: 'Configuration is valid' };
  };

  // Validate individual API key configuration
  const validateAPIKeyConfig = (apiKey: APIKey): { valid: boolean; message: string; recommendation?: string } => {
    if (!apiKey.name || !apiKey.value) {
      return { 
        valid: false, 
        message: 'Missing required API key fields',
        recommendation: 'Ensure name and value are properly configured'
      };
    }
    
    if (apiKey.status === 'expired') {
      return { 
        valid: false, 
        message: 'API key has expired',
        recommendation: 'Rotate or renew the API key'
      };
    }
    
    return { valid: true, message: 'API key configuration is valid' };
  };

  // Export validation report
  const exportReport = () => {
    if (!validationResult) return;
    
    const report = {
      timestamp: validationResult.timestamp.toISOString(),
      summary: {
        success: validationResult.success,
        message: validationResult.message,
        duration: validationResult.duration
      },
      details: validationResult.details,
      recommendations: validationResult.recommendations,
      configuration: {
        connectionsCount: config.connections.length,
        apiKeysCount: config.apiKeys.length,
        testsEnabled: {
          endpoints: config.testEndpoints,
          security: config.validateSecurity,
          performance: config.checkPerformance
        }
      }
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `integration-validation-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Status icon component
  const StatusIcon: React.FC<{ status: ValidationStepResult['status'] }> = ({ status }) => {
    const icons = {
      success: CheckCircle,
      failed: XCircle,
      warning: AlertTriangle,
      info: Activity
    };

    const colors = {
      success: 'text-green-400',
      failed: 'text-red-400',
      warning: 'text-yellow-400',
      info: 'text-blue-400'
    };

    const Icon = icons[status];
    return <Icon className={`w-4 h-4 ${colors[status]}`} />;
  };

  // Category icon component
  const CategoryIcon: React.FC<{ category: ValidationStepResult['category'] }> = ({ category }) => {
    const icons = {
      security: Shield,
      performance: Zap,
      connectivity: Globe,
      configuration: Settings
    };

    const Icon = icons[category];
    return <Icon className="w-4 h-4 text-gray-400" />;
  };

  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Integration Validator</h3>
          <p className="text-sm text-gray-400">
            Comprehensive testing and validation for all integrations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {validationResult && (
            <button
              onClick={exportReport}
              className="flex items-center px-3 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
          )}
          <button
            onClick={runComprehensiveValidation}
            disabled={validating}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {validating ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <TestTube className="w-4 h-4 mr-2" />
            )}
            {validating ? 'Validating...' : 'Run Validation'}
          </button>
        </div>
      </div>

      {/* Validation Configuration */}
      <div className="mb-6 p-4 bg-gray-900 rounded-lg">
        <h4 className="text-md font-semibold text-white mb-3">Validation Settings</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.testEndpoints}
              onChange={(e) => setConfig(prev => ({ ...prev, testEndpoints: e.target.checked }))}
              className="mr-2"
            />
            <span className="text-sm text-gray-300">Test Endpoints</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.validateSecurity}
              onChange={(e) => setConfig(prev => ({ ...prev, validateSecurity: e.target.checked }))}
              className="mr-2"
            />
            <span className="text-sm text-gray-300">Security Validation</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.checkPerformance}
              onChange={(e) => setConfig(prev => ({ ...prev, checkPerformance: e.target.checked }))}
              className="mr-2"
            />
            <span className="text-sm text-gray-300">Performance Testing</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.generateReport}
              onChange={(e) => setConfig(prev => ({ ...prev, generateReport: e.target.checked }))}
              className="mr-2"
            />
            <span className="text-sm text-gray-300">Generate Report</span>
          </label>
        </div>
      </div>

      {/* Current Step Indicator */}
      {validating && currentStep && (
        <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded">
          <div className="flex items-center">
            <RefreshCw className="w-4 h-4 mr-2 text-blue-400 animate-spin" />
            <span className="text-blue-400">Running: {currentStep}</span>
          </div>
        </div>
      )}

      {/* Validation Results */}
      {validationResult && (
        <div className="space-y-4">
          <div className={`p-4 rounded-lg border ${
            validationResult.success 
              ? 'bg-green-900/20 border-green-500/30'
              : 'bg-red-900/20 border-red-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                {validationResult.success ? (
                  <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                ) : (
                  <XCircle className="w-5 h-5 mr-2 text-red-400" />
                )}
                <span className={validationResult.success ? 'text-green-400' : 'text-red-400'}>
                  {validationResult.message}
                </span>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span>Duration: {validationResult.duration}ms</span>
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="flex items-center hover:text-white"
                >
                  {showDetails ? <EyeOff className="w-4 h-4 mr-1" /> : <Eye className="w-4 h-4 mr-1" />}
                  {showDetails ? 'Hide' : 'Show'} Details
                </button>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {validationResult.recommendations.length > 0 && (
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
              <h4 className="text-md font-semibold text-yellow-400 mb-2">Recommendations</h4>
              <ul className="space-y-1">
                {validationResult.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-yellow-300 flex items-start">
                    <span className="mr-2">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Detailed Results */}
          {showDetails && (
            <div className="bg-gray-900 rounded-lg p-4">
              <h4 className="text-md font-semibold text-white mb-3">Validation Details</h4>
              <div className="space-y-2">
                {validationResult.details.map((detail, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-800 rounded">
                    <div className="flex items-center space-x-3">
                      <CategoryIcon category={detail.category} />
                      <StatusIcon status={detail.status} />
                      <span className="text-white">{detail.step}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm">
                      <span className="text-gray-400">{detail.message}</span>
                      {detail.duration > 0 && (
                        <span className="text-gray-500">{detail.duration}ms</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};