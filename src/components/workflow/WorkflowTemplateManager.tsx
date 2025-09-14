/**
 * WorkflowTemplateManager - Enhanced workflow template management with AI integration
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap, Plus, Search, Filter, Star, Download, Eye, Copy, Tag, Clock, Users, TrendingUp,
  Grid, List, ChevronDown, ChevronUp, Bookmark, BookmarkCheck, Settings, Database,
  Mail, FileText, Code, Webhook, Share2, Play, Pause, Edit, Trash2, MessageSquare,
  Bot, Sparkles, Wand2, Brain, Target, Workflow as WorkflowIcon
} from 'lucide-react';
import type { WorkflowTemplate, WorkflowDefinition } from '../../types/workflow';
import { workflowManagementService } from '../../services/workflowManagementService';

export interface WorkflowTemplateManagerProps {
  onSelectTemplate?: (template: WorkflowTemplate) => void;
  onCreateFromTemplate?: (template: WorkflowTemplate) => void;
  onChatIntegration?: (template: WorkflowTemplate, action: string) => void;
  selectedTemplateId?: string;
}

interface TemplateFilter {
  category?: string;
  tags?: string[];
  popularity?: 'high' | 'medium' | 'low';
  isOfficial?: boolean;
  search?: string;
  aiEnabled?: boolean;
}

// Enhanced workflow templates with AI integration
const ENHANCED_TEMPLATES: WorkflowTemplate[] = [
  {
    id: 'ai_research_pipeline',
    name: 'AI Research Pipeline',
    description: 'Automated research workflow with AI-powered analysis, summarization, and insights generation',
    category: 'Research & Analysis',
    tags: ['ai', 'research', 'automation', 'analysis', 'chatbot'],
    popularity: 95,
    isOfficial: true,
    definition: {
      name: 'AI Research Pipeline',
      description: 'Automated research workflow with AI-powered analysis',
      status: 'active',
      triggers: [
        {
          id: 'trigger_research_1',
          type: 'document_upload',
          config: { fileTypes: ['pdf', 'docx', 'txt'], aiAnalysis: true },
          enabled: true
        },
        {
          id: 'trigger_research_2',
          type: 'api_call',
          config: { endpoint: '/api/research/start', aiTrigger: true },
          enabled: true
        }
      ],
      conditions: [
        {
          id: 'cond_research_1',
          type: 'document_type',
          operator: 'equals',
          value: 'research_paper'
        }
      ],
      actions: [
        {
          id: 'action_research_1',
          type: 'ai_analysis',
          name: 'AI Content Analysis',
          config: { 
            model: 'gpt-4',
            analysisType: 'comprehensive',
            extractKeywords: true,
            generateSummary: true,
            identifyThemes: true,
            chatbotIntegration: true
          },
          enabled: true,
          order: 1
        },
        {
          id: 'action_research_2',
          type: 'auto_tag',
          name: 'Smart Tagging',
          config: { 
            aiModel: 'gpt-4',
            useSemanticAnalysis: true,
            chatbotFeedback: true
          },
          enabled: true,
          order: 2
        },
        {
          id: 'action_research_3',
          type: 'generate_insights',
          name: 'Generate Research Insights',
          config: { 
            insightTypes: ['trends', 'gaps', 'recommendations'],
            chatbotSummary: true
          },
          enabled: true,
          order: 3
        },
        {
          id: 'action_research_4',
          type: 'chatbot_notification',
          name: 'Notify via Chatbot',
          config: { 
            message: 'Research analysis complete! New insights are available.',
            includeResults: true,
            enableInteraction: true
          },
          enabled: true,
          order: 4
        }
      ],
      tags: ['ai', 'research', 'automation'],
      version: 1,
      isTemplate: true
    }
  },
  {
    id: 'smart_document_processor',
    name: 'Smart Document Processor',
    description: 'AI-powered document processing with OCR, classification, and intelligent extraction',
    category: 'Document Management',
    tags: ['ai', 'ocr', 'classification', 'extraction', 'chatbot'],
    popularity: 88,
    isOfficial: true,
    definition: {
      name: 'Smart Document Processor',
      description: 'AI-powered document processing pipeline',
      status: 'active',
      triggers: [
        {
          id: 'trigger_doc_1',
          type: 'document_upload',
          config: { fileTypes: ['pdf', 'jpg', 'png', 'docx'], aiProcessing: true },
          enabled: true
        }
      ],
      conditions: [],
      actions: [
        {
          id: 'action_doc_1',
          type: 'ai_ocr',
          name: 'AI OCR Processing',
          config: { 
            model: 'vision-transformer',
            extractText: true,
            extractTables: true,
            extractImages: true
          },
          enabled: true,
          order: 1
        },
        {
          id: 'action_doc_2',
          type: 'ai_classification',
          name: 'Document Classification',
          config: { 
            model: 'bert-classifier',
            categories: ['research', 'legal', 'financial', 'technical'],
            confidence_threshold: 0.8
          },
          enabled: true,
          order: 2
        },
        {
          id: 'action_doc_3',
          type: 'ai_extraction',
          name: 'Smart Data Extraction',
          config: { 
            extractEntities: true,
            extractKeyPhrases: true,
            extractSentiment: true,
            chatbotSummary: true
          },
          enabled: true,
          order: 3
        },
        {
          id: 'action_doc_4',
          type: 'chatbot_interaction',
          name: 'Interactive Results',
          config: { 
            enableQuestions: true,
            suggestActions: true,
            provideInsights: true
          },
          enabled: true,
          order: 4
        }
      ],
      tags: ['ai', 'document', 'processing'],
      version: 1,
      isTemplate: true
    }
  },
  {
    id: 'conversational_analytics',
    name: 'Conversational Analytics',
    description: 'AI-driven analytics with natural language queries and chatbot integration',
    category: 'Analytics & Insights',
    tags: ['ai', 'analytics', 'nlp', 'chatbot', 'insights'],
    popularity: 92,
    isOfficial: true,
    definition: {
      name: 'Conversational Analytics',
      description: 'Natural language analytics with AI chatbot',
      status: 'active',
      triggers: [
        {
          id: 'trigger_analytics_1',
          type: 'schedule',
          config: { cron: '0 9 * * *', aiAnalysis: true },
          enabled: true
        },
        {
          id: 'trigger_analytics_2',
          type: 'api_call',
          config: { endpoint: '/api/analytics/query', nlpEnabled: true },
          enabled: true
        }
      ],
      conditions: [],
      actions: [
        {
          id: 'action_analytics_1',
          type: 'ai_data_analysis',
          name: 'AI Data Analysis',
          config: { 
            analysisTypes: ['trends', 'anomalies', 'predictions'],
            nlpQueries: true,
            chatbotInterface: true
          },
          enabled: true,
          order: 1
        },
        {
          id: 'action_analytics_2',
          type: 'generate_insights',
          name: 'Generate Insights',
          config: { 
            insightTypes: ['patterns', 'recommendations', 'alerts'],
            naturalLanguage: true
          },
          enabled: true,
          order: 2
        },
        {
          id: 'action_analytics_3',
          type: 'chatbot_dashboard',
          name: 'Interactive Dashboard',
          config: { 
            enableQueries: true,
            voiceInterface: true,
            realTimeUpdates: true
          },
          enabled: true,
          order: 3
        }
      ],
      tags: ['ai', 'analytics', 'chatbot'],
      version: 1,
      isTemplate: true
    }
  },
  {
    id: 'intelligent_workflow_orchestrator',
    name: 'Intelligent Workflow Orchestrator',
    description: 'AI-powered workflow management with adaptive execution and chatbot control',
    category: 'Workflow Management',
    tags: ['ai', 'orchestration', 'adaptive', 'chatbot', 'automation'],
    popularity: 85,
    isOfficial: true,
    definition: {
      name: 'Intelligent Workflow Orchestrator',
      description: 'AI-powered adaptive workflow management',
      status: 'active',
      triggers: [
        {
          id: 'trigger_orchestrator_1',
          type: 'manual',
          config: { aiAssisted: true, chatbotTrigger: true },
          enabled: true
        }
      ],
      conditions: [
        {
          id: 'cond_orchestrator_1',
          type: 'ai_condition',
          operator: 'ai_evaluate',
          value: 'optimal_execution_time'
        }
      ],
      actions: [
        {
          id: 'action_orchestrator_1',
          type: 'ai_workflow_optimization',
          name: 'Optimize Workflow Path',
          config: { 
            optimizationCriteria: ['speed', 'accuracy', 'cost'],
            adaptiveExecution: true,
            chatbotFeedback: true
          },
          enabled: true,
          order: 1
        },
        {
          id: 'action_orchestrator_2',
          type: 'dynamic_routing',
          name: 'Dynamic Task Routing',
          config: { 
            aiDecisionMaking: true,
            loadBalancing: true,
            chatbotMonitoring: true
          },
          enabled: true,
          order: 2
        },
        {
          id: 'action_orchestrator_3',
          type: 'chatbot_control',
          name: 'Chatbot Control Interface',
          config: { 
            enableCommands: true,
            voiceControl: true,
            realTimeStatus: true
          },
          enabled: true,
          order: 3
        }
      ],
      tags: ['ai', 'orchestration', 'chatbot'],
      version: 1,
      isTemplate: true
    }
  },
  {
    id: 'ai_integration_hub',
    name: 'AI Integration Hub',
    description: 'Intelligent integration management with AI-powered configuration and chatbot assistance',
    category: 'Integration Management',
    tags: ['ai', 'integration', 'configuration', 'chatbot', 'automation'],
    popularity: 78,
    isOfficial: true,
    definition: {
      name: 'AI Integration Hub',
      description: 'Intelligent integration management system',
      status: 'active',
      triggers: [
        {
          id: 'trigger_integration_1',
          type: 'api_call',
          config: { endpoint: '/api/integrations/configure', aiAssisted: true },
          enabled: true
        }
      ],
      conditions: [],
      actions: [
        {
          id: 'action_integration_1',
          type: 'ai_config_generation',
          name: 'AI Configuration Generation',
          config: { 
            autoDetectAPIs: true,
            generateMappings: true,
            optimizeSettings: true,
            chatbotGuidance: true
          },
          enabled: true,
          order: 1
        },
        {
          id: 'action_integration_2',
          type: 'intelligent_testing',
          name: 'Intelligent Testing',
          config: { 
            aiTestGeneration: true,
            adaptiveRetries: true,
            chatbotReporting: true
          },
          enabled: true,
          order: 2
        },
        {
          id: 'action_integration_3',
          type: 'chatbot_setup_wizard',
          name: 'Chatbot Setup Wizard',
          config: { 
            guidedSetup: true,
            troubleshooting: true,
            voiceAssistance: true
          },
          enabled: true,
          order: 3
        }
      ],
      tags: ['ai', 'integration', 'chatbot'],
      version: 1,
      isTemplate: true
    }
  }
];

export const WorkflowTemplateManager: React.FC<WorkflowTemplateManagerProps> = ({
  onSelectTemplate,
  onCreateFromTemplate,
  onChatIntegration,
  selectedTemplateId
}) => {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Filter and search state
  const [filter, setFilter] = useState<TemplateFilter>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [bookmarkedTemplates, setBookmarkedTemplates] = useState<Set<string>>(new Set());

  // Categories and tags for filtering
  const [categories, setCategories] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);

  // Load templates
  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      // Combine service templates with enhanced AI templates
      const serviceTemplates = await workflowManagementService.getWorkflowTemplates();
      const allTemplates = [...ENHANCED_TEMPLATES, ...serviceTemplates];
      
      setTemplates(allTemplates);
      
      // Extract categories and tags
      const uniqueCategories = [...new Set(allTemplates.map(t => t.category))];
      const uniqueTags = [...new Set(allTemplates.flatMap(t => t.tags))];
      
      setCategories(uniqueCategories);
      setAllTags(uniqueTags);
      setError(null);
    } catch (err) {
      setError('Failed to load workflow templates');
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  // Filter and sort templates
  const filteredAndSortedTemplates = React.useMemo(() => {
    let filtered = templates;

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(template =>
        template.name.toLowerCase().includes(search) ||
        template.description.toLowerCase().includes(search) ||
        template.tags.some(tag => tag.toLowerCase().includes(search))
      );
    }

    // Apply category filter
    if (filter.category) {
      filtered = filtered.filter(template => template.category === filter.category);
    }

    // Apply tags filter
    if (filter.tags && filter.tags.length > 0) {
      filtered = filtered.filter(template =>
        filter.tags!.some(tag => template.tags.includes(tag))
      );
    }

    // Apply AI filter
    if (filter.aiEnabled) {
      filtered = filtered.filter(template =>
        template.tags.includes('ai') || template.tags.includes('chatbot')
      );
    }

    // Apply popularity filter
    if (filter.popularity) {
      const popularityRanges = {
        high: [80, 100],
        medium: [50, 79],
        low: [0, 49]
      };
      const [min, max] = popularityRanges[filter.popularity];
      filtered = filtered.filter(template => 
        template.popularity >= min && template.popularity <= max
      );
    }

    // Apply official filter
    if (filter.isOfficial !== undefined) {
      filtered = filtered.filter(template => template.isOfficial === filter.isOfficial);
    }

    // Sort by popularity by default
    filtered.sort((a, b) => b.popularity - a.popularity);

    return filtered;
  }, [templates, searchTerm, filter]);

  // Handle template actions
  const handleSelectTemplate = (template: WorkflowTemplate) => {
    onSelectTemplate?.(template);
  };

  const handleCreateFromTemplate = (template: WorkflowTemplate) => {
    onCreateFromTemplate?.(template);
  };

  const handleChatIntegration = (template: WorkflowTemplate, action: string) => {
    onChatIntegration?.(template, action);
  };

  // Toggle bookmark
  const toggleBookmark = (templateId: string) => {
    setBookmarkedTemplates(prev => {
      const newBookmarks = new Set(prev);
      if (newBookmarks.has(templateId)) {
        newBookmarks.delete(templateId);
      } else {
        newBookmarks.add(templateId);
      }
      return newBookmarks;
    });
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof TemplateFilter, value: any) => {
    setFilter(prev => ({ ...prev, [key]: value }));
  };

  // Toggle tag filter
  const toggleTagFilter = (tag: string) => {
    setFilter(prev => ({
      ...prev,
      tags: prev.tags?.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...(prev.tags || []), tag]
    }));
  };

  // Clear filters
  const clearFilters = () => {
    setFilter({});
    setSearchTerm('');
  };

  // Get icon for template category
  const getCategoryIcon = (category: string) => {
    const iconMap: Record<string, React.ComponentType<any>> = {
      'Research & Analysis': Brain,
      'Document Management': FileText,
      'Analytics & Insights': TrendingUp,
      'Workflow Management': WorkflowIcon,
      'Integration Management': Webhook,
      'Communication': Mail,
      'Data Processing': Database,
      'Development': Code
    };
    return iconMap[category] || Settings;
  };

  // Get popularity badge
  const getPopularityBadge = (popularity: number) => {
    if (popularity >= 90) return { label: 'Hot', color: 'bg-red-500' };
    if (popularity >= 80) return { label: 'Popular', color: 'bg-green-500' };
    if (popularity >= 50) return { label: 'Trending', color: 'bg-yellow-500' };
    return { label: 'New', color: 'bg-blue-500' };
  };

  // Check if template has AI features
  const hasAIFeatures = (template: WorkflowTemplate) => {
    return template.tags.includes('ai') || template.tags.includes('chatbot');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading AI-powered templates...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-gray-900 text-white">
        <div className="text-center">
          <div className="text-red-400 mb-4">
            <Settings className="w-12 h-12 mx-auto mb-2" />
            <p>{error}</p>
          </div>
          <button
            onClick={loadTemplates}
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
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              <Sparkles className="w-6 h-6 mr-2 text-purple-400" />
              AI Workflow Templates
            </h2>
            <p className="text-gray-400">Intelligent workflow templates with AI integration and chatbot features</p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* AI Filter Toggle */}
            <button
              onClick={() => handleFilterChange('aiEnabled', !filter.aiEnabled)}
              className={`flex items-center px-3 py-2 rounded-lg text-sm ${
                filter.aiEnabled ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Bot className="w-4 h-4 mr-1" />
              AI Only
            </button>
            
            {/* View mode toggle */}
            <div className="flex items-center bg-gray-700 rounded p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-purple-600' : 'hover:bg-gray-600'}`}
                title="Grid View"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-purple-600' : 'hover:bg-gray-600'}`}
                title="List View"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Search and filters */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search AI templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 rounded-lg ${showFilters ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            {showFilters ? <ChevronUp className="w-4 h-4 ml-2" /> : <ChevronDown className="w-4 h-4 ml-2" />}
          </button>
        </div>

        {/* Filters panel */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-800 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Category filter */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                <select
                  value={filter.category || ''}
                  onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-purple-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>

              {/* Popularity filter */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Popularity</label>
                <select
                  value={filter.popularity || ''}
                  onChange={(e) => handleFilterChange('popularity', e.target.value || undefined)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-purple-500"
                >
                  <option value="">All</option>
                  <option value="high">High (80%+)</option>
                  <option value="medium">Medium (50-79%)</option>
                  <option value="low">Low (0-49%)</option>
                </select>
              </div>

              {/* Official filter */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Source</label>
                <select
                  value={filter.isOfficial === undefined ? '' : filter.isOfficial.toString()}
                  onChange={(e) => handleFilterChange('isOfficial', e.target.value === '' ? undefined : e.target.value === 'true')}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-purple-500"
                >
                  <option value="">All Sources</option>
                  <option value="true">Official</option>
                  <option value="false">Community</option>
                </select>
              </div>

              {/* Clear filters */}
              <div className="flex items-end">
                <button
                  onClick={clearFilters}
                  className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm"
                >
                  Clear Filters
                </button>
              </div>
            </div>

            {/* Tags filter */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">Tags</label>
              <div className="flex flex-wrap gap-2">
                {allTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => toggleTagFilter(tag)}
                    className={`px-3 py-1 rounded-full text-sm flex items-center ${
                      filter.tags?.includes(tag)
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {tag === 'ai' && <Bot className="w-3 h-3 mr-1" />}
                    {tag === 'chatbot' && <MessageSquare className="w-3 h-3 mr-1" />}
                    <Tag className="w-3 h-3 mr-1" />
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results summary */}
      <div className="px-6 py-3 bg-gray-800 border-b border-gray-700">
        <p className="text-sm text-gray-400">
          Showing {filteredAndSortedTemplates.length} of {templates.length} templates
          {filter.aiEnabled && <span className="text-purple-400 ml-2">(AI-powered only)</span>}
        </p>
      </div>

      {/* Templates */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredAndSortedTemplates.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-400 mb-2">No templates found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAndSortedTemplates.map(template => {
              const CategoryIcon = getCategoryIcon(template.category);
              const popularityBadge = getPopularityBadge(template.popularity);
              const isSelected = selectedTemplateId === template.id;
              const isBookmarked = bookmarkedTemplates.has(template.id);
              const isAIPowered = hasAIFeatures(template);

              return (
                <div
                  key={template.id}
                  className={`bg-gray-800 rounded-lg border-2 transition-all cursor-pointer hover:border-purple-500 ${
                    isSelected ? 'border-purple-500 ring-2 ring-purple-500/20' : 'border-gray-700'
                  } ${isAIPowered ? 'bg-gradient-to-br from-gray-800 to-purple-900/20' : ''}`}
                  onClick={() => handleSelectTemplate(template)}
                >
                  <div className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center">
                        <div className={`p-2 rounded ${popularityBadge.color} bg-opacity-20 mr-3 relative`}>
                          <CategoryIcon className="w-5 h-5" />
                          {isAIPowered && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full flex items-center justify-center">
                              <Sparkles className="w-2 h-2 text-white" />
                            </div>
                          )}
                        </div>
                        <div>
                          <h3 className="font-semibold text-white truncate flex items-center">
                            {template.name}
                            {isAIPowered && <Bot className="w-4 h-4 ml-1 text-purple-400" />}
                          </h3>
                          <p className="text-xs text-gray-400">{template.category}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {template.isOfficial && (
                          <div className="bg-blue-500 bg-opacity-20 text-blue-400 px-2 py-1 rounded text-xs">
                            Official
                          </div>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleBookmark(template.id);
                          }}
                          className="p-1 hover:bg-gray-700 rounded"
                        >
                          {isBookmarked ? (
                            <BookmarkCheck className="w-4 h-4 text-yellow-400" />
                          ) : (
                            <Bookmark className="w-4 h-4 text-gray-400" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-300 mb-4 line-clamp-2">{template.description}</p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {template.tags.slice(0, 3).map(tag => (
                        <span 
                          key={tag} 
                          className={`px-2 py-1 rounded text-xs flex items-center ${
                            tag === 'ai' || tag === 'chatbot' 
                              ? 'bg-purple-600 text-white' 
                              : 'bg-gray-700 text-gray-300'
                          }`}
                        >
                          {tag === 'ai' && <Bot className="w-3 h-3 mr-1" />}
                          {tag === 'chatbot' && <MessageSquare className="w-3 h-3 mr-1" />}
                          {tag}
                        </span>
                      ))}
                      {template.tags.length > 3 && (
                        <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
                          +{template.tags.length - 3}
                        </span>
                      )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center text-xs text-gray-400">
                          <TrendingUp className="w-3 h-3 mr-1" />
                          {template.popularity}%
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${popularityBadge.color} bg-opacity-20`}>
                          {popularityBadge.label}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {isAIPowered && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleChatIntegration(template, 'discuss');
                            }}
                            className="p-1 hover:bg-gray-700 rounded"
                            title="Discuss with AI"
                          >
                            <MessageSquare className="w-4 h-4 text-purple-400" />
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateFromTemplate(template);
                          }}
                          className="p-1 hover:bg-gray-700 rounded"
                          title="Create Workflow"
                        >
                          <Plus className="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAndSortedTemplates.map(template => {
              const CategoryIcon = getCategoryIcon(template.category);
              const popularityBadge = getPopularityBadge(template.popularity);
              const isSelected = selectedTemplateId === template.id;
              const isBookmarked = bookmarkedTemplates.has(template.id);
              const isAIPowered = hasAIFeatures(template);

              return (
                <div
                  key={template.id}
                  className={`bg-gray-800 rounded-lg border-2 transition-all cursor-pointer hover:border-purple-500 ${
                    isSelected ? 'border-purple-500 ring-2 ring-purple-500/20' : 'border-gray-700'
                  } ${isAIPowered ? 'bg-gradient-to-r from-gray-800 to-purple-900/20' : ''}`}
                  onClick={() => handleSelectTemplate(template)}
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <div className={`p-3 rounded ${popularityBadge.color} bg-opacity-20 mr-4 relative`}>
                          <CategoryIcon className="w-6 h-6" />
                          {isAIPowered && (
                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-purple-500 rounded-full flex items-center justify-center">
                              <Sparkles className="w-3 h-3 text-white" />
                            </div>
                          )}
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center mb-1">
                            <h3 className="font-semibold text-white mr-3 flex items-center">
                              {template.name}
                              {isAIPowered && <Bot className="w-4 h-4 ml-2 text-purple-400" />}
                            </h3>
                            {template.isOfficial && (
                              <span className="bg-blue-500 bg-opacity-20 text-blue-400 px-2 py-1 rounded text-xs">
                                Official
                              </span>
                            )}
                            <span className={`ml-2 px-2 py-1 rounded text-xs ${popularityBadge.color} bg-opacity-20`}>
                              {popularityBadge.label}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-300 mb-2">{template.description}</p>
                          
                          <div className="flex items-center space-x-4 text-xs text-gray-400">
                            <span>{template.category}</span>
                            <div className="flex items-center">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              {template.popularity}% popularity
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {template.tags.slice(0, 4).map(tag => (
                                <span 
                                  key={tag} 
                                  className={`px-2 py-1 rounded flex items-center ${
                                    tag === 'ai' || tag === 'chatbot' 
                                      ? 'bg-purple-600 text-white' 
                                      : 'bg-gray-700 text-gray-300'
                                  }`}
                                >
                                  {tag === 'ai' && <Bot className="w-3 h-3 mr-1" />}
                                  {tag === 'chatbot' && <MessageSquare className="w-3 h-3 mr-1" />}
                                  {tag}
                                </span>
                              ))}
                              {template.tags.length > 4 && (
                                <span className="px-2 py-1 bg-gray-700 rounded">
                                  +{template.tags.length - 4}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleBookmark(template.id);
                          }}
                          className="p-2 hover:bg-gray-700 rounded"
                        >
                          {isBookmarked ? (
                            <BookmarkCheck className="w-4 h-4 text-yellow-400" />
                          ) : (
                            <Bookmark className="w-4 h-4 text-gray-400" />
                          )}
                        </button>
                        {isAIPowered && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleChatIntegration(template, 'discuss');
                            }}
                            className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm flex items-center"
                          >
                            <MessageSquare className="w-4 h-4 mr-1" />
                            Chat
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateFromTemplate(template);
                          }}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm flex items-center"
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Create
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};