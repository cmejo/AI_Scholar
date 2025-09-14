import React, { useState } from 'react';
import { FileText, Eye, Heart, MessageCircle, TrendingUp, Filter } from 'lucide-react';

interface ContentItem {
  title: string;
  views: number;
  engagement: number;
}

interface ContentAnalyticsProps {
  data: ContentItem[];
}

export const ContentAnalytics: React.FC<ContentAnalyticsProps> = ({ data }) => {
  const [sortBy, setSortBy] = useState<'views' | 'engagement'>('views');
  const [filterType, setFilterType] = useState<'all' | 'trending' | 'popular'>('all');

  const processData = () => {
    let filteredData = [...data];

    // Apply filters
    if (filterType === 'trending') {
      filteredData = filteredData.filter(item => item.engagement > 70);
    } else if (filterType === 'popular') {
      filteredData = filteredData.filter(item => item.views > 1000);
    }

    // Sort data
    filteredData.sort((a, b) => {
      if (sortBy === 'views') {
        return b.views - a.views;
      } else {
        return b.engagement - a.engagement;
      }
    });

    return filteredData.slice(0, 10);
  };

  const processedData = processData();
  const maxViews = Math.max(...processedData.map(item => item.views));
  const maxEngagement = Math.max(...processedData.map(item => item.engagement));

  const getEngagementColor = (engagement: number) => {
    if (engagement >= 80) return 'text-green-400';
    if (engagement >= 60) return 'text-yellow-400';
    if (engagement >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  const getEngagementBg = (engagement: number) => {
    if (engagement >= 80) return 'bg-green-500';
    if (engagement >= 60) return 'bg-yellow-500';
    if (engagement >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center">
          <FileText className="w-5 h-5 mr-2 text-purple-500" />
          Content Analytics
        </h3>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as 'all' | 'trending' | 'popular')}
              className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Content</option>
              <option value="trending">Trending</option>
              <option value="popular">Popular</option>
            </select>
          </div>
          
          <div className="flex space-x-1 bg-gray-700 rounded p-1">
            <button
              onClick={() => setSortBy('views')}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                sortBy === 'views'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Views
            </button>
            <button
              onClick={() => setSortBy('engagement')}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                sortBy === 'engagement'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Engagement
            </button>
          </div>
        </div>
      </div>

      {/* Content List */}
      <div className="space-y-3">
        {processedData.map((item, index) => (
          <div
            key={index}
            className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <h4 className="text-white font-medium truncate mb-2">
                  {item.title}
                </h4>
                
                <div className="flex items-center space-x-4 text-sm">
                  <div className="flex items-center space-x-1 text-gray-300">
                    <Eye className="w-4 h-4" />
                    <span>{item.views.toLocaleString()}</span>
                  </div>
                  
                  <div className={`flex items-center space-x-1 ${getEngagementColor(item.engagement)}`}>
                    <Heart className="w-4 h-4" />
                    <span>{item.engagement}%</span>
                  </div>
                  
                  {item.engagement > 70 && (
                    <div className="flex items-center space-x-1 text-green-400">
                      <TrendingUp className="w-4 h-4" />
                      <span className="text-xs">Trending</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="ml-4 text-right">
                <div className="text-lg font-bold text-white">#{index + 1}</div>
                <div className="text-xs text-gray-400">Rank</div>
              </div>
            </div>
            
            {/* Progress Bars */}
            <div className="mt-3 space-y-2">
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Views</span>
                  <span>{((item.views / maxViews) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(item.views / maxViews) * 100}%` }}
                  />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Engagement</span>
                  <span>{item.engagement}%</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${getEngagementBg(item.engagement)}`}
                    style={{ width: `${item.engagement}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="border-t border-gray-700 pt-4 mt-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {processedData.reduce((sum, item) => sum + item.views, 0).toLocaleString()}
            </p>
            <p className="text-sm text-gray-400">Total Views</p>
          </div>
          
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {Math.round(processedData.reduce((sum, item) => sum + item.engagement, 0) / processedData.length)}%
            </p>
            <p className="text-sm text-gray-400">Avg Engagement</p>
          </div>
          
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {processedData.filter(item => item.engagement > 70).length}
            </p>
            <p className="text-sm text-gray-400">Trending Items</p>
          </div>
          
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {Math.round(processedData.reduce((sum, item) => sum + item.views, 0) / processedData.length).toLocaleString()}
            </p>
            <p className="text-sm text-gray-400">Avg Views</p>
          </div>
        </div>
      </div>

      {/* Content Categories */}
      <div className="border-t border-gray-700 pt-4 mt-6">
        <h4 className="text-lg font-medium text-white mb-3">Content Categories</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { name: 'Research Papers', count: 45, color: 'bg-purple-500' },
            { name: 'Chat Conversations', count: 128, color: 'bg-blue-500' },
            { name: 'Document Analysis', count: 67, color: 'bg-green-500' },
            { name: 'Voice Interactions', count: 23, color: 'bg-yellow-500' },
            { name: 'Knowledge Graphs', count: 34, color: 'bg-red-500' },
            { name: 'Workflows', count: 12, color: 'bg-indigo-500' },
          ].map((category, index) => (
            <div key={index} className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${category.color}`} />
                <span className="text-white text-sm font-medium">{category.name}</span>
              </div>
              <p className="text-lg font-bold text-white">{category.count}</p>
              <p className="text-xs text-gray-400">items</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};