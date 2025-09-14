/**
 * WorkflowIntegrationHub - Unified hub for workflows and integrations with AI chatbot integration
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Workflow, Plug, Bot, MessageSquare, Sparkles, Zap, Settings, Plus, Search,
  Filter, Grid, List, ChevronDown, ChevronUp, Play, Pause, Edit, Trash2,
  Eye, Download, Copy, Share2, RefreshCw, AlertCircle, CheckCircle,
  Clock, TrendingUp, Users, Star, Bookmark, BookmarkCheck, Target,
  Brain, Wand2, Code, Database, Cloud, Mail, Webhook
} from 'lucide-react';
import { WorkflowTemplateManager } from './workflow/WorkflowTemplateManager';
import { IntegrationCatalog } from './integration/IntegrationCatalog';
import type { WorkflowTemplate, WorkflowDefinition } from '../types/workflow';
import type { IntegrationCatalogItem, Integration } from '../types/integration';
import { workflowManagementService } from '../services/workflowManagementService';
import { integrationManagementService } from '../services/integrationManagementService';

export interface WorkflowIntegrationHubProps {
  onChatMessage?: (message: string, context?: any) => void;
  onShowChat?: () => void;
}

type TabType = 'overview' | 'workflows' | 'integrations' | 'ai-assistant' | 'templates';

interface HubStats {
  workflows: {
    total: number;
    active: number;
    templates: number;
    aiPowered: number;
  };
  integrations: {
    total: number;
    connected: number;
    available: number;
    aiPowered: number;
  };
  activity: {
    recentExecutions: number;
    successRate: number;
    avgResponseTime: number;
  };
}

export const WorkflowIntegrationHub: React.FC<WorkflowIntegrationHubProps> = ({
  onChatMessage,
  onShowChat
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Data state
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [catalogItems, setCatalogItems] = useState<IntegrationCatalogItem[]>([]);
  const [stats, setStats] = useState<HubStats | null>(null);

  // AI Assistant state
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);

  // Load all data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [
        workflowsData,
        integrationsData,
        templatesData,
        catalogData,
        workflowStats,
        integrationStats
      ] = await Promise.all([
        workflowManagementService.getWorkflows(1, 50),
        integrationManagementService.getIntegrations(),
        workflowManagementService.getWorkflowTemplates(),
        integrationManagementService.getIntegrationCatalog(),
        workflowManagementService.getWorkflowStats(),
        integrationManagementService.getIntegrationStats()
      ]);

      setWorkflows(workflowsData.data);
      setIntegrations(integrationsData);
      setTemplates(templatesData);
      setCatalogItems(catalogData);

      // Calculate combined stats
      const hubStats: HubStats = {
        workflows: {
          total: workflowStats.totalWorkflows,
          active: workflowStats.activeWorkflows,
          templates: templatesData.length,
          aiPowered: templatesData.filter(t => t.tags.includes('ai') || t.tags.includes('chatbot')).length
        },
        integrations: {
          total: integrationStats.totalIntegrations,
          connected: integrationStats.connectedIntegrations,
          available: catalogData.length,
          aiPowered: catalogData.filter(i => i.tags.includes('ai') || i.tags.includes('chatbot')).length
        },
        activity: {
          recentExecutions: workflowStats.executionsToday,
          successRate: (workflowStats.successfulExecutions / workflowStats.totalExecutions) * 100,
          avgResponseTime: workflowStats.averageExecutionTime * 1000 // Convert to ms
        }
      };

      setStats(hubStats);
      generateAISuggestions(hubStats);
      setError(null);
    } catch (err) {
      setError('Failed to load workflow and integration data');
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Generate AI suggestions based on current state
  const generateAISuggestions = (hubStats: HubStats) => {
    const suggestions = [];

    if (hubStats.workflows.aiPowered === 0) {
      suggestions.push("🤖 Try creating an AI-powered workflow to automate your research tasks");
    }

    if (hubStats.integrations.aiPowered === 0) {
      suggestions.push("🔌 Connect AI services like OpenAI or Anthropic to enhance your workflows");
    }

    if (hubStats.activity.successRate < 90) {
      suggestions.push("⚡ Let me help optimize your workflows for better success rates");
    }

    if (hubStats.workflows.total === 0) {
      suggestions.push("🚀 Start with a template! I can recommend the best AI workflow for your needs");
    }

    if (hubStats.integrations.connected < 3) {
      suggestions.push("🌟 Connect more services to unlock powerful automation possibilities");
    }

    suggestions.push("💡 Ask me anything about workflows, integrations, or AI automation!");

    setAiSuggestions(suggestions);
  };

  // Handle workflow template actions
  const handleTemplateSelect = (template: WorkflowTemplate) => {
    if (onChatMessage) {
      onChatMessage(
        `I'd like to learn more about the "${template.name}" workflow template. Can you explain how it works and help me set it up?`,
        { type: 'workflow_template', template }
      );
      onShowChat?.();
    }
  };

  const handleCreateFromTemplate = (template: WorkflowTemplate) => {
    if (onChatMessage) {
      onChatMessage(
        `Please help me create a new workflow based on the "${template.name}" template. Guide me through the configuration process.`,
        { type: 'create_workflow', template }
      );
      onShowChat?.();
    }
  };

  const handleWorkflowChatIntegration = (template: WorkflowTemplate, action: string) => {
    if (onChatMessage) {
      const messages = {
        discuss: `Let's discuss the "${template.name}" workflow template. What are its key features and benefits?`,
        optimize: `How can I optimize the "${template.name}" workflow for better performance?`,
        customize: `Help me customize the "${template.name}" template for my specific needs.`
      };
      
      onChatMessage(
        messages[action as keyof typeof messages] || messages.discuss,
        { type: 'workflow_chat', template, action }
      );
      onShowChat?.();
    }
  };

  // Handle integration actions
  const handleInstallIntegration = (item: IntegrationCatalogItem) => {
    if (onChatMessage) {
      onChatMessage(
        `I want to install the "${item.name}" integration. Can you guide me through the setup process and explain what it can do?`,
        { type: 'install_integration', integration: item }
      );
      onShowChat?.();
    }
  };

  const handleIntegrationChatIntegration = (item: IntegrationCatalogItem, action: string) => {
    if (onChatMessage) {
      const messages = {
        discuss: `Tell me about the "${item.name}" integration. What features does it offer and how can it help my workflows?`,
        setup: `Help me set up the "${item.name}" integration step by step.`,
        troubleshoot: `I'm having issues with the "${item.name}" integration. Can you help troubleshoot?`
      };
      
      onChatMessage(
        messages[action as keyof typeof messages] || messages.discuss,
        { type: 'integration_chat', integration: item, action }
      );
      onShowChat?.();
    }
  };

  // Handle AI suggestions
  const handleAISuggestion = (suggestion: string) => {
    if (onChatMessage) {
      onChatMessage(suggestion);
      onShowChat?.();
    }
  };

  // Render overview tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Workflows</p>
                <p className="text-2xl font-bold">{stats.workflows.active}</p>
                <p className="text-xs text-purple-400">{stats.workflows.aiPowered} AI-powered</p>
              </div>
              <Workflow className="w-8 h-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Connected Integrations</p>
                <p className="text-2xl font-bold">{stats.integrations.connected}</p>
                <p className="text-xs text-blue-400">{stats.integrations.aiPowered} AI-enabled</p>
              </div>
              <Plug className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Success Rate</p>
                <p className="text-2xl font-bold">{stats.activity.successRate.toFixed(1)}%</p>
                <p className="text-xs text-green-400">Last 30 days</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Avg Response Time</p>
                <p className="text-2xl font-bold">{stats.activity.avgResponseTime.toFixed(0)}ms</p>
                <p className="text-xs text-yellow-400">Recent executions</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
        </div>
      )}

      {/* AI Assistant Panel */}
      <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Bot className="w-6 h-6 text-purple-400 mr-2" />
            <h3 className="text-lg font-semibold">AI Assistant</h3>
          </div>
          <button
            onClick={() => setAiAssistantOpen(!aiAssistantOpen)}
            className="flex items-center px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm"
          >
            <MessageSquare className="w-4 h-4 mr-1" />
            Chat
          </button>
        </div>

        <p className="text-gray-300 mb-4">
          I can help you create workflows, set up integrations, and optimize your automation processes.
        </p>

        {/* AI Suggestions */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-400">Suggestions for you:</h4>
          {aiSuggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleAISuggestion(suggestion)}
              className="block w-full text-left p-3 bg-gray-800/50 hover:bg-gray-700/50 rounded-lg text-sm transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Workflows */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center">
              <Workflow className="w-5 h-5 mr-2 text-purple-400" />
              Recent Workflows
            </h3>
            <button
              onClick={() => setActiveTab('workflows')}
              className="text-purple-400 hover:text-purple-300 text-sm"
            >
              View All
            </button>
          </div>

          <div className="space-y-3">
            {workflows.slice(0, 3).map(workflow => (
              <div key={workflow.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
                <div>
                  <p className="font-medium">{workflow.name}</p>
                  <p className="text-xs text-gray-400">{workflow.status}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {workflow.tags.includes('ai') && <Bot className="w-4 h-4 text-purple-400" />}
                  <button
                    onClick={() => handleWorkflowChatIntegration({ 
                      id: workflow.id, 
                      name: workflow.name, 
                      description: workflow.description,
                      category: 'Custom',
                      tags: workflow.tags,
                      popularity: 0,
                      isOfficial: false,
                      definition: workflow
                    }, 'discuss')}
                    className="p-1 hover:bg-gray-600 rounded"
                  >
                    <MessageSquare className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Integrations */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center">
              <Plug className="w-5 h-5 mr-2 text-blue-400" />
              Active Integrations
            </h3>
            <button
              onClick={() => setActiveTab('integrations')}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              View All
            </button>
          </div>

          <div className="space-y-3">
            {integrations.slice(0, 3).map(integration => (
              <div key={integration.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
                <div>
                  <p className="font-medium">{integration.name}</p>
                  <p className="text-xs text-gray-400">{integration.status}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {integration.status === 'connected' ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-red-400" />
                  )}
                  <button
                    onClick={() => handleIntegrationChatIntegration({
                      id: integration.id,
                      name: integration.name,
                      description: integration.description,
                      category: integration.category,
                      provider: 'Custom',
                      icon: 'custom',
                      type: integration.type,
                      features: [],
                      pricing: 'custom',
                      documentation: '',
                      setupComplexity: 'medium',
                      popularity: 0,
                      rating: 0,
                      reviews: 0,
                      tags: []
                    }, 'discuss')}
                    className="p-1 hover:bg-gray-600 rounded"
                  >
                    <MessageSquare className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Render AI Assistant tab
  const renderAIAssistant = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-8 border border-purple-500/20">
        <div className="text-center mb-8">
          <Bot className="w-16 h-16 text-purple-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">AI Workflow & Integration Assistant</h2>
          <p className="text-gray-300">
            I'm here to help you create, optimize, and manage your workflows and integrations using AI.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => handleAISuggestion("Help me create a new AI-powered workflow for document processing")}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
          >
            <Workflow className="w-6 h-6 text-purple-400 mb-2" />
            <h3 className="font-semibold mb-1">Create Workflow</h3>
            <p className="text-sm text-gray-400">Build AI-powered automation</p>
          </button>

          <button
            onClick={() => handleAISuggestion("Show me the best AI integrations for my research workflows")}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
          >
            <Plug className="w-6 h-6 text-blue-400 mb-2" />
            <h3 className="font-semibold mb-1">Find Integrations</h3>
            <p className="text-sm text-gray-400">Discover AI-powered services</p>
          </button>

          <button
            onClick={() => handleAISuggestion("Analyze my current workflows and suggest optimizations")}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
          >
            <TrendingUp className="w-6 h-6 text-green-400 mb-2" />
            <h3 className="font-semibold mb-1">Optimize Performance</h3>
            <p className="text-sm text-gray-400">Improve efficiency with AI</p>
          </button>

          <button
            onClick={() => handleAISuggestion("Help me troubleshoot workflow execution issues")}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
          >
            <Settings className="w-6 h-6 text-yellow-400 mb-2" />
            <h3 className="font-semibold mb-1">Troubleshoot</h3>
            <p className="text-sm text-gray-400">Fix issues with AI help</p>
          </button>

          <button
            onClick={() => handleAISuggestion("Explain how to use AI models in my workflows")}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
          >
            <Brain className="w-6 h-6 text-pink-400 mb-2" />
            <h3 className="font-semibold mb-1">AI Integration</h3>
            <p className="text-sm text-gray-400">Connect AI models</p>
          </button>

          <button
            onClick={() => handleAISuggestion("What are the best practices for workflow automation?")}
            className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
          >
            <Target className="w-6 h-6 text-orange-400 mb-2" />
            <h3 className="font-semibold mb-1">Best Practices</h3>
            <p className="text-sm text-gray-400">Learn automation tips</p>
          </button>
        </div>

        {/* Chat Interface Prompt */}
        <div className="text-center">
          <button
            onClick={() => {
              onChatMessage?.("Hi! I'd like help with workflows and integrations. What can you do for me?");
              onShowChat?.();
            }}
            className="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-colors"
          >
            <MessageSquare className="w-5 h-5 mr-2" />
            Start Conversation
          </button>
        </div>
      </div>

      {/* AI Suggestions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Sparkles className="w-5 h-5 mr-2 text-purple-400" />
          Personalized Suggestions
        </h3>
        <div className="space-y-3">
          {aiSuggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleAISuggestion(suggestion)}
              className="block w-full text-left p-4 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <p className="text-sm">{suggestion}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading workflow and integration hub...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-gray-900 text-white">
        <div className="text-center">
          <div className="text-red-400 mb-4">
            <AlertCircle className="w-12 h-12 mx-auto mb-2" />
            <p>{error}</p>
          </div>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center">
              <Sparkles className="w-8 h-8 mr-3 text-purple-400" />
              AI Workflow & Integration Hub
            </h1>
            <p className="text-gray-400 mt-1">
              Intelligent automation with AI-powered workflows and integrations
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                onChatMessage?.("I need help with workflows and integrations. What can you assist me with?");
                onShowChat?.();
              }}
              className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
            >
              <Bot className="w-4 h-4 mr-2" />
              AI Assistant
            </button>
            <button
              onClick={loadData}
              className="flex items-center px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', label: 'Overview', icon: TrendingUp },
              { id: 'workflows', label: 'Workflows', icon: Workflow },
              { id: 'integrations', label: 'Integrations', icon: Plug },
              { id: 'templates', label: 'Templates', icon: Copy },
              { id: 'ai-assistant', label: 'AI Assistant', icon: Bot }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-purple-500 text-purple-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'workflows' && (
          <WorkflowTemplateManager
            onSelectTemplate={handleTemplateSelect}
            onCreateFromTemplate={handleCreateFromTemplate}
            onChatIntegration={handleWorkflowChatIntegration}
          />
        )}
        {activeTab === 'integrations' && (
          <IntegrationCatalog
            onInstallIntegration={handleInstallIntegration}
            onChatIntegration={handleIntegrationChatIntegration}
            installedIntegrations={integrations}
          />
        )}
        {activeTab === 'templates' && (
          <WorkflowTemplateManager
            onSelectTemplate={handleTemplateSelect}
            onCreateFromTemplate={handleCreateFromTemplate}
            onChatIntegration={handleWorkflowChatIntegration}
          />
        )}
        {activeTab === 'ai-assistant' && renderAIAssistant()}
      </div>
    </div>
  );
};