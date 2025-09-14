/**
 * User Behavior Analytics Component - User activity visualization
 * Implements part of task 2.3: Add UserBehaviorAnalytics component with user activity visualization
 */

import React, { useState, useMemo } from 'react';
import { 
  Users, 
  User, 
  Clock, 
  Activity, 
  TrendingUp, 
  Calendar,
  Search,
  Filter,
  Eye,
  MessageSquare,
  Star,
  BarChart3,
  PieChart
} from 'lucide-react';
import { UserAnalytics, QueryAnalytics } from '../../../types/ui';

interface UserBehaviorAnalyticsProps {
  users: UserAnalytics[];
  queries: QueryAnalytics[];
  loading?: boolean;
  timeRange: string;
}

interface UserSegment {
  name: string;
  count: number;
  percentage: number;
  color: string;
  description: string;
}

interface ActivityPattern {
  hour: number;
  activity: number;
  label: string;
}

interface UserInsight {
  type: 'engagement' | 'satisfaction' | 'activity' | 'retention';
  title: string;
  value: string;
  trend: 'up' | 'down' | 'stable';
  description: string;
  icon: React.ReactNode;
}

export const UserBehaviorAnalytics: React.FC<UserBehaviorAnalyticsProps> = ({
  users,
  queries,
  loading = false,
  timeRange
}) => {
  const [selectedView, setSelectedView] = useState<'overview' | 'segments' | 'activity' | 'engagement'>('overview');
  const [sortBy, setSortBy] = useState<'queryCount' | 'lastActive' | 'satisfactionScore'>('queryCount');
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all');

  // Calculate user segments
  const userSegments = useMemo((): UserSegment[] => {
    if (!users.length) return [];

    const totalUsers = users.length;
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Segment by activity level
    const highActivity = users.filter(u => u.queryCount >= 50);
    const mediumActivity = users.filter(u => u.queryCount >= 10 && u.queryCount < 50);
    const lowActivity = users.filter(u => u.queryCount < 10);

    // Segment by recency
    const activeUsers = users.filter(u => new Date(u.lastActive) > weekAgo);
    const recentUsers = users.filter(u => {
      const lastActive = new Date(u.lastActive);
      return lastActive <= weekAgo && lastActive > monthAgo;
    });
    const inactiveUsers = users.filter(u => new Date(u.lastActive) <= monthAgo);

    return [
      {
        name: 'Power Users',
        count: highActivity.length,
        percentage: (highActivity.length / totalUsers) * 100,
        color: 'bg-green-500',
        description: '50+ queries'
      },
      {
        name: 'Regular Users',
        count: mediumActivity.length,
        percentage: (mediumActivity.length / totalUsers) * 100,
        color: 'bg-blue-500',
        description: '10-49 queries'
      },
      {
        name: 'Light Users',
        count: lowActivity.length,
        percentage: (lowActivity.length / totalUsers) * 100,
        color: 'bg-yellow-500',
        description: '<10 queries'
      },
      {
        name: 'Active',
        count: activeUsers.length,
        percentage: (activeUsers.length / totalUsers) * 100,
        color: 'bg-green-400',
        description: 'Last 7 days'
      },
      {
        name: 'Recent',
        count: recentUsers.length,
        percentage: (recentUsers.length / totalUsers) * 100,
        color: 'bg-yellow-400',
        description: '7-30 days ago'
      },
      {
        name: 'Inactive',
        count: inactiveUsers.length,
        percentage: (inactiveUsers.length / totalUsers) * 100,
        color: 'bg-gray-500',
        description: '>30 days ago'
      }
    ];
  }, [users]);

  // Calculate activity patterns by hour
  const activityPatterns = useMemo((): ActivityPattern[] => {
    if (!queries.length) return [];

    const hourlyActivity = new Array(24).fill(0);
    
    queries.forEach(query => {
      const hour = new Date(query.timestamp).getHours();
      hourlyActivity[hour] += query.count;
    });

    const maxActivity = Math.max(...hourlyActivity);

    return hourlyActivity.map((activity, hour) => ({
      hour,
      activity: maxActivity > 0 ? (activity / maxActivity) * 100 : 0,
      label: `${hour}:00`
    }));
  }, [queries]);

  // Calculate user insights
  const userInsights = useMemo((): UserInsight[] => {
    if (!users.length) return [];

    const totalQueries = users.reduce((sum, u) => sum + u.queryCount, 0);
    const avgSatisfaction = users.reduce((sum, u) => sum + u.satisfactionScore, 0) / users.length;
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const activeUsers = users.filter(u => new Date(u.lastActive) > weekAgo).length;
    const retentionRate = (activeUsers / users.length) * 100;

    return [
      {
        type: 'engagement',
        title: 'Avg Queries per User',
        value: (totalQueries / users.length).toFixed(1),
        trend: 'up',
        description: 'User engagement level',
        icon: <MessageSquare className="w-5 h-5 text-blue-400" />
      },
      {
        type: 'satisfaction',
        title: 'Satisfaction Score',
        value: `${(avgSatisfaction * 100).toFixed(1)}%`,
        trend: avgSatisfaction > 0.7 ? 'up' : avgSatisfaction > 0.5 ? 'stable' : 'down',
        description: 'Overall user satisfaction',
        icon: <Star className="w-5 h-5 text-yellow-400" />
      },
      {
        type: 'activity',
        title: 'Active Users',
        value: activeUsers.toString(),
        trend: 'up',
        description: 'Users active in last 7 days',
        icon: <Activity className="w-5 h-5 text-green-400" />
      },
      {
        type: 'retention',
        title: 'Retention Rate',
        value: `${retentionRate.toFixed(1)}%`,
        trend: retentionRate > 70 ? 'up' : retentionRate > 50 ? 'stable' : 'down',
        description: 'Weekly user retention',
        icon: <Users className="w-5 h-5 text-purple-400" />
      }
    ];
  }, [users]);

  // Filter and sort users
  const filteredUsers = useMemo(() => {
    let filtered = [...users];

    // Apply activity filter
    if (filterActive !== 'all') {
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      if (filterActive === 'active') {
        filtered = filtered.filter(u => new Date(u.lastActive) > weekAgo);
      } else {
        filtered = filtered.filter(u => new Date(u.lastActive) <= weekAgo);
      }
    }

    // Sort users
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'queryCount':
          return b.queryCount - a.queryCount;
        case 'lastActive':
          return new Date(b.lastActive).getTime() - new Date(a.lastActive).getTime();
        case 'satisfactionScore':
          return b.satisfactionScore - a.satisfactionScore;
        default:
          return 0;
      }
    });

    return filtered.slice(0, 10); // Top 10 users
  }, [users, filterActive, sortBy]);

  // Activity heatmap component
  const ActivityHeatmap: React.FC = () => (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-gray-300">Activity by Hour</h4>
      <div className="flex items-end justify-between h-32 space-x-1">
        {activityPatterns.map((pattern, index) => (
          <div key={index} className="flex-1 flex flex-col items-center group">
            <div className="flex-1 flex items-end">
              <div
                className="w-full bg-blue-500 rounded-t transition-all duration-300 hover:bg-blue-400"
                style={{ height: `${Math.max(pattern.activity, 2)}%` }}
                title={`${pattern.label}: ${pattern.activity.toFixed(1)}% activity`}
              />
            </div>
            {index % 4 === 0 && (
              <div className="text-xs text-gray-500 mt-1">{pattern.label}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  // User segment chart
  const UserSegmentChart: React.FC<{ segments: UserSegment[] }> = ({ segments }) => (
    <div className="space-y-4">
      {segments.map((segment, index) => (
        <div key={index} className="flex items-center space-x-4">
          <div className={`w-4 h-4 rounded ${segment.color}`} />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-white">{segment.name}</span>
              <span className="text-sm text-gray-400">{segment.count} users</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${segment.color}`}
                style={{ width: `${segment.percentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">{segment.description}</p>
          </div>
          <span className="text-sm font-medium text-white">
            {segment.percentage.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h2 className="text-xl font-semibold text-white">User Behavior Analytics</h2>
          <p className="text-sm text-gray-400">User activity and engagement insights for {timeRange}</p>
        </div>
        
        {/* View selector */}
        <div className="flex items-center space-x-2">
          {['overview', 'segments', 'activity', 'engagement'].map((view) => (
            <button
              key={view}
              onClick={() => setSelectedView(view as any)}
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                selectedView === view 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* User Insights Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {userInsights.map((insight, index) => (
          <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              {insight.icon}
              {insight.trend === 'up' ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : insight.trend === 'down' ? (
                <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />
              ) : (
                <Activity className="w-4 h-4 text-gray-400" />
              )}
            </div>
            <div className="mb-1">
              <span className="text-2xl font-bold text-white">{insight.value}</span>
            </div>
            <div className="text-sm text-gray-400">{insight.title}</div>
            <div className="text-xs text-gray-500 mt-1">{insight.description}</div>
          </div>
        ))}
      </div>

      {/* Main Content Based on Selected View */}
      {selectedView === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* User Segments */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">User Segments</h3>
            <UserSegmentChart segments={userSegments.slice(0, 3)} />
          </div>

          {/* Activity Patterns */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Activity Patterns</h3>
            <ActivityHeatmap />
          </div>
        </div>
      )}

      {selectedView === 'segments' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Detailed User Segments</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-4">By Activity Level</h4>
              <UserSegmentChart segments={userSegments.slice(0, 3)} />
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-4">By Recency</h4>
              <UserSegmentChart segments={userSegments.slice(3, 6)} />
            </div>
          </div>
        </div>
      )}

      {selectedView === 'activity' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Activity Analysis</h3>
          <div className="space-y-6">
            <ActivityHeatmap />
            
            {/* Activity summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-700 rounded-lg">
                <div className="text-2xl font-bold text-white">
                  {activityPatterns.reduce((max, p) => Math.max(max, p.activity), 0).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-400">Peak Activity</div>
              </div>
              <div className="text-center p-4 bg-gray-700 rounded-lg">
                <div className="text-2xl font-bold text-white">
                  {activityPatterns.findIndex(p => p.activity === Math.max(...activityPatterns.map(p => p.activity)))}:00
                </div>
                <div className="text-sm text-gray-400">Peak Hour</div>
              </div>
              <div className="text-center p-4 bg-gray-700 rounded-lg">
                <div className="text-2xl font-bold text-white">
                  {(activityPatterns.reduce((sum, p) => sum + p.activity, 0) / 24).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-400">Avg Activity</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedView === 'engagement' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">Filters:</span>
            </div>
            
            <select
              value={filterActive}
              onChange={(e) => setFilterActive(e.target.value as any)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
            >
              <option value="all">All Users</option>
              <option value="active">Active Users</option>
              <option value="inactive">Inactive Users</option>
            </select>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
            >
              <option value="queryCount">Sort by Queries</option>
              <option value="lastActive">Sort by Last Active</option>
              <option value="satisfactionScore">Sort by Satisfaction</option>
            </select>
          </div>

          {/* Top Users List */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Top Users</h3>
            <div className="space-y-3">
              {filteredUsers.map((user, index) => (
                <div key={user.id} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{user.name}</p>
                      <p className="text-xs text-gray-400">
                        Last active: {new Date(user.lastActive).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-6 text-right">
                    <div>
                      <p className="text-sm font-medium text-white">{user.queryCount}</p>
                      <p className="text-xs text-gray-400">queries</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {(user.satisfactionScore * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-gray-400">satisfaction</p>
                    </div>
                    <div className="flex items-center space-x-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-3 h-3 ${
                            i < user.satisfactionScore * 5 
                              ? 'text-yellow-400 fill-current' 
                              : 'text-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserBehaviorAnalytics;