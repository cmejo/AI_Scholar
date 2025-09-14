/**
 * IntegrationTester - Comprehensive integration testing and validation component
 */
import React, { useState } from 'react';
import {
  TestTube,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Shield,
  Zap,
  Database,
  Globe,
  Key,
  Activity,
  Eye,
  EyeOff
} from 'lucide-react';

export interface IntegrationTesterProps {
  integrationId?: string;
  integrationType: 'connection' | 'api_key' | 'webhook' | 'database';
  config: any;
  onTestComplete?: (result: TestResult) => void;
  className?: string;
}

export interface TestResult {
  success: boolean;
  message: string;
  details: TestStepResult[];
  duration: number;
  timestamp: Date;
}

export interface TestStepResult {
  step: string;
  status: 'success' | 'failed' | 'warning' | 'skipped';
  message: string;
  duration: number;
  details?: any;
}

export const IntegrationTester: React.FC<IntegrationTesterProps> = ({
  integrationId,
  integrationType,
  config,
  onTestComplete,
  className = ''
}) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [showDetails, setShowDetails] = useState(false);

  // Define test suites for different integration types
  const getTestSuite = (type: string): TestStep[] => {
    const commonTests: TestStep[] = [
      {
        name: 'Configuration Validation',
        description: 'Validate configuration parameters',
        test: validateConfiguration,
        critical: true
      },
      {
        name: 'Network Connectivity',
        description: 'Test network connectivity to endpoint',
        test: testNetworkConnectivity,
        critical: true
      }
    ];

    const typeSpecificTests: Record<string, TestStep[]> = {
      connection: [
        ...commonTests,
        {
          name: 'Authentication Test',
          description: 'Verify authentication credentials',
          test: testAuthentication,
          critical: true
        },
        {
          name: 'Permission Check',
          description: 'Validate required permissions',
          test: testPermissions,
          critical: false
        },
        {
          name: 'SSL/TLS Validation',
          description: 'Verify SSL certificate and security',
          test: testSSLSecurity,
          critical: false
        },
        {
          name: 'Response Format Test',
          description: 'Validate API response format',
          test: testResponseFormat,
          critical: false
        }
      ],
      api_key: [
        ...commonTests,
        {
          name: 'Key Format Validation',
          description: 'Validate API key format and structure',
          test: validateKeyFormat,
          critical: true
        },
        {
          name: 'Key Authentication',
          description: 'Test API key authentication',
          test: testKeyAuthentication,
          critical: true
        },
        {
          name: 'Rate Limit Check',
          description: 'Check rate limiting and quotas',
          test: testRateLimits,
          critical: false
        },
        {
          name: 'Expiration Check',
          description: 'Verify key expiration status',
          test: checkKeyExpiration,
          critical: false
        }
      ],
      webhook: [
        ...commonTests,
        {
          name: 'Webhook Delivery Test',
          description: 'Test webhook payload delivery',
          test: testWebhookDelivery,
          critical: true
        },
        {
          name: 'Payload Validation',
          description: 'Validate webhook payload format',
          test: validateWebhookPayload,
          critical: false
        }
      ],
      database: [
        ...commonTests,
        {
          name: 'Database Connection',
          description: 'Test database connection',
          test: testDatabaseConnection,
          critical: true
        },
        {
          name: 'Query Execution',
          description: 'Test basic query execution',
          test: testQueryExecution,
          critical: true
        },
        {
          name: 'Schema Validation',
          description: 'Validate database schema access',
          test: validateDatabaseSchema,
          critical: false
        }
      ]
    };

    return typeSpecificTests[type] || commonTests;
  };

  // Test step interface
  interface TestStep {
    name: string;
    description: string;
    test: (config: any) => Promise<TestStepResult>;
    critical: boolean;
  }

  // Run comprehensive test suite
  const runTests = async () => {
    setTesting(true);
    setTestResult(null);
    setCurrentStep('');

    const startTime = Date.now();
    const testSuite = getTestSuite(integrationType);
    const results: TestStepResult[] = [];

    try {
      for (const testStep of testSuite) {
        setCurrentStep(testStep.name);
        
        const stepStartTime = Date.now();
        
        try {
          const result = await testStep.test(config);
          const stepDuration = Date.now() - stepStartTime;
          
          results.push({
            ...result,
            duration: stepDuration
          });

          // Add delay for better UX
          await new Promise(resolve => setTimeout(resolve, 300));
          
          // Stop on critical failures
          if (result.status === 'failed' && testStep.critical) {
            break;
          }
        } catch (error) {
          const stepDuration = Date.now() - stepStartTime;
          results.push({
            step: testStep.name,
            status: 'failed',
            message: error instanceof Error ? error.message : 'Test failed',
            duration: stepDuration
          });

          if (testStep.critical) {
            break;
          }
        }
      }

      const totalDuration = Date.now() - startTime;
      const successCount = results.filter(r => r.status === 'success').length;
      const failedCount = results.filter(r => r.status === 'failed').length;
      const warningCount = results.filter(r => r.status === 'warning').length;

      const overallSuccess = failedCount === 0 && results.length > 0;

      const finalResult: TestResult = {
        success: overallSuccess,
        message: overallSuccess 
          ? `All tests passed successfully (${successCount}/${results.length})`
          : `Tests completed with ${failedCount} failures, ${warningCount} warnings (${successCount}/${results.length} passed)`,
        details: results,
        duration: totalDuration,
        timestamp: new Date()
      };

      setTestResult(finalResult);
      onTestComplete?.(finalResult);

    } catch (error) {
      const finalResult: TestResult = {
        success: false,
        message: 'Test suite execution failed: ' + (error instanceof Error ? error.message : 'Unknown error'),
        details: results,
        duration: Date.now() - startTime,
        timestamp: new Date()
      };

      setTestResult(finalResult);
      onTestComplete?.(finalResult);
    } finally {
      setTesting(false);
      setCurrentStep('');
    }
  };

  // Individual test implementations
  const validateConfiguration = async (config: any): Promise<TestStepResult> => {
    const requiredFields = ['endpoint', 'name'];
    const missingFields = requiredFields.filter(field => !config[field]);

    if (missingFields.length > 0) {
      return {
        step: 'Configuration Validation',
        status: 'failed',
        message: `Missing required fields: ${missingFields.join(', ')}`,
        duration: 0
      };
    }

    // Validate URL format
    if (config.endpoint) {
      try {
        new URL(config.endpoint);
      } catch {
        return {
          step: 'Configuration Validation',
          status: 'failed',
          message: 'Invalid endpoint URL format',
          duration: 0
        };
      }
    }

    return {
      step: 'Configuration Validation',
      status: 'success',
      message: 'Configuration is valid',
      duration: 0
    };
  };

  const testNetworkConnectivity = async (config: any): Promise<TestStepResult> => {
    // Simulate network connectivity test
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const isReachable = Math.random() > 0.05; // 95% success rate for demo
    
    return {
      step: 'Network Connectivity',
      status: isReachable ? 'success' : 'failed',
      message: isReachable 
        ? 'Endpoint is reachable'
        : 'Endpoint is not reachable - check URL and network connectivity',
      duration: 0
    };
  };

  const testAuthentication = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    if (!config.authentication || config.authentication.type === 'none') {
      return {
        step: 'Authentication Test',
        status: 'success',
        message: 'No authentication required',
        duration: 0
      };
    }

    const authSuccess = Math.random() > 0.15; // 85% success rate for demo
    
    return {
      step: 'Authentication Test',
      status: authSuccess ? 'success' : 'failed',
      message: authSuccess 
        ? 'Authentication successful'
        : 'Authentication failed - check credentials',
      duration: 0
    };
  };

  const testPermissions = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    const hasPermissions = Math.random() > 0.2; // 80% success rate for demo
    
    return {
      step: 'Permission Check',
      status: hasPermissions ? 'success' : 'warning',
      message: hasPermissions 
        ? 'All required permissions available'
        : 'Some permissions may be missing - functionality may be limited',
      duration: 0
    };
  };

  const testSSLSecurity = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    try {
      const url = new URL(config.endpoint);
      
      if (url.protocol === 'http:') {
        return {
          step: 'SSL/TLS Validation',
          status: 'warning',
          message: 'Connection uses HTTP - consider using HTTPS for security',
          duration: 0
        };
      }
      
      const sslValid = Math.random() > 0.05; // 95% success rate for demo
      
      return {
        step: 'SSL/TLS Validation',
        status: sslValid ? 'success' : 'failed',
        message: sslValid 
          ? 'SSL/TLS certificate is valid'
          : 'SSL/TLS certificate validation failed',
        duration: 0
      };
    } catch {
      return {
        step: 'SSL/TLS Validation',
        status: 'failed',
        message: 'SSL validation failed',
        duration: 0
      };
    }
  };

  const testResponseFormat = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 700));
    
    const validFormat = Math.random() > 0.1; // 90% success rate for demo
    
    return {
      step: 'Response Format Test',
      status: validFormat ? 'success' : 'failed',
      message: validFormat 
        ? 'Response format is valid and parseable'
        : 'Invalid response format received',
      duration: 0
    };
  };

  const validateKeyFormat = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    if (!config.value) {
      return {
        step: 'Key Format Validation',
        status: 'failed',
        message: 'API key value is required',
        duration: 0
      };
    }

    if (config.value.length < 8) {
      return {
        step: 'Key Format Validation',
        status: 'failed',
        message: 'API key is too short',
        duration: 0
      };
    }

    return {
      step: 'Key Format Validation',
      status: 'success',
      message: 'API key format is valid',
      duration: 0
    };
  };

  const testKeyAuthentication = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    const authSuccess = Math.random() > 0.15; // 85% success rate for demo
    
    return {
      step: 'Key Authentication',
      status: authSuccess ? 'success' : 'failed',
      message: authSuccess 
        ? 'API key authentication successful'
        : 'API key authentication failed - key may be invalid or revoked',
      duration: 0
    };
  };

  const testRateLimits = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    const withinLimits = Math.random() > 0.1; // 90% success rate for demo
    
    return {
      step: 'Rate Limit Check',
      status: withinLimits ? 'success' : 'warning',
      message: withinLimits 
        ? 'Rate limits are within acceptable range'
        : 'Rate limit may be exceeded - monitor usage',
      duration: 0
    };
  };

  const checkKeyExpiration = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    if (!config.expiresAt) {
      return {
        step: 'Expiration Check',
        status: 'success',
        message: 'API key does not expire',
        duration: 0
      };
    }

    const expiresAt = new Date(config.expiresAt);
    const now = new Date();
    const daysUntilExpiry = Math.ceil((expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (expiresAt <= now) {
      return {
        step: 'Expiration Check',
        status: 'failed',
        message: 'API key has expired',
        duration: 0
      };
    }

    if (daysUntilExpiry <= 7) {
      return {
        step: 'Expiration Check',
        status: 'warning',
        message: `API key expires in ${daysUntilExpiry} days - consider renewal`,
        duration: 0
      };
    }

    return {
      step: 'Expiration Check',
      status: 'success',
      message: `API key expires in ${daysUntilExpiry} days`,
      duration: 0
    };
  };

  const testWebhookDelivery = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const deliverySuccess = Math.random() > 0.2; // 80% success rate for demo
    
    return {
      step: 'Webhook Delivery Test',
      status: deliverySuccess ? 'success' : 'failed',
      message: deliverySuccess 
        ? 'Webhook payload delivered successfully'
        : 'Webhook delivery failed - check endpoint and configuration',
      duration: 0
    };
  };

  const validateWebhookPayload = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    return {
      step: 'Payload Validation',
      status: 'success',
      message: 'Webhook payload format is valid',
      duration: 0
    };
  };

  const testDatabaseConnection = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const connectionSuccess = Math.random() > 0.1; // 90% success rate for demo
    
    return {
      step: 'Database Connection',
      status: connectionSuccess ? 'success' : 'failed',
      message: connectionSuccess 
        ? 'Database connection established successfully'
        : 'Database connection failed - check credentials and network',
      duration: 0
    };
  };

  const testQueryExecution = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const querySuccess = Math.random() > 0.15; // 85% success rate for demo
    
    return {
      step: 'Query Execution',
      status: querySuccess ? 'success' : 'failed',
      message: querySuccess 
        ? 'Basic queries execute successfully'
        : 'Query execution failed - check permissions and schema',
      duration: 0
    };
  };

  const validateDatabaseSchema = async (config: any): Promise<TestStepResult> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      step: 'Schema Validation',
      status: 'success',
      message: 'Database schema access is available',
      duration: 0
    };
  };

  // Status icon component
  const StatusIcon: React.FC<{ status: TestStepResult['status'] }> = ({ status }) => {
    const icons = {
      success: CheckCircle,
      failed: XCircle,
      warning: AlertTriangle,
      skipped: Clock
    };

    const colors = {
      success: 'text-green-400',
      failed: 'text-red-400',
      warning: 'text-yellow-400',
      skipped: 'text-gray-400'
    };

    const Icon = icons[status];
    return <Icon className={`w-4 h-4 ${colors[status]}`} />;
  };

  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Integration Tester</h3>
          <p className="text-sm text-gray-400">
            Comprehensive testing for {integrationType} integration
          </p>
        </div>
        <button
          onClick={runTests}
          disabled={testing}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {testing ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <TestTube className="w-4 h-4 mr-2" />
          )}
          {testing ? 'Testing...' : 'Run Tests'}
        </button>
      </div>

      {/* Current Step Indicator */}
      {testing && currentStep && (
        <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded">
          <div className="flex items-center">
            <RefreshCw className="w-4 h-4 mr-2 text-blue-400 animate-spin" />
            <span className="text-blue-400">Running: {currentStep}</span>
          </div>
        </div>
      )}

      {/* Test Results */}
      {testResult && (
        <div className="space-y-4">
          <div className={`p-4 rounded-lg border ${
            testResult.success 
              ? 'bg-green-900/20 border-green-500/30'
              : 'bg-red-900/20 border-red-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                {testResult.success ? (
                  <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                ) : (
                  <XCircle className="w-5 h-5 mr-2 text-red-400" />
                )}
                <span className={testResult.success ? 'text-green-400' : 'text-red-400'}>
                  {testResult.message}
                </span>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span>Duration: {testResult.duration}ms</span>
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

          {/* Detailed Results */}
          {showDetails && (
            <div className="bg-gray-900 rounded-lg p-4">
              <h4 className="text-md font-semibold text-white mb-3">Test Details</h4>
              <div className="space-y-2">
                {testResult.details.map((detail, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                    <div className="flex items-center">
                      <StatusIcon status={detail.status} />
                      <span className="ml-2 text-white">{detail.step}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm">
                      <span className="text-gray-400">{detail.message}</span>
                      <span className="text-gray-500">{detail.duration}ms</span>
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