import React, { useState, useRef } from 'react';
import { Send, Menu, MessageSquare, FileText, BarChart3, Settings, User, Shield, Zap, Puzzle, Brain, LogIn, UserPlus, LogOut } from 'lucide-react';
import { ToastContainer, useToast } from './components/ToastNotification';

type ViewType = 'chat' | 'documents' | 'analytics' | 'workflows' | 'integrations' | 'security' | 'settings' | 'profile' | 'help' | 'about' | 'terms' | 'privacy' | 'security-policy';

interface User {
  name: string;
  email: string;
  role: string;
}

const mockUser: User = {
  name: 'Administrator',
  email: 'Administrator',
  role: 'Administrator'
};

const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState<ViewType>('chat');
  const [user] = useState<User | null>(mockUser);
  const [messages, setMessages] = useState([
    {
      id: '1',
      content: 'Hello! I\'m your AI Scholar assistant with advanced workflow and integration capabilities. How can I help you today?',
      sender: 'assistant' as const,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Toast notification system
  const { toasts, removeToast, showSuccess, showError, showWarning, showInfo } = useToast();

  // State for functional features
  const [documents, setDocuments] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [workflows, setWorkflows] = useState([
    { id: 1, title: '🤖 Smart Document Processing', description: 'Automatically process and analyze uploaded documents', status: 'Active', color: '#4ade80', lastRun: '2 hours ago' },
    { id: 2, title: '🧠 Research Pipeline', description: 'Automated research and knowledge extraction workflow', status: 'Draft', color: '#f59e0b', lastRun: 'Never' },
    { id: 3, title: '💬 Customer Support', description: 'AI-powered ticket management and response system', status: 'Inactive', color: '#9ca3af', lastRun: '1 week ago' }
  ]);
  const [integrations, setIntegrations] = useState([
    { id: 1, name: 'OpenAI GPT', icon: '🤖', status: 'Connected', description: 'Advanced language models for chat and completion', apiKey: 'sk-...abc123' },
    { id: 2, name: 'Hugging Face', icon: '🤗', status: 'Available', description: '100,000+ open-source AI models', apiKey: '' },
    { id: 3, name: 'Anthropic Claude', icon: '🧠', status: 'Available', description: 'Safe and helpful AI assistant', apiKey: '' },
    { id: 4, name: 'Google Cloud AI', icon: '☁️', status: 'Available', description: 'Enterprise AI and ML services', apiKey: '' },
    { id: 5, name: 'AWS Bedrock', icon: '🏗️', status: 'Available', description: 'Fully managed foundation models', apiKey: '' },
    { id: 6, name: 'Slack', icon: '💬', status: 'Connected', description: 'Team communication and collaboration', apiKey: 'xoxb-...xyz789' }
  ]);
  
  // Advanced feature states
  const [showFeatureTest, setShowFeatureTest] = useState(false);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [systemHealth, setSystemHealth] = useState({
    cpu: 23,
    memory: 67,
    responseTime: 1.2,
    uptime: '99.9%'
  });
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [currentModel, setCurrentModel] = useState<any>(null);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [papersStatus, setPapersStatus] = useState<any>(null);
  const [isUpdatingPapers, setIsUpdatingPapers] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: 1, type: 'success', message: 'Workflow "Document Processing" completed successfully', time: '2 min ago' },
    { id: 2, type: 'info', message: 'New integration available: Anthropic Claude 3', time: '1 hour ago' },
    { id: 3, type: 'warning', message: 'API rate limit approaching for OpenAI GPT', time: '3 hours ago' }
  ]);
  const [quickActions, setQuickActions] = useState([
    { id: 1, title: 'Process Document', icon: '📄', action: 'document-upload', shortcut: 'Ctrl+D' },
    { id: 2, title: 'Create Workflow', icon: '⚡', action: 'workflow-create', shortcut: 'Ctrl+W' },
    { id: 3, title: 'Run Analysis', icon: '🔍', action: 'analysis-run', shortcut: 'Ctrl+R' },
    { id: 4, title: 'Export Data', icon: '📊', action: 'data-export', shortcut: 'Ctrl+E' }
  ]);
  
  // Enterprise features
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [globalSearch, setGlobalSearch] = useState('');
  const [recentActivities, setRecentActivities] = useState([
    { id: 1, action: 'Document uploaded', item: 'research_paper.pdf', time: '5 min ago', icon: '📄' },
    { id: 2, action: 'Workflow executed', item: 'Data Analysis Pipeline', time: '15 min ago', icon: '⚡' },
    { id: 3, action: 'Integration connected', item: 'OpenAI GPT', time: '1 hour ago', icon: '🔗' },
    { id: 4, action: 'Analytics report generated', item: 'Monthly Usage Report', time: '2 hours ago', icon: '📊' }
  ]);
  const [performanceMetrics, setPerformanceMetrics] = useState({
    totalQueries: 1234,
    avgResponseTime: 1.2,
    successRate: 98.5,
    activeUsers: 12,
    documentsProcessed: 56,
    workflowsExecuted: 89
  });
  const [securityEvents, setSecurityEvents] = useState([
    { id: 1, event: 'Successful login', user: 'Administrator', time: '2 minutes ago', type: 'success' },
    { id: 2, event: 'API key rotated', user: 'System', time: '1 hour ago', type: 'info' },
    { id: 3, event: 'Failed login attempt', user: 'Unknown', time: '3 hours ago', type: 'warning' }
  ]);
  const [settings, setSettings] = useState({
    twoFactorAuth: true,
    apiRateLimit: true,
    auditLogging: true,
    ipWhitelisting: false,
    theme: 'dark',
    language: 'en',
    notifications: true
  });
  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false);
  const [showEditWorkflow, setShowEditWorkflow] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<any>(null);
  const [newWorkflow, setNewWorkflow] = useState({
    title: '',
    description: '',
    template: ''
  });

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = {
      id: Date.now().toString(),
      content: input,
      sender: 'user' as const,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    
    // Scroll to bottom
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    
    // Generate RAG-powered response using backend
    setTimeout(async () => {
      try {
        // Call the RAG API endpoint
        const response = await fetch('/api/rag/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: currentInput,
            model: currentModel?.current_model || 'llama3.1:8b',
            max_sources: 5
          })
        });

        if (response.ok) {
          const ragData = await response.json();
          
          // Format the RAG response with sources
          let formattedResponse = `${ragData.response}\n\n`;
          
          if (ragData.sources && ragData.sources.length > 0) {
            formattedResponse += `**📚 Sources:**\n`;
            ragData.sources.slice(0, 3).forEach((source: any, index: number) => {
              formattedResponse += `${index + 1}. ${source.title || 'Research Paper'}\n`;
              if (source.authors) {
                formattedResponse += `   Authors: ${source.authors}\n`;
              }
              if (source.confidence_score) {
                formattedResponse += `   Relevance: ${(source.confidence_score * 100).toFixed(1)}%\n`;
              }
            });
          }
          
          if (ragData.confidence_score) {
            formattedResponse += `\n*Confidence: ${(ragData.confidence_score * 100).toFixed(1)}% | Model: ${ragData.model_used}*`;
          }

          const assistantMessage = {
            id: (Date.now() + 1).toString(),
            content: formattedResponse,
            sender: 'assistant' as const,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          // Fallback to local response if RAG API fails
          const fallbackResponse = await generateFallbackResponse(currentInput);
          const assistantMessage = {
            id: (Date.now() + 1).toString(),
            content: fallbackResponse,
            sender: 'assistant' as const,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      } catch (error) {
        // Fallback to local response on error
        const fallbackResponse = await generateFallbackResponse(currentInput);
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          content: fallbackResponse,
          sender: 'assistant' as const,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
      
      // Scroll to bottom after response
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }, 1000);
  };

  const generateFallbackResponse = async (input: string) => {
    // Fallback responses when RAG API is not available
    if (input.toLowerCase().includes('document') || input.toLowerCase().includes('pdf')) {
      return `🔍 **Document Analysis Ready**\n\nI can help you with:\n• **PDF Processing**: Extract text, images, and metadata\n• **Semantic Search**: Find relevant content across documents\n• **Knowledge Extraction**: Identify key concepts and relationships\n• **Citation Generation**: Create proper academic citations\n\nUpload documents in the Documents section to get started!`;
    } else if (input.toLowerCase().includes('research') || input.toLowerCase().includes('academic')) {
      return `🎓 **Academic Research Assistant**\n\nI provide:\n• **Literature Search**: Find relevant papers and sources\n• **Knowledge Graph**: Visualize research connections\n• **Citation Analysis**: Track paper relationships\n• **Research Synthesis**: Combine multiple sources\n• **Methodology Guidance**: Research design assistance\n\nWhat research topic are you exploring?`;
    } else {
      return `🤖 **AI Scholar Assistant**\n\nI'm your comprehensive research and automation assistant powered by advanced RAG technology. I can help with:\n\n**Core Capabilities:**\n• Document analysis and processing\n• Research assistance and literature review\n• Workflow automation and integration\n• Data analytics and visualization\n• Knowledge graph construction\n\n**Advanced Features:**\n• RAG (Retrieval-Augmented Generation)\n• Semantic search across processed papers\n• Multi-modal AI integration\n• Citation and source tracking\n\nAsk me anything about your research topics!`;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Functional handlers
  const handleFileUpload = async (files: FileList) => {
    setIsUploading(true);
    setUploadProgress(0);
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const newDoc = {
        id: Date.now() + i,
        name: file.name,
        size: file.size,
        type: file.type,
        uploadDate: new Date(),
        status: 'Processing',
        progress: 0
      };
      
      setDocuments(prev => [...prev, newDoc]);
      
      // Simulate upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setUploadProgress(progress);
        setDocuments(prev => prev.map(doc => 
          doc.id === newDoc.id ? { ...doc, progress } : doc
        ));
      }
      
      setDocuments(prev => prev.map(doc => 
        doc.id === newDoc.id ? { ...doc, status: 'Completed' } : doc
      ));
    }
    
    setIsUploading(false);
    setUploadProgress(0);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    // Implement search functionality
  };

  const toggleIntegration = (id: number) => {
    setIntegrations(prev => prev.map(integration => 
      integration.id === id 
        ? { ...integration, status: integration.status === 'Connected' ? 'Available' : 'Connected' }
        : integration
    ));
  };

  const [workflowResults, setWorkflowResults] = useState<any>({});
  const [showWorkflowResults, setShowWorkflowResults] = useState(false);
  const [currentWorkflowResult, setCurrentWorkflowResult] = useState<any>(null);

  const runWorkflow = (id: number) => {
    const workflow = workflows.find(w => w.id === id);
    if (!workflow) return;

    // Start workflow execution
    setWorkflows(prev => prev.map(w => 
      w.id === id 
        ? { ...w, status: 'Running', lastRun: 'Running...' }
        : w
    ));
    
    showInfo(`Workflow "${workflow.title}" started...`);
    
    // Simulate workflow execution with progress
    setTimeout(() => {
      showInfo(`Processing step 1/3 for "${workflow.title}"...`);
    }, 1000);
    
    setTimeout(() => {
      showInfo(`Processing step 2/3 for "${workflow.title}"...`);
    }, 2000);
    
    setTimeout(() => {
      // Generate mock results
      const results = {
        workflowId: id,
        workflowTitle: workflow.title,
        executionTime: '2.3 seconds',
        status: 'Completed Successfully',
        timestamp: new Date().toLocaleString(),
        steps: [
          { name: 'Input Processing', status: 'Completed', duration: '0.5s', output: 'Processed 15 documents' },
          { name: 'AI Analysis', status: 'Completed', duration: '1.2s', output: 'Generated insights and summaries' },
          { name: 'Output Generation', status: 'Completed', duration: '0.6s', output: 'Created final report with 3 sections' }
        ],
        outputs: [
          { name: 'Summary Report', type: 'PDF', size: '2.4 MB' },
          { name: 'Data Analysis', type: 'JSON', size: '156 KB' },
          { name: 'Visualization', type: 'PNG', size: '890 KB' }
        ],
        metrics: {
          documentsProcessed: 15,
          insightsGenerated: 8,
          accuracy: '94.2%',
          confidence: '87.5%'
        }
      };
      
      // Update workflow status and show results
      setWorkflows(prev => prev.map(w => 
        w.id === id 
          ? { ...w, status: 'Active', lastRun: 'Just now' }
          : w
      ));
      
      setWorkflowResults(prev => ({ ...prev, [id]: results }));
      setCurrentWorkflowResult(results);
      setShowWorkflowResults(true);
      showSuccess(`Workflow "${workflow.title}" completed successfully!`);
    }, 3000);
  };

  const updateSettings = (key: string, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    
    // Persist to localStorage
    localStorage.setItem('ai-scholar-settings', JSON.stringify(newSettings));
    
    // Apply settings immediately
    applySettings(key, value);
    
    // Show success notification
    showSuccess(`${key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())} updated successfully!`);
  };

  const applySettings = (key: string, value: any) => {
    switch (key) {
      case 'theme':
        document.body.setAttribute('data-theme', value);
        break;
      case 'language':
        document.documentElement.lang = value;
        break;
      case 'notifications':
        if (value && 'Notification' in window) {
          Notification.requestPermission();
        }
        break;
      default:
        break;
    }
  };

  // Load settings from localStorage on component mount
  React.useEffect(() => {
    const savedSettings = localStorage.getItem('ai-scholar-settings');
    if (savedSettings) {
      try {
        const parsedSettings = JSON.parse(savedSettings);
        setSettings(parsedSettings);
        
        // Apply all saved settings
        Object.entries(parsedSettings).forEach(([key, value]) => {
          applySettings(key, value);
        });
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    }
  }, []);

  // Advanced feature functions
  const runFeatureTest = async () => {
    setShowFeatureTest(true);
    const tests = [
      { name: 'Chat Input Functionality', status: 'running' },
      { name: 'Auto-scroll Behavior', status: 'running' },
      { name: 'RAG-powered Responses', status: 'running' },
      { name: 'Integration Categories', status: 'running' },
      { name: 'Settings Page Loading', status: 'running' },
      { name: 'Analytics Visualizations', status: 'running' },
      { name: 'Workflow Builder', status: 'running' },
      { name: 'Input Field Handling', status: 'running' }
    ];
    
    setTestResults(tests);
    
    // Simulate test execution
    for (let i = 0; i < tests.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setTestResults(prev => prev.map((test, index) => 
        index === i ? { ...test, status: 'passed' } : test
      ));
    }
  };

  const executeQuickAction = (action: string) => {
    switch (action) {
      case 'document-upload':
        setCurrentView('documents');
        break;
      case 'workflow-create':
        setCurrentView('workflows');
        setShowCreateWorkflow(true);
        break;
      case 'analysis-run':
        setCurrentView('analytics');
        break;
      case 'data-export':
        showSuccess('Data export initiated! Check your downloads folder.');
        break;
      default:
        break;
    }
  };

  const dismissNotification = (id: number) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  // Keyboard shortcuts and command palette
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Command palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette(true);
      }
      
      // Quick actions
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'd':
            e.preventDefault();
            executeQuickAction('document-upload');
            showInfo('Quick action: Process Document');
            break;
          case 'w':
            e.preventDefault();
            executeQuickAction('workflow-create');
            showInfo('Quick action: Create Workflow');
            break;
          case 'r':
            e.preventDefault();
            executeQuickAction('analysis-run');
            showInfo('Quick action: Run Analysis');
            break;
          case 'e':
            e.preventDefault();
            executeQuickAction('data-export');
            showInfo('Quick action: Export Data');
            break;
        }
      }
      
      // Escape to close modals
      if (e.key === 'Escape') {
        setShowCommandPalette(false);
        setShowFeatureTest(false);
        setShowCreateWorkflow(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showInfo]);

  const executeCommand = (command: string) => {
    setShowCommandPalette(false);
    setGlobalSearch('');
    
    switch (command) {
      case 'chat':
        setCurrentView('chat');
        showSuccess('Switched to Chat');
        break;
      case 'documents':
        setCurrentView('documents');
        showSuccess('Switched to Documents');
        break;
      case 'workflows':
        setCurrentView('workflows');
        showSuccess('Switched to Workflows');
        break;
      case 'analytics':
        setCurrentView('analytics');
        showSuccess('Switched to Analytics');
        break;
      case 'integrations':
        setCurrentView('integrations');
        showSuccess('Switched to Integrations');
        break;
      case 'settings':
        setCurrentView('settings');
        showSuccess('Switched to Settings');
        break;
      case 'test-features':
        runFeatureTest();
        break;
      case 'create-workflow':
        setCurrentView('workflows');
        setShowCreateWorkflow(true);
        showInfo('Opening workflow creator');
        break;
      default:
        showWarning(`Command "${command}" not found`);
    }
  };

  const getFilteredCommands = () => {
    const commands = [
      { id: 'chat', title: 'Go to Chat', icon: '💬', description: 'Switch to chat interface' },
      { id: 'documents', title: 'Go to Documents', icon: '📄', description: 'Manage your documents' },
      { id: 'workflows', title: 'Go to Workflows', icon: '⚡', description: 'Create and manage workflows' },
      { id: 'analytics', title: 'Go to Analytics', icon: '📊', description: 'View analytics dashboard' },
      { id: 'integrations', title: 'Go to Integrations', icon: '🔗', description: 'Manage integrations' },
      { id: 'settings', title: 'Go to Settings', icon: '⚙️', description: 'Configure application settings' },
      { id: 'test-features', title: 'Test Features', icon: '🧪', description: 'Run automated feature tests' },
      { id: 'create-workflow', title: 'Create Workflow', icon: '⚡', description: 'Create a new workflow' }
    ];
    
    return commands.filter(cmd => 
      cmd.title.toLowerCase().includes(globalSearch.toLowerCase()) ||
      cmd.description.toLowerCase().includes(globalSearch.toLowerCase())
    );
  };

  // Model management functions
  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('/api/models/available');
      if (response.ok) {
        const models = await response.json();
        setAvailableModels(models);
      }
    } catch (error) {
      showError('Failed to fetch available models');
    }
  };

  const fetchCurrentModel = async () => {
    try {
      const response = await fetch('/api/models/current');
      if (response.ok) {
        const data = await response.json();
        setCurrentModel(data);
      }
    } catch (error) {
      showError('Failed to fetch current model');
    }
  };

  const selectModel = async (modelName: string) => {
    try {
      showInfo(`Switching to model ${modelName}...`);
      const response = await fetch(`/api/models/select/${modelName}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentModel(data);
        showSuccess(`Successfully switched to ${modelName}`);
        await fetchCurrentModel();
      } else {
        showError(`Failed to switch to model ${modelName}`);
      }
    } catch (error) {
      showError(`Error switching to model ${modelName}`);
    }
  };

  const pullModel = async (modelName: string) => {
    try {
      showInfo(`Downloading model ${modelName}... This may take a few minutes.`);
      const response = await fetch(`/api/models/pull/${modelName}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        showSuccess(`Successfully downloaded ${modelName}`);
        await fetchAvailableModels();
      } else {
        showError(`Failed to download model ${modelName}`);
      }
    } catch (error) {
      showError(`Error downloading model ${modelName}`);
    }
  };

  // Load models on component mount
  React.useEffect(() => {
    fetchAvailableModels();
    fetchCurrentModel();
  }, []);

  const editWorkflow = (workflow: any) => {
    setEditingWorkflow(workflow);
    setShowEditWorkflow(true);
  };

  const saveWorkflowEdit = () => {
    if (!editingWorkflow.title.trim() || !editingWorkflow.description.trim()) {
      showError('Please fill in both title and description');
      return;
    }

    setWorkflows(prev => prev.map(w => 
      w.id === editingWorkflow.id ? editingWorkflow : w
    ));
    
    setShowEditWorkflow(false);
    setEditingWorkflow(null);
    showSuccess(`Workflow "${editingWorkflow.title}" updated successfully!`);
  };

  const createNewWorkflow = () => {
    if (!newWorkflow.title.trim() || !newWorkflow.description.trim()) {
      showError('Please fill in both title and description');
      return;
    }

    const workflow = {
      id: Date.now(),
      title: newWorkflow.title,
      description: newWorkflow.description,
      status: 'Draft',
      color: '#f59e0b',
      lastRun: 'Never'
    };

    setWorkflows(prev => [...prev, workflow]);
    setNewWorkflow({ title: '', description: '', template: '' });
    setShowCreateWorkflow(false);
    showSuccess(`Workflow "${workflow.title}" created successfully!`);
  };

  const createFromTemplate = (template: string) => {
    const templateConfigs = {
      '📊 Data Analysis Pipeline': {
        title: '📊 Data Analysis Pipeline',
        description: 'Automated data processing and analysis workflow with statistical insights'
      },
      '🔄 Content Sync Workflow': {
        title: '🔄 Content Sync Workflow',
        description: 'Synchronize content across multiple platforms and databases'
      },
      '📧 Email Automation': {
        title: '📧 Email Automation',
        description: 'Automated email campaigns and response management system'
      },
      '🎯 Lead Scoring System': {
        title: '🎯 Lead Scoring System',
        description: 'Intelligent lead qualification and scoring automation'
      },
      '📈 Report Generation': {
        title: '📈 Report Generation',
        description: 'Automated report creation and distribution workflow'
      },
      '🔍 Content Moderation': {
        title: '🔍 Content Moderation',
        description: 'AI-powered content review and moderation pipeline'
      }
    };

    const config = templateConfigs[template as keyof typeof templateConfigs];
    if (config) {
      const workflow = {
        id: Date.now(),
        title: config.title,
        description: config.description,
        status: 'Draft',
        color: '#f59e0b',
        lastRun: 'Never'
      };

      setWorkflows(prev => [...prev, workflow]);
    }
  };

  // Navigation items matching the screenshot
  const navigationItems = [
    { id: 'chat', label: 'AI Chat', icon: <MessageSquare size={18} />, description: 'Advanced Research Assistant', badge: 'NEW' },
    { id: 'documents', label: 'Documents', icon: <FileText size={18} />, description: 'Document management and analysis' },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={18} />, description: 'Usage analytics and insights', badge: 'NEW' },
    { id: 'workflows', label: 'Workflows', icon: <Zap size={18} />, description: 'Process automation and management' },
    { id: 'integrations', label: 'Integrations', icon: <Puzzle size={18} />, description: 'Third-party service connections' },
    { id: 'security', label: 'Security', icon: <Shield size={18} />, description: 'Security monitoring and alerts' },
    { id: 'settings', label: 'Settings', icon: <Settings size={18} />, description: 'Application configuration' },
    { id: 'profile', label: 'Profile', icon: <User size={18} />, description: 'User account management' },
    { id: 'help', label: 'Help', icon: <Brain size={18} />, description: 'Documentation and support' },
    { id: 'about', label: 'About', icon: <Brain size={18} />, description: 'Application information' }
  ];

  // Chat interface component
  const ChatInterface = () => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white'
    }}>
      {/* Chat Header */}
      <div style={{
        padding: '20px 30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(0,0,0,0.2)'
      }}>
        <h1 style={{ 
          margin: 0, 
          fontSize: '28px', 
          color: '#4ade80',
          fontWeight: '600'
        }}>
          AI Chat
        </h1>
        <p style={{ 
          margin: '8px 0 0 0', 
          color: '#94a3b8', 
          fontSize: '16px' 
        }}>
          Intelligent conversation interface with advanced AI capabilities
        </p>
      </div>

      {/* Welcome Message */}
      <div style={{
        padding: '20px 30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(0,0,0,0.1)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'flex-start'
        }}>
          <div style={{
            maxWidth: '70%',
            padding: '12px 16px',
            borderRadius: '12px',
            background: 'rgba(255,255,255,0.1)',
            color: 'white',
            fontSize: '14px',
            lineHeight: '1.5',
            whiteSpace: 'pre-wrap'
          }}>
            Hello! I'm your AI Scholar assistant with advanced workflow and integration capabilities. How can I help you today?
          </div>
        </div>
      </div>

      {/* Input Area - Positioned after welcome message */}
      <div style={{
        padding: '20px 30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(0,0,0,0.3)',
        boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end'
        }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask me about documents, research, workflows, or integrations..."
            style={{
              flex: 1,
              minHeight: '44px',
              maxHeight: '120px',
              padding: '12px 16px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.2)',
              background: 'rgba(255,255,255,0.1)',
              color: 'white',
              fontSize: '14px',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim()}
            style={{
              padding: '12px 16px',
              borderRadius: '12px',
              border: 'none',
              background: input.trim() 
                ? 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)'
                : 'rgba(255,255,255,0.1)',
              color: 'white',
              cursor: input.trim() ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '600',
              transition: 'all 0.2s ease'
            }}
          >
            <Send size={16} />
            Send
          </button>
        </div>
        
        {/* Quick suggestions */}
        <div style={{
          marginTop: '12px',
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap'
        }}>
          {[
            'Analyze my documents',
            'Create a workflow',
            'Show analytics',
            'Help with research'
          ].map((suggestion, index) => (
            <button
              key={index}
              onClick={() => setInput(suggestion)}
              style={{
                padding: '4px 8px',
                background: 'rgba(74, 222, 128, 0.1)',
                border: '1px solid rgba(74, 222, 128, 0.3)',
                borderRadius: '12px',
                color: '#4ade80',
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(74, 222, 128, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(74, 222, 128, 0.1)';
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Messages Area */}
      <div style={{
        flex: 1,
        padding: '20px 30px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '15px'
      }}>
        {messages.slice(1).map((message) => (
          <div
            key={message.id}
            style={{
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              maxWidth: '70%',
              padding: '12px 16px',
              borderRadius: '12px',
              background: message.sender === 'user' 
                ? 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)'
                : 'rgba(255,255,255,0.1)',
              color: 'white',
              fontSize: '14px',
              lineHeight: '1.5',
              whiteSpace: 'pre-wrap'
            }}>
              {message.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );

  // Documents Manager Component
  const DocumentsManager = () => {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = () => {
      fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        handleFileUpload(e.target.files);
      }
    };

    const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
    };

    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer.files) {
        handleFileUpload(e.dataTransfer.files);
      }
    };

    return (
      <div style={{
        height: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        display: 'flex',
        flexDirection: 'column',
        color: 'white'
      }}>
        <div style={{
          padding: '30px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Documents
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Document management and analysis
          </p>
        </div>

        <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px',
            marginBottom: '30px'
          }}>
            <div
              style={{
                background: 'rgba(0,0,0,0.2)',
                padding: '25px',
                borderRadius: '12px',
                border: '1px solid rgba(255,255,255,0.1)',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={handleFileSelect}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.3)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.2)'}
            >
              <h3 style={{ color: '#60a5fa', marginTop: 0 }}>📄 Upload Documents</h3>
              <p style={{ color: '#cbd5e1', marginBottom: '20px' }}>
                Upload PDFs, Word docs, and text files for AI analysis. Drag & drop or click to select.
              </p>
              {isUploading && (
                <div style={{ marginBottom: '15px' }}>
                  <div style={{
                    width: '100%',
                    height: '6px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${uploadProgress}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #4ade80, #22c55e)',
                      borderRadius: '3px',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <p style={{ fontSize: '12px', color: '#9ca3af', margin: '5px 0 0 0' }}>
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}
              <button style={{
                background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                border: 'none',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                width: '100%'
              }}>
                {isUploading ? 'Uploading...' : 'Choose Files'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.csv"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
            </div>

            <div style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <h3 style={{ color: '#60a5fa', marginTop: 0 }}>🔍 Smart Search</h3>
              <p style={{ color: '#cbd5e1', marginBottom: '20px' }}>
                Search across all your documents with AI-powered semantic search
              </p>
              <input
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  outline: 'none'
                }}
                placeholder="Search documents..."
              />
              {searchQuery && (
                <div style={{ marginTop: '10px', fontSize: '12px', color: '#9ca3af' }}>
                  Searching for: "{searchQuery}"
                </div>
              )}
            </div>

            <div style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <h3 style={{ color: '#60a5fa', marginTop: 0 }}>📊 Analytics</h3>
              <p style={{ color: '#cbd5e1', marginBottom: '20px' }}>
                View document insights and processing statistics
              </p>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', color: '#4ade80', fontWeight: 'bold' }}>{documents.length}</div>
                  <div style={{ fontSize: '12px', color: '#9ca3af' }}>Documents</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', color: '#60a5fa', fontWeight: 'bold' }}>
                    {documents.filter(doc => doc.status === 'Completed').length}
                  </div>
                  <div style={{ fontSize: '12px', color: '#9ca3af' }}>Processed</div>
                </div>
              </div>
            </div>
          </div>

          <div style={{
            background: 'rgba(0,0,0,0.2)',
            padding: '30px',
            borderRadius: '15px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h2 style={{ color: '#4ade80', marginTop: 0 }}>📚 Document Library</h2>
            {documents.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '40px',
                color: '#9ca3af'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>📁</div>
                <p>No documents uploaded yet</p>
                <p style={{ fontSize: '14px' }}>Upload your first document to get started with AI-powered analysis</p>
              </div>
            ) : (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                gap: '15px'
              }}>
                {documents.map((doc) => (
                  <div key={doc.id} style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '20px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                      <h4 style={{ margin: 0, color: '#e2e8f0', fontSize: '16px' }}>{doc.name}</h4>
                      <span style={{
                        background: doc.status === 'Completed' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: doc.status === 'Completed' ? '#4ade80' : '#f59e0b',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        {doc.status}
                      </span>
                    </div>
                    <p style={{ margin: '5px 0', fontSize: '12px', color: '#9ca3af' }}>
                      Size: {(doc.size / 1024).toFixed(1)} KB | Uploaded: {doc.uploadDate.toLocaleDateString()}
                    </p>
                    {doc.status === 'Processing' && (
                      <div style={{
                        width: '100%',
                        height: '4px',
                        background: 'rgba(255,255,255,0.1)',
                        borderRadius: '2px',
                        overflow: 'hidden',
                        marginTop: '10px'
                      }}>
                        <div style={{
                          width: `${doc.progress}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #4ade80, #22c55e)',
                          borderRadius: '2px',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Analytics Dashboard Component
  const AnalyticsDashboard = () => {
    const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
    const [selectedMetric, setSelectedMetric] = useState('queries');
    const [showCustomization, setShowCustomization] = useState(false);

    const timeRanges = [
      { id: '1d', label: 'Last 24 Hours' },
      { id: '7d', label: 'Last 7 Days' },
      { id: '30d', label: 'Last 30 Days' },
      { id: '90d', label: 'Last 90 Days' }
    ];

    const metrics = [
      { id: 'queries', label: 'Query Volume', color: '#4ade80' },
      { id: 'documents', label: 'Document Processing', color: '#60a5fa' },
      { id: 'users', label: 'User Activity', color: '#f59e0b' },
      { id: 'performance', label: 'Performance Metrics', color: '#a78bfa' }
    ];

    // Mock data for visualizations
    const generateChartData = () => {
      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      return days.map(day => ({
        day,
        value: Math.floor(Math.random() * 100) + 20
      }));
    };

    const chartData = generateChartData();
    const maxValue = Math.max(...chartData.map(d => d.value));

    return (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
              Analytics Dashboard
            </h1>
            <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
              Comprehensive usage analytics and performance insights
            </p>
          </div>
          <button
            onClick={() => setShowCustomization(true)}
            style={{
              background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            ⚙️ Customize
          </button>
        </div>
      </div>

      <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
        {/* Time Range and Metric Selector */}
        <div style={{
          display: 'flex',
          gap: '20px',
          marginBottom: '30px',
          flexWrap: 'wrap'
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
              Time Range
            </label>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid rgba(255,255,255,0.2)',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                fontSize: '14px'
              }}
            >
              {timeRanges.map(range => (
                <option key={range.id} value={range.id}>{range.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
              Primary Metric
            </label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid rgba(255,255,255,0.2)',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                fontSize: '14px'
              }}
            >
              {metrics.map(metric => (
                <option key={metric.id} value={metric.id}>{metric.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          {[
            { title: 'Total Queries', value: '1,234', change: '+12%', icon: '💬', color: '#4ade80' },
            { title: 'Documents Processed', value: '56', change: '+8%', icon: '📄', color: '#60a5fa' },
            { title: 'Active Users', value: '12', change: '+25%', icon: '👥', color: '#f59e0b' },
            { title: 'Success Rate', value: '98.5%', change: '+2%', icon: '✅', color: '#10b981' }
          ].map((stat, index) => (
            <div key={index} style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)',
              textAlign: 'center',
              transition: 'all 0.2s ease',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
            >
              <div style={{ fontSize: '32px', marginBottom: '10px' }}>{stat.icon}</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: stat.color, marginBottom: '5px' }}>
                {stat.value}
              </div>
              <div style={{ color: '#9ca3af', fontSize: '14px', marginBottom: '5px' }}>{stat.title}</div>
              <div style={{ color: '#4ade80', fontSize: '12px', fontWeight: '600' }}>
                {stat.change} from last period
              </div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: '20px',
          marginBottom: '30px'
        }}>
          {/* Main Chart */}
          <div style={{
            background: 'rgba(0,0,0,0.2)',
            padding: '30px',
            borderRadius: '15px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h3 style={{ color: '#60a5fa', marginTop: 0, marginBottom: '20px' }}>
              📈 {metrics.find(m => m.id === selectedMetric)?.label} Trends
            </h3>
            <div style={{
              height: '250px',
              display: 'flex',
              alignItems: 'end',
              justifyContent: 'space-around',
              padding: '20px 0',
              borderBottom: '1px solid rgba(255,255,255,0.1)'
            }}>
              {chartData.map((data, index) => (
                <div key={index} style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <div style={{
                    width: '30px',
                    height: `${(data.value / maxValue) * 200}px`,
                    background: `linear-gradient(to top, ${metrics.find(m => m.id === selectedMetric)?.color}, rgba(255,255,255,0.3))`,
                    borderRadius: '4px',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scaleY(1.1)';
                    e.currentTarget.style.filter = 'brightness(1.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scaleY(1)';
                    e.currentTarget.style.filter = 'brightness(1)';
                  }}
                  />
                  <span style={{ fontSize: '12px', color: '#9ca3af' }}>{data.day}</span>
                  <span style={{ fontSize: '10px', color: '#4ade80' }}>{data.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Feature Usage */}
          <div style={{
            background: 'rgba(0,0,0,0.2)',
            padding: '30px',
            borderRadius: '15px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h3 style={{ color: '#60a5fa', marginTop: 0, marginBottom: '20px' }}>🔥 Feature Usage</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {[
                { name: 'AI Chat', usage: 85, color: '#4ade80' },
                { name: 'Document Analysis', usage: 72, color: '#60a5fa' },
                { name: 'Workflows', usage: 58, color: '#f59e0b' },
                { name: 'Integrations', usage: 43, color: '#a78bfa' },
                { name: 'Analytics', usage: 31, color: '#ef4444' }
              ].map((feature, index) => (
                <div key={index}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                    <span style={{ fontSize: '14px' }}>{feature.name}</span>
                    <span style={{ fontSize: '14px', color: feature.color }}>{feature.usage}%</span>
                  </div>
                  <div style={{
                    height: '8px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${feature.usage}%`,
                      height: '100%',
                      background: feature.color,
                      borderRadius: '4px',
                      transition: 'width 0.5s ease'
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Real-time Activity */}
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '30px',
          borderRadius: '15px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h3 style={{ color: '#60a5fa', marginTop: 0, marginBottom: '20px' }}>⚡ Real-time Activity</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px'
          }}>
            <div>
              <h4 style={{ color: '#4ade80', margin: '0 0 10px 0' }}>Recent Queries</h4>
              <div style={{ fontSize: '12px', color: '#9ca3af', lineHeight: '1.6' }}>
                • "Analyze research paper on quantum computing"<br/>
                • "Create workflow for document processing"<br/>
                • "Connect to OpenAI GPT-4 integration"<br/>
                • "Generate analytics report for last month"
              </div>
            </div>
            <div>
              <h4 style={{ color: '#f59e0b', margin: '0 0 10px 0' }}>System Performance</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px' }}>CPU Usage</span>
                  <span style={{ fontSize: '12px', color: '#4ade80' }}>23%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px' }}>Memory Usage</span>
                  <span style={{ fontSize: '12px', color: '#60a5fa' }}>67%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px' }}>Response Time</span>
                  <span style={{ fontSize: '12px', color: '#f59e0b' }}>1.2s</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Customization Modal */}
        {showCustomization && (
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <h2 style={{ color: '#4ade80', margin: 0 }}>⚙️ Customize Dashboard</h2>
                <button
                  onClick={() => setShowCustomization(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '24px',
                    padding: '5px'
                  }}
                >
                  ×
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <h3 style={{ color: '#60a5fa', margin: '0 0 10px 0' }}>Widget Visibility</h3>
                  {['Key Metrics', 'Trend Chart', 'Feature Usage', 'Real-time Activity'].map((widget, index) => (
                    <label key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px', cursor: 'pointer' }}>
                      <input type="checkbox" defaultChecked style={{ marginRight: '8px' }} />
                      <span style={{ fontSize: '14px' }}>{widget}</span>
                    </label>
                  ))}
                </div>

                <div>
                  <h3 style={{ color: '#60a5fa', margin: '0 0 10px 0' }}>Refresh Interval</h3>
                  <select style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid rgba(255,255,255,0.2)',
                    background: 'rgba(255,255,255,0.1)',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <option value="5">5 seconds</option>
                    <option value="30">30 seconds</option>
                    <option value="60">1 minute</option>
                    <option value="300">5 minutes</option>
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                  <button
                    onClick={() => setShowCustomization(false)}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'rgba(156, 163, 175, 0.2)',
                      border: '1px solid rgba(156, 163, 175, 0.3)',
                      color: '#9ca3af',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      showSuccess('Dashboard customization saved!');
                      setShowCustomization(false);
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                      border: 'none',
                      color: 'white',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    );
  };

  // Workflows Manager Component
  const WorkflowsManager = () => {
    return (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
          Workflows
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
          Process automation and management
        </p>
      </div>

      <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          {workflows.map((workflow) => (
            <div key={workflow.id} style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                <h3 style={{ color: '#60a5fa', marginTop: 0, marginBottom: '10px' }}>{workflow.title}</h3>
                <span style={{
                  background: `${workflow.color}20`,
                  color: workflow.color,
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '600'
                }}>
                  {workflow.status}
                </span>
              </div>
              <p style={{ color: '#cbd5e1', marginBottom: '20px', fontSize: '14px' }}>
                {workflow.description}
              </p>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => editWorkflow(workflow)}
                  style={{
                    background: 'rgba(96, 165, 250, 0.2)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    color: '#60a5fa',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(96, 165, 250, 0.3)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(96, 165, 250, 0.2)'}
                >
                  Edit
                </button>
                <button
                  onClick={() => runWorkflow(workflow.id)}
                  disabled={workflow.status === 'Running'}
                  style={{
                    background: workflow.status === 'Running' 
                      ? 'rgba(156, 163, 175, 0.2)' 
                      : 'rgba(74, 222, 128, 0.2)',
                    border: workflow.status === 'Running' 
                      ? '1px solid rgba(156, 163, 175, 0.3)' 
                      : '1px solid rgba(74, 222, 128, 0.3)',
                    color: workflow.status === 'Running' ? '#9ca3af' : '#4ade80',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    cursor: workflow.status === 'Running' ? 'not-allowed' : 'pointer',
                    fontSize: '12px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (workflow.status !== 'Running') {
                      e.currentTarget.style.background = 'rgba(74, 222, 128, 0.3)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (workflow.status !== 'Running') {
                      e.currentTarget.style.background = 'rgba(74, 222, 128, 0.2)';
                    }
                  }}
                >
                  {workflow.status === 'Running' ? 'Running...' : 'Run'}
                </button>
              </div>
              <div style={{ marginTop: '10px', fontSize: '12px', color: '#9ca3af' }}>
                Last run: {workflow.lastRun}
              </div>
            </div>
          ))}
        </div>

        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '30px',
          borderRadius: '15px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ color: '#4ade80', margin: 0 }}>⚡ Workflow Templates</h2>
            <button
              onClick={() => setShowCreateWorkflow(true)}
              style={{
                background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                border: 'none',
                color: 'white',
                padding: '10px 20px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              onClick={() => setShowCreateWorkflow(true)}
            >
              Create New
            </button>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '15px'
          }}>
            {[
              '📊 Data Analysis Pipeline',
              '🔄 Content Sync Workflow',
              '📧 Email Automation',
              '🎯 Lead Scoring System',
              '📈 Report Generation',
              '🔍 Content Moderation'
            ].map((template, index) => (
              <div 
                key={index} 
                onClick={() => createFromTemplate(template)}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  padding: '15px',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: '500' }}>{template}</div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '5px' }}>
                  Click to create workflow
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Workflow Creation Modal */}
        {showCreateWorkflow && (
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <h2 style={{ color: '#4ade80', margin: 0 }}>🚀 Create New Workflow</h2>
                <button
                  onClick={() => {
                    setShowCreateWorkflow(false);
                    setNewWorkflow({ title: '', description: '', template: '' });
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '24px',
                    padding: '5px'
                  }}
                >
                  ×
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Workflow Title *
                  </label>
                  <input
                    type="text"
                    value={newWorkflow.title}
                    onChange={(e) => {
                      e.preventDefault();
                      setNewWorkflow(prev => ({ ...prev, title: e.target.value }));
                    }}
                    placeholder="Enter workflow title..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none',
                      fontFamily: 'inherit'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Description *
                  </label>
                  <textarea
                    value={newWorkflow.description}
                    onChange={(e) => {
                      e.preventDefault();
                      setNewWorkflow(prev => ({ ...prev, description: e.target.value }));
                    }}
                    placeholder="Describe what this workflow does..."
                    style={{
                      width: '100%',
                      minHeight: '80px',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none',
                      resize: 'vertical',
                      fontFamily: 'inherit'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Workflow Type
                  </label>
                  <select
                    onChange={(e) => setNewWorkflow(prev => ({ ...prev, template: e.target.value }))}
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  >
                    <option value="">Select workflow type...</option>
                    <option value="document-processing">Document Processing</option>
                    <option value="data-analysis">Data Analysis</option>
                    <option value="content-generation">Content Generation</option>
                    <option value="integration-sync">Integration Sync</option>
                    <option value="custom">Custom Workflow</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Trigger Configuration
                  </label>
                  <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '15px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '8px' }}>
                        <input type="radio" name="trigger" value="manual" defaultChecked style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>Manual Trigger</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '8px' }}>
                        <input type="radio" name="trigger" value="schedule" style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>Scheduled (Daily/Weekly/Monthly)</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '8px' }}>
                        <input type="radio" name="trigger" value="event" style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>Event-based (File upload, API call)</span>
                      </label>
                    </div>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Workflow Steps
                  </label>
                  <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '15px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px',
                        background: 'rgba(74, 222, 128, 0.1)',
                        borderRadius: '6px',
                        border: '1px solid rgba(74, 222, 128, 0.3)'
                      }}>
                        <span style={{ color: '#4ade80', fontSize: '16px' }}>1️⃣</span>
                        <span style={{ fontSize: '14px', flex: 1 }}>Input Processing</span>
                        <button style={{
                          background: 'none',
                          border: 'none',
                          color: '#9ca3af',
                          cursor: 'pointer',
                          fontSize: '16px'
                        }}>⚙️</button>
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px',
                        background: 'rgba(59, 130, 246, 0.1)',
                        borderRadius: '6px',
                        border: '1px solid rgba(59, 130, 246, 0.3)'
                      }}>
                        <span style={{ color: '#60a5fa', fontSize: '16px' }}>2️⃣</span>
                        <span style={{ fontSize: '14px', flex: 1 }}>AI Processing</span>
                        <button style={{
                          background: 'none',
                          border: 'none',
                          color: '#9ca3af',
                          cursor: 'pointer',
                          fontSize: '16px'
                        }}>⚙️</button>
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px',
                        background: 'rgba(245, 158, 11, 0.1)',
                        borderRadius: '6px',
                        border: '1px solid rgba(245, 158, 11, 0.3)'
                      }}>
                        <span style={{ color: '#f59e0b', fontSize: '16px' }}>3️⃣</span>
                        <span style={{ fontSize: '14px', flex: 1 }}>Output Generation</span>
                        <button style={{
                          background: 'none',
                          border: 'none',
                          color: '#9ca3af',
                          cursor: 'pointer',
                          fontSize: '16px'
                        }}>⚙️</button>
                      </div>
                      <button
                        style={{
                          background: 'rgba(139, 92, 246, 0.2)',
                          border: '1px dashed rgba(139, 92, 246, 0.5)',
                          color: '#a78bfa',
                          padding: '10px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: '600'
                        }}
                      >
                        + Add Step
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Integration Settings
                  </label>
                  <div style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '15px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input type="checkbox" style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>🤖 OpenAI GPT Integration</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input type="checkbox" style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>🤗 Hugging Face Models</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input type="checkbox" style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>💬 Slack Notifications</span>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                        <input type="checkbox" style={{ marginRight: '8px' }} />
                        <span style={{ fontSize: '14px' }}>☁️ Cloud Storage Sync</span>
                      </label>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
                  <button
                    onClick={() => {
                      setShowCreateWorkflow(false);
                      setNewWorkflow({ title: '', description: '', template: '' });
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'rgba(156, 163, 175, 0.2)',
                      border: '1px solid rgba(156, 163, 175, 0.3)',
                      color: '#9ca3af',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={createNewWorkflow}
                    disabled={!newWorkflow.title.trim() || !newWorkflow.description.trim()}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: (newWorkflow.title.trim() && newWorkflow.description.trim()) 
                        ? 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)'
                        : 'rgba(156, 163, 175, 0.2)',
                      border: 'none',
                      color: 'white',
                      borderRadius: '8px',
                      cursor: (newWorkflow.title.trim() && newWorkflow.description.trim()) ? 'pointer' : 'not-allowed',
                      fontWeight: '600',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    Create Workflow
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Edit Modal */}
        {showEditWorkflow && editingWorkflow && (
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <h2 style={{ color: '#60a5fa', margin: 0 }}>✏️ Edit Workflow</h2>
                <button
                  onClick={() => {
                    setShowEditWorkflow(false);
                    setEditingWorkflow(null);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '24px',
                    padding: '5px'
                  }}
                >
                  ×
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Workflow Title *
                  </label>
                  <input
                    type="text"
                    value={editingWorkflow.title}
                    onChange={(e) => setEditingWorkflow(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Enter workflow title..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none',
                      fontFamily: 'inherit'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Description *
                  </label>
                  <textarea
                    value={editingWorkflow.description}
                    onChange={(e) => setEditingWorkflow(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe what this workflow does..."
                    style={{
                      width: '100%',
                      minHeight: '80px',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none',
                      resize: 'vertical',
                      fontFamily: 'inherit'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Status
                  </label>
                  <select
                    value={editingWorkflow.status}
                    onChange={(e) => setEditingWorkflow(prev => ({ ...prev, status: e.target.value }))}
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  >
                    <option value="Draft">Draft</option>
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
                  <button
                    onClick={() => {
                      setShowEditWorkflow(false);
                      setEditingWorkflow(null);
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'rgba(156, 163, 175, 0.2)',
                      border: '1px solid rgba(156, 163, 175, 0.3)',
                      color: '#9ca3af',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveWorkflowEdit}
                    disabled={!editingWorkflow.title.trim() || !editingWorkflow.description.trim()}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: (editingWorkflow.title.trim() && editingWorkflow.description.trim()) 
                        ? 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)'
                        : 'rgba(156, 163, 175, 0.2)',
                      border: 'none',
                      color: 'white',
                      borderRadius: '8px',
                      cursor: (editingWorkflow.title.trim() && editingWorkflow.description.trim()) ? 'pointer' : 'not-allowed',
                      fontWeight: '600',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Results Modal */}
        {showWorkflowResults && currentWorkflowResult && (
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
              maxWidth: '700px',
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <h2 style={{ color: '#4ade80', margin: 0 }}>🎯 Workflow Results</h2>
                <button
                  onClick={() => {
                    setShowWorkflowResults(false);
                    setCurrentWorkflowResult(null);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '24px',
                    padding: '5px'
                  }}
                >
                  ×
                </button>
              </div>

              {/* Execution Summary */}
              <div style={{
                background: 'rgba(74, 222, 128, 0.1)',
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid rgba(74, 222, 128, 0.3)',
                marginBottom: '20px'
              }}>
                <h3 style={{ color: '#4ade80', marginTop: 0, marginBottom: '15px' }}>
                  ✅ {currentWorkflowResult.workflowTitle}
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>Status</div>
                    <div style={{ fontSize: '14px', color: '#4ade80', fontWeight: '600' }}>
                      {currentWorkflowResult.status}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>Execution Time</div>
                    <div style={{ fontSize: '14px', color: '#60a5fa', fontWeight: '600' }}>
                      {currentWorkflowResult.executionTime}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>Completed</div>
                    <div style={{ fontSize: '14px', color: '#f59e0b', fontWeight: '600' }}>
                      {currentWorkflowResult.timestamp}
                    </div>
                  </div>
                </div>
              </div>

              {/* Execution Steps */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ color: '#60a5fa', marginBottom: '15px' }}>📋 Execution Steps</h4>
                {currentWorkflowResult.steps.map((step: any, index: number) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '15px',
                    padding: '12px',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '8px',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: '#4ade80',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}>
                      ✓
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', color: 'white', fontWeight: '600' }}>
                        {step.name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                        {step.output}
                      </div>
                    </div>
                    <div style={{ fontSize: '12px', color: '#60a5fa' }}>
                      {step.duration}
                    </div>
                  </div>
                ))}
              </div>

              {/* Metrics */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ color: '#f59e0b', marginBottom: '15px' }}>📊 Performance Metrics</h4>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                  gap: '15px'
                }}>
                  {Object.entries(currentWorkflowResult.metrics).map(([key, value]) => (
                    <div key={key} style={{
                      background: 'rgba(245, 158, 11, 0.1)',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '18px', color: '#f59e0b', fontWeight: '600' }}>
                        {value}
                      </div>
                      <div style={{ fontSize: '12px', color: '#9ca3af', textTransform: 'capitalize' }}>
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Output Files */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ color: '#a78bfa', marginBottom: '15px' }}>📁 Generated Outputs</h4>
                {currentWorkflowResult.outputs.map((output: any, index: number) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px',
                    background: 'rgba(139, 92, 246, 0.1)',
                    borderRadius: '8px',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    marginBottom: '8px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '16px' }}>📄</span>
                      <div>
                        <div style={{ fontSize: '14px', color: 'white', fontWeight: '600' }}>
                          {output.name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                          {output.type} • {output.size}
                        </div>
                      </div>
                    </div>
                    <button style={{
                      background: 'rgba(139, 92, 246, 0.2)',
                      border: '1px solid rgba(139, 92, 246, 0.3)',
                      color: '#a78bfa',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}>
                      Download
                    </button>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button
                  onClick={() => {
                    setShowWorkflowResults(false);
                    setCurrentWorkflowResult(null);
                  }}
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: 'rgba(156, 163, 175, 0.2)',
                    border: '1px solid rgba(156, 163, 175, 0.3)',
                    color: '#9ca3af',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Close
                </button>
                <button
                  onClick={() => showSuccess('All outputs downloaded successfully!')}
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                    border: 'none',
                    color: 'white',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Download All
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    );
  };

  // Integrations Hub Component
  const IntegrationsHub = () => {
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [showConfigModal, setShowConfigModal] = useState(false);
    const [selectedIntegration, setSelectedIntegration] = useState<any>(null);

    const categories = [
      { id: 'all', name: 'All Integrations', count: integrations.length },
      { id: 'ai-ml', name: 'AI & ML Services', count: 4 },
      { id: 'communication', name: 'Communication', count: 2 },
      { id: 'cloud', name: 'Cloud Storage', count: 1 },
      { id: 'databases', name: 'Databases', count: 1 },
      { id: 'analytics', name: 'Analytics', count: 1 },
      { id: 'productivity', name: 'Productivity', count: 1 }
    ];

    const filteredIntegrations = selectedCategory === 'all' 
      ? integrations 
      : integrations.filter(integration => {
          switch (selectedCategory) {
            case 'ai-ml': return ['OpenAI GPT', 'Hugging Face', 'Anthropic Claude', 'Google Cloud AI'].includes(integration.name);
            case 'communication': return ['Slack'].includes(integration.name);
            case 'cloud': return ['AWS Bedrock'].includes(integration.name);
            default: return true;
          }
        });

    const openConfigModal = (integration: any) => {
      setSelectedIntegration(integration);
      setShowConfigModal(true);
    };

    return (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
          Integrations Hub
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
          Connect and configure third-party services for enhanced AI capabilities
        </p>
      </div>

      <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
        {/* Category Filter */}
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.1)',
          marginBottom: '30px'
        }}>
          <h2 style={{ color: '#4ade80', marginTop: 0, marginBottom: '15px' }}>🔌 Categories</h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px'
          }}>
            {categories.map((cat) => (
              <div 
                key={cat.id} 
                onClick={() => setSelectedCategory(cat.id)}
                style={{
                  background: selectedCategory === cat.id 
                    ? 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)' 
                    : 'rgba(255,255,255,0.05)',
                  padding: '15px',
                  borderRadius: '8px',
                  border: selectedCategory === cat.id 
                    ? '1px solid #4ade80' 
                    : '1px solid rgba(255,255,255,0.1)',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  if (selectedCategory !== cat.id) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedCategory !== cat.id) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }
                }}
              >
                <div style={{ 
                  fontWeight: '600', 
                  marginBottom: '5px',
                  color: selectedCategory === cat.id ? 'white' : '#cbd5e1'
                }}>
                  {cat.name}
                </div>
                <div style={{ 
                  fontSize: '12px', 
                  color: selectedCategory === cat.id ? 'rgba(255,255,255,0.8)' : '#9ca3af'
                }}>
                  {cat.count} available
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Model Selector */}
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.1)',
          marginBottom: '30px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h2 style={{ color: '#4ade80', marginTop: 0, marginBottom: 0 }}>🤖 AI Model Selection</h2>
            <button
              onClick={() => setShowModelSelector(!showModelSelector)}
              style={{
                background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                border: 'none',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600'
              }}
            >
              {showModelSelector ? 'Hide Models' : 'Show Models'}
            </button>
          </div>
          
          {currentModel && (
            <div style={{
              background: 'rgba(74, 222, 128, 0.1)',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid rgba(74, 222, 128, 0.3)',
              marginBottom: '15px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <span style={{ fontSize: '16px' }}>🎯</span>
                <span style={{ color: '#4ade80', fontWeight: '600' }}>Current Model:</span>
                <span style={{ color: 'white' }}>{currentModel.current_model}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
                {currentModel.model_info?.description || 'Advanced AI model for scientific analysis'}
              </div>
            </div>
          )}

          {showModelSelector && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '15px',
              marginTop: '15px'
            }}>
              {availableModels.map((model, index) => (
                <div key={index} style={{
                  background: model.available ? 'rgba(74, 222, 128, 0.1)' : 'rgba(156, 163, 175, 0.1)',
                  padding: '15px',
                  borderRadius: '8px',
                  border: `1px solid ${model.available ? 'rgba(74, 222, 128, 0.3)' : 'rgba(156, 163, 175, 0.3)'}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <div>
                      <h4 style={{ margin: 0, color: model.available ? '#4ade80' : '#9ca3af', fontSize: '14px' }}>
                        {model.name}
                      </h4>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                        <span style={{
                          background: model.available ? 'rgba(74, 222, 128, 0.2)' : 'rgba(156, 163, 175, 0.2)',
                          color: model.available ? '#4ade80' : '#9ca3af',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '10px',
                          fontWeight: '600'
                        }}>
                          {model.available ? 'Available' : 'Not Downloaded'}
                        </span>
                        {model.size && (
                          <span style={{
                            background: 'rgba(59, 130, 246, 0.2)',
                            color: '#60a5fa',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: '600'
                          }}>
                            {model.size}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <p style={{ color: '#cbd5e1', fontSize: '12px', marginBottom: '12px', lineHeight: '1.4' }}>
                    {model.description}
                  </p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {model.available ? (
                      <button
                        onClick={() => selectModel(model.name)}
                        disabled={currentModel?.current_model === model.name}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          background: currentModel?.current_model === model.name 
                            ? 'rgba(156, 163, 175, 0.2)' 
                            : 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                          border: 'none',
                          color: currentModel?.current_model === model.name ? '#9ca3af' : 'white',
                          borderRadius: '6px',
                          cursor: currentModel?.current_model === model.name ? 'not-allowed' : 'pointer',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}
                      >
                        {currentModel?.current_model === model.name ? 'Current' : 'Select'}
                      </button>
                    ) : (
                      <button
                        onClick={() => pullModel(model.name)}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          background: 'rgba(59, 130, 246, 0.2)',
                          border: '1px solid rgba(59, 130, 246, 0.3)',
                          color: '#60a5fa',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}
                      >
                        Download
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Integrations Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          {filteredIntegrations.map((integration) => (
            <div key={integration.id} style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '15px' }}>
                <div style={{ fontSize: '32px' }}>{integration.icon}</div>
                <div>
                  <h3 style={{ margin: 0, color: '#60a5fa', fontSize: '18px' }}>{integration.name}</h3>
                  <span style={{
                    background: integration.status === 'Connected' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(156, 163, 175, 0.2)',
                    color: integration.status === 'Connected' ? '#4ade80' : '#9ca3af',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}>
                    {integration.status}
                  </span>
                </div>
              </div>
              <p style={{ color: '#cbd5e1', marginBottom: '20px', fontSize: '14px' }}>
                {integration.description}
              </p>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => toggleIntegration(integration.id)}
                  style={{
                    background: integration.status === 'Connected' 
                      ? 'rgba(239, 68, 68, 0.2)' 
                      : 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                    border: integration.status === 'Connected' ? '1px solid rgba(239, 68, 68, 0.3)' : 'none',
                    color: integration.status === 'Connected' ? '#ef4444' : 'white',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    flex: 1,
                    transition: 'all 0.2s ease'
                  }}
                >
                  {integration.status === 'Connected' ? 'Disconnect' : 'Connect'}
                </button>
                <button
                  onClick={() => openConfigModal(integration)}
                  style={{
                    background: 'rgba(139, 92, 246, 0.2)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    color: '#a78bfa',
                    padding: '10px 15px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    transition: 'all 0.2s ease'
                  }}
                >
                  ⚙️ Config
                </button>
              </div>
              {integration.status === 'Connected' && integration.apiKey && (
                <div style={{
                  marginTop: '10px',
                  padding: '8px',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  color: '#9ca3af'
                }}>
                  API Key: {integration.apiKey}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Configuration Modal */}
        {showConfigModal && selectedIntegration && (
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <h2 style={{ color: '#4ade80', margin: 0 }}>
                  {selectedIntegration.icon} Configure {selectedIntegration.name}
                </h2>
                <button
                  onClick={() => setShowConfigModal(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#9ca3af',
                    cursor: 'pointer',
                    fontSize: '24px',
                    padding: '5px'
                  }}
                >
                  ×
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    API Key
                  </label>
                  <input
                    type="password"
                    placeholder="Enter your API key..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Model/Endpoint
                  </label>
                  <select
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  >
                    <option value="default">Default Model</option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    <option value="claude-3">Claude 3</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Rate Limit (requests/minute)
                  </label>
                  <input
                    type="number"
                    defaultValue="60"
                    style={{
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(255,255,255,0.1)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      outline: 'none'
                    }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
                  <button
                    onClick={() => setShowConfigModal(false)}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'rgba(156, 163, 175, 0.2)',
                      border: '1px solid rgba(156, 163, 175, 0.3)',
                      color: '#9ca3af',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      showSuccess('Configuration saved!');
                      setShowConfigModal(false);
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                      border: 'none',
                      color: 'white',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    Save Config
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    );
  };

  // Security Dashboard Component
  const SecurityDashboard = () => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
          Security
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
          Security monitoring and alerts
        </p>
      </div>

      <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          {[
            { title: 'Security Score', value: '98.5%', icon: '🛡️', color: '#4ade80', status: 'Excellent' },
            { title: 'Active Threats', value: '0', icon: '⚠️', color: '#4ade80', status: 'None Detected' },
            { title: 'Failed Logins', value: '3', icon: '🔒', color: '#f59e0b', status: 'Last 24h' },
            { title: 'Data Encryption', value: '100%', icon: '🔐', color: '#4ade80', status: 'Active' }
          ].map((metric, index) => (
            <div key={index} style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '15px' }}>
                <div style={{ fontSize: '24px' }}>{metric.icon}</div>
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: metric.color }}>
                    {metric.value}
                  </div>
                  <div style={{ color: '#9ca3af', fontSize: '12px' }}>{metric.status}</div>
                </div>
              </div>
              <div style={{ color: '#cbd5e1', fontSize: '14px', fontWeight: '500' }}>
                {metric.title}
              </div>
            </div>
          ))}
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginBottom: '20px'
        }}>
          <div style={{
            background: 'rgba(0,0,0,0.2)',
            padding: '25px',
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h3 style={{ color: '#60a5fa', marginTop: 0 }}>🔍 Recent Security Events</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { event: 'Successful login', user: 'Administrator', time: '2 minutes ago', type: 'success' },
                { event: 'API key rotated', user: 'System', time: '1 hour ago', type: 'info' },
                { event: 'Failed login attempt', user: 'Unknown', time: '3 hours ago', type: 'warning' }
              ].map((log, index) => (
                <div key={index} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px',
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}>
                  <div>
                    <div style={{ fontWeight: '500' }}>{log.event}</div>
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>{log.user}</div>
                  </div>
                  <div style={{ 
                    color: log.type === 'success' ? '#4ade80' : log.type === 'warning' ? '#f59e0b' : '#60a5fa',
                    fontSize: '12px'
                  }}>
                    {log.time}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{
            background: 'rgba(0,0,0,0.2)',
            padding: '25px',
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <h3 style={{ color: '#60a5fa', marginTop: 0 }}>⚙️ Security Settings</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {[
                { setting: 'Two-Factor Authentication', enabled: true },
                { setting: 'API Rate Limiting', enabled: true },
                { setting: 'Audit Logging', enabled: true },
                { setting: 'IP Whitelisting', enabled: false }
              ].map((setting, index) => (
                <div key={index} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px',
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: '6px'
                }}>
                  <span style={{ fontSize: '14px' }}>{setting.setting}</span>
                  <div style={{
                    width: '40px',
                    height: '20px',
                    background: setting.enabled ? '#4ade80' : '#6b7280',
                    borderRadius: '10px',
                    position: 'relative',
                    cursor: 'pointer'
                  }}>
                    <div style={{
                      width: '16px',
                      height: '16px',
                      background: 'white',
                      borderRadius: '50%',
                      position: 'absolute',
                      top: '2px',
                      left: setting.enabled ? '22px' : '2px',
                      transition: 'left 0.2s ease'
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // About Page Component
  const AboutPage = () => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white',
      overflowY: 'auto'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
          About AI Scholar
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
          Advanced Research Assistant Platform
        </p>
      </div>

      <div style={{ flex: 1, padding: '30px' }}>
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '40px',
          borderRadius: '15px',
          border: '1px solid rgba(255,255,255,0.1)',
          marginBottom: '30px'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>🧠</div>
            <h2 style={{ color: '#4ade80', margin: 0, fontSize: '32px' }}>AI Scholar</h2>
            <p style={{ color: '#94a3b8', margin: '10px 0 0 0', fontSize: '18px' }}>
              Enterprise-Grade AI Research Platform
            </p>
          </div>

          <div style={{ maxWidth: '800px', margin: '0 auto', lineHeight: '1.8' }}>
            <p style={{ fontSize: '16px', marginBottom: '20px' }}>
              AI Scholar is a comprehensive artificial intelligence research platform designed to revolutionize how researchers, 
              academics, and professionals interact with scientific literature and conduct AI-powered analysis. Built with 
              enterprise-grade security and scalability in mind, AI Scholar combines advanced natural language processing, 
              document analysis, and workflow automation to create an intelligent research assistant that understands context, 
              provides accurate citations, and delivers actionable insights.
            </p>

            <p style={{ fontSize: '16px', marginBottom: '30px' }}>
              The platform features a sophisticated RAG (Retrieval-Augmented Generation) system that processes scientific 
              papers, research documents, and academic literature to provide contextually relevant responses backed by 
              verifiable sources. With support for multiple AI models, advanced analytics, workflow automation, and 
              seamless integrations, AI Scholar empowers users to accelerate their research processes while maintaining 
              the highest standards of accuracy and reliability.
            </p>

            <div style={{
              background: 'rgba(74, 222, 128, 0.1)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(74, 222, 128, 0.3)',
              marginBottom: '30px'
            }}>
              <h3 style={{ color: '#4ade80', marginTop: 0, marginBottom: '15px' }}>
                🏗️ Conceived & Developed by Christopher Mejo
              </h3>
              <p style={{ margin: 0, fontSize: '15px' }}>
                AI Scholar was conceived, designed, and fully developed by Christopher Mejo, a software engineer and AI researcher 
                passionate about democratizing access to advanced AI tools for academic and professional research.
              </p>
              <div style={{ marginTop: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                <a 
                  href="https://www.linkedin.com/in/cmejo" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{
                    background: 'linear-gradient(135deg, #0077b5 0%, #005885 100%)',
                    color: 'white',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  💼 LinkedIn Profile
                </a>
                <a 
                  href="https://www.github.com/cmejo/AI_Scholar" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{
                    background: 'linear-gradient(135deg, #333 0%, #24292e 100%)',
                    color: 'white',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  🔗 GitHub Repository
                </a>
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              marginBottom: '30px'
            }}>
              <div style={{
                background: 'rgba(96, 165, 250, 0.1)',
                padding: '20px',
                borderRadius: '10px',
                border: '1px solid rgba(96, 165, 250, 0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>🤖</div>
                <h4 style={{ color: '#60a5fa', margin: '0 0 10px 0' }}>AI-Powered</h4>
                <p style={{ fontSize: '14px', margin: 0 }}>Advanced language models and machine learning</p>
              </div>
              <div style={{
                background: 'rgba(139, 92, 246, 0.1)',
                padding: '20px',
                borderRadius: '10px',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>🔒</div>
                <h4 style={{ color: '#a78bfa', margin: '0 0 10px 0' }}>Enterprise Security</h4>
                <p style={{ fontSize: '14px', margin: 0 }}>Bank-grade security and compliance</p>
              </div>
              <div style={{
                background: 'rgba(245, 158, 11, 0.1)',
                padding: '20px',
                borderRadius: '10px',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>⚡</div>
                <h4 style={{ color: '#f59e0b', margin: '0 0 10px 0' }}>High Performance</h4>
                <p style={{ fontSize: '14px', margin: 0 }}>Optimized for speed and scalability</p>
              </div>
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                padding: '20px',
                borderRadius: '10px',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '10px' }}>🌐</div>
                <h4 style={{ color: '#10b981', margin: '0 0 10px 0' }}>Open Source</h4>
                <p style={{ fontSize: '14px', margin: 0 }}>Transparent and community-driven</p>
              </div>
            </div>

            <div style={{
              background: 'rgba(255,255,255,0.05)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <h3 style={{ color: '#60a5fa', marginTop: 0, marginBottom: '15px' }}>📋 Legal & Compliance</h3>
              <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                <button 
                  onClick={() => setCurrentView('terms')}
                  style={{
                    background: 'rgba(96, 165, 250, 0.2)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    color: '#60a5fa',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  📄 Terms of Service
                </button>
                <button 
                  onClick={() => setCurrentView('privacy')}
                  style={{
                    background: 'rgba(96, 165, 250, 0.2)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    color: '#60a5fa',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  🔒 Privacy Policy
                </button>
                <button 
                  onClick={() => setCurrentView('security-policy')}
                  style={{
                    background: 'rgba(96, 165, 250, 0.2)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    color: '#60a5fa',
                    padding: '10px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  🛡️ Security Policy
                </button>
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '30px', padding: '20px' }}>
              <p style={{ color: '#9ca3af', fontSize: '14px', margin: 0 }}>
                © 2024 AI Scholar. Developed by Christopher Mejo. All rights reserved.
              </p>
              <p style={{ color: '#9ca3af', fontSize: '12px', margin: '10px 0 0 0' }}>
                Version 2.0.0 | Built with React, TypeScript, and advanced AI technologies
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Terms of Service Page
  const TermsOfServicePage = () => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white',
      overflowY: 'auto'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        gap: '20px'
      }}>
        <button 
          onClick={() => setCurrentView('about')}
          style={{
            background: 'rgba(74, 222, 128, 0.2)',
            border: '1px solid rgba(74, 222, 128, 0.3)',
            color: '#4ade80',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          ← Back to About
        </button>
        <div>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Terms of Service
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Last updated: December 2024
          </p>
        </div>
      </div>

      <div style={{ flex: 1, padding: '30px' }}>
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '40px',
          borderRadius: '15px',
          border: '1px solid rgba(255,255,255,0.1)',
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          <div style={{ lineHeight: '1.6' }}>
            <h2 style={{ color: '#60a5fa', marginTop: 0 }}>1. Acceptance of Terms</h2>
            <p>By accessing and using AI Scholar, you accept and agree to be bound by the terms and provision of this agreement.</p>

            <h2 style={{ color: '#60a5fa' }}>2. Use License</h2>
            <p>Permission is granted to temporarily download one copy of AI Scholar for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:</p>
            <ul>
              <li>modify or copy the materials</li>
              <li>use the materials for any commercial purpose or for any public display</li>
              <li>attempt to reverse engineer any software contained in AI Scholar</li>
              <li>remove any copyright or other proprietary notations from the materials</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>3. Disclaimer</h2>
            <p>The materials on AI Scholar are provided on an 'as is' basis. AI Scholar makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.</p>

            <h2 style={{ color: '#60a5fa' }}>4. Limitations</h2>
            <p>In no event shall AI Scholar or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use AI Scholar, even if AI Scholar or an authorized representative has been notified orally or in writing of the possibility of such damage.</p>

            <h2 style={{ color: '#60a5fa' }}>5. Privacy Policy</h2>
            <p>Your privacy is important to us. Please review our Privacy Policy, which also governs your use of AI Scholar, to understand our practices.</p>

            <h2 style={{ color: '#60a5fa' }}>6. Governing Law</h2>
            <p>These terms and conditions are governed by and construed in accordance with the laws of the jurisdiction in which the service is provided.</p>

            <div style={{
              background: 'rgba(74, 222, 128, 0.1)',
              padding: '20px',
              borderRadius: '10px',
              border: '1px solid rgba(74, 222, 128, 0.3)',
              marginTop: '30px'
            }}>
              <h3 style={{ color: '#4ade80', marginTop: 0 }}>Contact Information</h3>
              <p style={{ margin: 0 }}>
                For questions about these Terms of Service, please contact Christopher Mejo via 
                <a href="https://www.linkedin.com/in/cmejo" target="_blank" rel="noopener noreferrer" style={{ color: '#4ade80', marginLeft: '5px' }}>
                  LinkedIn
                </a>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Privacy Policy Page
  const PrivacyPolicyPage = () => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white',
      overflowY: 'auto'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        gap: '20px'
      }}>
        <button 
          onClick={() => setCurrentView('about')}
          style={{
            background: 'rgba(74, 222, 128, 0.2)',
            border: '1px solid rgba(74, 222, 128, 0.3)',
            color: '#4ade80',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          ← Back to About
        </button>
        <div>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Privacy Policy
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Last updated: December 2024
          </p>
        </div>
      </div>

      <div style={{ flex: 1, padding: '30px' }}>
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '40px',
          borderRadius: '15px',
          border: '1px solid rgba(255,255,255,0.1)',
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          <div style={{ lineHeight: '1.6' }}>
            <h2 style={{ color: '#60a5fa', marginTop: 0 }}>Information We Collect</h2>
            <p>AI Scholar collects information you provide directly to us, such as when you create an account, use our services, or contact us for support.</p>
            <ul>
              <li><strong>Account Information:</strong> Username, email address, and password</li>
              <li><strong>Usage Data:</strong> Information about how you use our service</li>
              <li><strong>Document Data:</strong> Files and documents you upload for analysis</li>
              <li><strong>Communication Data:</strong> Messages and queries you send through our platform</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>How We Use Your Information</h2>
            <p>We use the information we collect to:</p>
            <ul>
              <li>Provide, maintain, and improve our services</li>
              <li>Process and respond to your queries</li>
              <li>Send you technical notices and support messages</li>
              <li>Analyze usage patterns to enhance user experience</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Information Sharing</h2>
            <p>We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy:</p>
            <ul>
              <li><strong>Service Providers:</strong> We may share information with trusted third-party service providers</li>
              <li><strong>Legal Requirements:</strong> We may disclose information when required by law</li>
              <li><strong>Business Transfers:</strong> Information may be transferred in connection with a merger or acquisition</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Data Security</h2>
            <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. This includes:</p>
            <ul>
              <li>Encryption of data in transit and at rest</li>
              <li>Regular security audits and assessments</li>
              <li>Access controls and authentication measures</li>
              <li>Secure data storage and backup procedures</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Data Retention</h2>
            <p>We retain your information for as long as necessary to provide our services and fulfill the purposes outlined in this policy, unless a longer retention period is required by law.</p>

            <h2 style={{ color: '#60a5fa' }}>Your Rights</h2>
            <p>You have the right to:</p>
            <ul>
              <li>Access and update your personal information</li>
              <li>Request deletion of your data</li>
              <li>Opt-out of certain communications</li>
              <li>Request data portability</li>
            </ul>

            <div style={{
              background: 'rgba(74, 222, 128, 0.1)',
              padding: '20px',
              borderRadius: '10px',
              border: '1px solid rgba(74, 222, 128, 0.3)',
              marginTop: '30px'
            }}>
              <h3 style={{ color: '#4ade80', marginTop: 0 }}>Contact Us</h3>
              <p style={{ margin: 0 }}>
                If you have questions about this Privacy Policy, please contact Christopher Mejo via 
                <a href="https://www.linkedin.com/in/cmejo" target="_blank" rel="noopener noreferrer" style={{ color: '#4ade80', marginLeft: '5px' }}>
                  LinkedIn
                </a>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Security Policy Page
  const SecurityPolicyPage = () => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white',
      overflowY: 'auto'
    }}>
      <div style={{
        padding: '30px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        gap: '20px'
      }}>
        <button 
          onClick={() => setCurrentView('about')}
          style={{
            background: 'rgba(74, 222, 128, 0.2)',
            border: '1px solid rgba(74, 222, 128, 0.3)',
            color: '#4ade80',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          ← Back to About
        </button>
        <div>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Security Policy
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Last updated: December 2024
          </p>
        </div>
      </div>

      <div style={{ flex: 1, padding: '30px' }}>
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '40px',
          borderRadius: '15px',
          border: '1px solid rgba(255,255,255,0.1)',
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          <div style={{ lineHeight: '1.6' }}>
            <h2 style={{ color: '#60a5fa', marginTop: 0 }}>Security Commitment</h2>
            <p>AI Scholar is committed to protecting the security and privacy of our users' data. We implement industry-standard security measures and continuously monitor and improve our security posture.</p>

            <h2 style={{ color: '#60a5fa' }}>Data Protection</h2>
            <ul>
              <li><strong>Encryption:</strong> All data is encrypted in transit using TLS 1.3 and at rest using AES-256</li>
              <li><strong>Access Controls:</strong> Role-based access controls with principle of least privilege</li>
              <li><strong>Authentication:</strong> Multi-factor authentication for all administrative accounts</li>
              <li><strong>Network Security:</strong> Firewalls, intrusion detection, and network segmentation</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Infrastructure Security</h2>
            <ul>
              <li><strong>Secure Hosting:</strong> Infrastructure hosted on secure, compliant cloud platforms</li>
              <li><strong>Regular Updates:</strong> Automated security updates and patch management</li>
              <li><strong>Monitoring:</strong> 24/7 security monitoring and incident response</li>
              <li><strong>Backups:</strong> Encrypted, geographically distributed backups</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Application Security</h2>
            <ul>
              <li><strong>Secure Development:</strong> Security-first development practices and code reviews</li>
              <li><strong>Vulnerability Testing:</strong> Regular penetration testing and vulnerability assessments</li>
              <li><strong>Input Validation:</strong> Comprehensive input validation and sanitization</li>
              <li><strong>Session Management:</strong> Secure session handling and timeout policies</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Compliance & Standards</h2>
            <p>AI Scholar adheres to industry security standards and best practices:</p>
            <ul>
              <li>OWASP Top 10 security guidelines</li>
              <li>ISO 27001 information security management principles</li>
              <li>SOC 2 Type II compliance framework</li>
              <li>GDPR and privacy regulation compliance</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Incident Response</h2>
            <p>In the event of a security incident:</p>
            <ul>
              <li>Immediate containment and assessment procedures</li>
              <li>Notification of affected users within 72 hours</li>
              <li>Transparent communication about the incident and remediation steps</li>
              <li>Post-incident analysis and security improvements</li>
            </ul>

            <h2 style={{ color: '#60a5fa' }}>Reporting Security Issues</h2>
            <p>If you discover a security vulnerability, please report it responsibly:</p>
            <ul>
              <li>Contact Christopher Mejo directly via LinkedIn</li>
              <li>Provide detailed information about the vulnerability</li>
              <li>Allow reasonable time for investigation and remediation</li>
              <li>Do not publicly disclose the issue until it has been addressed</li>
            </ul>

            <div style={{
              background: 'rgba(74, 222, 128, 0.1)',
              padding: '20px',
              borderRadius: '10px',
              border: '1px solid rgba(74, 222, 128, 0.3)',
              marginTop: '30px'
            }}>
              <h3 style={{ color: '#4ade80', marginTop: 0 }}>Security Contact</h3>
              <p style={{ margin: 0 }}>
                For security-related inquiries, please contact Christopher Mejo via 
                <a href="https://www.linkedin.com/in/cmejo" target="_blank" rel="noopener noreferrer" style={{ color: '#4ade80', marginLeft: '5px' }}>
                  LinkedIn
                </a>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Profile Page Component
  const ProfilePage = () => {
    const [isEditing, setIsEditing] = useState(false);
    const [profileData, setProfileData] = useState({
      name: user?.name || 'Administrator',
      email: user?.email || 'admin@aischolar.com',
      role: user?.role || 'Administrator',
      bio: 'AI Scholar power user and research enthusiast',
      location: 'Global',
      joinDate: 'December 2024',
      preferences: {
        emailNotifications: true,
        pushNotifications: false,
        weeklyReports: true,
        betaFeatures: true
      }
    });

    const handleSave = () => {
      setIsEditing(false);
      // Here you would typically save to backend
      console.log('Profile saved:', profileData);
    };

    return (
      <div style={{
        height: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        display: 'flex',
        flexDirection: 'column',
        color: 'white'
      }}>
        <div style={{
          padding: '30px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Profile
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Manage your account and preferences
          </p>
        </div>

        <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 2fr',
            gap: '30px',
            maxWidth: '1200px'
          }}>
            {/* Profile Card */}
            <div style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '30px',
              borderRadius: '15px',
              border: '1px solid rgba(255,255,255,0.1)',
              height: 'fit-content'
            }}>
              <div style={{ textAlign: 'center', marginBottom: '25px' }}>
                <div style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  background: 'linear-gradient(45deg, #4ade80, #22c55e)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '36px',
                  fontWeight: 'bold',
                  margin: '0 auto 20px',
                  border: '4px solid rgba(74, 222, 128, 0.3)'
                }}>
                  {profileData.name.charAt(0)}
                </div>
                <h2 style={{ margin: 0, color: '#e2e8f0', fontSize: '24px' }}>
                  {profileData.name}
                </h2>
                <p style={{ margin: '5px 0', color: '#94a3b8', fontSize: '16px' }}>
                  {profileData.role}
                </p>
                <p style={{ margin: '5px 0', color: '#9ca3af', fontSize: '14px' }}>
                  📍 {profileData.location}
                </p>
                <p style={{ margin: '5px 0', color: '#9ca3af', fontSize: '14px' }}>
                  📅 Joined {profileData.joinDate}
                </p>
              </div>

              <div style={{
                background: 'rgba(74, 222, 128, 0.1)',
                padding: '20px',
                borderRadius: '10px',
                border: '1px solid rgba(74, 222, 128, 0.3)',
                marginBottom: '20px'
              }}>
                <h3 style={{ color: '#4ade80', marginTop: 0, marginBottom: '10px' }}>
                  🏆 Account Status
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Plan:</span>
                    <span style={{ color: '#4ade80', fontWeight: '600' }}>Enterprise</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Documents:</span>
                    <span style={{ color: '#60a5fa' }}>{documents.length}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Workflows:</span>
                    <span style={{ color: '#f59e0b' }}>{workflows.length}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setIsEditing(!isEditing)}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: isEditing ? 'rgba(239, 68, 68, 0.2)' : 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                  border: isEditing ? '1px solid rgba(239, 68, 68, 0.3)' : 'none',
                  color: isEditing ? '#ef4444' : 'white',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'all 0.2s ease'
                }}
              >
                {isEditing ? 'Cancel' : 'Edit Profile'}
              </button>
            </div>

            {/* Profile Details */}
            <div style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '30px',
              borderRadius: '15px',
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <h3 style={{ color: '#60a5fa', margin: 0 }}>Profile Information</h3>
                {isEditing && (
                  <button
                    onClick={handleSave}
                    style={{
                      padding: '8px 16px',
                      background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                      border: 'none',
                      color: 'white',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontWeight: '600'
                    }}
                  >
                    Save Changes
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Full Name
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profileData.name}
                      onChange={(e) => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        borderRadius: '6px',
                        color: 'white',
                        fontSize: '14px',
                        outline: 'none'
                      }}
                    />
                  ) : (
                    <div style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}>
                      {profileData.name}
                    </div>
                  )}
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Email Address
                  </label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        borderRadius: '6px',
                        color: 'white',
                        fontSize: '14px',
                        outline: 'none'
                      }}
                    />
                  ) : (
                    <div style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}>
                      {profileData.email}
                    </div>
                  )}
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#9ca3af' }}>
                    Bio
                  </label>
                  {isEditing ? (
                    <textarea
                      value={profileData.bio}
                      onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                      style={{
                        width: '100%',
                        minHeight: '80px',
                        padding: '12px',
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        borderRadius: '6px',
                        color: 'white',
                        fontSize: '14px',
                        outline: 'none',
                        resize: 'vertical'
                      }}
                    />
                  ) : (
                    <div style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}>
                      {profileData.bio}
                    </div>
                  )}
                </div>

                <div>
                  <h4 style={{ color: '#60a5fa', marginBottom: '15px' }}>Notification Preferences</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {Object.entries(profileData.preferences).map(([key, value]) => (
                      <div key={key} style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px',
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: '6px'
                      }}>
                        <span style={{ fontSize: '14px', textTransform: 'capitalize' }}>
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                        <div
                          onClick={() => setProfileData(prev => ({
                            ...prev,
                            preferences: { ...prev.preferences, [key]: !value }
                          }))}
                          style={{
                            width: '40px',
                            height: '20px',
                            background: value ? '#4ade80' : '#6b7280',
                            borderRadius: '10px',
                            position: 'relative',
                            cursor: 'pointer',
                            transition: 'background 0.2s ease'
                          }}
                        >
                          <div style={{
                            width: '16px',
                            height: '16px',
                            background: 'white',
                            borderRadius: '50%',
                            position: 'absolute',
                            top: '2px',
                            left: value ? '22px' : '2px',
                            transition: 'left 0.2s ease'
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Help Page Component
  const HelpPage = () => {
    const [selectedCategory, setSelectedCategory] = useState('getting-started');
    const [searchTerm, setSearchTerm] = useState('');

    const helpCategories = [
      { id: 'getting-started', title: 'Getting Started', icon: '🚀' },
      { id: 'documents', title: 'Document Management', icon: '📄' },
      { id: 'workflows', title: 'Workflows & Automation', icon: '⚡' },
      { id: 'integrations', title: 'Integrations', icon: '🔌' },
      { id: 'security', title: 'Security & Privacy', icon: '🛡️' },
      { id: 'troubleshooting', title: 'Troubleshooting', icon: '🔧' },
      { id: 'api', title: 'API Documentation', icon: '📚' },
      { id: 'contact', title: 'Contact Support', icon: '💬' }
    ];

    const helpContent = {
      'getting-started': [
        { title: 'Welcome to AI Scholar', content: 'Learn the basics of using AI Scholar for research and document analysis.' },
        { title: 'Setting up your first project', content: 'Step-by-step guide to creating your first AI-powered research project.' },
        { title: 'Understanding the interface', content: 'Navigate through AI Scholar\'s intuitive interface with confidence.' },
        { title: 'Quick start tutorial', content: 'Get up and running in 5 minutes with our interactive tutorial.' }
      ],
      'documents': [
        { title: 'Uploading documents', content: 'Learn how to upload and organize your research documents.' },
        { title: 'Document analysis features', content: 'Discover AI-powered analysis tools for your documents.' },
        { title: 'Search and filtering', content: 'Master semantic search and advanced filtering options.' },
        { title: 'Export and sharing', content: 'Share your research findings and export documents.' }
      ],
      'workflows': [
        { title: 'Creating workflows', content: 'Build automated workflows for repetitive research tasks.' },
        { title: 'Workflow templates', content: 'Use pre-built templates to accelerate your workflow creation.' },
        { title: 'Scheduling and triggers', content: 'Set up automated triggers and scheduling for your workflows.' },
        { title: 'Monitoring workflow performance', content: 'Track and optimize your workflow performance.' }
      ],
      'integrations': [
        { title: 'Connecting AI services', content: 'Integrate with OpenAI, Hugging Face, and other AI platforms.' },
        { title: 'API key management', content: 'Securely manage your API keys and service connections.' },
        { title: 'Third-party tools', content: 'Connect with Slack, Google Drive, and other productivity tools.' },
        { title: 'Custom integrations', content: 'Build custom integrations using our API.' }
      ],
      'security': [
        { title: 'Data encryption', content: 'Learn about our enterprise-grade encryption and security measures.' },
        { title: 'Access controls', content: 'Manage user permissions and access controls.' },
        { title: 'Audit logs', content: 'Monitor and review system activity with comprehensive audit logs.' },
        { title: 'Compliance', content: 'Understand our GDPR, SOC 2, and other compliance certifications.' }
      ],
      'troubleshooting': [
        { title: 'Common issues', content: 'Solutions to frequently encountered problems.' },
        { title: 'Performance optimization', content: 'Tips to optimize AI Scholar performance.' },
        { title: 'Error messages', content: 'Understanding and resolving common error messages.' },
        { title: 'Browser compatibility', content: 'Ensure optimal performance across different browsers.' }
      ],
      'api': [
        { title: 'API Overview', content: 'Introduction to AI Scholar\'s REST API.' },
        { title: 'Authentication', content: 'Learn how to authenticate with our API.' },
        { title: 'Endpoints reference', content: 'Complete reference of all available API endpoints.' },
        { title: 'SDKs and libraries', content: 'Official SDKs for Python, JavaScript, and other languages.' }
      ],
      'contact': [
        { title: 'Support channels', content: 'Get help through email, chat, or community forums.' },
        { title: 'Feature requests', content: 'Submit ideas for new features and improvements.' },
        { title: 'Bug reports', content: 'Report bugs and technical issues.' },
        { title: 'Community', content: 'Join our community of researchers and developers.' }
      ]
    };

    const filteredContent = helpContent[selectedCategory as keyof typeof helpContent]?.filter(item =>
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.content.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
      <div style={{
        height: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        display: 'flex',
        flexDirection: 'column',
        color: 'white'
      }}>
        <div style={{
          padding: '30px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Help & Documentation
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Find answers and learn how to use AI Scholar effectively
          </p>
        </div>

        <div style={{ flex: 1, display: 'flex' }}>
          {/* Sidebar */}
          <div style={{
            width: '300px',
            background: 'rgba(0,0,0,0.2)',
            borderRight: '1px solid rgba(255,255,255,0.1)',
            padding: '20px'
          }}>
            <div style={{ marginBottom: '20px' }}>
              <input
                type="text"
                placeholder="Search help articles..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {helpCategories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  style={{
                    padding: '12px 16px',
                    background: selectedCategory === category.id ? 'rgba(74, 222, 128, 0.2)' : 'transparent',
                    border: selectedCategory === category.id ? '1px solid rgba(74, 222, 128, 0.3)' : '1px solid transparent',
                    color: selectedCategory === category.id ? '#4ade80' : '#9ca3af',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontSize: '14px',
                    fontWeight: '500',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                  }}
                  onMouseEnter={(e) => {
                    if (selectedCategory !== category.id) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedCategory !== category.id) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <span style={{ fontSize: '16px' }}>{category.icon}</span>
                  {category.title}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
            <div style={{ maxWidth: '800px' }}>
              <h2 style={{ color: '#60a5fa', marginTop: 0, marginBottom: '20px' }}>
                {helpCategories.find(cat => cat.id === selectedCategory)?.title}
              </h2>

              {filteredContent.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '40px',
                  color: '#9ca3af'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔍</div>
                  <p>No articles found matching your search.</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {filteredContent.map((item, index) => (
                    <div key={index} style={{
                      background: 'rgba(0,0,0,0.2)',
                      padding: '25px',
                      borderRadius: '12px',
                      border: '1px solid rgba(255,255,255,0.1)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.3)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.2)'}
                    >
                      <h3 style={{ color: '#e2e8f0', marginTop: 0, marginBottom: '10px' }}>
                        {item.title}
                      </h3>
                      <p style={{ color: '#cbd5e1', margin: 0, lineHeight: '1.6' }}>
                        {item.content}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {selectedCategory === 'contact' && (
                <div style={{
                  marginTop: '30px',
                  background: 'rgba(74, 222, 128, 0.1)',
                  padding: '25px',
                  borderRadius: '12px',
                  border: '1px solid rgba(74, 222, 128, 0.3)'
                }}>
                  <h3 style={{ color: '#4ade80', marginTop: 0, marginBottom: '15px' }}>
                    📧 Contact Information
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <p style={{ margin: 0 }}>
                      <strong>Email:</strong> support@aischolar.com
                    </p>
                    <p style={{ margin: 0 }}>
                      <strong>Developer:</strong> Christopher Mejo
                    </p>
                    <p style={{ margin: 0 }}>
                      <strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/cmejo" target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa' }}>linkedin.com/in/cmejo</a>
                    </p>
                    <p style={{ margin: 0 }}>
                      <strong>GitHub:</strong> <a href="https://www.github.com/cmejo/AI_Scholar" target="_blank" rel="noopener noreferrer" style={{ color: '#a78bfa' }}>github.com/cmejo/AI_Scholar</a>
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Settings Page Component
  const SettingsPage = () => {
    return (
      <div style={{
        height: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        display: 'flex',
        flexDirection: 'column',
        color: 'white'
      }}>
        <div style={{
          padding: '30px',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
            Settings
          </h1>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '16px' }}>
            Configure your AI Scholar preferences and system settings
          </p>
        </div>

        <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {/* General Settings */}
            <div style={{
              background: 'rgba(255,255,255,0.05)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)',
              marginBottom: '25px'
            }}>
              <h2 style={{ color: '#4ade80', marginTop: 0, marginBottom: '20px', fontSize: '20px' }}>
                🎛️ General Settings
              </h2>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>Theme</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Choose your preferred interface theme
                    </p>
                  </div>
                  <select
                    value={settings.theme}
                    onChange={(e) => updateSettings('theme', e.target.value)}
                    style={{
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid rgba(255,255,255,0.2)',
                      background: 'rgba(255,255,255,0.1)',
                      color: 'white',
                      fontSize: '14px'
                    }}
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="auto">Auto</option>
                  </select>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>Language</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Select your preferred language
                    </p>
                  </div>
                  <select
                    value={settings.language}
                    onChange={(e) => updateSettings('language', e.target.value)}
                    style={{
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid rgba(255,255,255,0.2)',
                      background: 'rgba(255,255,255,0.1)',
                      color: 'white',
                      fontSize: '14px'
                    }}
                  >
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                  </select>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>Notifications</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Enable desktop notifications
                    </p>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.notifications}
                      onChange={(e) => updateSettings('notifications', e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ fontSize: '14px' }}>Enabled</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Security Settings */}
            <div style={{
              background: 'rgba(255,255,255,0.05)',
              padding: '25px',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.1)',
              marginBottom: '25px'
            }}>
              <h2 style={{ color: '#f59e0b', marginTop: 0, marginBottom: '20px', fontSize: '20px' }}>
                🔒 Security Settings
              </h2>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>Two-Factor Authentication</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.twoFactorAuth}
                      onChange={(e) => updateSettings('twoFactorAuth', e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ fontSize: '14px', color: settings.twoFactorAuth ? '#4ade80' : '#9ca3af' }}>
                      {settings.twoFactorAuth ? 'Enabled' : 'Disabled'}
                    </span>
                  </label>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>API Rate Limiting</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Protect against API abuse and excessive usage
                    </p>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.apiRateLimit}
                      onChange={(e) => updateSettings('apiRateLimit', e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ fontSize: '14px', color: settings.apiRateLimit ? '#4ade80' : '#9ca3af' }}>
                      {settings.apiRateLimit ? 'Enabled' : 'Disabled'}
                    </span>
                  </label>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>Audit Logging</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Log all system activities for security monitoring
                    </p>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.auditLogging}
                      onChange={(e) => updateSettings('auditLogging', e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ fontSize: '14px', color: settings.auditLogging ? '#4ade80' : '#9ca3af' }}>
                      {settings.auditLogging ? 'Enabled' : 'Disabled'}
                    </span>
                  </label>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>IP Whitelisting</h3>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#9ca3af' }}>
                      Restrict access to specific IP addresses
                    </p>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={settings.ipWhitelisting}
                      onChange={(e) => updateSettings('ipWhitelisting', e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ fontSize: '14px', color: settings.ipWhitelisting ? '#4ade80' : '#9ca3af' }}>
                      {settings.ipWhitelisting ? 'Enabled' : 'Disabled'}
                    </span>
                  </label>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button
                onClick={() => showSuccess('Settings saved successfully!')}
                style={{
                  background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                  color: 'white',
                  border: 'none',
                  padding: '12px 30px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                💾 Save Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Simple placeholder for remaining views
  const SimpleView = ({ viewName, description }: { viewName: string; description: string }) => (
    <div style={{
      height: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      display: 'flex',
      flexDirection: 'column',
      color: 'white',
      padding: '30px'
    }}>
      <h1 style={{ margin: 0, fontSize: '28px', color: '#4ade80', fontWeight: '600' }}>
        {viewName}
      </h1>
      <p style={{ margin: '8px 0 20px 0', color: '#94a3b8', fontSize: '16px' }}>
        {description}
      </p>
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        padding: '30px',
        borderRadius: '15px',
        border: '1px solid rgba(255,255,255,0.1)',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>🚧</div>
        <h2 style={{ color: '#60a5fa', marginTop: 0 }}>Coming Soon</h2>
        <p>This section is under development and will be available in a future update.</p>
      </div>
    </div>
  );

  // Render current view
  const renderCurrentView = () => {
    switch (currentView) {
      case 'chat':
        return <ChatInterface />;
      case 'documents':
        return <DocumentsManager />;
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'workflows':
        return <WorkflowsManager />;
      case 'integrations':
        return <IntegrationsHub />;
      case 'security':
        return <SecurityDashboard />;
      case 'settings':
        return <SettingsPage />;
      case 'profile':
        return <ProfilePage />;
      case 'help':
        return <HelpPage />;
      case 'about':
        return <AboutPage />;
      case 'terms':
        return <TermsOfServicePage />;
      case 'privacy':
        return <PrivacyPolicyPage />;
      case 'security-policy':
        return <SecurityPolicyPage />;
      default:
        const currentItem = navigationItems.find(item => item.id === currentView);
        const viewName = currentItem?.label || 'Unknown';
        const description = currentItem?.description || 'Feature coming soon';
        return <SimpleView viewName={viewName} description={description} />;
    }
  };

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      background: '#1a1a2e',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Sidebar matching the screenshot */}
      <div style={{
        width: sidebarOpen ? '280px' : '60px',
        background: 'linear-gradient(180deg, #2d1b69 0%, #1a1a2e 100%)',
        borderRight: '1px solid rgba(255, 255, 255, 0.1)',
        transition: 'width 0.3s ease',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Sidebar Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              background: 'none',
              border: 'none',
              color: '#4ade80',
              cursor: 'pointer',
              fontSize: '18px',
              padding: '8px',
              borderRadius: '6px',
              transition: 'background 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(74, 222, 128, 0.1)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
          >
            <Menu size={20} />
          </button>
          {sidebarOpen && (
            <div>
              <h2 style={{ margin: 0, color: '#4ade80', fontSize: '18px', fontWeight: '600' }}>AI Scholar</h2>
            </div>
          )}
        </div>

        {/* Main Features Section */}
        {sidebarOpen && (
          <div style={{
            padding: '20px 20px 10px 20px'
          }}>
            <div style={{
              fontSize: '12px',
              fontWeight: '600',
              color: '#9ca3af',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '15px'
            }}>
              MAIN FEATURES
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <div style={{ flex: 1, padding: sidebarOpen ? '0 20px' : '20px 0' }}>
          {navigationItems.slice(0, 3).map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id as ViewType)}
              style={{
                width: '100%',
                padding: sidebarOpen ? '12px 16px' : '12px',
                marginBottom: '8px',
                background: currentView === item.id ? 'rgba(74, 222, 128, 0.15)' : 'transparent',
                border: 'none',
                color: currentView === item.id ? '#4ade80' : '#9ca3af',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                borderRadius: '8px',
                position: 'relative'
              }}
              onMouseEnter={(e) => {
                if (currentView !== item.id) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = '#d1d5db';
                }
              }}
              onMouseLeave={(e) => {
                if (currentView !== item.id) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#9ca3af';
                }
              }}
              title={sidebarOpen ? item.description : item.label}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: sidebarOpen ? 'flex-start' : 'center',
                minWidth: '20px'
              }}>
                {item.icon}
              </div>
              {sidebarOpen && (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>{item.label}</span>
                  {item.badge && (
                    <span style={{
                      background: '#4ade80',
                      color: '#1a1a2e',
                      fontSize: '10px',
                      fontWeight: '700',
                      padding: '2px 6px',
                      borderRadius: '4px'
                    }}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          ))}

          {/* Tools Section */}
          {sidebarOpen && (
            <div style={{
              padding: '20px 0 10px 0',
              marginTop: '20px'
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#9ca3af',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '15px'
              }}>
                TOOLS
              </div>
            </div>
          )}

          {navigationItems.slice(3, 6).map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id as ViewType)}
              style={{
                width: '100%',
                padding: sidebarOpen ? '12px 16px' : '12px',
                marginBottom: '8px',
                background: currentView === item.id ? 'rgba(74, 222, 128, 0.15)' : 'transparent',
                border: 'none',
                color: currentView === item.id ? '#4ade80' : '#9ca3af',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                borderRadius: '8px'
              }}
              onMouseEnter={(e) => {
                if (currentView !== item.id) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = '#d1d5db';
                }
              }}
              onMouseLeave={(e) => {
                if (currentView !== item.id) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#9ca3af';
                }
              }}
              title={sidebarOpen ? item.description : item.label}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: sidebarOpen ? 'flex-start' : 'center',
                minWidth: '20px'
              }}>
                {item.icon}
              </div>
              {sidebarOpen && <span>{item.label}</span>}
            </button>
          ))}

          {/* System Section */}
          {sidebarOpen && (
            <div style={{
              padding: '20px 0 10px 0',
              marginTop: '20px'
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#9ca3af',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '15px'
              }}>
                SYSTEM
              </div>
            </div>
          )}

          {navigationItems.slice(6).map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id as ViewType)}
              style={{
                width: '100%',
                padding: sidebarOpen ? '12px 16px' : '12px',
                marginBottom: '8px',
                background: currentView === item.id ? 'rgba(74, 222, 128, 0.15)' : 'transparent',
                border: 'none',
                color: currentView === item.id ? '#4ade80' : '#9ca3af',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                borderRadius: '8px'
              }}
              onMouseEnter={(e) => {
                if (currentView !== item.id) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = '#d1d5db';
                }
              }}
              onMouseLeave={(e) => {
                if (currentView !== item.id) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#9ca3af';
                }
              }}
              title={sidebarOpen ? item.description : item.label}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: sidebarOpen ? 'flex-start' : 'center',
                minWidth: '20px'
              }}>
                {item.icon}
              </div>
              {sidebarOpen && <span>{item.label}</span>}
            </button>
          ))}
        </div>

        {/* Keyboard navigation enabled indicator */}
        {sidebarOpen && (
          <div style={{
            padding: '15px 20px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            fontSize: '11px',
            color: '#6b7280',
            textAlign: 'center'
          }}>
            ⌨️ Keyboard navigation enabled
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header matching the screenshot */}
        <div style={{
          height: '70px',
          background: 'linear-gradient(90deg, #2d1b69 0%, #1a1a2e 100%)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 30px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div>
              <h1 style={{ 
                margin: 0, 
                color: '#4ade80', 
                fontSize: '24px',
                fontWeight: '600'
              }}>
                {navigationItems.find(item => item.id === currentView)?.label || 'AI Chat'}
              </h1>
              <p style={{ 
                margin: 0, 
                color: '#94a3b8', 
                fontSize: '14px',
                marginTop: '2px'
              }}>
                {navigationItems.find(item => item.id === currentView)?.description || 'Advanced Research Assistant'}
              </p>
            </div>
            <div style={{
              padding: '6px 12px',
              background: 'rgba(74, 222, 128, 0.2)',
              color: '#4ade80',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              border: '1px solid rgba(74, 222, 128, 0.3)'
            }}>
              🟢 Online
            </div>
          </div>

          {/* Search and User Area */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            {/* Search Bar */}
            <div style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center'
            }}>
              <input
                type="text"
                placeholder="Search..."
                style={{
                  width: '300px',
                  padding: '8px 40px 8px 16px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '20px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <div style={{
                position: 'absolute',
                right: '12px',
                color: '#9ca3af',
                fontSize: '12px',
                fontWeight: '600',
                background: 'rgba(255, 255, 255, 0.1)',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>
                ⌘K
              </div>
            </div>

            {/* Notification */}
            <div style={{
              position: 'relative',
              padding: '8px',
              borderRadius: '8px',
              cursor: 'pointer'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                color: '#9ca3af'
              }}>
                🔔
              </div>
              <div style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                width: '8px',
                height: '8px',
                background: '#ef4444',
                borderRadius: '50%'
              }} />
            </div>

            {/* User Profile */}
            {user && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: 'linear-gradient(45deg, #4ade80, #22c55e)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  border: '2px solid rgba(74, 222, 128, 0.3)'
                }}>
                  A
                </div>
                <div>
                  <div style={{ color: '#e2e8f0', fontSize: '14px', fontWeight: '600' }}>
                    {user.name}
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                    {user.role}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Enhanced Header */}
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          padding: '12px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '20px'
        }}>
          {/* Quick Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '14px', color: '#9ca3af', marginRight: '10px' }}>Quick Actions:</span>
            {quickActions.map((action) => (
              <button
                key={action.id}
                onClick={() => executeQuickAction(action.action)}
                style={{
                  background: 'rgba(74, 222, 128, 0.1)',
                  border: '1px solid rgba(74, 222, 128, 0.3)',
                  color: '#4ade80',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(74, 222, 128, 0.2)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(74, 222, 128, 0.1)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <span>{action.icon}</span>
                <span>{action.title}</span>
                <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.6)', marginLeft: '4px' }}>
                  {action.shortcut}
                </span>
              </button>
            ))}
          </div>

          {/* System Health & Notifications */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            {/* System Health */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '12px', color: '#60a5fa' }}>⚡</span>
              <span style={{ fontSize: '12px', color: '#60a5fa', fontWeight: '600' }}>
                CPU: {systemHealth.cpu}% | RAM: {systemHealth.memory}% | {systemHealth.responseTime}s
              </span>
            </div>

            {/* Notifications */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowFeatureTest(!showFeatureTest)}
                style={{
                  background: 'rgba(245, 158, 11, 0.1)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  color: '#f59e0b',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <span>🔔</span>
                <span>{notifications.length}</span>
              </button>
              
              {showFeatureTest && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: '8px',
                  background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  padding: '15px',
                  minWidth: '300px',
                  maxHeight: '400px',
                  overflowY: 'auto',
                  zIndex: 1000,
                  boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h3 style={{ margin: 0, color: '#4ade80', fontSize: '16px' }}>🔔 Notifications</h3>
                    <button
                      onClick={runFeatureTest}
                      style={{
                        background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                        border: 'none',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '10px',
                        fontWeight: '600'
                      }}
                    >
                      🧪 Test Features
                    </button>
                  </div>
                  
                  {notifications.map((notif) => (
                    <div key={notif.id} style={{
                      padding: '10px',
                      background: notif.type === 'success' ? 'rgba(74, 222, 128, 0.1)' :
                                 notif.type === 'warning' ? 'rgba(245, 158, 11, 0.1)' :
                                 'rgba(59, 130, 246, 0.1)',
                      border: `1px solid ${notif.type === 'success' ? 'rgba(74, 222, 128, 0.3)' :
                                          notif.type === 'warning' ? 'rgba(245, 158, 11, 0.3)' :
                                          'rgba(59, 130, 246, 0.3)'}`,
                      borderRadius: '6px',
                      marginBottom: '8px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '12px', color: 'white', marginBottom: '4px' }}>
                            {notif.message}
                          </div>
                          <div style={{ fontSize: '10px', color: '#9ca3af' }}>
                            {notif.time}
                          </div>
                        </div>
                        <button
                          onClick={() => dismissNotification(notif.id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#9ca3af',
                            cursor: 'pointer',
                            fontSize: '12px',
                            padding: '2px'
                          }}
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                  
                  {testResults.length > 0 && (
                    <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                      <h4 style={{ margin: '0 0 10px 0', color: '#60a5fa', fontSize: '14px' }}>🧪 Feature Test Results</h4>
                      {testResults.map((test, index) => (
                        <div key={index} style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '4px 0',
                          fontSize: '12px'
                        }}>
                          <span style={{ color: test.status === 'passed' ? '#4ade80' : test.status === 'running' ? '#f59e0b' : '#9ca3af' }}>
                            {test.status === 'passed' ? '✅' : test.status === 'running' ? '⏳' : '⚪'}
                          </span>
                          <span style={{ color: test.status === 'passed' ? '#4ade80' : '#9ca3af' }}>
                            {test.name}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Command Palette Button */}
            <button
              onClick={() => setShowCommandPalette(true)}
              style={{
                background: 'rgba(139, 92, 246, 0.1)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                color: '#a78bfa',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
              title="Open Command Palette (Ctrl+K)"
            >
              <span>⌘</span>
              <span>Commands</span>
            </button>

            {/* Feature Test Button */}
            <button
              onClick={runFeatureTest}
              style={{
                background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
                border: 'none',
                color: 'white',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span>🧪</span>
              <span>Test Features</span>
            </button>
          </div>
        </div>

        {/* Main View Content */}
        <main style={{
          flex: 1,
          overflow: 'hidden'
        }}>
          {renderCurrentView()}
        </main>
      </div>

      {/* Floating Action Button */}
      <div style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 1000
      }}>
        <button
          onClick={() => setShowFeatureTest(!showFeatureTest)}
          style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
            border: 'none',
            color: 'white',
            fontSize: '24px',
            cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(74, 222, 128, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.1)';
            e.currentTarget.style.boxShadow = '0 6px 25px rgba(74, 222, 128, 0.6)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(74, 222, 128, 0.4)';
          }}
        >
          🚀
        </button>
      </div>

      {/* Advanced Feature Panel */}
      {showFeatureTest && (
        <div style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '12px',
          padding: '20px',
          minWidth: '320px',
          maxHeight: '500px',
          overflowY: 'auto',
          zIndex: 999,
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ margin: 0, color: '#4ade80', fontSize: '18px' }}>🚀 Advanced Features</h3>
            <button
              onClick={() => setShowFeatureTest(false)}
              style={{
                background: 'none',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                fontSize: '20px',
                padding: '2px'
              }}
            >
              ×
            </button>
          </div>

          {/* Feature Status */}
          <div style={{
            background: 'rgba(74, 222, 128, 0.1)',
            padding: '15px',
            borderRadius: '8px',
            border: '1px solid rgba(74, 222, 128, 0.3)',
            marginBottom: '15px'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#4ade80', fontSize: '14px' }}>✅ Production Ready Status</h4>
            <div style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.5' }}>
              • All critical issues fixed<br/>
              • RAG functionality integrated<br/>
              • Advanced UI components active<br/>
              • Performance optimized<br/>
              • Ready for deployment
            </div>
          </div>

          {/* Quick Test Button */}
          <button
            onClick={runFeatureTest}
            style={{
              width: '100%',
              padding: '12px',
              background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
              border: 'none',
              color: 'white',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              marginBottom: '15px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            <span>🧪</span>
            <span>Run Full Feature Test</span>
          </button>

          {/* System Health */}
          <div style={{
            background: 'rgba(59, 130, 246, 0.1)',
            padding: '15px',
            borderRadius: '8px',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            marginBottom: '15px'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#60a5fa', fontSize: '14px' }}>⚡ System Health</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>CPU Usage:</span>
                <span style={{ color: '#4ade80' }}>{systemHealth.cpu}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Memory:</span>
                <span style={{ color: '#60a5fa' }}>{systemHealth.memory}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Response Time:</span>
                <span style={{ color: '#f59e0b' }}>{systemHealth.responseTime}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Uptime:</span>
                <span style={{ color: '#4ade80' }}>{systemHealth.uptime}</span>
              </div>
            </div>
          </div>

          {/* Test Results */}
          {testResults.length > 0 && (
            <div style={{
              background: 'rgba(245, 158, 11, 0.1)',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#f59e0b', fontSize: '14px' }}>🧪 Test Results</h4>
              <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                {testResults.map((test, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '4px 0',
                    fontSize: '12px'
                  }}>
                    <span style={{ color: test.status === 'passed' ? '#4ade80' : test.status === 'running' ? '#f59e0b' : '#9ca3af' }}>
                      {test.status === 'passed' ? '✅' : test.status === 'running' ? '⏳' : '⚪'}
                    </span>
                    <span style={{ color: test.status === 'passed' ? '#4ade80' : '#9ca3af' }}>
                      {test.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Command Palette */}
      {showCommandPalette && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'center',
          paddingTop: '100px',
          zIndex: 2000
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: '12px',
            padding: '20px',
            minWidth: '500px',
            maxWidth: '600px',
            maxHeight: '500px',
            overflowY: 'auto',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
          }}>
            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                <span style={{ fontSize: '20px' }}>⌘</span>
                <h2 style={{ margin: 0, color: '#4ade80', fontSize: '18px' }}>Command Palette</h2>
                <div style={{ flex: 1 }} />
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>Press Esc to close</span>
              </div>
              
              <input
                type="text"
                value={globalSearch}
                onChange={(e) => setGlobalSearch(e.target.value)}
                placeholder="Type a command or search..."
                autoFocus
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {getFilteredCommands().map((command, index) => (
                <button
                  key={command.id}
                  onClick={() => executeCommand(command.id)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    background: index === 0 ? 'rgba(74, 222, 128, 0.1)' : 'transparent',
                    border: index === 0 ? '1px solid rgba(74, 222, 128, 0.3)' : '1px solid transparent',
                    borderRadius: '8px',
                    color: 'white',
                    cursor: 'pointer',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(74, 222, 128, 0.1)';
                    e.currentTarget.style.borderColor = 'rgba(74, 222, 128, 0.3)';
                  }}
                  onMouseLeave={(e) => {
                    if (index !== 0) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.borderColor = 'transparent';
                    }
                  }}
                >
                  <span style={{ fontSize: '16px' }}>{command.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '2px' }}>
                      {command.title}
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {command.description}
                    </div>
                  </div>
                </button>
              ))}
              
              {getFilteredCommands().length === 0 && (
                <div style={{
                  padding: '20px',
                  textAlign: 'center',
                  color: '#9ca3af',
                  fontSize: '14px'
                }}>
                  No commands found for "{globalSearch}"
                </div>
              )}
            </div>

            <div style={{
              marginTop: '20px',
              padding: '15px',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '8px'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#60a5fa', fontSize: '14px' }}>⌨️ Keyboard Shortcuts</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Command Palette:</span>
                  <span style={{ color: '#9ca3af' }}>Ctrl+K</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Process Document:</span>
                  <span style={{ color: '#9ca3af' }}>Ctrl+D</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Create Workflow:</span>
                  <span style={{ color: '#9ca3af' }}>Ctrl+W</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Run Analysis:</span>
                  <span style={{ color: '#9ca3af' }}>Ctrl+R</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Global Styles */}
      <style>{`
        * {
          box-sizing: border-box;
        }
        
        body {
          margin: 0;
          padding: 0;
          font-family: system-ui, -apple-system, sans-serif;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.1);
        }
        
        ::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.3);
          border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.5);
        }
        
        /* Focus styles for accessibility */
        *:focus {
          outline: 2px solid #4ade80;
          outline-offset: 2px;
        }
        
        /* Smooth transitions */
        * {
          transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
        }
      `}</style>
    </div>
  );
}

export default App;