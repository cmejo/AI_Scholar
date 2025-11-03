import React, { useState } from 'react';
import { 
  Zap, Plus, Play, Pause, Edit, Trash2, 
  CheckCircle, BarChart3, X
} from 'lucide-react';
import { withRetry } from '../utils/retryMechanism';
import { announceToScreenReader } from '../hooks/useKeyboardShortcuts';
import { announceToScreenReader } from '../hooks/useKeyboardShortcuts';
import { announceToScreenReader } from '../hooks/useKeyboardShortcuts';
import { announceToScreenReader } from '../hooks/useKeyboardShortcuts';
import { announceToScreenReader } from '../hooks/useKeyboardShortcuts';
import { announceToScreenReader } from '../hooks/useKeyboardShortcuts';
import { withRetry } from '../utils/retryMechanism';
import { T } from 'vitest/dist/chunks/reporters.d.BFLkQcL6.js';
import { T } from 'vitest/dist/chunks/reporters.d.BFLkQcL6.js';
import { T } from 'vitest/dist/chunks/environment.d.cL3nLXbE.js';
import { T } from 'vitest/dist/chunks/environment.d.cL3nLXbE.js';
import { T } from 'vitest/dist/chunks/environment.d.cL3nLXbE.js';
import { T } from 'vitest/dist/chunks/reporters.d.BFLkQcL6.js';

interface Workflow {
  id: number;
  title: string;
  description: string;
  status: 'Active' | 'Draft' | 'Inactive';
  color: string;
  lastRun: string;
  triggers: string[];
  actions: string[];
  executions: number;
  successRate: number;
}

const WorkflowsView: React.FC = () => {
  // Add CSS animations and validation styles
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateX(-10px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
      
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      
      @keyframes pulse {
        0%, 100% {
          opacity: 1;
        }
        50% {
          opacity: 0.7;
        }
      }
      
      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
        20%, 40%, 60%, 80% { transform: translateX(2px); }
      }
      
      @keyframes validationSuccess {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      .validation-error {
        animation: shake 0.5s ease-in-out;
      }
      
      .validation-success {
        animation: validationSuccess 0.3s ease-in-out;
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);
  const [workflows, setWorkflows] = useState<Workflow[]>([
    { 
      id: 1, 
      title: '🤖 Smart Document Processing', 
      description: 'Automatically process and analyze uploaded documents using AI', 
      status: 'Active', 
      color: '#4ade80', 
      lastRun: '2 hours ago',
      triggers: ['Document Upload', 'File Change'],
      actions: ['Extract Text', 'Analyze Content', 'Generate Summary'],
      executions: 156,
      successRate: 98.5
    },
    { 
      id: 2, 
      title: '🧠 Research Pipeline', 
      description: 'Automated research and knowledge extraction workflow', 
      status: 'Draft', 
      color: '#f59e0b', 
      lastRun: 'Never',
      triggers: ['Manual Trigger', 'Scheduled'],
      actions: ['Search Papers', 'Extract Insights', 'Generate Report'],
      executions: 0,
      successRate: 0
    },
    { 
      id: 3, 
      title: '💬 Customer Support', 
      description: 'AI-powered ticket management and response system', 
      status: 'Inactive', 
      color: '#9ca3af', 
      lastRun: '1 week ago',
      triggers: ['New Ticket', 'Email Received'],
      actions: ['Categorize Issue', 'Generate Response', 'Route to Agent'],
      executions: 89,
      successRate: 94.2
    },
    { 
      id: 4, 
      title: '📊 Analytics Automation', 
      description: 'Generate daily analytics reports and insights', 
      status: 'Active', 
      color: '#8b5cf6', 
      lastRun: '1 hour ago',
      triggers: ['Daily Schedule', 'Data Update'],
      actions: ['Collect Metrics', 'Generate Charts', 'Send Report'],
      executions: 45,
      successRate: 100
    }
  ]);

  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false);
  const [showEditWorkflow, setShowEditWorkflow] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null);
  const [workflowStep, setWorkflowStep] = useState(1);
  const [newWorkflow, setNewWorkflow] = useState({
    title: '',
    description: '',
    template: 'custom',
    triggers: [] as string[],
    actions: [] as string[],
    schedule: 'manual',
    enabled: false
  });

  // Enhanced validation and error handling state
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [fieldTouched, setFieldTouched] = useState<{[key: string]: boolean}>({});
  const [duplicateAttempts, setDuplicateAttempts] = useState<{[key: string]: number}>({});
  const [focusedWorkflow, setFocusedWorkflow] = useState<number | null>(null);
  const [announcements, setAnnouncements] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [operationInProgress, setOperationInProgress] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<{message: string, timestamp: number} | null>(null);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const [criticalError, setCriticalError] = useState<string | null>(null);
  const [saveInProgress, setSaveInProgress] = useState<{[key: number]: boolean}>({});
  const [operationHistory, setOperationHistory] = useState<{operation: string, timestamp: number, success: boolean}[]>([]);

  // Helper function to safely get workflow values
  const getWorkflowValue = (field: 'title' | 'description', isEditing = false): string => {
    const workflow = isEditing ? editingWorkflow : newWorkflow;
    if (!workflow) return '';
    return workflow[field] || '';
  };

  // Helper function to get template-based suggestions
  const getTemplateSuggestions = (templateId: string, type: 'triggers' | 'actions') => {
    const template = workflowTemplates.find(t => t.id === templateId);
    if (!template) return [];
    
    const suggestions = type === 'triggers' ? template.suggestedTriggers : template.suggestedActions;
    const availableItems = type === 'triggers' ? availableTriggers : availableActions;
    const currentItems = type === 'triggers' 
      ? (editingWorkflow ? editingWorkflow.triggers : newWorkflow.triggers)
      : (editingWorkflow ? editingWorkflow.actions : newWorkflow.actions);
    
    return suggestions
      ?.map(name => availableItems.find(item => item.name === name))
      .filter(item => item && !currentItems.includes(item.name)) || [];
  };

  // Accessibility helper functions
  const announceToScreenReader = (message: string) => {
    setAnnouncements(prev => [...prev, message]);
    // Clear announcement after a short delay
    setTimeout(() => {
      setAnnouncements(prev => prev.slice(1));
    }, 1000);
  };

  // Keyboard navigation for workflows
  const handleWorkflowKeyDown = (event: React.KeyboardEvent, workflowId: number) => {
    switch (event.key) {
      case 'ArrowUp':
      case 'ArrowDown':
        event.preventDefault();
        const workflowIds = workflows.map(w => w.id);
        const currentIndex = workflowIds.indexOf(workflowId);
        const nextIndex = event.key === 'ArrowDown' 
          ? (currentIndex + 1) % workflowIds.length
          : (currentIndex - 1 + workflowIds.length) % workflowIds.length;
        
        setFocusedWorkflow(workflowIds[nextIndex]);
        const nextWorkflow = workflows.find(w => w.id === workflowIds[nextIndex]);
        if (nextWorkflow) {
          announceToScreenReader(`Focused on ${nextWorkflow.title} workflow`);
        }
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        const workflow = workflows.find(w => w.id === workflowId);
        if (workflow) {
          setEditingWorkflow(workflow);
          setShowEditWorkflow(true);
          announceToScreenReader(`Opened ${workflow.title} for editing`);
        }
        break;
      case 'Delete':
      case 'Backspace':
        event.preventDefault();
        const workflowToDelete = workflows.find(w => w.id === workflowId);
        if (workflowToDelete) {
          deleteWorkflow(workflowId);
          announceToScreenReader(`Deleted ${workflowToDelete.title} workflow`);
        }
        break;
    }
  };

  // Enhanced error handling functions with user-friendly messages
  const handleError = (error: any, operation: string, showToUser = true) => {
    console.error(`Error in ${operation}:`, error);
    
    let errorMessage: string;
    let userFriendlyMessage: string;
    
    // Determine error type and create appropriate messages
    if (error instanceof Error) {
      errorMessage = error.message;
      
      // Create user-friendly messages based on error type
      if (error.message.includes('validation') || error.message.includes('invalid')) {
        userFriendlyMessage = 'Please check your input and fix any validation errors before continuing.';
      } else if (error.message.includes('duplicate') || error.message.includes('exists')) {
        userFriendlyMessage = 'A workflow with this name already exists. Please choose a different name.';
      } else if (error.message.includes('network') || error.message.includes('fetch')) {
        userFriendlyMessage = 'Network connection issue. Please check your internet connection and try again.';
        setNetworkError(userFriendlyMessage);
      } else if (error.message.includes('permission') || error.message.includes('access')) {
        userFriendlyMessage = 'You don\'t have permission to perform this action.';
      } else if (error.message.includes('storage') || error.message.includes('quota')) {
        userFriendlyMessage = 'Storage is full. Please free up some space and try again.';
      } else {
        userFriendlyMessage = `Workflow operation failed: ${error.message}`;
      }
    } else if (typeof error === 'string') {
      errorMessage = error;
      userFriendlyMessage = error;
    } else {
      errorMessage = `An unexpected error occurred during ${operation}`;
      userFriendlyMessage = 'Something went wrong. Please try again or contact support if the problem persists.';
    }
    
    // Log operation history
    setOperationHistory(prev => [...prev.slice(-9), {
      operation,
      timestamp: Date.now(),
      success: false
    }]);
    
    setLastError({
      message: errorMessage,
      timestamp: Date.now()
    });
    
    if (showToUser) {
      setOperationError(userFriendlyMessage);
      announceToScreenReader(`Error: ${userFriendlyMessage}`);
      
      // Auto-clear error after 8 seconds for user-friendly messages
      setTimeout(() => {
        setOperationError(null);
        setNetworkError(null);
      }, 8000);
    }
    
    return errorMessage;
  };

  // Retry mechanism for failed operations
  const withRetry = async <T>(
    operation: () => Promise<T>, 
    operationName: string, 
    maxRetries = 3
  ): Promise<T | null> => {
    let lastError: any = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        setRetryCount(attempt - 1);
        return await operation();
      } catch (error) {
        lastError = error;
        console.warn(`${operationName} attempt ${attempt} failed:`, error);
        
        if (attempt < maxRetries) {
          // Exponential backoff: wait 1s, 2s, 4s between retries
          const delay = Math.pow(2, attempt - 1) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // All retries failed
    handleError(lastError, operationName);
    setRetryCount(0);
    return null;
  };

  // Safe async operation wrapper
  const safeAsyncOperation = async (
    operation: () => Promise<void>,
    operationName: string,
    loadingMessage?: string
  ) => {
    try {
      setIsLoading(true);
      setIsSubmitting(true);
      setOperationInProgress(loadingMessage || operationName);
      setOperationError(null);
      
      await withRetry(operation, operationName);
      
    } catch (error) {
      handleError(error, operationName);
    } finally {
      setIsLoading(false);
      setIsSubmitting(false);
      setOperationInProgress(null);
    }
  };

  // Validation functions
  const validateField = (field: string, value: string | string[], isEditing = false): string | null => {
    
    switch (field) {
      case 'title':
        if (!value || (typeof value === 'string' && !value.trim())) {
          return 'Title is required';
        }
        if (typeof value === 'string' && value.trim().length < 3) {
          return 'Title must be at least 3 characters long';
        }
        if (typeof value === 'string' && value.trim().length > 100) {
          return 'Title must be less than 100 characters';
        }
        // Check for duplicate titles (excluding current workflow when editing)
        const existingWorkflow = workflows.find(w => 
          w.title.toLowerCase() === (value as string).trim().toLowerCase() && 
          (!isEditing || w.id !== editingWorkflow?.id)
        );
        if (existingWorkflow) {
          return 'A workflow with this title already exists';
        }
        return null;
      
      case 'description':
        if (!value || (typeof value === 'string' && !value.trim())) {
          return 'Description is required';
        }
        if (typeof value === 'string' && value.trim().length < 10) {
          return 'Description must be at least 10 characters long';
        }
        if (typeof value === 'string' && value.trim().length > 500) {
          return 'Description must be less than 500 characters';
        }
        return null;
      
      case 'triggers':
        // Triggers are optional, but if provided should be valid
        return null;
      
      case 'actions':
        // Actions are optional, but if provided should be valid
        return null;
      
      default:
        return null;
    }
  };

  const validateCurrentStep = (step: number, isEditing = false): boolean => {
    const errors: {[key: string]: string} = {};
    
    // Check if we have a valid workflow
    if (!getWorkflowValue('title', isEditing) && !getWorkflowValue('description', isEditing)) return false;

    if (step === 1 || isEditing) {
      const titleError = validateField('title', getWorkflowValue('title', isEditing), isEditing);
      const descriptionError = validateField('description', getWorkflowValue('description', isEditing), isEditing);
      
      if (titleError) errors.title = titleError;
      if (descriptionError) errors.description = descriptionError;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const isFormComplete = (isEditing = false): boolean => {
    return getWorkflowValue('title', isEditing).trim().length > 0 && 
           getWorkflowValue('description', isEditing).trim().length > 0 &&
           validateCurrentStep(isEditing ? 1 : workflowStep, isEditing);
  };

  const updateWorkflow = async () => {
    if (!editingWorkflow) {
      handleError(new Error('No workflow selected for editing'), 'update workflow');
      return;
    }
    
    const workflowId = editingWorkflow.id;
    
    try {
      setIsSubmitting(true);
      setSaveInProgress(prev => ({ ...prev, [workflowId]: true }));
      setOperationError(null);
      setCriticalError(null);
      
      // Comprehensive validation
      if (!validateCurrentStep(1, true)) {
        throw new Error('Validation failed: Please fix all errors before saving');
      }

      // Validate workflow data integrity
      if (!editingWorkflow.title?.trim()) {
        throw new Error('Workflow title is required');
      }
      
      if (!editingWorkflow.description?.trim()) {
        throw new Error('Workflow description is required');
      }
      
      if (editingWorkflow.title.trim().length < 3) {
        throw new Error('Workflow title must be at least 3 characters long');
      }
      
      if (editingWorkflow.description.trim().length < 10) {
        throw new Error('Workflow description must be at least 10 characters long');
      }

      // Check for duplicate titles (excluding current workflow)
      const duplicateWorkflow = workflows.find(w => 
        w.id !== workflowId && 
        w.title.toLowerCase().trim() === editingWorkflow.title.toLowerCase().trim()
      );
      
      if (duplicateWorkflow) {
        throw new Error(`A workflow named "${editingWorkflow.title}" already exists`);
      }

      // Simulate async operation with potential failure
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          // Simulate occasional network failures for testing
          if (Math.random() < 0.1) {
            reject(new Error('Network timeout: Unable to save workflow'));
          } else {
            resolve(undefined);
          }
        }, 500);
      });

      // Update workflow with validation
      const updatedWorkflow = {
        ...editingWorkflow,
        title: editingWorkflow.title.trim(),
        description: editingWorkflow.description.trim(),
        triggers: editingWorkflow.triggers || [],
        actions: editingWorkflow.actions || []
      };

      setWorkflows(prev => prev.map(workflow => 
        workflow.id === workflowId ? updatedWorkflow : workflow
      ));
      
      // Log successful operation
      setOperationHistory(prev => [...prev.slice(-9), {
        operation: `update workflow "${updatedWorkflow.title}"`,
        timestamp: Date.now(),
        success: true
      }]);
      
      // Reset form state
      setShowEditWorkflow(false);
      setEditingWorkflow(null);
      setWorkflowStep(1);
      setValidationErrors({});
      setFieldTouched({});
      setOperationError(null);
      
      announceToScreenReader(`Workflow "${updatedWorkflow.title}" updated successfully`);
      
    } catch (error) {
      handleError(error, 'update workflow');
      
      // Don't close the modal on error, let user fix issues
      announceToScreenReader('Failed to update workflow. Please check the errors and try again.');
      
    } finally {
      setIsSubmitting(false);
      setSaveInProgress(prev => {
        const newState = { ...prev };
        delete newState[workflowId];
        return newState;
      });
    }
  };

  const workflowTemplates = [
    { 
      id: 'document', 
      name: 'Document Processing', 
      description: 'Process uploaded documents automatically with AI analysis',
      category: 'Content Management',
      icon: '📄',
      complexity: 'Beginner',
      estimatedTime: '5-10 minutes',
      defaultTriggers: ['Document Upload', 'File Change'],
      defaultActions: ['Extract Text', 'Analyze Content', 'Generate Summary'],
      suggestedTriggers: ['API Call', 'Webhook', 'Time-based'],
      suggestedActions: ['Validate Input', 'Transform Data', 'Send Notification'],
      useCase: 'Automatically process and analyze documents when they are uploaded or modified',
      benefits: ['Saves manual processing time', 'Consistent analysis quality', 'Immediate processing']
    },
    { 
      id: 'research', 
      name: 'Research Assistant', 
      description: 'Automated research and analysis pipeline for academic work',
      category: 'Research & Analysis',
      icon: '🔬',
      complexity: 'Intermediate',
      estimatedTime: '10-15 minutes',
      defaultTriggers: ['Manual Trigger', 'Scheduled'],
      defaultActions: ['Search Papers', 'Extract Insights', 'Generate Report'],
      suggestedTriggers: ['Data Update', 'Email Received'],
      suggestedActions: ['Save to Database', 'Send Report', 'Generate Charts'],
      useCase: 'Conduct automated research and generate comprehensive analysis reports',
      benefits: ['Accelerates research process', 'Comprehensive analysis', 'Regular updates']
    },
    { 
      id: 'support', 
      name: 'Customer Support', 
      description: 'AI-powered support ticket handling and response system',
      category: 'Customer Service',
      icon: '🎧',
      complexity: 'Advanced',
      estimatedTime: '15-20 minutes',
      defaultTriggers: ['New Ticket', 'Email Received'],
      defaultActions: ['Categorize Issue', 'Generate Response', 'Route to Agent'],
      suggestedTriggers: ['API Call', 'Webhook'],
      suggestedActions: ['Send Notification', 'Save to Database', 'Generate Report'],
      useCase: 'Automatically handle customer support tickets with AI-powered responses',
      benefits: ['24/7 support availability', 'Consistent response quality', 'Reduced response time']
    },
    { 
      id: 'analytics', 
      name: 'Analytics Report', 
      description: 'Automated analytics and reporting with data visualization',
      category: 'Business Intelligence',
      icon: '📊',
      complexity: 'Intermediate',
      estimatedTime: '10-15 minutes',
      defaultTriggers: ['Daily Schedule', 'Data Update'],
      defaultActions: ['Collect Metrics', 'Generate Charts', 'Send Report'],
      suggestedTriggers: ['Time-based', 'API Call'],
      suggestedActions: ['Transform Data', 'Save to Database', 'Send Notification'],
      useCase: 'Generate automated analytics reports with data visualization',
      benefits: ['Regular insights delivery', 'Data-driven decisions', 'Time-saving automation']
    },
    { 
      id: 'content-moderation', 
      name: 'Content Moderation', 
      description: 'Automated content review and moderation system',
      category: 'Content Management',
      icon: '🛡️',
      complexity: 'Advanced',
      estimatedTime: '15-20 minutes',
      defaultTriggers: ['Document Upload', 'API Call'],
      defaultActions: ['Analyze Content', 'Categorize Issue', 'Send Notification'],
      suggestedTriggers: ['Webhook', 'Manual Trigger'],
      suggestedActions: ['Generate Response', 'Save to Database', 'Route to Agent'],
      useCase: 'Automatically review and moderate content for compliance and quality',
      benefits: ['Consistent moderation standards', 'Faster content review', 'Reduced manual effort']
    },
    { 
      id: 'data-pipeline', 
      name: 'Data Processing Pipeline', 
      description: 'Automated data ingestion, transformation, and storage workflow',
      category: 'Data Management',
      icon: '🔄',
      complexity: 'Advanced',
      estimatedTime: '20-25 minutes',
      defaultTriggers: ['Data Update', 'Scheduled'],
      defaultActions: ['Transform Data', 'Validate Input', 'Save to Database'],
      suggestedTriggers: ['API Call', 'File Change'],
      suggestedActions: ['Generate Report', 'Send Notification', 'Generate Charts'],
      useCase: 'Process and transform data automatically with validation and storage',
      benefits: ['Data quality assurance', 'Automated processing', 'Scalable data handling']
    },
    { 
      id: 'notification-system', 
      name: 'Smart Notification System', 
      description: 'Intelligent notification and alert management workflow',
      category: 'Communication',
      icon: '🔔',
      complexity: 'Beginner',
      estimatedTime: '5-10 minutes',
      defaultTriggers: ['Manual Trigger', 'Time-based'],
      defaultActions: ['Send Notification', 'Generate Response'],
      suggestedTriggers: ['Data Update', 'API Call'],
      suggestedActions: ['Save to Database', 'Route to Agent', 'Generate Report'],
      useCase: 'Send intelligent notifications based on various triggers and conditions',
      benefits: ['Timely alerts', 'Reduced notification fatigue', 'Contextual messaging']
    },
    { 
      id: 'custom', 
      name: 'Custom Workflow', 
      description: 'Build your own workflow from scratch with full customization',
      category: 'Custom',
      icon: '⚙️',
      complexity: 'Expert',
      estimatedTime: '20+ minutes',
      defaultTriggers: [],
      defaultActions: [],
      suggestedTriggers: [],
      suggestedActions: [],
      useCase: 'Create a completely custom workflow tailored to your specific needs',
      benefits: ['Full customization', 'Unlimited flexibility', 'Unique solutions']
    }
  ];

  const availableTriggers = [
    { id: 'manual', name: 'Manual Trigger', category: 'manual', color: '#8b5cf6', description: 'Manually triggered by user action' },
    { id: 'schedule', name: 'Scheduled', category: 'scheduled', color: '#06b6d4', description: 'Runs on a predefined schedule' },
    { id: 'document-upload', name: 'Document Upload', category: 'event', color: '#10b981', description: 'Triggered when documents are uploaded' },
    { id: 'file-change', name: 'File Change', category: 'event', color: '#10b981', description: 'Triggered when files are modified' },
    { id: 'email-received', name: 'Email Received', category: 'event', color: '#10b981', description: 'Triggered by incoming emails' },
    { id: 'new-ticket', name: 'New Ticket', category: 'event', color: '#10b981', description: 'Triggered when support tickets are created' },
    { id: 'data-update', name: 'Data Update', category: 'event', color: '#10b981', description: 'Triggered when data changes occur' },
    { id: 'api-call', name: 'API Call', category: 'api', color: '#f59e0b', description: 'Triggered by external API calls' },
    { id: 'webhook', name: 'Webhook', category: 'api', color: '#f59e0b', description: 'Triggered by webhook notifications' },
    { id: 'time-based', name: 'Time-based', category: 'scheduled', color: '#06b6d4', description: 'Triggered at specific times' }
  ];

  const availableActions = [
    { id: 'extract-text', name: 'Extract Text', category: 'processing', color: '#8b5cf6', description: 'Extract text content from documents' },
    { id: 'analyze-content', name: 'Analyze Content', category: 'analysis', color: '#06b6d4', description: 'Perform content analysis and insights' },
    { id: 'generate-summary', name: 'Generate Summary', category: 'processing', color: '#8b5cf6', description: 'Create automated summaries' },
    { id: 'search-papers', name: 'Search Papers', category: 'analysis', color: '#06b6d4', description: 'Search academic papers and research' },
    { id: 'extract-insights', name: 'Extract Insights', category: 'analysis', color: '#06b6d4', description: 'Extract key insights from data' },
    { id: 'generate-report', name: 'Generate Report', category: 'processing', color: '#8b5cf6', description: 'Generate comprehensive reports' },
    { id: 'categorize-issue', name: 'Categorize Issue', category: 'processing', color: '#8b5cf6', description: 'Automatically categorize issues' },
    { id: 'generate-response', name: 'Generate Response', category: 'communication', color: '#10b981', description: 'Generate automated responses' },
    { id: 'route-to-agent', name: 'Route to Agent', category: 'communication', color: '#10b981', description: 'Route to appropriate team member' },
    { id: 'collect-metrics', name: 'Collect Metrics', category: 'storage', color: '#f59e0b', description: 'Collect and store performance metrics' },
    { id: 'generate-charts', name: 'Generate Charts', category: 'processing', color: '#8b5cf6', description: 'Create data visualizations' },
    { id: 'send-report', name: 'Send Report', category: 'communication', color: '#10b981', description: 'Send reports to stakeholders' },
    { id: 'send-notification', name: 'Send Notification', category: 'communication', color: '#10b981', description: 'Send notifications and alerts' },
    { id: 'save-to-database', name: 'Save to Database', category: 'storage', color: '#f59e0b', description: 'Store data in database' },
    { id: 'transform-data', name: 'Transform Data', category: 'processing', color: '#8b5cf6', description: 'Transform and format data' },
    { id: 'validate-input', name: 'Validate Input', category: 'processing', color: '#8b5cf6', description: 'Validate input data and formats' }
  ];

  const createNewWorkflow = async () => {
    try {
      setIsSubmitting(true);
      setOperationError(null);
      setCriticalError(null);
      
      // Comprehensive validation
      if (!validateCurrentStep(3, false)) {
        throw new Error('Validation failed: Please complete all required fields and fix any errors');
      }

      // Validate workflow data
      if (!newWorkflow.title?.trim()) {
        throw new Error('Workflow title is required');
      }
      
      if (!newWorkflow.description?.trim()) {
        throw new Error('Workflow description is required');
      }
      
      if (newWorkflow.title.trim().length < 3) {
        throw new Error('Workflow title must be at least 3 characters long');
      }
      
      if (newWorkflow.description.trim().length < 10) {
        throw new Error('Workflow description must be at least 10 characters long');
      }

      // Check for duplicate titles
      const duplicateWorkflow = workflows.find(w => 
        w.title.toLowerCase().trim() === newWorkflow.title.toLowerCase().trim()
      );
      
      if (duplicateWorkflow) {
        throw new Error(`A workflow named "${newWorkflow.title}" already exists`);
      }

      // Validate triggers and actions arrays
      if (!Array.isArray(newWorkflow.triggers)) {
        throw new Error('Invalid triggers data');
      }
      
      if (!Array.isArray(newWorkflow.actions)) {
        throw new Error('Invalid actions data');
      }

      // Simulate async operation with potential failure
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          // Simulate occasional failures for testing
          if (Math.random() < 0.1) {
            reject(new Error('Network timeout: Unable to create workflow'));
          } else {
            resolve(undefined);
          }
        }, 500);
      });

      // Create workflow with validated data
      const workflow: Workflow = {
        id: Date.now(),
        title: newWorkflow.title.trim(),
        description: newWorkflow.description.trim(),
        status: newWorkflow.enabled ? 'Active' : 'Draft',
        color: '#60a5fa',
        lastRun: 'Never',
        triggers: newWorkflow.triggers.length > 0 ? [...newWorkflow.triggers] : ['Manual Trigger'],
        actions: newWorkflow.actions.length > 0 ? [...newWorkflow.actions] : ['Custom Action'],
        executions: 0,
        successRate: 0
      };

      // Validate the created workflow object
      if (!workflow.title || !workflow.description) {
        throw new Error('Failed to create valid workflow object');
      }

      setWorkflows(prev => [workflow, ...prev]);
      
      // Log successful operation
      setOperationHistory(prev => [...prev.slice(-9), {
        operation: `create workflow "${workflow.title}"`,
        timestamp: Date.now(),
        success: true
      }]);
      
      // Reset form state
      setShowCreateWorkflow(false);
      setNewWorkflow({ 
        title: '', 
        description: '', 
        template: 'custom',
        triggers: [],
        actions: [],
        schedule: 'manual',
        enabled: false
      });
      setWorkflowStep(1);
      setValidationErrors({});
      setFieldTouched({});
      setOperationError(null);
      setDuplicateAttempts({});
      
      announceToScreenReader(`Workflow "${workflow.title}" created successfully`);
      
    } catch (error) {
      handleError(error, 'create workflow');
      
      // Don't close the modal on error, let user fix issues
      announceToScreenReader('Failed to create workflow. Please check the errors and try again.');
      
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleWorkflowStatus = (id: number) => {
    try {
      const workflow = workflows.find(w => w.id === id);
      if (!workflow) {
        throw new Error(`Workflow with ID ${id} not found`);
      }
      
      const newStatus = workflow.status === 'Active' ? 'Inactive' : 'Active';
      
      setWorkflows(prev => prev.map(w => {
        if (w.id === id) {
          return { ...w, status: newStatus };
        }
        return w;
      }));
      
      // Log operation
      setOperationHistory(prev => [...prev.slice(-9), {
        operation: `toggle workflow "${workflow.title}" to ${newStatus}`,
        timestamp: Date.now(),
        success: true
      }]);
      
      announceToScreenReader(`Workflow "${workflow.title}" ${newStatus === 'Active' ? 'activated' : 'deactivated'}`);
      
    } catch (error) {
      handleError(error, 'toggle workflow status');
    }
  };

  const deleteWorkflow = (id: number) => {
    try {
      const workflow = workflows.find(w => w.id === id);
      if (!workflow) {
        throw new Error(`Workflow with ID ${id} not found`);
      }
      
      // Confirm deletion for active workflows
      if (workflow.status === 'Active') {
        const confirmed = window.confirm(
          `"${workflow.title}" is currently active. Are you sure you want to delete it? This action cannot be undone.`
        );
        if (!confirmed) {
          return;
        }
      } else {
        const confirmed = window.confirm(
          `Are you sure you want to delete "${workflow.title}"? This action cannot be undone.`
        );
        if (!confirmed) {
          return;
        }
      }
      
      setWorkflows(prev => prev.filter(w => w.id !== id));
      
      // Log operation
      setOperationHistory(prev => [...prev.slice(-9), {
        operation: `delete workflow "${workflow.title}"`,
        timestamp: Date.now(),
        success: true
      }]);
      
      announceToScreenReader(`Workflow "${workflow.title}" deleted successfully`);
      
    } catch (error) {
      handleError(error, 'delete workflow');
    }
  };

  const addTrigger = (triggerId: string) => {
    const trigger = availableTriggers.find(t => t.id === triggerId);
    if (!trigger) return;

    const currentTriggers = editingWorkflow ? editingWorkflow.triggers : newWorkflow.triggers;
    
    if (currentTriggers.includes(trigger.name)) {
      // Handle duplicate attempt with visual feedback
      const attemptKey = `trigger-${triggerId}`;
      setDuplicateAttempts(prev => ({
        ...prev,
        [attemptKey]: (prev[attemptKey] || 0) + 1
      }));
      
      // Add shake animation to the duplicate trigger
      const triggerElement = document.querySelector(`[data-trigger-id="${triggerId}"]`);
      if (triggerElement) {
        triggerElement.classList.add('validation-error');
        setTimeout(() => {
          triggerElement.classList.remove('validation-error');
        }, 500);
      }
      return;
    }

    if (editingWorkflow) {
      setEditingWorkflow(prev => prev ? {
        ...prev,
        triggers: [...prev.triggers, trigger.name]
      } : null);
    } else {
      setNewWorkflow(prev => ({
        ...prev,
        triggers: [...prev.triggers, trigger.name]
      }));
    }
  };

  const removeTrigger = (triggerName: string) => {
    if (editingWorkflow) {
      setEditingWorkflow(prev => prev ? {
        ...prev,
        triggers: prev.triggers.filter(t => t !== triggerName)
      } : null);
    } else {
      setNewWorkflow(prev => ({
        ...prev,
        triggers: prev.triggers.filter(t => t !== triggerName)
      }));
    }
  };

  const addAction = (actionId: string) => {
    const action = availableActions.find(a => a.id === actionId);
    if (!action) return;

    const currentActions = editingWorkflow ? editingWorkflow.actions : newWorkflow.actions;
    
    if (currentActions.includes(action.name)) {
      // Handle duplicate attempt with visual feedback
      const attemptKey = `action-${actionId}`;
      setDuplicateAttempts(prev => ({
        ...prev,
        [attemptKey]: (prev[attemptKey] || 0) + 1
      }));
      
      // Add shake animation to the duplicate action
      const actionElement = document.querySelector(`[data-action-id="${actionId}"]`);
      if (actionElement) {
        actionElement.classList.add('validation-error');
        setTimeout(() => {
          actionElement.classList.remove('validation-error');
        }, 500);
      }
      return;
    }

    if (editingWorkflow) {
      setEditingWorkflow(prev => prev ? {
        ...prev,
        actions: [...prev.actions, action.name]
      } : null);
    } else {
      setNewWorkflow(prev => ({
        ...prev,
        actions: [...prev.actions, action.name]
      }));
    }
  };

  const removeAction = (actionName: string) => {
    if (editingWorkflow) {
      setEditingWorkflow(prev => prev ? {
        ...prev,
        actions: prev.actions.filter(a => a !== actionName)
      } : null);
    } else {
      setNewWorkflow(prev => ({
        ...prev,
        actions: prev.actions.filter(a => a !== actionName)
      }));
    }
  };

  // Helper function to get category color for better visual organization
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'manual': return '#8b5cf6';
      case 'scheduled': return '#06b6d4';
      case 'event': return '#10b981';
      case 'api': return '#f59e0b';
      case 'processing': return '#8b5cf6';
      case 'analysis': return '#06b6d4';
      case 'communication': return '#10b981';
      case 'storage': return '#f59e0b';
      default: return '#9ca3af';
    }
  };

  const getStatusIcon = (status: Workflow['status']) => {
    switch (status) {
      case 'Active':
        return <CheckCircle size={16} style={{ color: '#10b981' }} />;
      case 'Draft':
        return <Edit size={16} style={{ color: '#f59e0b' }} />;
      case 'Inactive':
        return <Pause size={16} style={{ color: '#9ca3af' }} />;
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { name: 'Basic Info', description: 'Title, description & template' },
      { name: 'Triggers', description: 'When to run the workflow' },
      { name: 'Actions & Settings', description: 'What the workflow does' }
    ];
    
    return (
      <div style={{
        background: 'rgba(255,255,255,0.03)',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '24px',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          {steps.map((step, index) => (
            <React.Fragment key={index}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                flex: 1
              }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: index + 1 <= workflowStep 
                    ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
                    : 'rgba(255,255,255,0.1)',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  fontWeight: '600',
                  border: index + 1 === workflowStep ? '2px solid #8b5cf6' : '2px solid transparent',
                  transition: 'all 0.3s ease'
                }}>
                  {index + 1 < workflowStep ? '✓' : index + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    color: index + 1 <= workflowStep ? 'white' : '#9ca3af',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '2px'
                  }}>
                    {step.name}
                  </div>
                  <div style={{
                    color: '#6b7280',
                    fontSize: '12px',
                    lineHeight: '1.3'
                  }}>
                    {step.description}
                  </div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div style={{
                  width: '40px',
                  height: '2px',
                  background: index + 1 < workflowStep 
                    ? 'linear-gradient(90deg, #8b5cf6 0%, #7c3aed 100%)'
                    : 'rgba(255,255,255,0.2)',
                  margin: '0 16px',
                  borderRadius: '1px',
                  transition: 'all 0.3s ease'
                }} />
              )}
            </React.Fragment>
          ))}
        </div>
        
        {/* Progress Bar */}
        <div style={{
          width: '100%',
          height: '4px',
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '2px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${(workflowStep / steps.length) * 100}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #8b5cf6 0%, #7c3aed 100%)',
            borderRadius: '2px',
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>
    );
  };

  const renderBasicInfoStep = () => {
    const currentWorkflow = editingWorkflow || newWorkflow;
    const isEditing = !!editingWorkflow;

    const handleTemplateSelection = (templateId: string) => {
      const template = workflowTemplates.find(t => t.id === templateId);
      if (template && template.id !== 'custom') {
        setNewWorkflow(prev => ({
          ...prev,
          template: templateId,
          title: template.name,
          description: template.description,
          triggers: [...template.defaultTriggers],
          actions: [...template.defaultActions]
        }));
      } else {
        setNewWorkflow(prev => ({
          ...prev,
          template: templateId,
          title: '',
          description: '',
          triggers: [],
          actions: []
        }));
      }
    };

    return (
      <>
        {!isEditing && (
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '12px', 
              fontSize: '16px', 
              color: 'white',
              fontWeight: '600'
            }}>
              Choose a Template
            </label>
            <div style={{
              fontSize: '13px',
              color: '#9ca3af',
              marginBottom: '16px',
              lineHeight: '1.4'
            }}>
              Templates provide pre-configured workflows with recommended triggers and actions. 
              You can customize them after selection or start from scratch with a custom workflow.
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '12px'
            }}>
              {workflowTemplates.map(template => {
                const isSelected = newWorkflow.template === template.id;
                const complexityColor = {
                  'Beginner': '#10b981',
                  'Intermediate': '#f59e0b', 
                  'Advanced': '#ef4444',
                  'Expert': '#8b5cf6'
                }[template.complexity] || '#9ca3af';
                
                return (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelection(template.id)}
                    style={{
                      padding: '20px',
                      background: isSelected 
                        ? 'linear-gradient(135deg, #8b5cf6 20%, #7c3aed 100%)'
                        : 'rgba(255,255,255,0.05)',
                      border: `2px solid ${isSelected ? '#8b5cf6' : 'rgba(255,255,255,0.1)'}`,
                      borderRadius: '16px',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '14px',
                      textAlign: 'left',
                      transition: 'all 0.3s ease',
                      position: 'relative',
                      minHeight: '200px',
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'rgba(139, 92, 246, 0.1)';
                        e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                        e.currentTarget.style.transform = 'translateY(-4px)';
                        e.currentTarget.style.boxShadow = '0 8px 25px rgba(139, 92, 246, 0.15)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                      }
                    }}
                  >
                    {/* Header with icon and title */}
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '12px',
                      marginBottom: '12px'
                    }}>
                      <div style={{
                        fontSize: '24px',
                        lineHeight: '1'
                      }}>
                        {template.icon}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          fontWeight: '600', 
                          fontSize: '16px',
                          marginBottom: '4px'
                        }}>
                          {template.name}
                        </div>
                        <div style={{
                          fontSize: '11px',
                          color: isSelected ? 'rgba(255,255,255,0.7)' : '#9ca3af',
                          textTransform: 'uppercase',
                          fontWeight: '600',
                          letterSpacing: '0.5px'
                        }}>
                          {template.category}
                        </div>
                      </div>
                      {isSelected && (
                        <div style={{
                          padding: '4px 8px',
                          background: 'rgba(255,255,255,0.2)',
                          borderRadius: '12px',
                          fontSize: '10px',
                          fontWeight: '700',
                          color: 'white',
                          letterSpacing: '0.5px'
                        }}>
                          ✓ SELECTED
                        </div>
                      )}
                    </div>

                    {/* Description */}
                    <div style={{ 
                      fontSize: '13px', 
                      color: isSelected ? 'rgba(255,255,255,0.9)' : '#d1d5db',
                      lineHeight: '1.5',
                      marginBottom: '16px',
                      flex: 1
                    }}>
                      {template.description}
                    </div>

                    {/* Metadata */}
                    <div style={{
                      display: 'flex',
                      gap: '12px',
                      marginBottom: '12px',
                      flexWrap: 'wrap'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                        color: isSelected ? 'rgba(255,255,255,0.8)' : '#9ca3af'
                      }}>
                        <div style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          background: complexityColor
                        }} />
                        {template.complexity}
                      </div>
                      <div style={{
                        fontSize: '11px',
                        color: isSelected ? 'rgba(255,255,255,0.8)' : '#9ca3af'
                      }}>
                        ⏱️ {template.estimatedTime}
                      </div>
                    </div>

                    {/* Included components */}
                    {template.defaultTriggers && template.defaultTriggers.length > 0 && (
                      <div style={{ 
                        fontSize: '11px',
                        color: isSelected ? 'rgba(255,255,255,0.7)' : '#9ca3af',
                        marginBottom: '8px'
                      }}>
                        <strong>Includes:</strong> {template.defaultTriggers.slice(0, 2).join(', ')}
                        {template.defaultTriggers.length > 2 && ` +${template.defaultTriggers.length - 2} more`}
                      </div>
                    )}

                    {/* Benefits preview */}
                    {template.benefits && template.benefits.length > 0 && (
                      <div style={{ 
                        fontSize: '10px',
                        color: isSelected ? 'rgba(255,255,255,0.6)' : '#6b7280',
                        fontStyle: 'italic'
                      }}>
                        💡 {template.benefits[0]}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontSize: '14px', 
            color: '#9ca3af',
            fontWeight: '500'
          }}>
            Workflow Title *
          </label>
          <input
            type="text"
            value={getWorkflowValue('title', isEditing)}
            onChange={(e) => {
              const value = e.target.value;
              if (isEditing) {
                setEditingWorkflow(prev => prev ? { ...prev, title: value } : null);
              } else {
                setNewWorkflow(prev => ({ ...prev, title: value }));
              }
              
              // Real-time validation
              setFieldTouched(prev => ({ ...prev, title: true }));
              const error = validateField('title', value, isEditing);
              setValidationErrors(prev => ({
                ...prev,
                title: error || ''
              }));
            }}
            onBlur={() => {
              setFieldTouched(prev => ({ ...prev, title: true }));
              const error = validateField('title', getWorkflowValue('title', isEditing), isEditing);
              setValidationErrors(prev => ({
                ...prev,
                title: error || ''
              }));
            }}
            placeholder="Enter a descriptive title for your workflow..."
            className={validationErrors.title && fieldTouched.title ? 'validation-error' : 
                      (getWorkflowValue('title', isEditing).trim() && !validationErrors.title ? 'validation-success' : '')}
            style={{
              width: '100%',
              padding: '12px',
              background: 'rgba(255,255,255,0.1)',
              border: `2px solid ${
                validationErrors.title && fieldTouched.title ? '#ef4444' :
                getWorkflowValue('title', isEditing).trim() && !validationErrors.title ? '#10b981' :
                getWorkflowValue('title', isEditing).trim() ? '#8b5cf6' : 'rgba(255,255,255,0.2)'
              }`,
              borderRadius: '8px',
              color: 'white',
              fontSize: '14px',
              outline: 'none',
              transition: 'border-color 0.2s ease'
            }}
          />
          {validationErrors.title && fieldTouched.title && (
            <div style={{
              fontSize: '12px',
              color: '#ef4444',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              ⚠️ {validationErrors.title}
            </div>
          )}
          {getWorkflowValue('title', isEditing).trim() && !validationErrors.title && fieldTouched.title && (
            <div style={{
              fontSize: '12px',
              color: '#10b981',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              ✓ Title looks good
            </div>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '8px', 
            fontSize: '14px', 
            color: '#9ca3af',
            fontWeight: '500'
          }}>
            Description *
          </label>
          <textarea
            value={getWorkflowValue('description', isEditing)}
            onChange={(e) => {
              const value = e.target.value;
              if (isEditing) {
                setEditingWorkflow(prev => prev ? { ...prev, description: value } : null);
              } else {
                setNewWorkflow(prev => ({ ...prev, description: value }));
              }
              
              // Real-time validation
              setFieldTouched(prev => ({ ...prev, description: true }));
              const error = validateField('description', value, isEditing);
              setValidationErrors(prev => ({
                ...prev,
                description: error || ''
              }));
            }}
            onBlur={() => {
              setFieldTouched(prev => ({ ...prev, description: true }));
              const error = validateField('description', getWorkflowValue('description', isEditing), isEditing);
              setValidationErrors(prev => ({
                ...prev,
                description: error || ''
              }));
            }}
            placeholder="Describe what this workflow does and when it should be used..."
            rows={3}
            className={validationErrors.description && fieldTouched.description ? 'validation-error' : 
                      (getWorkflowValue('description', isEditing).trim() && !validationErrors.description ? 'validation-success' : '')}
            style={{
              width: '100%',
              padding: '12px',
              background: 'rgba(255,255,255,0.1)',
              border: `2px solid ${
                validationErrors.description && fieldTouched.description ? '#ef4444' :
                getWorkflowValue('description', isEditing).trim() && !validationErrors.description ? '#10b981' :
                getWorkflowValue('description', isEditing).trim() ? '#8b5cf6' : 'rgba(255,255,255,0.2)'
              }`,
              borderRadius: '8px',
              color: 'white',
              fontSize: '14px',
              resize: 'vertical',
              outline: 'none',
              fontFamily: 'inherit',
              transition: 'border-color 0.2s ease'
            }}
          />
          {validationErrors.description && fieldTouched.description && (
            <div style={{
              fontSize: '12px',
              color: '#ef4444',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              ⚠️ {validationErrors.description}
            </div>
          )}
          {getWorkflowValue('description', isEditing).trim() && !validationErrors.description && fieldTouched.description && (
            <div style={{
              fontSize: '12px',
              color: '#10b981',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              ✓ Description looks good ({getWorkflowValue('description', isEditing).trim().length} characters)
            </div>
          )}
        </div>

        {isEditing && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontSize: '14px', 
              color: '#9ca3af',
              fontWeight: '500'
            }}>
              Status
            </label>
            <select
              value={editingWorkflow?.status}
              onChange={(e) => setEditingWorkflow(prev => prev ? { ...prev, status: e.target.value as Workflow['status'] } : null)}
              style={{
                width: '100%',
                padding: '12px',
                background: 'rgba(255,255,255,0.1)',
                border: '2px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: 'white',
                fontSize: '14px',
                outline: 'none'
              }}
            >
              <option value="Active" style={{ background: '#1a1a2e' }}>Active</option>
              <option value="Draft" style={{ background: '#1a1a2e' }}>Draft</option>
              <option value="Inactive" style={{ background: '#1a1a2e' }}>Inactive</option>
            </select>
          </div>
        )}

        {/* Step Summary */}
        <div style={{
          background: 'rgba(139, 92, 246, 0.1)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '8px',
          padding: '12px',
          marginTop: '16px'
        }}>
          <div style={{ 
            fontSize: '12px', 
            color: '#c4b5fd', 
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            STEP 1 SUMMARY
          </div>
          <div style={{ fontSize: '14px', color: 'white' }}>
            {currentWorkflow.title.trim() || 'Untitled Workflow'} - {currentWorkflow.description.trim() || 'No description'}
          </div>
          {!isEditing && newWorkflow.template !== 'custom' && (
            (() => {
              const selectedTemplate = workflowTemplates.find(t => t.id === newWorkflow.template);
              if (!selectedTemplate) return null;
              
              return (
                <div style={{
                  marginTop: '16px',
                  padding: '16px',
                  background: 'rgba(139, 92, 246, 0.1)',
                  border: '1px solid rgba(139, 92, 246, 0.2)',
                  borderRadius: '12px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px'
                  }}>
                    <div style={{ fontSize: '16px' }}>{selectedTemplate.icon}</div>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#c4b5fd'
                    }}>
                      Using {selectedTemplate.name} Template
                    </div>
                  </div>
                  
                  <div style={{
                    fontSize: '12px',
                    color: '#d1d5db',
                    marginBottom: '12px',
                    lineHeight: '1.4'
                  }}>
                    <strong>Use Case:</strong> {selectedTemplate.useCase}
                  </div>
                  
                  {selectedTemplate.benefits && selectedTemplate.benefits.length > 0 && (
                    <div style={{
                      fontSize: '11px',
                      color: '#9ca3af'
                    }}>
                      <strong>Key Benefits:</strong>
                      <ul style={{
                        margin: '4px 0 0 16px',
                        padding: 0,
                        listStyle: 'disc'
                      }}>
                        {selectedTemplate.benefits.slice(0, 3).map((benefit, index) => (
                          <li key={index} style={{ marginBottom: '2px' }}>{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })()
          )}
        </div>
      </>
    );
  };

  const renderTriggersStep = () => {
    const currentTriggers = editingWorkflow ? editingWorkflow.triggers : newWorkflow.triggers;

    return (
      <>
        <div style={{ marginBottom: '24px' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '12px'
          }}>
            <label style={{ 
              fontSize: '16px', 
              color: 'white',
              fontWeight: '600'
            }}>
              Selected Triggers
            </label>
            <div style={{
              padding: '2px 8px',
              background: currentTriggers.length > 0 ? '#10b981' : '#6b7280',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: '600',
              color: 'white'
            }}>
              {currentTriggers.length} selected
            </div>
          </div>
          
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginBottom: '16px',
            minHeight: '60px',
            padding: '16px',
            background: 'rgba(255,255,255,0.05)',
            border: `2px solid ${currentTriggers.length > 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: '12px',
            transition: 'border-color 0.2s ease'
          }}>
            {currentTriggers.length === 0 ? (
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '100%',
                color: '#6b7280', 
                fontSize: '14px',
                fontStyle: 'italic'
              }}>
                Select triggers from the options below to define when your workflow runs
              </div>
            ) : (
              currentTriggers.map((trigger, index) => {
                const triggerData = availableTriggers.find(t => t.name === trigger);
                const categoryColor = triggerData ? getCategoryColor(triggerData.category) : '#8b5cf6';
                return (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 14px',
                      background: `linear-gradient(135deg, ${categoryColor}90 0%, ${categoryColor}70 100%)`,
                      border: `1px solid ${categoryColor}60`,
                      borderRadius: '24px',
                      fontSize: '13px',
                      color: 'white',
                      fontWeight: '500',
                      transition: 'all 0.2s ease',
                      animation: 'slideIn 0.3s ease'
                    }}
                  >
                    <span style={{
                      fontSize: '10px',
                      padding: '3px 7px',
                      background: 'rgba(255,255,255,0.25)',
                      borderRadius: '10px',
                      textTransform: 'uppercase',
                      fontWeight: '700',
                      letterSpacing: '0.5px'
                    }}>
                      {triggerData?.category || 'trigger'}
                    </span>
                    <span style={{ fontWeight: '600' }}>{trigger}</span>
                    <button
                      onClick={() => removeTrigger(trigger)}
                      style={{
                        background: 'rgba(255,255,255,0.2)',
                        border: 'none',
                        color: 'white',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        borderRadius: '50%',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.4)';
                        e.currentTarget.style.transform = 'scale(1.1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
                        e.currentTarget.style.transform = 'scale(1)';
                      }}
                    >
                      <X size={12} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '12px', 
            fontSize: '16px', 
            color: 'white',
            fontWeight: '600'
          }}>
            Available Triggers
          </label>
          <div style={{ 
            fontSize: '13px', 
            color: '#9ca3af',
            marginBottom: '16px'
          }}>
            Choose one or more triggers that will start your workflow. You can combine different trigger types.
          </div>

          {/* Template-based suggestions */}
          {!editingWorkflow && newWorkflow.template && newWorkflow.template !== 'custom' && (
            (() => {
              const selectedTemplate = workflowTemplates.find(t => t.id === newWorkflow.template);
              if (selectedTemplate && selectedTemplate.suggestedTriggers && selectedTemplate.suggestedTriggers.length > 0) {
                return (
                  <div style={{
                    background: 'rgba(139, 92, 246, 0.1)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '20px'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px'
                    }}>
                      <div style={{ fontSize: '16px' }}>💡</div>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: '600',
                        color: '#c4b5fd'
                      }}>
                        Suggested for {selectedTemplate.name}
                      </div>
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#d1d5db',
                      marginBottom: '12px',
                      lineHeight: '1.4'
                    }}>
                      Based on your template selection, these additional triggers might be useful:
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      flexWrap: 'wrap'
                    }}>
                      {selectedTemplate.suggestedTriggers.map(triggerName => {
                        const trigger = availableTriggers.find(t => t.name === triggerName);
                        const isAlreadySelected = (editingWorkflow ? editingWorkflow.triggers : newWorkflow.triggers).includes(triggerName);
                        
                        if (!trigger || isAlreadySelected) return null;
                        
                        return (
                          <button
                            key={trigger.id}
                            onClick={() => addTrigger(trigger.id)}
                            style={{
                              padding: '6px 12px',
                              background: 'rgba(139, 92, 246, 0.2)',
                              border: '1px solid rgba(139, 92, 246, 0.4)',
                              borderRadius: '16px',
                              color: '#c4b5fd',
                              fontSize: '11px',
                              fontWeight: '500',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'rgba(139, 92, 246, 0.3)';
                              e.currentTarget.style.color = 'white';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)';
                              e.currentTarget.style.color = '#c4b5fd';
                            }}
                          >
                            + {trigger.name}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              }
              return null;
            })()
          )}
          
          {/* Category Filter */}
          <div style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '16px',
            flexWrap: 'wrap'
          }}>
            {['all', 'manual', 'scheduled', 'event', 'api'].map(category => (
              <button
                key={category}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '16px',
                  color: '#9ca3af',
                  fontSize: '12px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {category === 'all' ? 'All Categories' : category}
              </button>
            ))}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '12px'
          }}>
            {availableTriggers.map(trigger => {
              const isSelected = currentTriggers.includes(trigger.name);
              const categoryColor = getCategoryColor(trigger.category);
              return (
                <button
                  key={trigger.id}
                  data-trigger-id={trigger.id}
                  onClick={() => addTrigger(trigger.id)}
                  disabled={isSelected}
                  style={{
                    padding: '18px',
                    background: isSelected 
                      ? `linear-gradient(135deg, ${categoryColor}30 0%, ${categoryColor}20 100%)`
                      : 'rgba(255,255,255,0.05)',
                    border: `2px solid ${isSelected ? categoryColor : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: '12px',
                    color: isSelected ? '#c4b5fd' : 'white',
                    cursor: isSelected ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                    opacity: isSelected ? 0.7 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = `linear-gradient(135deg, ${categoryColor}20 0%, ${categoryColor}10 100%)`;
                      e.currentTarget.style.borderColor = `${categoryColor}60`;
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = `0 8px 25px ${categoryColor}20`;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    marginBottom: '10px'
                  }}>
                    <div style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: categoryColor,
                      boxShadow: `0 0 8px ${categoryColor}60`
                    }} />
                    <div style={{ fontWeight: '600', fontSize: '15px', flex: 1 }}>{trigger.name}</div>
                    {isSelected && (
                      <div style={{
                        padding: '3px 8px',
                        background: categoryColor,
                        borderRadius: '12px',
                        fontSize: '10px',
                        fontWeight: '700',
                        color: 'white',
                        letterSpacing: '0.5px'
                      }}>
                        ✓ ADDED
                      </div>
                    )}
                  </div>
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#9ca3af', 
                    textTransform: 'uppercase',
                    fontWeight: '600',
                    marginBottom: '6px',
                    letterSpacing: '0.5px'
                  }}>
                    {trigger.category}
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#d1d5db',
                    lineHeight: '1.5'
                  }}>
                    {trigger.description}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step Summary */}
        <div style={{
          background: 'rgba(139, 92, 246, 0.1)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '8px',
          padding: '12px',
          marginTop: '16px'
        }}>
          <div style={{ 
            fontSize: '12px', 
            color: '#c4b5fd', 
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            STEP 2 SUMMARY
          </div>
          <div style={{ fontSize: '14px', color: 'white' }}>
            {currentTriggers.length === 0 
              ? 'No triggers selected - workflow will need to be started manually'
              : `${currentTriggers.length} trigger${currentTriggers.length > 1 ? 's' : ''} selected: ${currentTriggers.slice(0, 2).join(', ')}${currentTriggers.length > 2 ? ` +${currentTriggers.length - 2} more` : ''}`
            }
          </div>
        </div>
      </>
    );
  };

  const renderActionsStep = () => {
    const currentActions = editingWorkflow ? editingWorkflow.actions : newWorkflow.actions;
    const currentSchedule = editingWorkflow ? 'manual' : newWorkflow.schedule;
    const currentEnabled = editingWorkflow ? editingWorkflow.status === 'Active' : newWorkflow.enabled;

    return (
      <>
        <div style={{ marginBottom: '24px' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '12px'
          }}>
            <label style={{ 
              fontSize: '16px', 
              color: 'white',
              fontWeight: '600'
            }}>
              Selected Actions
            </label>
            <div style={{
              padding: '2px 8px',
              background: currentActions.length > 0 ? '#10b981' : '#6b7280',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: '600',
              color: 'white'
            }}>
              {currentActions.length} selected
            </div>
          </div>
          
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginBottom: '16px',
            minHeight: '60px',
            padding: '16px',
            background: 'rgba(255,255,255,0.05)',
            border: `2px solid ${currentActions.length > 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: '12px',
            transition: 'border-color 0.2s ease'
          }}>
            {currentActions.length === 0 ? (
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '100%',
                color: '#6b7280', 
                fontSize: '14px',
                fontStyle: 'italic'
              }}>
                Select actions from the options below to define what your workflow does
              </div>
            ) : (
              currentActions.map((action, index) => {
                const actionData = availableActions.find(a => a.name === action);
                const categoryColor = actionData ? getCategoryColor(actionData.category) : '#06b6d4';
                return (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 14px',
                      background: `linear-gradient(135deg, ${categoryColor}90 0%, ${categoryColor}70 100%)`,
                      border: `1px solid ${categoryColor}60`,
                      borderRadius: '24px',
                      fontSize: '13px',
                      color: 'white',
                      fontWeight: '500',
                      transition: 'all 0.2s ease',
                      animation: 'slideIn 0.3s ease'
                    }}
                  >
                    <span style={{
                      fontSize: '10px',
                      padding: '3px 7px',
                      background: 'rgba(255,255,255,0.25)',
                      borderRadius: '10px',
                      textTransform: 'uppercase',
                      fontWeight: '700',
                      letterSpacing: '0.5px'
                    }}>
                      {actionData?.category || 'action'}
                    </span>
                    <span style={{ fontWeight: '600' }}>{action}</span>
                    <button
                      onClick={() => removeAction(action)}
                      style={{
                        background: 'rgba(255,255,255,0.2)',
                        border: 'none',
                        color: 'white',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        borderRadius: '50%',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.4)';
                        e.currentTarget.style.transform = 'scale(1.1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
                        e.currentTarget.style.transform = 'scale(1)';
                      }}
                    >
                      <X size={12} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '12px', 
            fontSize: '16px', 
            color: 'white',
            fontWeight: '600'
          }}>
            Available Actions
          </label>
          <div style={{ 
            fontSize: '13px', 
            color: '#9ca3af',
            marginBottom: '16px'
          }}>
            Choose one or more actions that your workflow will perform. Actions will execute in the order selected.
          </div>

          {/* Template-based action suggestions */}
          {!editingWorkflow && newWorkflow.template && newWorkflow.template !== 'custom' && (
            (() => {
              const selectedTemplate = workflowTemplates.find(t => t.id === newWorkflow.template);
              if (selectedTemplate && selectedTemplate.suggestedActions && selectedTemplate.suggestedActions.length > 0) {
                return (
                  <div style={{
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '20px'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px'
                    }}>
                      <div style={{ fontSize: '16px' }}>🎯</div>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: '600',
                        color: '#6ee7b7'
                      }}>
                        Recommended Actions for {selectedTemplate.name}
                      </div>
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#d1d5db',
                      marginBottom: '12px',
                      lineHeight: '1.4'
                    }}>
                      These actions work well with your selected template and can enhance your workflow:
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      flexWrap: 'wrap'
                    }}>
                      {selectedTemplate.suggestedActions.map(actionName => {
                        const action = availableActions.find(a => a.name === actionName);
                        const isAlreadySelected = (editingWorkflow ? editingWorkflow.actions : newWorkflow.actions).includes(actionName);
                        
                        if (!action || isAlreadySelected) return null;
                        
                        return (
                          <button
                            key={action.id}
                            onClick={() => addAction(action.id)}
                            style={{
                              padding: '6px 12px',
                              background: 'rgba(16, 185, 129, 0.2)',
                              border: '1px solid rgba(16, 185, 129, 0.4)',
                              borderRadius: '16px',
                              color: '#6ee7b7',
                              fontSize: '11px',
                              fontWeight: '500',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'rgba(16, 185, 129, 0.3)';
                              e.currentTarget.style.color = 'white';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'rgba(16, 185, 129, 0.2)';
                              e.currentTarget.style.color = '#6ee7b7';
                            }}
                          >
                            + {action.name}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              }
              return null;
            })()
          )}
          
          {/* Category Filter */}
          <div style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '16px',
            flexWrap: 'wrap'
          }}>
            {['all', 'processing', 'analysis', 'communication', 'storage'].map(category => (
              <button
                key={category}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '16px',
                  color: '#9ca3af',
                  fontSize: '12px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {category === 'all' ? 'All Categories' : category}
              </button>
            ))}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '12px',
            marginBottom: '24px'
          }}>
            {availableActions.map(action => {
              const isSelected = currentActions.includes(action.name);
              const categoryColor = getCategoryColor(action.category);
              return (
                <button
                  key={action.id}
                  data-action-id={action.id}
                  onClick={() => addAction(action.id)}
                  disabled={isSelected}
                  style={{
                    padding: '18px',
                    background: isSelected 
                      ? `linear-gradient(135deg, ${categoryColor}30 0%, ${categoryColor}20 100%)`
                      : 'rgba(255,255,255,0.05)',
                    border: `2px solid ${isSelected ? categoryColor : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: '12px',
                    color: isSelected ? '#c4b5fd' : 'white',
                    cursor: isSelected ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                    opacity: isSelected ? 0.7 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = `linear-gradient(135deg, ${categoryColor}20 0%, ${categoryColor}10 100%)`;
                      e.currentTarget.style.borderColor = `${categoryColor}60`;
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = `0 8px 25px ${categoryColor}20`;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    marginBottom: '10px'
                  }}>
                    <div style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: categoryColor,
                      boxShadow: `0 0 8px ${categoryColor}60`
                    }} />
                    <div style={{ fontWeight: '600', fontSize: '15px', flex: 1 }}>{action.name}</div>
                    {isSelected && (
                      <div style={{
                        padding: '3px 8px',
                        background: categoryColor,
                        borderRadius: '12px',
                        fontSize: '10px',
                        fontWeight: '700',
                        color: 'white',
                        letterSpacing: '0.5px'
                      }}>
                        ✓ ADDED
                      </div>
                    )}
                  </div>
                  <div style={{ 
                    fontSize: '11px', 
                    color: '#9ca3af', 
                    textTransform: 'uppercase',
                    fontWeight: '600',
                    marginBottom: '6px',
                    letterSpacing: '0.5px'
                  }}>
                    {action.category}
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    color: '#d1d5db',
                    lineHeight: '1.5'
                  }}>
                    {action.description}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {!editingWorkflow && (
          <>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px', 
                color: '#9ca3af',
                fontWeight: '500'
              }}>
                Execution Schedule
              </label>
              <select
                value={currentSchedule}
                onChange={(e) => setNewWorkflow(prev => ({ ...prev, schedule: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '2px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none'
                }}
              >
                <option value="manual" style={{ background: '#1a1a2e' }}>Manual Trigger Only</option>
                <option value="hourly" style={{ background: '#1a1a2e' }}>Every Hour</option>
                <option value="daily" style={{ background: '#1a1a2e' }}>Daily at 9:00 AM</option>
                <option value="weekly" style={{ background: '#1a1a2e' }}>Weekly on Mondays</option>
              </select>
            </div>

            <div style={{ 
              marginBottom: '20px',
              padding: '16px',
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: 'pointer',
                fontSize: '14px',
                color: 'white',
                fontWeight: '500'
              }}>
                <input
                  type="checkbox"
                  checked={currentEnabled}
                  onChange={(e) => setNewWorkflow(prev => ({ ...prev, enabled: e.target.checked }))}
                  style={{
                    width: '18px',
                    height: '18px',
                    accentColor: '#8b5cf6'
                  }}
                />
                <div>
                  <div>Enable workflow immediately after creation</div>
                  <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>
                    The workflow will be set to Active status and can start running based on its triggers
                  </div>
                </div>
              </label>
            </div>
          </>
        )}

        {/* Step Summary */}
        <div style={{
          background: 'rgba(139, 92, 246, 0.1)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '8px',
          padding: '12px',
          marginTop: '16px'
        }}>
          <div style={{ 
            fontSize: '12px', 
            color: '#c4b5fd', 
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            STEP 3 SUMMARY
          </div>
          <div style={{ fontSize: '14px', color: 'white', marginBottom: '4px' }}>
            {currentActions.length === 0 
              ? 'No actions selected - workflow will not perform any operations'
              : `${currentActions.length} action${currentActions.length > 1 ? 's' : ''} selected: ${currentActions.slice(0, 2).join(', ')}${currentActions.length > 2 ? ` +${currentActions.length - 2} more` : ''}`
            }
          </div>
          {!editingWorkflow && (
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>
              Schedule: {currentSchedule} • Status: {currentEnabled ? 'Active' : 'Draft'}
            </div>
          )}
        </div>
      </>
    );
  };

  return (
    <div 
      style={{
        padding: '24px',
        height: '100%',
        overflow: 'auto'
      }}
      role="main"
      aria-label="Workflow management page"
    >
      {/* Screen Reader Announcements */}
      <div 
        aria-live="polite" 
        aria-atomic="true" 
        style={{ 
          position: 'absolute', 
          left: '-10000px', 
          width: '1px', 
          height: '1px', 
          overflow: 'hidden' 
        }}
      >
        {announcements.map((announcement, index) => (
          <div key={index}>{announcement}</div>
        ))}
      </div>

      {/* Critical Error Display */}
      {criticalError && (
        <div style={{
          background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
          border: '1px solid #ef4444',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          animation: 'fadeIn 0.3s ease-in-out'
        }} role="alert" aria-live="assertive">
          <div style={{
            width: '24px',
            height: '24px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            ⚠️
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
              Critical Error
            </div>
            <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
              {criticalError}
            </div>
          </div>
          <button
            onClick={() => setCriticalError(null)}
            style={{
              background: 'none',
              border: 'none',
              color: 'rgba(255,255,255,0.8)',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            aria-label="Dismiss critical error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Network Error Display */}
      {networkError && (
        <div style={{
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          border: '1px solid #fbbf24',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          animation: 'fadeIn 0.3s ease-in-out'
        }} role="alert" aria-live="polite">
          <div style={{
            width: '24px',
            height: '24px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            🌐
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
              Network Issue
            </div>
            <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
              {networkError}
            </div>
          </div>
          <button
            onClick={() => setNetworkError(null)}
            style={{
              background: 'none',
              border: 'none',
              color: 'rgba(255,255,255,0.8)',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            aria-label="Dismiss network error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Loading State Display */}
      {isLoading && operationInProgress && (
        <div style={{
          background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
          border: '1px solid #60a5fa',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          animation: 'fadeIn 0.3s ease-in-out'
        }} role="status" aria-live="polite">
          <div style={{
            width: '24px',
            height: '24px',
            border: '2px solid rgba(255,255,255,0.3)',
            borderTop: '2px solid white',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            flexShrink: 0
          }}></div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
              Processing...
            </div>
            <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
              {operationInProgress}
              {retryCount > 0 && ` (Retry ${retryCount}/3)`}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <div>
          <h1 style={{
            color: 'white',
            margin: 0,
            fontSize: '24px',
            fontWeight: '600'
          }}>
            Workflow Automation
          </h1>
          <p style={{
            color: '#9ca3af',
            margin: '4px 0 0 0',
            fontSize: '14px'
          }}>
            Create and manage automated workflows for your AI tasks
          </p>
        </div>
        
        <button
          onClick={() => {
            setShowCreateWorkflow(true);
            announceToScreenReader('Opened workflow creation dialog');
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500'
          }}
          aria-label="Create new workflow"
          title="Create a new automated workflow"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              setShowCreateWorkflow(true);
              announceToScreenReader('Opened workflow creation dialog');
            }
          }}
        >
          <Plus size={16} aria-hidden="true" />
          Create Workflow
        </button>
      </header>

      {/* Workflow Stats */}
      <section 
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}
        aria-label="Workflow statistics"
      >
        <div 
          style={{
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            padding: '20px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}
          role="region"
          aria-label="Total workflows count"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Zap size={20} style={{ color: '#8b5cf6' }} aria-hidden="true" />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>Total Workflows</span>
          </div>
          <div 
            style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}
            aria-label={`${workflows.length} total workflows`}
          >
            {workflows.length}
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Play size={20} style={{ color: '#10b981' }} />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>Active</span>
          </div>
          <div style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}>
            {workflows.filter(w => w.status === 'Active').length}
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <BarChart3 size={20} style={{ color: '#f59e0b' }} />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>Total Executions</span>
          </div>
          <div style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}>
            {workflows.reduce((sum, w) => sum + w.executions, 0)}
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <CheckCircle size={20} style={{ color: '#06b6d4' }} />
            <span style={{ color: 'white', fontSize: '16px', fontWeight: '500' }}>Avg Success Rate</span>
          </div>
          <div style={{ color: 'white', fontSize: '24px', fontWeight: '600' }}>
            {workflows.length > 0 ? Math.round(workflows.reduce((sum, w) => sum + w.successRate, 0) / workflows.length) : 0}%
          </div>
        </div>
      </section>

      {/* Workflows List */}
      <div style={{
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '12px',
        overflow: 'hidden'
      }}>
        {workflows.length === 0 ? (
          <div 
            style={{
              padding: '40px',
              textAlign: 'center',
              color: '#9ca3af'
            }}
            role="status"
            aria-label="No workflows available"
          >
            <Zap size={32} style={{ marginBottom: '12px' }} aria-hidden="true" />
            <p style={{ margin: 0, fontSize: '16px' }}>No workflows created yet</p>
          </div>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {workflows.map((workflow, index) => (
              <li key={workflow.id}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '20px',
                    borderBottom: index < workflows.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                    transition: 'background-color 0.2s ease',
                    border: focusedWorkflow === workflow.id ? '2px solid rgba(96, 165, 250, 0.8)' : '2px solid transparent',
                    borderRadius: '8px'
                  }}
                  role="article"
                  aria-label={`${workflow.title} workflow - ${workflow.status} - ${workflow.executions} executions - ${workflow.successRate}% success rate`}
                  tabIndex={0}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  onKeyDown={(e) => handleWorkflowKeyDown(e, workflow.id)}
                  onFocus={() => setFocusedWorkflow(workflow.id)}
                  onBlur={() => setFocusedWorkflow(null)}
                >
              <div style={{
                width: '50px',
                height: '50px',
                borderRadius: '12px',
                background: `linear-gradient(135deg, ${workflow.color}40 0%, ${workflow.color}60 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '16px'
              }}>
                <Zap size={24} style={{ color: workflow.color }} />
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '4px'
                }}>
                  <h3 style={{
                    color: 'white',
                    margin: 0,
                    fontSize: '16px',
                    fontWeight: '500'
                  }}>
                    {workflow.title}
                  </h3>
                  {getStatusIcon(workflow.status)}
                  <span style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    textTransform: 'uppercase',
                    fontWeight: '500'
                  }}>
                    {workflow.status}
                  </span>
                </div>
                
                <p style={{
                  margin: '0 0 8px 0',
                  fontSize: '14px',
                  color: '#9ca3af'
                }}>
                  {workflow.description}
                </p>
                
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  fontSize: '12px',
                  color: '#6b7280'
                }}>
                  <span>Last run: {workflow.lastRun}</span>
                  <span>Executions: {workflow.executions}</span>
                  <span>Success: {workflow.successRate}%</span>
                </div>
              </div>
              
              <div 
                style={{
                  display: 'flex',
                  gap: '8px'
                }}
                role="group"
                aria-label={`Actions for ${workflow.title} workflow`}
              >
                <button
                  onClick={() => {
                    toggleWorkflowStatus(workflow.id);
                    announceToScreenReader(`${workflow.status === 'Active' ? 'Paused' : 'Started'} ${workflow.title} workflow`);
                  }}
                  style={{
                    padding: '8px',
                    background: 'rgba(255,255,255,0.1)',
                    border: 'none',
                    borderRadius: '6px',
                    color: workflow.status === 'Active' ? '#ef4444' : '#10b981',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  aria-label={workflow.status === 'Active' ? `Pause ${workflow.title} workflow` : `Start ${workflow.title} workflow`}
                  title={workflow.status === 'Active' ? 'Pause Workflow' : 'Start Workflow'}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      toggleWorkflowStatus(workflow.id);
                      announceToScreenReader(`${workflow.status === 'Active' ? 'Paused' : 'Started'} ${workflow.title} workflow`);
                    }
                  }}
                >
                  {workflow.status === 'Active' ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
                </button>
                
                <button
                  onClick={() => {
                    setEditingWorkflow(workflow);
                    setShowEditWorkflow(true);
                    announceToScreenReader(`Opened ${workflow.title} for editing`);
                  }}
                  style={{
                    padding: '8px',
                    background: 'rgba(255,255,255,0.1)',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  aria-label={`Edit ${workflow.title} workflow`}
                  title="Edit workflow"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setEditingWorkflow(workflow);
                      setShowEditWorkflow(true);
                      announceToScreenReader(`Opened ${workflow.title} for editing`);
                    }
                  }}
                >
                  <Edit size={16} aria-hidden="true" />
                </button>
                
                <button
                  onClick={() => {
                    deleteWorkflow(workflow.id);
                    announceToScreenReader(`Deleted ${workflow.title} workflow`);
                  }}
                  style={{
                    padding: '8px',
                    background: 'rgba(255,255,255,0.1)',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#ef4444',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  aria-label={`Delete ${workflow.title} workflow`}
                  title="Delete workflow"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      deleteWorkflow(workflow.id);
                      announceToScreenReader(`Deleted ${workflow.title} workflow`);
                    }
                  }}
                >
                  <Trash2 size={16} aria-hidden="true" />
                </button>
              </div>
                </div>
              </li>
            ))
          </ul>
        )}
        
        {/* Keyboard navigation help */}
        {workflows.length > 0 && (
          <div style={{
            marginTop: '16px',
            padding: '12px',
            background: 'rgba(96, 165, 250, 0.1)',
            borderRadius: '8px',
            fontSize: '11px',
            color: '#9ca3af'
          }}>
            <div style={{ fontWeight: '600', marginBottom: '4px', color: '#60a5fa' }}>
              Keyboard Navigation:
            </div>
            <div>↑↓ Navigate workflows • Enter/Space Edit • Delete/Backspace Remove</div>
          </div>
        )}
      </div>

      {/* Unified Workflow Modal */}
      {(showCreateWorkflow || showEditWorkflow) && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            padding: '30px',
            borderRadius: '15px',
            border: '1px solid rgba(255,255,255,0.2)',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '85vh',
            overflowY: 'auto'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px'
            }}>
              <h3 style={{
                color: 'white',
                margin: 0,
                fontSize: '20px',
                fontWeight: '600'
              }}>
                {editingWorkflow ? 'Edit Workflow' : 'Create New Workflow'}
              </h3>
              <button
                onClick={() => {
                  setShowCreateWorkflow(false);
                  setShowEditWorkflow(false);
                  setEditingWorkflow(null);
                  setWorkflowStep(1);
                  setNewWorkflow({ 
                    title: '', 
                    description: '', 
                    template: 'custom',
                    triggers: [],
                    actions: [],
                    schedule: 'manual',
                    enabled: false
                  });
                  // Reset validation state
                  setValidationErrors({});
                  setFieldTouched({});
                  setOperationError(null);
                  setDuplicateAttempts({});
                  setIsSubmitting(false);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Step Indicator - only show for creation */}
            {!editingWorkflow && renderStepIndicator()}

            {/* Form Completion Indicator */}
            {(editingWorkflow || workflowStep === 1) && (
              <div style={{
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '16px',
                border: '1px solid rgba(255,255,255,0.1)'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '8px'
                }}>
                  <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '600' }}>
                    FORM COMPLETION
                  </span>
                  <span style={{ 
                    fontSize: '12px', 
                    color: isFormComplete(!!editingWorkflow) ? '#10b981' : '#f59e0b',
                    fontWeight: '600'
                  }}>
                    {isFormComplete(!!editingWorkflow) ? '✓ COMPLETE' : '⚠ INCOMPLETE'}
                  </span>
                </div>
                <div style={{
                  width: '100%',
                  height: '4px',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${isFormComplete(!!editingWorkflow) ? 100 : 
                      getWorkflowValue('title', !!editingWorkflow).trim() && getWorkflowValue('description', !!editingWorkflow).trim() ? 80 :
                      getWorkflowValue('title', !!editingWorkflow).trim() || getWorkflowValue('description', !!editingWorkflow).trim() ? 40 : 0}%`,
                    height: '100%',
                    background: isFormComplete(!!editingWorkflow) 
                      ? 'linear-gradient(90deg, #10b981 0%, #059669 100%)'
                      : 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)',
                    borderRadius: '2px',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            )}

            {/* Step Content */}
            <div style={{ marginBottom: '24px' }}>
              {(editingWorkflow || workflowStep === 1) && renderBasicInfoStep()}
              {!editingWorkflow && workflowStep === 2 && renderTriggersStep()}
              {!editingWorkflow && workflowStep === 3 && renderActionsStep()}
              {editingWorkflow && (
                <>
                  <div style={{ marginTop: '24px', marginBottom: '20px' }}>
                    <h4 style={{ color: 'white', marginBottom: '12px', fontSize: '16px' }}>Triggers</h4>
                    {renderTriggersStep()}
                  </div>
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ color: 'white', marginBottom: '12px', fontSize: '16px' }}>Actions</h4>
                    {renderActionsStep()}
                  </div>
                </>
              )}
            </div>

            {/* Navigation Buttons */}
            <div style={{ 
              display: 'flex', 
              gap: '12px',
              paddingTop: '16px',
              borderTop: '1px solid rgba(255,255,255,0.1)'
            }}>
              {!editingWorkflow && workflowStep > 1 && (
                <button
                  onClick={() => setWorkflowStep(prev => prev - 1)}
                  style={{
                    padding: '14px 24px',
                    background: 'rgba(156, 163, 175, 0.15)',
                    border: '2px solid rgba(156, 163, 175, 0.3)',
                    color: '#d1d5db',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '14px',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(156, 163, 175, 0.25)';
                    e.currentTarget.style.borderColor = 'rgba(156, 163, 175, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(156, 163, 175, 0.15)';
                    e.currentTarget.style.borderColor = 'rgba(156, 163, 175, 0.3)';
                  }}
                >
                  ← Previous
                </button>
              )}
              
              <button
                onClick={() => {
                  setShowCreateWorkflow(false);
                  setShowEditWorkflow(false);
                  setEditingWorkflow(null);
                  setWorkflowStep(1);
                  setNewWorkflow({ 
                    title: '', 
                    description: '', 
                    template: 'custom',
                    triggers: [],
                    actions: [],
                    schedule: 'manual',
                    enabled: false
                  });
                  // Reset validation state
                  setValidationErrors({});
                  setFieldTouched({});
                  setOperationError(null);
                  setDuplicateAttempts({});
                  setIsSubmitting(false);
                }}
                style={{
                  flex: editingWorkflow ? 1 : 0,
                  padding: '14px 24px',
                  background: 'rgba(156, 163, 175, 0.15)',
                  border: '2px solid rgba(156, 163, 175, 0.3)',
                  color: '#d1d5db',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '14px',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(156, 163, 175, 0.25)';
                  e.currentTarget.style.borderColor = 'rgba(156, 163, 175, 0.5)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(156, 163, 175, 0.15)';
                  e.currentTarget.style.borderColor = 'rgba(156, 163, 175, 0.3)';
                }}
              >
                Cancel
              </button>

              {editingWorkflow ? (
                <button
                  onClick={updateWorkflow}
                  disabled={!isFormComplete(true) || isSubmitting}
                  style={{
                    flex: 1,
                    padding: '14px 24px',
                    background: (isFormComplete(true) && !isSubmitting) 
                      ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
                      : 'rgba(156, 163, 175, 0.2)',
                    border: 'none',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: (isFormComplete(true) && !isSubmitting) ? 'pointer' : 'not-allowed',
                    fontWeight: '600',
                    fontSize: '14px',
                    transition: 'all 0.2s ease',
                    opacity: (isFormComplete(true) && !isSubmitting) ? 1 : 0.6,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  {isSubmitting ? (
                    <>
                      <div style={{
                        width: '16px',
                        height: '16px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTop: '2px solid white',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }} />
                      Saving...
                    </>
                  ) : (
                    <>💾 Save Changes</>
                  )}
                </button>
              ) : workflowStep < 3 ? (
                <button
                  onClick={() => {
                    // Validation logic for each step
                    if (workflowStep === 1) {
                      if (!validateCurrentStep(1, false)) {
                        // Mark fields as touched to show validation errors
                        setFieldTouched({ title: true, description: true });
                        return;
                      }
                    }
                    setWorkflowStep(prev => prev + 1);
                  }}
                  disabled={workflowStep === 1 && !isFormComplete(false)}
                  style={{
                    flex: 1,
                    padding: '14px 24px',
                    background: (workflowStep === 1 && !isFormComplete(false))
                      ? 'rgba(156, 163, 175, 0.2)'
                      : 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                    border: 'none',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: (workflowStep === 1 && !isFormComplete(false)) ? 'not-allowed' : 'pointer',
                    fontWeight: '600',
                    fontSize: '14px',
                    transition: 'all 0.2s ease',
                    opacity: (workflowStep === 1 && !isFormComplete(false)) ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  {workflowStep === 1 ? 'Continue to Triggers' : 'Continue to Actions'} →
                </button>
              ) : (
                <button
                  onClick={createNewWorkflow}
                  disabled={!isFormComplete(false) || isSubmitting}
                  style={{
                    flex: 1,
                    padding: '14px 24px',
                    background: (isFormComplete(false) && !isSubmitting) 
                      ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                      : 'rgba(156, 163, 175, 0.2)',
                    border: 'none',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: (isFormComplete(false) && !isSubmitting) ? 'pointer' : 'not-allowed',
                    fontWeight: '600',
                    fontSize: '14px',
                    transition: 'all 0.2s ease',
                    opacity: (isFormComplete(false) && !isSubmitting) ? 1 : 0.6,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  {isSubmitting ? (
                    <>
                      <div style={{
                        width: '16px',
                        height: '16px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTop: '2px solid white',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }} />
                      Creating...
                    </>
                  ) : (
                    <>🚀 Create Workflow</>
                  )}
                </button>
              )}
            </div>

            {/* Validation Messages */}
            {operationError && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                color: '#fca5a5',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                ❌ {operationError}
              </div>
            )}

            {!editingWorkflow && workflowStep === 1 && Object.keys(validationErrors).some(key => validationErrors[key]) && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                color: '#fca5a5',
                fontSize: '13px'
              }}>
                <div style={{ fontWeight: '600', marginBottom: '4px' }}>⚠️ Please fix the following issues:</div>
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  {Object.entries(validationErrors).map(([field, error]) => 
                    error && (
                      <li key={field} style={{ marginBottom: '2px' }}>
                        {field.charAt(0).toUpperCase() + field.slice(1)}: {error}
                      </li>
                    )
                  )}
                </ul>
              </div>
            )}

            {!editingWorkflow && workflowStep === 1 && isFormComplete(false) && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: '8px',
                color: '#6ee7b7',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                ✅ Basic information is complete. Ready to proceed!
              </div>
            )}

            {!editingWorkflow && workflowStep === 2 && newWorkflow.triggers.length === 0 && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '8px',
                color: '#fbbf24',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                💡 No triggers selected. Your workflow will only run manually.
              </div>
            )}

            {!editingWorkflow && workflowStep === 3 && newWorkflow.actions.length === 0 && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '8px',
                color: '#fbbf24',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                💡 Consider adding at least one action to make your workflow functional
              </div>
            )}

            {Object.values(duplicateAttempts).some(count => count > 0) && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: '8px',
                color: '#fbbf24',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                🔄 Some items are already selected and cannot be added again
              </div>
            )}
          </div>
        </div>
      )}


    </div>
  );
};

export default WorkflowsView;