/**
 * @fileoverview Advanced Analytics and Insights Service
 * Provides comprehensive analytics tracking, reporting, and insights for the AI Scholar RAG chatbot.
 * Tracks query performance, document usage, user behavior, and system metrics.
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 * @since 2024-01-01
 */

import { AnalyticsData, DocumentAnalytics, PerformanceMetrics, QueryAnalytics, TrendData, UserAnalytics } from '../types';

/**
 * Advanced Analytics and Insights Service
 * 
 * This service provides comprehensive analytics capabilities including:
 * - Query performance tracking and analysis
 * - Document usage statistics and effectiveness metrics
 * - User behavior insights and engagement tracking
 * - System performance monitoring and trend analysis
 * - Knowledge gap identification and recommendations
 * 
 * @class AnalyticsService
 * @example
 * ```typescript
 * import { analyticsService } from './analyticsService';
 * 
 * // Log a query for analytics
 * analyticsService.logQuery({
 *   query: "What is machine learning?",
 *   userId: "user123",
 *   timestamp: new Date(),
 *   responseTime: 1500,
 *   success: true,
 *   satisfaction: 0.85,
 *   intent: "definition",
 *   documentsUsed: ["doc1", "doc2"]
 * });
 * 
 * // Get dashboard data
 * const dashboardData = analyticsService.getDashboardData({
 *   start: new Date('2024-01-01'),
 *   end: new Date('2024-01-31')
 * });
 * ```
 */
export class AnalyticsService {
  private queryLogs: QueryAnalytics[] = [];
  private documentStats: Map<string, DocumentAnalytics> = new Map();
  private userStats: Map<string, UserAnalytics> = new Map();
  private performanceMetrics: PerformanceMetrics[] = [];

  /**
   * Log query analytics data for tracking and analysis
   * 
   * Records comprehensive analytics data for each query including performance metrics,
   * user satisfaction, document usage, and success indicators. This data is used for
   * generating insights, identifying trends, and improving system performance.
   * 
   * @param {QueryAnalytics} analytics - Complete analytics data for the query
   * @param {string} analytics.query - The user's query text
   * @param {string} analytics.userId - Unique identifier for the user
   * @param {Date} analytics.timestamp - When the query was made
   * @param {number} analytics.responseTime - Response time in milliseconds
   * @param {boolean} analytics.success - Whether the query was successful
   * @param {number} analytics.satisfaction - User satisfaction score (0-1)
   * @param {string} analytics.intent - Classified intent of the query
   * @param {string[]} analytics.documentsUsed - Array of document IDs referenced
   * 
   * @returns {void}
   * 
   * @example
   * ```typescript
   * analyticsService.logQuery({
   *   query: "How does neural network training work?",
   *   userId: "user456",
   *   timestamp: new Date(),
   *   responseTime: 2300,
   *   success: true,
   *   satisfaction: 0.92,
   *   intent: "explanation",
   *   documentsUsed: ["ml_basics.pdf", "neural_networks.pdf"]
   * });
   * ```
   */
  logQuery(analytics: QueryAnalytics): void {
    this.queryLogs.push(analytics);
    this.updateUserStats(analytics);
    this.updateDocumentStats(analytics);
  }

  /**
   * Get comprehensive analytics dashboard data for a specified time range
   * 
   * Retrieves and aggregates all analytics data including queries, documents, users,
   * performance metrics, and trends for the specified time period. This data is
   * optimized for dashboard visualization and reporting.
   * 
   * @param {Object} timeRange - Time range for analytics data
   * @param {Date} timeRange.start - Start date for the analytics period
   * @param {Date} timeRange.end - End date for the analytics period
   * 
   * @returns {AnalyticsData} Comprehensive analytics data including:
   *   - queries: Array of query analytics within the time range
   *   - documents: Document usage statistics and metrics
   *   - users: User behavior and engagement metrics
   *   - performance: System performance metrics
   *   - trends: Trend analysis and patterns
   * 
   * @example
   * ```typescript
   * const lastMonth = analyticsService.getDashboardData({
   *   start: new Date('2024-01-01'),
   *   end: new Date('2024-01-31')
   * });
   * 
   * console.log(`Total queries: ${lastMonth.queries.length}`);
   * console.log(`Average response time: ${lastMonth.performance.averageResponseTime}ms`);
   * ```
   */
  getDashboardData(timeRange: { start: Date; end: Date }): AnalyticsData {
    const filteredQueries = this.queryLogs.filter(
      q => q.timestamp >= timeRange.start && q.timestamp <= timeRange.end
    );

    return {
      queries: filteredQueries,
      documents: Array.from(this.documentStats.values()),
      users: Array.from(this.userStats.values()),
      performance: this.calculatePerformanceMetrics(filteredQueries),
      trends: this.calculateTrends(filteredQueries)
    };
  }

  /**
   * Get query insights
   */
  getQueryInsights(): {
    mostCommonQueries: { query: string; count: number }[];
    averageResponseTime: number;
    successRate: number;
    topIntents: { intent: string; count: number }[];
    satisfactionScore: number;
  } {
    const queryFrequency = new Map<string, number>();
    const intentFrequency = new Map<string, number>();
    let totalResponseTime = 0;
    let successCount = 0;
    let totalSatisfaction = 0;
    let satisfactionCount = 0;

    this.queryLogs.forEach(log => {
      // Query frequency
      const normalizedQuery = log.query.toLowerCase().trim();
      queryFrequency.set(normalizedQuery, (queryFrequency.get(normalizedQuery) || 0) + 1);
      
      // Intent frequency
      intentFrequency.set(log.intent, (intentFrequency.get(log.intent) || 0) + 1);
      
      // Performance metrics
      totalResponseTime += log.responseTime;
      if (log.success) successCount++;
      
      // Satisfaction
      if (log.satisfaction > 0) {
        totalSatisfaction += log.satisfaction;
        satisfactionCount++;
      }
    });

    return {
      mostCommonQueries: Array.from(queryFrequency.entries())
        .map(([query, count]) => ({ query, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10),
      
      averageResponseTime: totalResponseTime / this.queryLogs.length,
      successRate: successCount / this.queryLogs.length,
      
      topIntents: Array.from(intentFrequency.entries())
        .map(([intent, count]) => ({ intent, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5),
      
      satisfactionScore: satisfactionCount > 0 ? totalSatisfaction / satisfactionCount : 0
    };
  }

  /**
   * Get document usage analytics
   */
  getDocumentInsights(): {
    mostReferencedDocuments: { documentId: string; references: number }[];
    leastUsedDocuments: { documentId: string; lastUsed: Date }[];
    documentEffectiveness: { documentId: string; effectiveness: number }[];
  } {
    const documentUsage = new Map<string, { references: number; lastUsed: Date; effectiveness: number }>();

    this.queryLogs.forEach(log => {
      log.documentsUsed.forEach(docId => {
        const current = documentUsage.get(docId) || { references: 0, lastUsed: new Date(0), effectiveness: 0 };
        current.references++;
        current.lastUsed = new Date(Math.max(current.lastUsed.getTime(), log.timestamp.getTime()));
        current.effectiveness += log.satisfaction;
        documentUsage.set(docId, current);
      });
    });

    const documents = Array.from(documentUsage.entries()).map(([docId, stats]) => ({
      documentId: docId,
      ...stats,
      effectiveness: stats.effectiveness / stats.references
    }));

    return {
      mostReferencedDocuments: documents
        .sort((a, b) => b.references - a.references)
        .slice(0, 10),
      
      leastUsedDocuments: documents
        .sort((a, b) => a.lastUsed.getTime() - b.lastUsed.getTime())
        .slice(0, 10),
      
      documentEffectiveness: documents
        .sort((a, b) => b.effectiveness - a.effectiveness)
        .slice(0, 10)
    };
  }

  /**
   * Identify knowledge gaps
   */
  identifyKnowledgeGaps(): {
    unansweredQueries: { query: string; frequency: number }[];
    lowSatisfactionTopics: { topic: string; avgSatisfaction: number }[];
    missingDocumentTypes: string[];
  } {
    const failedQueries = this.queryLogs.filter(log => !log.success);
    const lowSatisfactionQueries = this.queryLogs.filter(log => log.satisfaction < 0.5);

    const failedQueryFreq = new Map<string, number>();
    failedQueries.forEach(log => {
      const query = log.query.toLowerCase().trim();
      failedQueryFreq.set(query, (failedQueryFreq.get(query) || 0) + 1);
    });

    const topicSatisfaction = new Map<string, { total: number; count: number }>();
    lowSatisfactionQueries.forEach(log => {
      const topic = log.intent;
      const current = topicSatisfaction.get(topic) || { total: 0, count: 0 };
      current.total += log.satisfaction;
      current.count++;
      topicSatisfaction.set(topic, current);
    });

    return {
      unansweredQueries: Array.from(failedQueryFreq.entries())
        .map(([query, frequency]) => ({ query, frequency }))
        .sort((a, b) => b.frequency - a.frequency)
        .slice(0, 10),
      
      lowSatisfactionTopics: Array.from(topicSatisfaction.entries())
        .map(([topic, stats]) => ({ 
          topic, 
          avgSatisfaction: stats.total / stats.count 
        }))
        .sort((a, b) => a.avgSatisfaction - b.avgSatisfaction)
        .slice(0, 5),
      
      missingDocumentTypes: this.identifyMissingDocumentTypes()
    };
  }

  /**
   * Get user behavior insights
   */
  getUserInsights(): {
    activeUsers: number;
    averageSessionLength: number;
    userRetention: number;
    topUsers: { userId: string; queryCount: number }[];
  } {
    const userActivity = new Map<string, { queries: number; firstSeen: Date; lastSeen: Date }>();

    this.queryLogs.forEach(log => {
      const current = userActivity.get(log.userId) || {
        queries: 0,
        firstSeen: log.timestamp,
        lastSeen: log.timestamp
      };
      
      current.queries++;
      current.firstSeen = new Date(Math.min(current.firstSeen.getTime(), log.timestamp.getTime()));
      current.lastSeen = new Date(Math.max(current.lastSeen.getTime(), log.timestamp.getTime()));
      
      userActivity.set(log.userId, current);
    });

    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const activeUsers = Array.from(userActivity.values()).filter(
      user => user.lastSeen > weekAgo
    ).length;

    const totalSessionTime = Array.from(userActivity.values()).reduce(
      (sum, user) => sum + (user.lastSeen.getTime() - user.firstSeen.getTime()),
      0
    );

    return {
      activeUsers,
      averageSessionLength: totalSessionTime / userActivity.size / (1000 * 60), // minutes
      userRetention: activeUsers / userActivity.size,
      topUsers: Array.from(userActivity.entries())
        .map(([userId, stats]) => ({ userId, queryCount: stats.queries }))
        .sort((a, b) => b.queryCount - a.queryCount)
        .slice(0, 10)
    };
  }

  /**
   * Generate trend analysis
   */
  private calculateTrends(queries: QueryAnalytics[]): TrendData[] {
    const trends: TrendData[] = [];
    
    // Query volume trend
    const dailyQueries = this.groupByDay(queries);
    trends.push({
      period: 'daily',
      metric: 'query_volume',
      value: dailyQueries.reduce((sum, d) => sum + d.value, 0),
      change: 0, // Calculate change from previous period
      type: 'query_volume',
      data: dailyQueries,
      trend: this.calculateTrendDirection(dailyQueries.map(d => d.value))
    });

    // Response time trend
    const dailyResponseTimes = this.groupByDay(queries, 'responseTime');
    trends.push({
      period: 'daily',
      metric: 'response_time',
      value: dailyResponseTimes.reduce((sum, d) => sum + d.value, 0) / dailyResponseTimes.length,
      change: 0, // Calculate change from previous period
      type: 'response_time',
      data: dailyResponseTimes,
      trend: this.calculateTrendDirection(dailyResponseTimes.map(d => d.value))
    });

    // Satisfaction trend
    const dailySatisfaction = this.groupByDay(queries, 'satisfaction');
    trends.push({
      period: 'daily',
      metric: 'satisfaction',
      value: dailySatisfaction.reduce((sum, d) => sum + d.value, 0) / dailySatisfaction.length,
      change: 0, // Calculate change from previous period
      type: 'satisfaction',
      data: dailySatisfaction,
      trend: this.calculateTrendDirection(dailySatisfaction.map(d => d.value))
    });

    return trends;
  }

  /**
   * Group data by day
   */
  private groupByDay(queries: QueryAnalytics[], metric: keyof QueryAnalytics = 'timestamp'): { date: string; value: number }[] {
    const dailyData = new Map<string, number[]>();

    queries.forEach(query => {
      const date = query.timestamp.toISOString().split('T')[0];
      if (!dailyData.has(date)) {
        dailyData.set(date, []);
      }
      
      if (metric === 'timestamp') {
        dailyData.get(date)!.push(1); // Count queries
      } else {
        const value = query[metric] as number;
        if (typeof value === 'number') {
          dailyData.get(date)!.push(value);
        }
      }
    });

    return Array.from(dailyData.entries()).map(([date, values]) => ({
      date,
      value: metric === 'timestamp' 
        ? values.length 
        : values.reduce((sum, v) => sum + v, 0) / values.length
    })).sort((a, b) => a.date.localeCompare(b.date));
  }

  /**
   * Calculate trend direction
   */
  private calculateTrendDirection(values: number[]): 'up' | 'down' | 'stable' {
    if (values.length < 2) return 'stable';
    
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    
    const firstAvg = firstHalf.reduce((sum, v) => sum + v, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, v) => sum + v, 0) / secondHalf.length;
    
    const change = (secondAvg - firstAvg) / firstAvg;
    
    if (change > 0.05) return 'up';
    if (change < -0.05) return 'down';
    return 'stable';
  }

  /**
   * Update user statistics
   */
  private updateUserStats(analytics: QueryAnalytics): void {
    const userId = analytics.userId;
    const current = this.userStats.get(userId) || {
      id: userId,
      name: 'Unknown User',
      totalQueries: 0,
      averageSessionTime: 0,
      lastActive: new Date(),
      topTopics: [],
      averageResponseTime: 0,
      averageSatisfaction: 0
    };

    current.totalQueries++;
    current.averageResponseTime = ((current.averageResponseTime || 0) * (current.totalQueries - 1) + analytics.responseTime) / current.totalQueries;
    current.averageSatisfaction = ((current.averageSatisfaction || 0) * (current.totalQueries - 1) + analytics.satisfaction) / current.totalQueries;
    current.lastActive = analytics.timestamp;

    this.userStats.set(userId, current);
  }

  /**
   * Update document statistics
   */
  private updateDocumentStats(analytics: QueryAnalytics): void {
    analytics.documentsUsed.forEach(docId => {
      const current = this.documentStats.get(docId) || {
        id: docId,
        name: 'Unknown Document',
        views: 0,
        queries: 0,
        lastAccessed: new Date(),
        averageRelevance: 0,
        totalReferences: 0,
        averageSatisfaction: 0,
        lastUsed: new Date(),
        topQueries: []
      };

      current.totalReferences = (current.totalReferences || 0) + 1;
      current.averageSatisfaction = ((current.averageSatisfaction || 0) * (current.totalReferences - 1) + analytics.satisfaction) / current.totalReferences;
      current.lastUsed = analytics.timestamp;

      this.documentStats.set(docId, current);
    });
  }

  /**
   * Calculate performance metrics
   */
  private calculatePerformanceMetrics(queries: QueryAnalytics[]): PerformanceMetrics {
    const totalQueries = queries.length;
    const successfulQueries = queries.filter(q => q.success).length;
    const totalResponseTime = queries.reduce((sum, q) => sum + q.responseTime, 0);
    const totalSatisfaction = queries.reduce((sum, q) => sum + q.satisfaction, 0);

    return {
      totalQueries,
      successRate: successfulQueries / totalQueries,
      averageResponseTime: totalResponseTime / totalQueries,
      averageSatisfaction: totalSatisfaction / totalQueries,
      throughput: totalQueries / 24, // queries per hour (assuming 24-hour period)
      errorRate: (totalQueries - successfulQueries) / totalQueries,
      memoryUsage: 0, // Mock value
      cpuUsage: 0 // Mock value
    };
  }

  /**
   * Identify missing document types
   */
  private identifyMissingDocumentTypes(): string[] {
    // Analyze failed queries to suggest missing document types
    const failedQueries = this.queryLogs.filter(log => !log.success);
    const suggestedTypes: string[] = [];

    failedQueries.forEach(log => {
      const query = log.query.toLowerCase();
      if (query.includes('code') || query.includes('programming')) {
        suggestedTypes.push('Code Documentation');
      }
      if (query.includes('api') || query.includes('endpoint')) {
        suggestedTypes.push('API Documentation');
      }
      if (query.includes('tutorial') || query.includes('how to')) {
        suggestedTypes.push('Tutorial Content');
      }
    });

    return [...new Set(suggestedTypes)];
  }
}

export const analyticsService = new AnalyticsService();