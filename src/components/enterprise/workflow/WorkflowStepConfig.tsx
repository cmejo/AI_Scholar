/**
 * WorkflowStepConfig - Configuration interface for workflow steps
 * Provides forms for configuring triggers, conditions, and actions
 */
import React, { useState, useEffect } from 'react';
import {
  Settings,
  Save,
  X,
  AlertTriangle,
  Info,
  Clock,
  Code,
  Database,
  Mail,
  FileText,
  Tag,
  Webhook,
  MousePointer,
  Filter,
  Zap,
  Plus,
  Minus,
  Eye,
  EyeOff,
  HelpCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import type {
  WorkflowTrigger,
  WorkflowCondition,
  WorkflowAction
} from '../../../types/workflow';

export interface WorkflowStepConfigProps {
  step: WorkflowTrigger | WorkflowCondition | WorkflowAction;
  stepType: 'trigger' | 'condition' | 'action';
  onSave: (step: WorkflowTrigger | WorkflowCondition | WorkflowAction) => void;
  onCancel: () => void;
  onDelete?: () => void;
  isNew?: boolean;
}

interface ValidationError {
  field: string;
  message: string;
}

export const WorkflowStepConfig: React.FC<WorkflowStepConfigProps> = ({
  step,
  stepType,
  onSave,
  onCancel,
  onDelete,
  isNew = false
}) => {
  const [config, setConfig] = useState(step);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Update config when step changes
  useEffect(() => {
    setConfig(step);
  }, [step]);

  // Validation
  const validateConfig = (): ValidationError[] => {
    const newErrors: ValidationError[] = [];

    if (stepType === 'trigger') {
      const trigger = config as WorkflowTrigger;
      
      if (trigger.type === 'schedule' && !trigger.config.cron) {
        newErrors.push({ field: 'cron', message: 'Cron expression is required for scheduled triggers' });
      }
      
      if (trigger.type === 'webhook' && !trigger.config.url) {
        newErrors.push({ field: 'url', message: 'Webhook URL is required' });
      }
    } else if (stepType === 'condition') {
      const condition = config as WorkflowCondition;
      
      if (!condition.value && condition.value !== 0) {
        newErrors.push({ field: 'value', message: 'Condition value is required' });
      }
      
      if (condition.type === 'custom' && !condition.field) {
        newErrors.push({ field: 'field', message: 'Field name is required for custom conditions' });
      }
    } else if (stepType === 'action') {
      const action = config as WorkflowAction;
      
      if (!action.name?.trim()) {
        newErrors.push({ field: 'name', message: 'Action name is required' });
      }
      
      if (action.type === 'api_call' && !action.config.url) {
        newErrors.push({ field: 'url', message: 'API URL is required' });
      }
      
      if (action.type === 'send_notification' && !action.config.recipients) {
        newErrors.push({ field: 'recipients', message: 'Recipients are required for notifications' });
      }
    }

    return newErrors;
  };

  // Handle save
  const handleSave = () => {
    const validationErrors = validateConfig();
    setErrors(validationErrors);

    if (validationErrors.length === 0) {
      onSave(config);
    }
  };

  // Handle test
  const handleTest = async () => {
    try {
      // Mock test implementation
      await new Promise(resolve => setTimeout(resolve, 1000));
      setTestResult({ success: true, message: 'Configuration test passed' });
    } catch (error) {
      setTestResult({ success: false, message: 'Configuration test failed' });
    }
  };

  // Update config field
  const updateConfig = (field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear related errors
    setErrors(prev => prev.filter(error => error.field !== field));
  };

  // Update nested config field
  const updateNestedConfig = (path: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      config: {
        ...prev.config,
        [path]: value
      }
    }));
    
    // Clear related errors
    setErrors(prev => prev.filter(error => error.field !== path));
  };

  // Get field error
  const getFieldError = (field: string) => {
    return errors.find(error => error.field === field)?.message;
  };

  // Render trigger configuration
  const renderTriggerConfig = () => {
    const trigger = config as WorkflowTrigger;

    return (
      <div className="space-y-6">
        {/* Basic Configuration */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-green-400" />
            Trigger Configuration
          </h3>

          {/* Trigger Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Trigger Type
            </label>
            <select
              value={trigger.type}
              onChange={(e) => updateConfig('type', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="manual">Manual Trigger</option>
              <option value="schedule">Scheduled</option>
              <option value="document_upload">Document Upload</option>
              <option value="api_call">API Call</option>
              <option value="webhook">Webhook</option>
            </select>
          </div>

          {/* Type-specific configuration */}
          {trigger.type === 'schedule' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Cron Expression
                  <span className="text-red-400 ml-1">*</span>
                </label>
                <input
                  type="text"
                  value={trigger.config.cron || ''}
                  onChange={(e) => updateNestedConfig('cron', e.target.value)}
                  placeholder="0 9 * * * (daily at 9 AM)"
                  className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                    getFieldError('cron') ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                {getFieldError('cron') && (
                  <p className="text-red-400 text-sm mt-1">{getFieldError('cron')}</p>
                )}
                <p className="text-gray-400 text-sm mt-1">
                  Use standard cron format: minute hour day month weekday
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Timezone
                </label>
                <select
                  value={trigger.config.timezone || 'UTC'}
                  onChange={(e) => updateNestedConfig('timezone', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                </select>
              </div>
            </div>
          )}

          {trigger.type === 'document_upload' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  File Types
                </label>
                <input
                  type="text"
                  value={(trigger.config.fileTypes as string[])?.join(', ') || ''}
                  onChange={(e) => updateNestedConfig('fileTypes', e.target.value.split(',').map(s => s.trim()))}
                  placeholder="pdf, docx, txt"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
                <p className="text-gray-400 text-sm mt-1">
                  Comma-separated list of file extensions (leave empty for all types)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Maximum File Size (MB)
                </label>
                <input
                  type="number"
                  value={trigger.config.maxSize || ''}
                  onChange={(e) => updateNestedConfig('maxSize', parseInt(e.target.value))}
                  placeholder="10"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {trigger.type === 'webhook' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Webhook URL
                  <span className="text-red-400 ml-1">*</span>
                </label>
                <input
                  type="url"
                  value={trigger.config.url || ''}
                  onChange={(e) => updateNestedConfig('url', e.target.value)}
                  placeholder="https://example.com/webhook"
                  className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                    getFieldError('url') ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                {getFieldError('url') && (
                  <p className="text-red-400 text-sm mt-1">{getFieldError('url')}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Secret Token
                </label>
                <input
                  type="password"
                  value={trigger.config.secret || ''}
                  onChange={(e) => updateNestedConfig('secret', e.target.value)}
                  placeholder="Optional webhook secret"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {trigger.type === 'api_call' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  API Endpoint
                </label>
                <input
                  type="url"
                  value={trigger.config.endpoint || ''}
                  onChange={(e) => updateNestedConfig('endpoint', e.target.value)}
                  placeholder="https://api.example.com/trigger"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  HTTP Method
                </label>
                <select
                  value={trigger.config.method || 'GET'}
                  onChange={(e) => updateNestedConfig('method', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Enabled Toggle */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="trigger-enabled"
            checked={trigger.enabled}
            onChange={(e) => updateConfig('enabled', e.target.checked)}
            className="mr-2"
          />
          <label htmlFor="trigger-enabled" className="text-sm text-gray-300">
            Enable this trigger
          </label>
        </div>
      </div>
    );
  };

  // Render condition configuration
  const renderConditionConfig = () => {
    const condition = config as WorkflowCondition;

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Filter className="w-5 h-5 mr-2 text-yellow-400" />
            Condition Configuration
          </h3>

          {/* Condition Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Condition Type
            </label>
            <select
              value={condition.type}
              onChange={(e) => updateConfig('type', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="document_size">Document Size</option>
              <option value="document_type">Document Type</option>
              <option value="user_role">User Role</option>
              <option value="time_of_day">Time of Day</option>
              <option value="custom">Custom Logic</option>
            </select>
          </div>

          {/* Custom field for custom conditions */}
          {condition.type === 'custom' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Field Name
                <span className="text-red-400 ml-1">*</span>
              </label>
              <input
                type="text"
                value={condition.field || ''}
                onChange={(e) => updateConfig('field', e.target.value)}
                placeholder="metadata.category"
                className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                  getFieldError('field') ? 'border-red-500' : 'border-gray-600'
                }`}
              />
              {getFieldError('field') && (
                <p className="text-red-400 text-sm mt-1">{getFieldError('field')}</p>
              )}
            </div>
          )}

          {/* Operator */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Operator
            </label>
            <select
              value={condition.operator}
              onChange={(e) => updateConfig('operator', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="equals">Equals</option>
              <option value="not_equals">Not Equals</option>
              <option value="greater_than">Greater Than</option>
              <option value="less_than">Less Than</option>
              <option value="contains">Contains</option>
              <option value="matches">Matches (Regex)</option>
            </select>
          </div>

          {/* Value */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Value
              <span className="text-red-400 ml-1">*</span>
            </label>
            {condition.type === 'document_size' ? (
              <div className="flex">
                <input
                  type="number"
                  value={condition.value || ''}
                  onChange={(e) => updateConfig('value', parseInt(e.target.value))}
                  placeholder="1024"
                  className={`flex-1 px-3 py-2 bg-gray-700 border rounded-l focus:outline-none focus:border-blue-500 ${
                    getFieldError('value') ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                <span className="px-3 py-2 bg-gray-600 border border-l-0 border-gray-600 rounded-r text-gray-300">
                  bytes
                </span>
              </div>
            ) : condition.type === 'time_of_day' ? (
              <input
                type="time"
                value={condition.value || ''}
                onChange={(e) => updateConfig('value', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                  getFieldError('value') ? 'border-red-500' : 'border-gray-600'
                }`}
              />
            ) : (
              <input
                type="text"
                value={condition.value || ''}
                onChange={(e) => updateConfig('value', e.target.value)}
                placeholder="Enter condition value"
                className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                  getFieldError('value') ? 'border-red-500' : 'border-gray-600'
                }`}
              />
            )}
            {getFieldError('value') && (
              <p className="text-red-400 text-sm mt-1">{getFieldError('value')}</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Render action configuration
  const renderActionConfig = () => {
    const action = config as WorkflowAction;

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Settings className="w-5 h-5 mr-2 text-blue-400" />
            Action Configuration
          </h3>

          {/* Action Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Action Type
            </label>
            <select
              value={action.type}
              onChange={(e) => updateConfig('type', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="auto_tag">Auto Tag</option>
              <option value="send_notification">Send Notification</option>
              <option value="generate_summary">Generate Summary</option>
              <option value="update_metadata">Update Metadata</option>
              <option value="create_backup">Create Backup</option>
              <option value="api_call">API Call</option>
              <option value="transform_data">Transform Data</option>
            </select>
          </div>

          {/* Action Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Action Name
              <span className="text-red-400 ml-1">*</span>
            </label>
            <input
              type="text"
              value={action.name || ''}
              onChange={(e) => updateConfig('name', e.target.value)}
              placeholder="Enter action name"
              className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                getFieldError('name') ? 'border-red-500' : 'border-gray-600'
              }`}
            />
            {getFieldError('name') && (
              <p className="text-red-400 text-sm mt-1">{getFieldError('name')}</p>
            )}
          </div>

          {/* Type-specific configuration */}
          {action.type === 'auto_tag' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  AI Model
                </label>
                <select
                  value={action.config.aiModel || 'gpt-4'}
                  onChange={(e) => updateNestedConfig('aiModel', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3">Claude 3</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tag Categories
                </label>
                <input
                  type="text"
                  value={(action.config.categories as string[])?.join(', ') || ''}
                  onChange={(e) => updateNestedConfig('categories', e.target.value.split(',').map(s => s.trim()))}
                  placeholder="research, academic, technical"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {action.type === 'send_notification' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Recipients
                  <span className="text-red-400 ml-1">*</span>
                </label>
                <input
                  type="text"
                  value={(action.config.recipients as string[])?.join(', ') || ''}
                  onChange={(e) => updateNestedConfig('recipients', e.target.value.split(',').map(s => s.trim()))}
                  placeholder="user@example.com, admin@example.com"
                  className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                    getFieldError('recipients') ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                {getFieldError('recipients') && (
                  <p className="text-red-400 text-sm mt-1">{getFieldError('recipients')}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Subject Template
                </label>
                <input
                  type="text"
                  value={action.config.subject || ''}
                  onChange={(e) => updateNestedConfig('subject', e.target.value)}
                  placeholder="Workflow notification: {{workflow.name}}"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Message Template
                </label>
                <textarea
                  value={action.config.message || ''}
                  onChange={(e) => updateNestedConfig('message', e.target.value)}
                  placeholder="The workflow {{workflow.name}} has completed successfully."
                  rows={4}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {action.type === 'api_call' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  API URL
                  <span className="text-red-400 ml-1">*</span>
                </label>
                <input
                  type="url"
                  value={action.config.url || ''}
                  onChange={(e) => updateNestedConfig('url', e.target.value)}
                  placeholder="https://api.example.com/endpoint"
                  className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none focus:border-blue-500 ${
                    getFieldError('url') ? 'border-red-500' : 'border-gray-600'
                  }`}
                />
                {getFieldError('url') && (
                  <p className="text-red-400 text-sm mt-1">{getFieldError('url')}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  HTTP Method
                </label>
                <select
                  value={action.config.method || 'POST'}
                  onChange={(e) => updateNestedConfig('method', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Request Headers (JSON)
                </label>
                <textarea
                  value={JSON.stringify(action.config.headers || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      updateNestedConfig('headers', JSON.parse(e.target.value));
                    } catch {
                      // Invalid JSON, don't update
                    }
                  }}
                  placeholder='{"Content-Type": "application/json"}'
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500 font-mono text-sm"
                />
              </div>
            </div>
          )}

          {/* Order */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Execution Order
            </label>
            <input
              type="number"
              value={action.order || 1}
              onChange={(e) => updateConfig('order', parseInt(e.target.value))}
              min="1"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Enabled Toggle */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="action-enabled"
              checked={action.enabled}
              onChange={(e) => updateConfig('enabled', e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="action-enabled" className="text-sm text-gray-300">
              Enable this action
            </label>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold text-white">
          {isNew ? 'Create' : 'Edit'} {stepType.charAt(0).toUpperCase() + stepType.slice(1)}
        </h2>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-gray-700 rounded"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {stepType === 'trigger' && renderTriggerConfig()}
        {stepType === 'condition' && renderConditionConfig()}
        {stepType === 'action' && renderActionConfig()}

        {/* Test Result */}
        {testResult && (
          <div className={`mt-4 p-3 rounded-lg flex items-center ${
            testResult.success ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
          }`}>
            {testResult.success ? (
              <CheckCircle className="w-5 h-5 mr-2" />
            ) : (
              <XCircle className="w-5 h-5 mr-2" />
            )}
            {testResult.message}
          </div>
        )}

        {/* Validation Errors */}
        {errors.length > 0 && (
          <div className="mt-4 p-3 bg-red-900/50 border border-red-500 rounded-lg">
            <div className="flex items-center mb-2">
              <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-red-200 font-medium">Please fix the following errors:</span>
            </div>
            <ul className="list-disc list-inside text-red-200 text-sm space-y-1">
              {errors.map((error, index) => (
                <li key={index}>{error.message}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-4 border-t border-gray-700 bg-gray-750">
        <div className="flex items-center space-x-2">
          {onDelete && !isNew && (
            <button
              onClick={onDelete}
              className="flex items-center px-3 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
            >
              <X className="w-4 h-4 mr-1" />
              Delete
            </button>
          )}
          <button
            onClick={handleTest}
            className="flex items-center px-3 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm"
          >
            <Eye className="w-4 h-4 mr-1" />
            Test
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm"
          >
            <Save className="w-4 h-4 mr-1" />
            Save
          </button>
        </div>
      </div>
    </div>
  );
};