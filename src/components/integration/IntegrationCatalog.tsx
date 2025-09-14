/**
 * IntegrationCatalog - Enhanced integration catalog with AI-powered features and chatbot integration
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Filter, Star, Download, Eye, Copy, Tag, Clock, Users, TrendingUp,
  Grid, List, ChevronDown, ChevronUp, Bookmark, BookmarkCheck, Settings, Database,
  Mail, FileText, Code, Webhook, Share2, Play, Pause, Edit, Trash2, MessageSquare,
  Bot, Sparkles, Wand2, Brain, Target, Zap, Cloud, Shield, Globe, Cpu, 
  BarChart3, Headphones, Video, Calendar, ShoppingCart, CreditCard
} from 'lucide-react';
import type { IntegrationCatalogItem, Integration } from '../../types/integration';
import { integrationManagementService } from '../../services/integrationManagementService';

export interface IntegrationCatalogProps {
  onInstallIntegration?: (item: IntegrationCatalogItem) => void;
  onChatIntegration?: (item: IntegrationCatalogItem, action: string) => void;
  installedIntegrations?: Integration[];
}

interface CatalogFilter {
  category?: string;
  tags?: string[];
  pricing?: 'free' | 'paid' | 'freemium';
  complexity?: 'easy' | 'medium' | 'advanced';
  search?: string;
  aiEnabled?: boolean;
  rating?: number;
}

// Enhanced integration catalog with AI-powered integrations
const ENHANCED_CATALOG: IntegrationCatalogItem[] = [
  {
    id: 'openai-gpt',
    name: 'OpenAI GPT',
    description: 'Advanced AI language models for text generation, analysis, and conversation',
    category: 'AI & Machine Learning',
    provider: 'OpenAI',
    icon: 'openai',
    type: 'api',
    features: ['Text Generation', 'Code Completion', 'Language Translation', 'Content Analysis', 'Chatbot Integration'],
    pricing: 'paid',
    documentation: 'https://platform.openai.com/docs',
    setupComplexity: 'easy',
    popularity: 98,
    rating: 4.9,
    reviews: 15420,
    tags: ['ai', 'nlp', 'chatbot', 'text-generation', 'analysis']
  },
  {
    id: 'anthropic-claude',
    name: 'Anthropic Claude',
    description: 'Constitutional AI assistant for safe and helpful AI interactions',
    category: 'AI & Machine Learning',
    provider: 'Anthropic',
    icon: 'anthropic',
    type: 'api',
    features: ['Safe AI Conversations', 'Document Analysis', 'Code Review', 'Research Assistance'],
    pricing: 'paid',
    documentation: 'https://docs.anthropic.com',
    setupComplexity: 'easy',
    popularity: 92,
    rating: 4.8,
    reviews: 8750,
    tags: ['ai', 'safety', 'chatbot', 'analysis', 'research']
  },
  {
    id: 'huggingface-transformers',
    name: 'Hugging Face Transformers',
    description: 'Open-source machine learning models and datasets',
    category: 'AI & Machine Learning',
    provider: 'Hugging Face',
    icon: 'huggingface',
    type: 'api',
    features: ['Pre-trained Models', 'Custom Training', 'Model Hosting', 'Dataset Access'],
    pricing: 'freemium',
    documentation: 'https://huggingface.co/docs',
    setupComplexity: 'medium',
    popularity: 89,
    rating: 4.7,
    reviews: 12300,
    tags: ['ai', 'ml', 'models', 'open-source', 'training']
  },
  {
    id: 'google-ai-studio',
    name: 'Google AI Studio',
    description: 'Google\'s AI platform with Gemini models and advanced capabilities',
    category: 'AI & Machine Learning',
    provider: 'Google',
    icon: 'google',
    type: 'api',
    features: ['Gemini Models', 'Multimodal AI', 'Vision Analysis', 'Code Generation'],
    pricing: 'freemium',
    documentation: 'https://ai.google.dev',
    setupComplexity: 'medium',
    popularity: 85,
    rating: 4.6,
    reviews: 9800,
    tags: ['ai', 'multimodal', 'vision', 'code', 'google']
  },
  {
    id: 'slack-ai-bot',
    name: 'Slack AI Bot',
    description: 'AI-powered Slack integration for intelligent team communication',
    category: 'Communication',
    provider: 'Slack Technologies',
    icon: 'slack',
    type: 'webhook',
    features: ['AI Responses', 'Smart Notifications', 'Meeting Summaries', 'Task Automation'],
    pricing: 'freemium',
    documentation: 'https://api.slack.com/docs',
    setupComplexity: 'easy',
    popularity: 94,
    rating: 4.8,
    reviews: 18500,
    tags: ['communication', 'ai', 'chatbot', 'automation', 'team']
  },
  {
    id: 'discord-ai-assistant',
    name: 'Discord AI Assistant',
    description: 'Intelligent Discord bot with AI conversation and moderation',
    category: 'Communication',
    provider: 'Discord Inc.',
    icon: 'discord',
    type: 'webhook',
    features: ['AI Chat', 'Auto Moderation', 'Voice Commands', 'Game Integration'],
    pricing: 'freemium',
    documentation: 'https://discord.com/developers/docs',
    setupComplexity: 'medium',
    popularity: 87,
    rating: 4.5,
    reviews: 14200,
    tags: ['communication', 'ai', 'gaming', 'moderation', 'voice']
  },
  {
    id: 'aws-bedrock',
    name: 'AWS Bedrock',
    description: 'Fully managed service for foundation models via APIs',
    category: 'Cloud & Infrastructure',
    provider: 'Amazon Web Services',
    icon: 'aws',
    type: 'cloud',
    features: ['Foundation Models', 'Model Customization', 'Serverless Inference', 'Enterprise Security'],
    pricing: 'paid',
    documentation: 'https://docs.aws.amazon.com/bedrock/',
    setupComplexity: 'advanced',
    popularity: 82,
    rating: 4.4,
    reviews: 6700,
    tags: ['ai', 'cloud', 'enterprise', 'models', 'aws']
  },
  {
    id: 'azure-openai',
    name: 'Azure OpenAI Service',
    description: 'Enterprise-grade OpenAI models on Microsoft Azure',
    category: 'Cloud & Infrastructure',
    provider: 'Microsoft',
    icon: 'azure',
    type: 'cloud',
    features: ['GPT Models', 'Enterprise Security', 'Custom Fine-tuning', 'Content Filtering'],
    pricing: 'paid',
    documentation: 'https://docs.microsoft.com/azure/cognitive-services/openai/',
    setupComplexity: 'advanced',
    popularity: 79,
    rating: 4.3,
    reviews: 5400,
    tags: ['ai', 'cloud', 'enterprise', 'microsoft', 'security']
  },
  {
    id: 'pinecone-vector-db',
    name: 'Pinecone Vector Database',
    description: 'Vector database for AI applications and semantic search',
    category: 'Data & Analytics',
    provider: 'Pinecone Systems',
    icon: 'pinecone',
    type: 'database',
    features: ['Vector Search', 'Real-time Updates', 'Hybrid Search', 'AI Embeddings'],
    pricing: 'freemium',
    documentation: 'https://docs.pinecone.io',
    setupComplexity: 'medium',
    popularity: 76,
    rating: 4.5,
    reviews: 3200,
    tags: ['database', 'vector', 'search', 'ai', 'embeddings']
  },
  {
    id: 'weaviate-vector-db',
    name: 'Weaviate Vector Database',
    description: 'Open-source vector database with GraphQL and RESTful APIs',
    category: 'Data & Analytics',
    provider: 'Weaviate',
    icon: 'weaviate',
    type: 'database',
    features: ['GraphQL API', 'Multi-modal Search', 'Auto-classification', 'Semantic Search'],
    pricing: 'freemium',
    documentation: 'https://weaviate.io/developers/weaviate',
    setupComplexity: 'medium',
    popularity: 71,
    rating: 4.4,
    reviews: 2800,
    tags: ['database', 'vector', 'graphql', 'open-source', 'semantic']
  },
  {
    id: 'zapier-ai-automation',
    name: 'Zapier AI Automation',
    description: 'AI-powered workflow automation connecting 5000+ apps',
    category: 'Automation',
    provider: 'Zapier',
    icon: 'zapier',
    type: 'api',
    features: ['AI Workflows', 'App Integrations', 'Smart Triggers', 'Natural Language Automation'],
    pricing: 'freemium',
    documentation: 'https://zapier.com/developer',
    setupComplexity: 'easy',
    popularity: 91,
    rating: 4.6,
    reviews: 22100,
    tags: ['automation', 'ai', 'workflows', 'integration', 'no-code']
  },
  {
    id: 'make-ai-scenarios',
    name: 'Make AI Scenarios',
    description: 'Visual automation platform with AI-powered scenario building',
    category: 'Automation',
    provider: 'Make (formerly Integromat)',
    icon: 'make',
    type: 'api',
    features: ['Visual Builder', 'AI Assistance', 'Complex Workflows', 'Error Handling'],
    pricing: 'freemium',
    documentation: 'https://www.make.com/en/help',
    setupComplexity: 'medium',
    popularity: 84,
    rating: 4.5,
    reviews: 8900,
    tags: ['automation', 'ai', 'visual', 'workflows', 'complex']
  },
  {
    id: 'notion-ai',
    name: 'Notion AI',
    description: 'AI-powered workspace for notes, docs, and project management',
    category: 'Productivity',
    provider: 'Notion Labs',
    icon: 'notion',
    type: 'api',
    features: ['AI Writing', 'Smart Templates', 'Content Generation', 'Database Automation'],
    pricing: 'freemium',
    documentation: 'https://developers.notion.com',
    setupComplexity: 'easy',
    popularity: 88,
    rating: 4.7,
    reviews: 16800,
    tags: ['productivity', 'ai', 'writing', 'templates', 'workspace']
  },
  {
    id: 'airtable-ai',
    name: 'Airtable AI',
    description: 'AI-enhanced database and project management platform',
    category: 'Productivity',
    provider: 'Airtable',
    icon: 'airtable',
    type: 'api',
    features: ['AI Data Analysis', 'Smart Formulas', 'Automated Workflows', 'Content Generation'],
    pricing: 'freemium',
    documentation: 'https://airtable.com/developers',
    setupComplexity: 'easy',
    popularity: 83,
    rating: 4.4,
    reviews: 12400,
    tags: ['productivity', 'database', 'ai', 'analysis', 'automation']
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    description: 'AI pair programmer that helps you write code faster',
    category: 'Development',
    provider: 'GitHub',
    icon: 'github',
    type: 'api',
    features: ['Code Completion', 'Code Generation', 'Documentation', 'Test Writing'],
    pricing: 'paid',
    documentation: 'https://docs.github.com/copilot',
    setupComplexity: 'easy',
    popularity: 95,
    rating: 4.8,
    reviews: 28500,
    tags: ['development', 'ai', 'code', 'programming', 'assistant']
  },
  {
    id: 'replit-ai',
    name: 'Replit AI',
    description: 'AI-powered online IDE with code generation and debugging',
    category: 'Development',
    provider: 'Replit',
    icon: 'replit',
    type: 'api',
    features: ['Code Generation', 'Debugging', 'Explanation', 'Refactoring'],
    pricing: 'freemium',
    documentation: 'https://docs.replit.com',
    setupComplexity: 'easy',
    popularity: 78,
    rating: 4.3,
    reviews: 9200,
    tags: ['development', 'ai', 'ide', 'debugging', 'online']
  }
];

export const IntegrationCatalog: React.FC<IntegrationCatalogProps> = ({
  onInstallIntegration,
  onChatIntegration,
  installedIntegrations = []
}) => {
  const [catalog, setCatalog] = useState<IntegrationCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Filter and search state
  const [filter, setFilter] = useState<CatalogFilter>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [bookmarkedItems, setBookmarkedItems] = useState<Set<string>>(new Set());

  // Categories and tags for filtering
  const [categories, setCategories] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);

  // Load catalog
  const loadCatalog = useCallback(async () => {
    try {
      setLoading(true);
      // Combine service catalog with enhanced AI catalog
      const serviceCatalog = await integrationManagementService.getIntegrationCatalog();
      const allItems = [...ENHANCED_CATALOG, ...serviceCatalog];
      
      setCatalog(allItems);
      
      // Extract categories and tags
      const uniqueCategories = [...new Set(allItems.map(item => item.category))];
      const uniqueTags = [...new Set(allItems.flatMap(item => item.tags))];
      
      setCategories(uniqueCategories);
      setAllTags(uniqueTags);
      setError(null);
    } catch (err) {
      setError('Failed to load integration catalog');
      console.error('Failed to load catalog:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  // Filter and sort catalog items
  const filteredAndSortedItems = React.useMemo(() => {
    let filtered = catalog;

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(item =>
        item.name.toLowerCase().includes(search) ||
        item.description.toLowerCase().includes(search) ||
        item.provider.toLowerCase().includes(search) ||
        item.tags.some(tag => tag.toLowerCase().includes(search))
      );
    }

    // Apply category filter
    if (filter.category) {
      filtered = filtered.filter(item => item.category === filter.category);
    }

    // Apply tags filter
    if (filter.tags && filter.tags.length > 0) {
      filtered = filtered.filter(item =>
        filter.tags!.some(tag => item.tags.includes(tag))
      );
    }

    // Apply AI filter
    if (filter.aiEnabled) {
      filtered = filtered.filter(item =>
        item.tags.includes('ai') || item.tags.includes('chatbot') || item.tags.includes('ml')
      );
    }

    // Apply pricing filter
    if (filter.pricing) {
      filtered = filtered.filter(item => item.pricing === filter.pricing);
    }

    // Apply complexity filter
    if (filter.complexity) {
      filtered = filtered.filter(item => item.setupComplexity === filter.complexity);
    }

    // Apply rating filter
    if (filter.rating) {
      filtered = filtered.filter(item => item.rating >= filter.rating);
    }

    // Sort by popularity by default
    filtered.sort((a, b) => b.popularity - a.popularity);

    return filtered;
  }, [catalog, searchTerm, filter]);

  // Handle integration actions
  const handleInstallIntegration = (item: IntegrationCatalogItem) => {
    onInstallIntegration?.(item);
  };

  const handleChatIntegration = (item: IntegrationCatalogItem, action: string) => {
    onChatIntegration?.(item, action);
  };

  // Toggle bookmark
  const toggleBookmark = (itemId: string) => {
    setBookmarkedItems(prev => {
      const newBookmarks = new Set(prev);
      if (newBookmarks.has(itemId)) {
        newBookmarks.delete(itemId);
      } else {
        newBookmarks.add(itemId);
      }
      return newBookmarks;
    });
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof CatalogFilter, value: any) => {
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

  // Get icon for integration type
  const getTypeIcon = (type: string) => {
    const iconMap: Record<string, React.ComponentType<any>> = {
      'api': Code,
      'webhook': Webhook,
      'database': Database,
      'cloud': Cloud,
      'email': Mail,
      'custom': Settings
    };
    return iconMap[type] || Settings;
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    const iconMap: Record<string, React.ComponentType<any>> = {
      'AI & Machine Learning': Brain,
      'Communication': MessageSquare,
      'Cloud & Infrastructure': Cloud,
      'Data & Analytics': BarChart3,
      'Automation': Zap,
      'Productivity': Target,
      'Development': Code,
      'Security': Shield,
      'Media & Content': Video,
      'E-commerce': ShoppingCart,
      'Finance': CreditCard
    };
    return iconMap[category] || Settings;
  };

  // Get pricing badge
  const getPricingBadge = (pricing: string) => {
    const badges = {
      free: { label: 'Free', color: 'bg-green-500' },
      paid: { label: 'Paid', color: 'bg-red-500' },
      freemium: { label: 'Freemium', color: 'bg-yellow-500' }
    };
    return badges[pricing as keyof typeof badges] || badges.freemium;
  };

  // Get complexity badge
  const getComplexityBadge = (complexity: string) => {
    const badges = {
      easy: { label: 'Easy', color: 'bg-green-600' },
      medium: { label: 'Medium', color: 'bg-yellow-600' },
      advanced: { label: 'Advanced', color: 'bg-red-600' }
    };
    return badges[complexity as keyof typeof badges] || badges.medium;
  };

  // Check if integration has AI features
  const hasAIFeatures = (item: IntegrationCatalogItem) => {
    return item.tags.includes('ai') || item.tags.includes('chatbot') || item.tags.includes('ml');
  };

  // Check if integration is installed
  const isInstalled = (item: IntegrationCatalogItem) => {
    return installedIntegrations.some(integration => 
      integration.name.toLowerCase().includes(item.name.toLowerCase())
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading AI-powered integrations...</p>
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
            onClick={loadCatalog}
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
              AI Integration Catalog
            </h2>
            <p className="text-gray-400">Discover and install AI-powered integrations for your workflows</p>
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
              placeholder="Search AI integrations..."
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

              {/* Pricing filter */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Pricing</label>
                <select
                  value={filter.pricing || ''}
                  onChange={(e) => handleFilterChange('pricing', e.target.value || undefined)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-purple-500"
                >
                  <option value="">All Pricing</option>
                  <option value="free">Free</option>
                  <option value="freemium">Freemium</option>
                  <option value="paid">Paid</option>
                </select>
              </div>

              {/* Complexity filter */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Setup</label>
                <select
                  value={filter.complexity || ''}
                  onChange={(e) => handleFilterChange('complexity', e.target.value || undefined)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-purple-500"
                >
                  <option value="">All Levels</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>

              {/* Rating filter */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Min Rating</label>
                <select
                  value={filter.rating || ''}
                  onChange={(e) => handleFilterChange('rating', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-purple-500"
                >
                  <option value="">Any Rating</option>
                  <option value="4.5">4.5+ Stars</option>
                  <option value="4.0">4.0+ Stars</option>
                  <option value="3.5">3.5+ Stars</option>
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
                {allTags.slice(0, 15).map(tag => (
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
                    {tag === 'ml' && <Brain className="w-3 h-3 mr-1" />}
                    <Tag className="w-3 h-3 mr-1" />
                    {tag}
                  </button>
                ))}
                {allTags.length > 15 && (
                  <span className="px-3 py-1 bg-gray-700 text-gray-400 rounded-full text-sm">
                    +{allTags.length - 15} more
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results summary */}
      <div className="px-6 py-3 bg-gray-800 border-b border-gray-700">
        <p className="text-sm text-gray-400">
          Showing {filteredAndSortedItems.length} of {catalog.length} integrations
          {filter.aiEnabled && <span className="text-purple-400 ml-2">(AI-powered only)</span>}
        </p>
      </div>

      {/* Catalog Items */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredAndSortedItems.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-400 mb-2">No integrations found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAndSortedItems.map(item => {
              const TypeIcon = getTypeIcon(item.type);
              const CategoryIcon = getCategoryIcon(item.category);
              const pricingBadge = getPricingBadge(item.pricing);
              const complexityBadge = getComplexityBadge(item.setupComplexity);
              const isBookmarked = bookmarkedItems.has(item.id);
              const isAIPowered = hasAIFeatures(item);
              const installed = isInstalled(item);

              return (
                <div
                  key={item.id}
                  className={`bg-gray-800 rounded-lg border-2 transition-all hover:border-purple-500 border-gray-700 ${
                    isAIPowered ? 'bg-gradient-to-br from-gray-800 to-purple-900/20' : ''
                  }`}
                >
                  <div className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center">
                        <div className={`p-2 rounded ${pricingBadge.color} bg-opacity-20 mr-3 relative`}>
                          <CategoryIcon className="w-5 h-5" />
                          {isAIPowered && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full flex items-center justify-center">
                              <Sparkles className="w-2 h-2 text-white" />
                            </div>
                          )}
                        </div>
                        <div>
                          <h3 className="font-semibold text-white truncate flex items-center">
                            {item.name}
                            {isAIPowered && <Bot className="w-4 h-4 ml-1 text-purple-400" />}
                          </h3>
                          <p className="text-xs text-gray-400">{item.provider}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <span className={`px-2 py-1 rounded text-xs ${pricingBadge.color} bg-opacity-20`}>
                          {pricingBadge.label}
                        </span>
                        <button
                          onClick={() => toggleBookmark(item.id)}
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
                    <p className="text-sm text-gray-300 mb-4 line-clamp-2">{item.description}</p>

                    {/* Features */}
                    <div className="mb-4">
                      <div className="flex flex-wrap gap-1">
                        {item.features.slice(0, 2).map(feature => (
                          <span key={feature} className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                            {feature}
                          </span>
                        ))}
                        {item.features.length > 2 && (
                          <span className="px-2 py-1 bg-gray-700 text-gray-400 text-xs rounded">
                            +{item.features.length - 2}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center justify-between text-xs text-gray-400 mb-4">
                      <div className="flex items-center">
                        <Star className="w-3 h-3 mr-1 text-yellow-400" />
                        {item.rating} ({item.reviews.toLocaleString()})
                      </div>
                      <div className="flex items-center">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {item.popularity}%
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {item.tags.slice(0, 3).map(tag => (
                        <span 
                          key={tag} 
                          className={`px-2 py-1 rounded text-xs flex items-center ${
                            tag === 'ai' || tag === 'chatbot' || tag === 'ml'
                              ? 'bg-purple-600 text-white' 
                              : 'bg-gray-700 text-gray-300'
                          }`}
                        >
                          {tag === 'ai' && <Bot className="w-3 h-3 mr-1" />}
                          {tag === 'chatbot' && <MessageSquare className="w-3 h-3 mr-1" />}
                          {tag === 'ml' && <Brain className="w-3 h-3 mr-1" />}
                          {tag}
                        </span>
                      ))}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between">
                      <span className={`px-2 py-1 rounded text-xs ${complexityBadge.color} bg-opacity-20`}>
                        {complexityBadge.label} Setup
                      </span>
                      
                      <div className="flex items-center space-x-1">
                        {isAIPowered && (
                          <button
                            onClick={() => handleChatIntegration(item, 'discuss')}
                            className="p-1 hover:bg-gray-700 rounded"
                            title="Discuss with AI"
                          >
                            <MessageSquare className="w-4 h-4 text-purple-400" />
                          </button>
                        )}
                        <button
                          onClick={() => window.open(item.documentation, '_blank')}
                          className="p-1 hover:bg-gray-700 rounded"
                          title="Documentation"
                        >
                          <Eye className="w-4 h-4 text-gray-400" />
                        </button>
                        <button
                          onClick={() => handleInstallIntegration(item)}
                          disabled={installed}
                          className={`px-3 py-1 rounded text-xs ${
                            installed
                              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {installed ? 'Installed' : 'Install'}
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
            {filteredAndSortedItems.map(item => {
              const TypeIcon = getTypeIcon(item.type);
              const CategoryIcon = getCategoryIcon(item.category);
              const pricingBadge = getPricingBadge(item.pricing);
              const complexityBadge = getComplexityBadge(item.setupComplexity);
              const isBookmarked = bookmarkedItems.has(item.id);
              const isAIPowered = hasAIFeatures(item);
              const installed = isInstalled(item);

              return (
                <div
                  key={item.id}
                  className={`bg-gray-800 rounded-lg border-2 transition-all hover:border-purple-500 border-gray-700 ${
                    isAIPowered ? 'bg-gradient-to-r from-gray-800 to-purple-900/20' : ''
                  }`}
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <div className={`p-3 rounded ${pricingBadge.color} bg-opacity-20 mr-4 relative`}>
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
                              {item.name}
                              {isAIPowered && <Bot className="w-4 h-4 ml-2 text-purple-400" />}
                            </h3>
                            <span className={`px-2 py-1 rounded text-xs ${pricingBadge.color} bg-opacity-20`}>
                              {pricingBadge.label}
                            </span>
                            <span className={`ml-2 px-2 py-1 rounded text-xs ${complexityBadge.color} bg-opacity-20`}>
                              {complexityBadge.label}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-300 mb-2">{item.description}</p>
                          
                          <div className="flex items-center space-x-4 text-xs text-gray-400">
                            <span>{item.provider}</span>
                            <div className="flex items-center">
                              <Star className="w-3 h-3 mr-1 text-yellow-400" />
                              {item.rating} ({item.reviews.toLocaleString()})
                            </div>
                            <div className="flex items-center">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              {item.popularity}%
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {item.tags.slice(0, 4).map(tag => (
                                <span 
                                  key={tag} 
                                  className={`px-2 py-1 rounded flex items-center ${
                                    tag === 'ai' || tag === 'chatbot' || tag === 'ml'
                                      ? 'bg-purple-600 text-white' 
                                      : 'bg-gray-700 text-gray-300'
                                  }`}
                                >
                                  {tag === 'ai' && <Bot className="w-3 h-3 mr-1" />}
                                  {tag === 'chatbot' && <MessageSquare className="w-3 h-3 mr-1" />}
                                  {tag === 'ml' && <Brain className="w-3 h-3 mr-1" />}
                                  {tag}
                                </span>
                              ))}
                              {item.tags.length > 4 && (
                                <span className="px-2 py-1 bg-gray-700 rounded">
                                  +{item.tags.length - 4}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => toggleBookmark(item.id)}
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
                            onClick={() => handleChatIntegration(item, 'discuss')}
                            className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm flex items-center"
                          >
                            <MessageSquare className="w-4 h-4 mr-1" />
                            Chat
                          </button>
                        )}
                        <button
                          onClick={() => window.open(item.documentation, '_blank')}
                          className="px-3 py-2 bg-gray-600 hover:bg-gray-700 rounded text-sm"
                        >
                          Docs
                        </button>
                        <button
                          onClick={() => handleInstallIntegration(item)}
                          disabled={installed}
                          className={`px-4 py-2 rounded text-sm ${
                            installed
                              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {installed ? 'Installed' : 'Install'}
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