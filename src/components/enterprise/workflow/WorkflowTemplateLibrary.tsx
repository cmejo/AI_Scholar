/**
 * WorkflowTemplateLibrary - Template management and selection interface
 * Provides access to pre-built workflow templates
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Filter,
  Star,
  Download,
  Eye,
  Copy,
  Tag,
  Clock,
  Users,
  TrendingUp,
  Grid,
  List,
  ChevronDown,
  ChevronUp,
  Bookmark,
  BookmarkCheck,
  Zap,
  Settings,
  Database,
  Mail,
  FileText,
  Code,
  Webhook,
  Share2
} from 'lucide-react';
import type { WorkflowTemplate } from '../../../types/workflow';
import { WorkflowManagementService } from '../../../services/workflowManagementService';

export interface WorkflowTemplateLibraryProps {
  onSelectTemplate?: (template: WorkflowTemplate) => void;
  onPreviewTemplate?: (template: WorkflowTemplate) => void;
  selectedTemplateId?: string;
}

interface TemplateFilter {
  category?: string;
  tags?: string[];
  popularity?: 'high' | 'medium' | 'low';
  isOfficial?: boolean;
  search?: string;
}

interface TemplateSort {
  field: 'name' | 'popularity' | 'category' | 'createdAt';
  direction: 'asc' | 'desc';
}

const workflowService = new WorkflowManagementService();

export const WorkflowTemplateLibrary: React.FC<WorkflowTemplateLibraryProps> = ({
  onSelectTemplate,
  onPreviewTemplate,
  selectedTemplateId
}) => {
  // State
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Filter and search state
  const [filter, setFilter] = useState<TemplateFilter>({});
  const [sort, setSort] = useState<TemplateSort>({ field: 'popularity', direction: 'desc' });
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
      const templatesData = await workflowService.getWorkflowTemplates();
      setTemplates(templatesData);
      
      // Extract categories and tags
      const uniqueCategories = [...new Set(templatesData.map(t => t.category))];
      const uniqueTags = [...new Set(templatesData.flatMap(t => t.tags))];
      
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

    // Sort templates
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sort.field) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'popularity':
          aValue = a.popularity;
          bValue = b.popularity;
          break;
        case 'category':
          aValue = a.category.toLowerCase();
          bValue = b.category.toLowerCase();
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sort.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sort.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [templates, searchTerm, filter, sort]);

  // Handle template selection
  const handleSelectTemplate = (template: WorkflowTemplate) => {
    onSelectTemplate?.(template);
  };

  // Handle template preview
  const handlePreviewTemplate = (template: WorkflowTemplate) => {
    onPreviewTemplate?.(template);
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

  // Handle tag filter toggle
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
      'Document Management': FileText,
      'Analytics': TrendingUp,
      'Communication': Mail,
      'Integration': Webhook,
      'Automation': Settings,
      'Data Processing': Database,
      'Development': Code
    };
    return iconMap[category] || Settings;
  };

  // Get popularity badge
  const getPopularityBadge = (popularity: number) => {
    if (popularity >= 80) return { label: 'Popular', color: 'bg-green-500' };
    if (popularity >= 50) return { label: 'Trending', color: 'bg-yellow-500' };
    return { label: 'New', color: 'bg-blue-500' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading templates...</p>
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
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
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
            <h2 className="text-2xl font-bold">Workflow Templates</h2>
            <p className="text-gray-400">Choose from pre-built workflow templates to get started quickly</p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* View mode toggle */}
            <div className="flex items-center bg-gray-700 rounded p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
                title="Grid View"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
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
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 rounded-lg ${showFilters ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            {showFilters ? <ChevronUp className="w-4 h-4 ml-2" /> : <ChevronDown className="w-4 h-4 ml-2" />}
          </button>

          {/* Sort */}
          <select
            value={`${sort.field}-${sort.direction}`}
            onChange={(e) => {
              const [field, direction] = e.target.value.split('-');
              setSort({ field: field as TemplateSort['field'], direction: direction as 'asc' | 'desc' });
            }}
            className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
          >
            <option value="popularity-desc">Most Popular</option>
            <option value="name-asc">Name A-Z</option>
            <option value="name-desc">Name Z-A</option>
            <option value="category-asc">Category</option>
          </select>
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
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
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
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
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
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:outline-none focus:border-blue-500"
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
                    className={`px-3 py-1 rounded-full text-sm ${
                      filter.tags?.includes(tag)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <Tag className="w-3 h-3 mr-1 inline" />
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
        </p>
      </div>

      {/* Templates */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredAndSortedTemplates.length === 0 ? (
          <div className="text-center py-12">
            <Settings className="w-12 h-12 text-gray-500 mx-auto mb-4" />
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

              return (
                <div
                  key={template.id}
                  className={`bg-gray-800 rounded-lg border-2 transition-all cursor-pointer hover:border-blue-500 ${
                    isSelected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-gray-700'
                  }`}
                  onClick={() => handleSelectTemplate(template)}
                >
                  <div className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center">
                        <div className={`p-2 rounded ${popularityBadge.color} bg-opacity-20 mr-3`}>
                          <CategoryIcon className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-white truncate">{template.name}</h3>
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
                        <span key={tag} className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
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
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePreviewTemplate(template);
                          }}
                          className="p-1 hover:bg-gray-700 rounded"
                          title="Preview"
                        >
                          <Eye className="w-4 h-4 text-gray-400" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectTemplate(template);
                          }}
                          className="p-1 hover:bg-gray-700 rounded"
                          title="Use Template"
                        >
                          <Download className="w-4 h-4 text-gray-400" />
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

              return (
                <div
                  key={template.id}
                  className={`bg-gray-800 rounded-lg border-2 transition-all cursor-pointer hover:border-blue-500 ${
                    isSelected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-gray-700'
                  }`}
                  onClick={() => handleSelectTemplate(template)}
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <div className={`p-3 rounded ${popularityBadge.color} bg-opacity-20 mr-4`}>
                          <CategoryIcon className="w-6 h-6" />
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center mb-1">
                            <h3 className="font-semibold text-white mr-3">{template.name}</h3>
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
                                <span key={tag} className="px-2 py-1 bg-gray-700 rounded">
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
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePreviewTemplate(template);
                          }}
                          className="p-2 hover:bg-gray-700 rounded"
                          title="Preview"
                        >
                          <Eye className="w-4 h-4 text-gray-400" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectTemplate(template);
                          }}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                        >
                          Use Template
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