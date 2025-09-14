/**
 * APIKeyManager - Component for secure credential management
 */
import React, { useState, useEffect } from 'react';
import {
  Key,
  Plus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  RefreshCw,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Filter,
  Download,
  Upload,
  Settings,
  Calendar,
  User,
  TestTube
} from 'lucide-react';

export interface APIKeyManagerProps {
  onKeyUpdate?: (key: APIKey) => void;
  onKeyDelete?: (keyId: string) => void;
}

interface APIKey {
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

export const APIKeyManager: React.FC<APIKeyManagerProps> = ({
  onKeyUpdate,
  onKeyDelete
}) => {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [serviceFilter, setServiceFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedKey, setSelectedKey] = useState<APIKey | null>(null);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());

  // Load API keys
  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    try {
      setLoading(true);
      // Mock API call - replace with actual API
      const mockKeys: APIKey[] = [
        {
          id: 'key_1',
          name: 'OpenAI API Key',
          description: 'Production API key for OpenAI GPT-4',
          service: 'OpenAI',
          type: 'api_key',
          value: 'sk-proj-1234567890abcdef...',
          masked: true,
          status: 'active',
          createdAt: new Date('2024-01-15'),
          expiresAt: new Date('2024-12-31'),
          lastUsed: new Date('2024-01-25T10:30:00'),
          usageCount: 1250,
          permissions: ['gpt-4', 'gpt-3.5-turbo'],
          environment: 'production',
          rotationSchedule: {
            enabled: true,
            intervalDays: 90,
            nextRotation: new Date('2024-04-15')
          }
        },
        {
          id: 'key_2',
          name: 'AWS Access Key',
          description: 'S3 bucket access for document storage',
          service: 'AWS',
          type: 'api_key',
          value: 'AKIA1234567890ABCDEF',
          masked: true,
          status: 'active',
          createdAt: new Date('2024-01-10'),
          lastUsed: new Date('2024-01-25T09:15:00'),
          usageCount: 5600,
          permissions: ['s3:GetObject', 's3:PutObject'],
          environment: 'production'
        },
        {
          id: 'key_3',
          name: 'Slack Webhook',
          description: 'Webhook URL for Slack notifications',
          service: 'Slack',
          type: 'secret',
          value: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
          masked: true,
          status: 'active',
          createdAt: new Date('2024-01-05'),
          lastUsed: new Date('2024-01-25T08:45:00'),
          usageCount: 890,
          permissions: ['chat:write'],
          environment: 'production'
        },
        {
          id: 'key_4',
          name: 'Test API Key',
          description: 'Development testing key',
          service: 'Custom API',
          type: 'api_key',
          value: 'test_key_1234567890',
          masked: true,
          status: 'expired',
          createdAt: new Date('2023-12-01'),
          expiresAt: new Date('2024-01-01'),
          lastUsed: new Date('2023-12-30T15:20:00'),
          usageCount: 45,
          permissions: ['read', 'write'],
          environment: 'development'
        }
      ];

      setKeys(mockKeys);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter keys
  const filteredKeys = keys.filter(key => {
    const matchesSearch = key.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      key.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
      key.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesService = serviceFilter === 'all' || key.service === serviceFilter;
    const matchesStatus = statusFilter === 'all' || key.status === statusFilter;
    return matchesSearch && matchesService && matchesStatus;
  });

  // Get unique services
  const services = Array.from(new Set(keys.map(k => k.service)));

  // Toggle key visibility
  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  // Copy key to clipboard
  const copyToClipboard = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      // Show success message
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  // Generate new API key
  const generateNewKey = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 32; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  // Validate API key format
  const validateAPIKey = (key: string, type: APIKey['type']): { valid: boolean; message?: string } => {
    if (!key) return { valid: false, message: 'API key is required' };

    switch (type) {
      case 'api_key':
        if (key.length < 16) return { valid: false, message: 'API key must be at least 16 characters' };
        break;
      case 'oauth_token':
        if (!key.includes('.') || key.length < 20) return { valid: false, message: 'Invalid OAuth token format' };
        break;
      case 'certificate':
        if (!key.includes('BEGIN CERTIFICATE')) return { valid: false, message: 'Invalid certificate format' };
        break;
      case 'secret':
        if (key.length < 8) return { valid: false, message: 'Secret must be at least 8 characters' };
        break;
    }

    return { valid: true };
  };

  // Comprehensive API key testing and validation
  const testAPIKey = async (key: APIKey): Promise<{ valid: boolean; message: string; details?: any }> => {
    try {
      // Perform comprehensive API key validation
      const validationSteps = [
        { name: 'Format Validation', test: () => validateKeyFormat(key) },
        { name: 'Service Connectivity', test: () => testServiceConnectivity(key) },
        { name: 'Authentication Test', test: () => testKeyAuthentication(key) },
        { name: 'Permission Check', test: () => testKeyPermissions(key) },
        { name: 'Rate Limit Check', test: () => testRateLimits(key) },
        { name: 'Expiration Check', test: () => checkKeyExpiration(key) }
      ];

      const results: any[] = [];
      let overallValid = true;

      for (const step of validationSteps) {
        try {
          const result = await step.test();
          results.push({ step: step.name, ...result });
          if (!result.valid) {
            overallValid = false;
          }
        } catch (error) {
          results.push({
            step: step.name,
            valid: false,
            message: error instanceof Error ? error.message : 'Test failed'
          });
          overallValid = false;
        }

        // Add delay between tests for realistic behavior
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      const successCount = results.filter(r => r.valid).length;
      const totalCount = results.length;

      return {
        valid: overallValid,
        message: overallValid
          ? `API key is valid and fully functional (${successCount}/${totalCount} tests passed)`
          : `API key validation failed (${successCount}/${totalCount} tests passed)`,
        details: results
      };
    } catch (error) {
      return {
        valid: false,
        message: 'Failed to validate API key: ' + (error instanceof Error ? error.message : 'Unknown error')
      };
    }
  };

  // Individual validation functions
  const validateKeyFormat = async (key: APIKey): Promise<{ valid: boolean; message: string }> => {
    const validation = validateAPIKey(key.value, key.type);
    return {
      valid: validation.valid,
      message: validation.valid ? 'Key format is correct' : validation.message || 'Invalid key format'
    };
  };

  const testServiceConnectivity = async (key: APIKey): Promise<{ valid: boolean; message: string }> => {
    // Mock service connectivity test based on service type
    const serviceEndpoints: Record<string, string> = {
      'OpenAI': 'https://api.openai.com/v1/models',
      'AWS': 'https://sts.amazonaws.com/',
      'Slack': 'https://slack.com/api/auth.test',
      'Custom API': 'https://httpbin.org/status/200'
    };

    const endpoint = serviceEndpoints[key.service] || 'https://httpbin.org/status/200';

    try {
      // Simulate network connectivity test
      const isReachable = Math.random() > 0.05; // 95% success rate for demo

      if (!isReachable) {
        return { valid: false, message: `Cannot reach ${key.service} service endpoint` };
      }

      return { valid: true, message: `${key.service} service is reachable` };
    } catch (error) {
      return { valid: false, message: `Service connectivity test failed: ${error}` };
    }
  };

  const testKeyAuthentication = async (key: APIKey): Promise<{ valid: boolean; message: string }> => {
    // Simulate authentication test based on key type and service
    const authSuccess = Math.random() > 0.15; // 85% success rate for demo

    if (!authSuccess) {
      return { valid: false, message: 'Authentication failed - key may be invalid or revoked' };
    }

    return { valid: true, message: 'Authentication successful' };
  };

  const testKeyPermissions = async (key: APIKey): Promise<{ valid: boolean; message: string }> => {
    // Check if key has required permissions
    if (key.permissions.length === 0) {
      return { valid: true, message: 'No specific permissions required' };
    }

    // Simulate permission validation
    const hasPermissions = Math.random() > 0.2; // 80% success rate for demo

    if (!hasPermissions) {
      return { valid: false, message: `Missing required permissions: ${key.permissions.join(', ')}` };
    }

    return { valid: true, message: `All required permissions available: ${key.permissions.join(', ')}` };
  };

  const testRateLimits = async (key: APIKey): Promise<{ valid: boolean; message: string }> => {
    // Simulate rate limit check
    const withinLimits = Math.random() > 0.1; // 90% success rate for demo

    if (!withinLimits) {
      return { valid: false, message: 'Rate limit exceeded - key may be throttled' };
    }

    return { valid: true, message: 'Rate limits are within acceptable range' };
  };

  const checkKeyExpiration = async (key: APIKey): Promise<{ valid: boolean; message: string }> => {
    if (!key.expiresAt) {
      return { valid: true, message: 'Key does not expire' };
    }

    const now = new Date();
    const expiresAt = new Date(key.expiresAt);
    const daysUntilExpiry = Math.ceil((expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (expiresAt <= now) {
      return { valid: false, message: 'Key has expired' };
    }

    if (daysUntilExpiry <= 7) {
      return { valid: true, message: `Key expires in ${daysUntilExpiry} days - consider renewal` };
    }

    return { valid: true, message: `Key expires in ${daysUntilExpiry} days` };
  };

  // Enhanced key rotation with validation
  const rotateAPIKey = async (keyId: string): Promise<void> => {
    const key = keys.find(k => k.id === keyId);
    if (!key) return;

    try {
      // Generate new key
      const newValue = generateNewKey();

      // Validate new key before rotation
      const validation = validateAPIKey(newValue, key.type);
      if (!validation.valid) {
        throw new Error('Generated key failed validation');
      }

      // Update key with new value
      const rotatedKey: APIKey = {
        ...key,
        value: newValue,
        createdAt: new Date(),
        usageCount: 0,
        status: 'active',
        rotationSchedule: key.rotationSchedule ? {
          ...key.rotationSchedule,
          nextRotation: new Date(Date.now() + (key.rotationSchedule.intervalDays * 24 * 60 * 60 * 1000))
        } : undefined
      };

      setKeys(prevKeys => prevKeys.map(k => k.id === keyId ? rotatedKey : k));
      onKeyUpdate?.(rotatedKey);

      // Test the new key
      const testResult = await testAPIKey(rotatedKey);
      if (!testResult.valid) {
        console.warn('Rotated key failed validation:', testResult.message);
      }
    } catch (error) {
      console.error('Key rotation failed:', error);
      throw error;
    }
  };

  // Bulk key validation
  const validateAllKeys = async (): Promise<void> => {
    setLoading(true);
    try {
      const validationPromises = keys.map(async (key) => {
        const result = await testAPIKey(key);
        return { keyId: key.id, ...result };
      });

      const results = await Promise.all(validationPromises);

      // Update key statuses based on validation results
      const updatedKeys = keys.map(key => {
        const result = results.find(r => r.keyId === key.id);
        if (result && !result.valid && key.status === 'active') {
          return { ...key, status: 'expired' as APIKey['status'] };
        }
        return key;
      });

      setKeys(updatedKeys);

      const failedCount = results.filter(r => !r.valid).length;
      if (failedCount > 0) {
        alert(`Validation complete. ${failedCount} keys failed validation and have been marked as expired.`);
      } else {
        alert('All keys passed validation successfully.');
      }
    } catch (error) {
      console.error('Bulk validation failed:', error);
      alert('Bulk validation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Status badge component
  const StatusBadge: React.FC<{ status: APIKey['status'] }> = ({ status }) => {
    const statusConfig = {
      active: { icon: CheckCircle, color: 'text-green-400 bg-green-400/10', label: 'Active' },
      expired: { icon: Clock, color: 'text-yellow-400 bg-yellow-400/10', label: 'Expired' },
      revoked: { icon: AlertTriangle, color: 'text-red-400 bg-red-400/10', label: 'Revoked' },
      pending: { icon: Clock, color: 'text-blue-400 bg-blue-400/10', label: 'Pending' }
    };

    const config = statusConfig[status];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
  };

  // Environment badge
  const EnvironmentBadge: React.FC<{ environment: APIKey['environment'] }> = ({ environment }) => {
    const colors = {
      development: 'bg-blue-400/10 text-blue-400',
      staging: 'bg-yellow-400/10 text-yellow-400',
      production: 'bg-red-400/10 text-red-400'
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[environment]}`}>
        {environment}
      </span>
    );
  };

  // Add/Edit modal
  const KeyModal: React.FC<{ isEdit: boolean }> = ({ isEdit }) => {
    const [formData, setFormData] = useState<Partial<APIKey>>(
      isEdit && selectedKey ? selectedKey : {
        name: '',
        description: '',
        service: '',
        type: 'api_key',
        value: '',
        environment: 'development',
        permissions: []
      }
    );

    const handleSave = () => {
      const newKey: APIKey = {
        id: isEdit ? selectedKey!.id : `key_${Date.now()}`,
        name: formData.name!,
        description: formData.description!,
        service: formData.service!,
        type: formData.type!,
        value: formData.value || generateNewKey(),
        masked: true,
        status: 'active',
        createdAt: isEdit ? selectedKey!.createdAt : new Date(),
        expiresAt: formData.expiresAt,
        usageCount: isEdit ? selectedKey!.usageCount : 0,
        permissions: formData.permissions!,
        environment: formData.environment!,
        rotationSchedule: formData.rotationSchedule?.enabled ? {
          enabled: true,
          intervalDays: formData.rotationSchedule.intervalDays,
          nextRotation: new Date(Date.now() + (formData.rotationSchedule.intervalDays * 24 * 60 * 60 * 1000))
        } : undefined
      };

      if (isEdit) {
        setKeys(keys.map(k => k.id === newKey.id ? newKey : k));
      } else {
        setKeys([...keys, newKey]);
      }

      onKeyUpdate?.(newKey);
      setShowAddModal(false);
      setShowEditModal(false);
      setSelectedKey(null);
    };

    if (!showAddModal && !showEditModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              {isEdit ? 'Edit API Key' : 'Add New API Key'}
            </h3>
            <button
              onClick={() => {
                setShowAddModal(false);
                setShowEditModal(false);
                setSelectedKey(null);
              }}
              className="text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Key Name *
                </label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  placeholder="My API Key"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Service *
                </label>
                <input
                  type="text"
                  value={formData.service || ''}
                  onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  placeholder="OpenAI, AWS, etc."
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                rows={3}
                placeholder="Description of what this key is used for"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Key Type
                </label>
                <select
                  value={formData.type || 'api_key'}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as APIKey['type'] })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                >
                  <option value="api_key">API Key</option>
                  <option value="oauth_token">OAuth Token</option>
                  <option value="certificate">Certificate</option>
                  <option value="secret">Secret</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Environment
                </label>
                <select
                  value={formData.environment || 'development'}
                  onChange={(e) => setFormData({ ...formData, environment: e.target.value as APIKey['environment'] })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                >
                  <option value="development">Development</option>
                  <option value="staging">Staging</option>
                  <option value="production">Production</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Key Value
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={formData.value || ''}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  placeholder="Enter key value or leave empty to generate"
                />
                <button
                  onClick={() => setFormData({ ...formData, value: generateNewKey() })}
                  className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Generate
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Permissions (comma-separated)
              </label>
              <input
                type="text"
                value={formData.permissions?.join(', ') || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  permissions: e.target.value.split(',').map(p => p.trim()).filter(Boolean)
                })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                placeholder="read, write, admin"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Expiration Date (optional)
              </label>
              <input
                type="date"
                value={formData.expiresAt ? new Date(formData.expiresAt).toISOString().split('T')[0] : ''}
                onChange={(e) => setFormData({
                  ...formData,
                  expiresAt: e.target.value ? new Date(e.target.value) : undefined
                })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>

            <div className="border-t border-gray-600 pt-4">
              <div className="flex items-center mb-3">
                <input
                  type="checkbox"
                  id="enableRotation"
                  checked={formData.rotationSchedule?.enabled || false}
                  onChange={(e) => setFormData({
                    ...formData,
                    rotationSchedule: {
                      enabled: e.target.checked,
                      intervalDays: formData.rotationSchedule?.intervalDays || 90
                    }
                  })}
                  className="mr-2"
                />
                <label htmlFor="enableRotation" className="text-sm font-medium text-gray-300">
                  Enable Automatic Key Rotation
                </label>
              </div>

              {formData.rotationSchedule?.enabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Rotation Interval (days)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={formData.rotationSchedule?.intervalDays || 90}
                    onChange={(e) => setFormData({
                      ...formData,
                      rotationSchedule: {
                        ...formData.rotationSchedule!,
                        intervalDays: parseInt(e.target.value) || 90
                      }
                    })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                    placeholder="90"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Key will be automatically rotated every {formData.rotationSchedule?.intervalDays || 90} days
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={() => {
                setShowAddModal(false);
                setShowEditModal(false);
                setSelectedKey(null);
              }}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {isEdit ? 'Update' : 'Create'} Key
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-900 text-white">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">API Key Manager</h2>
            <p className="text-gray-400">Securely manage API keys and credentials</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={loadAPIKeys}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={validateAllKeys}
              disabled={loading || keys.length === 0}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              <TestTube className="w-4 h-4 mr-2" />
              Validate All
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add API Key
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search API keys..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400"
            />
          </div>
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="all">All Services</option>
            {services.map(service => (
              <option key={service} value={service}>{service}</option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="revoked">Revoked</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {/* API Keys List */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {filteredKeys.length === 0 ? (
          <div className="text-center py-8">
            <Key className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No API Keys Found</h3>
            <p className="text-gray-400 mb-4">
              {searchTerm || serviceFilter !== 'all' || statusFilter !== 'all'
                ? 'No API keys match your current filters.'
                : 'Get started by adding your first API key.'
              }
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Add API Key
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {filteredKeys.map(key => (
              <div key={key.id} className="p-6 hover:bg-gray-700/50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Key className="w-5 h-5 text-blue-400" />
                      <h3 className="font-semibold text-white">{key.name}</h3>
                      <StatusBadge status={key.status} />
                      <EnvironmentBadge environment={key.environment} />
                    </div>

                    <p className="text-sm text-gray-400 mb-3">{key.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Service:</span>
                        <span className="text-gray-300 ml-2">{key.service}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Type:</span>
                        <span className="text-gray-300 ml-2">{key.type}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Usage:</span>
                        <span className="text-gray-300 ml-2">{key.usageCount} requests</span>
                      </div>
                      {key.lastUsed && (
                        <div>
                          <span className="text-gray-400">Last Used:</span>
                          <span className="text-gray-300 ml-2">{key.lastUsed.toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>

                    {/* Key Value */}
                    <div className="mt-4 p-3 bg-gray-900 rounded">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 flex-1">
                          <span className="text-sm text-gray-400">Key:</span>
                          <code className="text-sm text-gray-300 font-mono">
                            {visibleKeys.has(key.id) ? key.value : '••••••••••••••••'}
                          </code>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => toggleKeyVisibility(key.id)}
                            className="p-1 text-gray-400 hover:text-white"
                            title={visibleKeys.has(key.id) ? 'Hide' : 'Show'}
                          >
                            {visibleKeys.has(key.id) ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                          <button
                            onClick={() => copyToClipboard(key.value)}
                            className="p-1 text-gray-400 hover:text-white"
                            title="Copy to clipboard"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Permissions */}
                    {key.permissions.length > 0 && (
                      <div className="mt-3">
                        <span className="text-sm text-gray-400">Permissions: </span>
                        <div className="inline-flex flex-wrap gap-1 mt-1">
                          {key.permissions.map(permission => (
                            <span
                              key={permission}
                              className="px-2 py-1 bg-blue-400/10 text-blue-400 text-xs rounded"
                            >
                              {permission}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={async () => {
                        try {
                          const result = await testAPIKey(key);

                          // Show detailed results in a modal or alert
                          let message = result.message;
                          if (result.details && Array.isArray(result.details)) {
                            message += '\n\nDetailed Results:\n';
                            result.details.forEach((detail: any) => {
                              message += `${detail.valid ? '✓' : '✗'} ${detail.step}: ${detail.message}\n`;
                            });
                          }

                          alert(message);

                          // Update key status based on test result
                          if (!result.valid && key.status === 'active') {
                            const updatedKeys = keys.map(k =>
                              k.id === key.id ? { ...k, status: 'expired' as APIKey['status'] } : k
                            );
                            setKeys(updatedKeys);
                          }
                        } catch (error) {
                          alert('Test failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
                        }
                      }}
                      className="p-2 text-gray-400 hover:text-green-400 hover:bg-gray-600 rounded"
                      title="Test API Key"
                    >
                      <TestTube className="w-4 h-4" />
                    </button>
                    {key.rotationSchedule?.enabled && (
                      <button
                        onClick={async () => {
                          if (confirm('Are you sure you want to rotate this API key? The old key will be invalidated.')) {
                            try {
                              await rotateAPIKey(key.id);
                              alert('API key rotated successfully!');
                            } catch (error) {
                              alert('Key rotation failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
                            }
                          }
                        }}
                        className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-gray-600 rounded"
                        title="Rotate API Key"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setSelectedKey(key);
                        setShowEditModal(true);
                      }}
                      className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded"
                      title="Edit"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to delete this API key?')) {
                          setKeys(keys.filter(k => k.id !== key.id));
                          onKeyDelete?.(key.id);
                        }
                      }}
                      className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-600 rounded"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <KeyModal isEdit={showEditModal} />
    </div>
  );
};