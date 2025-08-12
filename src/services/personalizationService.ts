/**
 * @fileoverview Personalization Service for managing user preferences and personalization data
 * Provides comprehensive user personalization capabilities including preferences management,
 * domain expertise tracking, and adaptive learning insights.
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 * @since 2024-01-01
 */

/**
 * User preferences configuration interface
 * Defines all customizable user settings for the application experience
 * 
 * @interface UserPreferences
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  defaultModel: string;
  responseLength: 'concise' | 'detailed' | 'comprehensive';
  enableVoice: boolean;
  enableNotifications: boolean;
  responseStyle: 'balanced' | 'technical' | 'conversational';
  citationPreference: 'inline' | 'footnotes' | 'bibliography';
  reasoningDisplay: boolean;
  uncertaintyTolerance: number;
  domainAdaptation: boolean;
  enableAdaptiveRetrieval: boolean;
}

/**
 * Domain expertise mapping interface
 * Maps domain names to expertise levels (0-1 scale)
 * 
 * @interface DomainExpertise
 */
export interface DomainExpertise {
  /** Domain name mapped to expertise level (0-1) */
  [domain: string]: number;
}

/**
 * Personalization statistics interface
 * Provides comprehensive metrics about personalization effectiveness
 * 
 * @interface PersonalizationStats
 */
export interface PersonalizationStats {
  /** Total number of searches performed */
  totalSearches: number;
  /** Number of searches that used personalization */
  personalizedSearches: number;
  /** Percentage of searches that were personalized (0-1) */
  personalizationRate: number;
  /** Top domains by search frequency */
  topDomains: { [domain: string]: number };
  /** Average number of results returned per search */
  avgResultsPerSearch: number;
  /** Average user satisfaction score (0-1) */
  avgSatisfaction?: number;
  /** Trend in user satisfaction over time */
  satisfactionTrend?: 'improving' | 'stable' | 'declining';
  /** Number of days covered by these statistics */
  periodDays: number;
}

/**
 * User feedback history interface
 * Tracks user feedback for personalization improvement
 * 
 * @interface FeedbackHistory
 */
export interface FeedbackHistory {
  /** Unique feedback identifier */
  id: string;
  /** ISO timestamp when feedback was given */
  timestamp: string;
  /** Type of feedback (rating, comment, etc.) */
  feedbackType: string;
  /** Numerical rating (1-5 scale) */
  rating?: number;
  /** Optional text comment */
  comment?: string;
  /** Whether feedback has been processed for personalization */
  processed: boolean;
  /** Associated message ID if applicable */
  messageId?: string;
}

/**
 * Learning insights interface
 * Provides analytics about user learning patterns and progress
 * 
 * @interface LearningInsights
 */
export interface LearningInsights {
  /** Total number of queries made by user */
  totalQueries: number;
  /** List of user's most frequently queried topics */
  favoriteTopics: string[];
  /** Average session duration in minutes */
  averageSessionLength: number;
  /** User's preferred response style */
  preferredResponseStyle: string;
  /** Monthly learning progress data */
  learningProgress: Array<{
    /** Month identifier (YYYY-MM) */
    month: string;
    /** Number of queries in that month */
    queries: number;
    /** Number of unique topics explored */
    uniqueTopics: number;
    /** Engagement score (0-1) */
    engagement: number;
  }>;
}

/**
 * Personalization effectiveness metrics interface
 * Compares performance before and after personalization implementation
 * 
 * @interface PersonalizationEffectiveness
 */
export interface PersonalizationEffectiveness {
  /** Metrics before personalization was enabled */
  beforePersonalization: {
    /** Average user satisfaction score (0-1) */
    avgSatisfaction: number;
    /** Average response time in milliseconds */
    avgResponseTime: number;
    /** Average relevance score (0-1) */
    avgRelevance: number;
  };
  /** Metrics after personalization was enabled */
  afterPersonalization: {
    /** Average user satisfaction score (0-1) */
    avgSatisfaction: number;
    /** Average response time in milliseconds */
    avgResponseTime: number;
    /** Average relevance score (0-1) */
    avgRelevance: number;
  };
  /** Calculated improvements */
  improvement: {
    /** Improvement in satisfaction (percentage) */
    satisfactionImprovement: number;
    /** Improvement in response time (percentage) */
    responseTimeImprovement: number;
    /** Improvement in relevance (percentage) */
    relevanceImprovement: number;
  };
}

/**
 * Personalization Service
 * 
 * Manages user preferences, domain expertise tracking, and adaptive learning.
 * Provides comprehensive personalization capabilities to enhance user experience
 * through intelligent adaptation to user behavior and preferences.
 * 
 * @class PersonalizationService
 * @example
 * ```typescript
 * import { personalizationService } from './personalizationService';
 * 
 * // Get user preferences
 * const preferences = await personalizationService.getUserPreferences('user123');
 * 
 * // Update preferences
 * await personalizationService.updateUserPreferences('user123', {
 *   theme: 'dark',
 *   responseLength: 'detailed'
 * });
 * 
 * // Get personalization stats
 * const stats = await personalizationService.getPersonalizationStats('user123');
 * ```
 */
class PersonalizationService {
  /** Base URL for API endpoints */
  private baseUrl = '/api';

  /**
   * Get user preferences
   * 
   * Retrieves the current preferences for a specific user, including theme,
   * language, response style, and other customization options.
   * 
   * @param {string} userId - Unique identifier for the user
   * @returns {Promise<UserPreferences>} User's current preferences
   * 
   * @example
   * ```typescript
   * const preferences = await personalizationService.getUserPreferences('user123');
   * console.log(preferences.theme); // 'dark' | 'light' | 'auto'
   * ```
   */
  async getUserPreferences(userId: string): Promise<UserPreferences> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/preferences`);
      if (!response.ok) {
        throw new Error(`Failed to fetch preferences: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching user preferences:', error);
      // Return default preferences
      return {
        theme: 'dark',
        language: 'en',
        defaultModel: 'mistral',
        responseLength: 'detailed',
        enableVoice: false,
        enableNotifications: true,
        responseStyle: 'balanced',
        citationPreference: 'inline',
        reasoningDisplay: true,
        uncertaintyTolerance: 0.5,
        domainAdaptation: true,
        enableAdaptiveRetrieval: true
      };
    }
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(userId: string, preferences: UserPreferences): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error(`Failed to update preferences: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error updating user preferences:', error);
      throw error;
    }
  }

  /**
   * Get user domain expertise
   */
  async getDomainExpertise(userId: string): Promise<DomainExpertise> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/domain-expertise`);
      if (!response.ok) {
        throw new Error(`Failed to fetch domain expertise: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching domain expertise:', error);
      return {};
    }
  }

  /**
   * Get personalization statistics
   */
  async getPersonalizationStats(userId: string): Promise<PersonalizationStats | null> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/personalization-stats`);
      if (!response.ok) {
        if (response.status === 404) {
          return null; // No stats available yet
        }
        throw new Error(`Failed to fetch personalization stats: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching personalization stats:', error);
      return null;
    }
  }

  /**
   * Get feedback history
   */
  async getFeedbackHistory(userId: string, limit: number = 50): Promise<FeedbackHistory[]> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/feedback-history?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch feedback history: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching feedback history:', error);
      return [];
    }
  }

  /**
   * Get learning insights
   */
  async getLearningInsights(userId: string): Promise<LearningInsights | null> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/learning-insights`);
      if (!response.ok) {
        if (response.status === 404) {
          return null; // No insights available yet
        }
        throw new Error(`Failed to fetch learning insights: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching learning insights:', error);
      return null;
    }
  }

  /**
   * Submit user feedback
   */
  async submitFeedback(
    userId: string,
    feedbackType: 'rating' | 'correction' | 'preference' | 'relevance',
    feedbackValue: unknown,
    messageId?: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feedbackType,
          feedbackValue,
          messageId,
          context
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit feedback: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  }

  /**
   * Submit thumbs up/down feedback
   */
  async submitThumbsFeedback(
    userId: string,
    messageId: string,
    isPositive: boolean,
    context?: Record<string, unknown>
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/feedback/thumbs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messageId,
          isPositive,
          context
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit thumbs feedback: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error submitting thumbs feedback:', error);
      throw error;
    }
  }

  /**
   * Submit detailed rating feedback
   */
  async submitDetailedRating(
    userId: string,
    messageId: string,
    rating: number,
    aspects?: { [aspect: string]: number },
    comment?: string,
    context?: Record<string, unknown>
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/feedback/detailed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messageId,
          rating,
          aspects,
          comment,
          context
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit detailed rating: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error submitting detailed rating:', error);
      throw error;
    }
  }

  /**
   * Get personalization effectiveness metrics
   */
  async getPersonalizationEffectiveness(userId: string): Promise<PersonalizationEffectiveness | null> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/personalization-effectiveness`);
      if (!response.ok) {
        if (response.status === 404) {
          return null; // No effectiveness data available yet
        }
        throw new Error(`Failed to fetch personalization effectiveness: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching personalization effectiveness:', error);
      return null;
    }
  }

  /**
   * Reset user personalization data
   */
  async resetPersonalizationData(userId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/personalization/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to reset personalization data: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error resetting personalization data:', error);
      throw error;
    }
  }

  /**
   * Export user personalization data
   */
  async exportPersonalizationData(userId: string): Promise<Blob> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/personalization/export`);
      if (!response.ok) {
        throw new Error(`Failed to export personalization data: ${response.statusText}`);
      }
      return await response.blob();
    } catch (error) {
      console.error('Error exporting personalization data:', error);
      throw error;
    }
  }

  /**
   * Get domain adaptation settings
   */
  async getDomainAdaptationSettings(userId: string): Promise<Record<string, unknown>> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/domain-adaptation`);
      if (!response.ok) {
        throw new Error(`Failed to fetch domain adaptation settings: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching domain adaptation settings:', error);
      return {};
    }
  }

  /**
   * Update domain adaptation settings
   */
  async updateDomainAdaptationSettings(userId: string, settings: Record<string, unknown>): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/domain-adaptation`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error(`Failed to update domain adaptation settings: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error updating domain adaptation settings:', error);
      throw error;
    }
  }

  /**
   * Get adaptive retrieval statistics
   */
  async getAdaptiveRetrievalStats(userId: string): Promise<Record<string, unknown>> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/adaptive-retrieval-stats`);
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to fetch adaptive retrieval stats: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching adaptive retrieval stats:', error);
      return null;
    }
  }

  /**
   * Trigger personalization model retraining
   */
  async triggerPersonalizationRetraining(userId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/personalization/retrain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger personalization retraining: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error triggering personalization retraining:', error);
      throw error;
    }
  }

  /**
   * Get user behavior analysis
   */
  async getUserBehaviorAnalysis(userId: string): Promise<Record<string, unknown>> {
    try {
      const response = await fetch(`${this.baseUrl}/users/${userId}/behavior-analysis`);
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to fetch user behavior analysis: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching user behavior analysis:', error);
      return null;
    }
  }
}

export const personalizationService = new PersonalizationService();
export default personalizationService;