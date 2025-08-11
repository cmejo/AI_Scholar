// Personalization Service for managing user preferences and personalization data

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

export interface DomainExpertise {
  [domain: string]: number;
}

export interface PersonalizationStats {
  totalSearches: number;
  personalizedSearches: number;
  personalizationRate: number;
  topDomains: { [domain: string]: number };
  avgResultsPerSearch: number;
  avgSatisfaction?: number;
  satisfactionTrend?: 'improving' | 'stable' | 'declining';
  periodDays: number;
}

export interface FeedbackHistory {
  id: string;
  timestamp: string;
  feedbackType: string;
  rating?: number;
  comment?: string;
  processed: boolean;
  messageId?: string;
}

export interface LearningInsights {
  totalQueries: number;
  favoriteTopics: string[];
  averageSessionLength: number;
  preferredResponseStyle: string;
  learningProgress: Array<{
    month: string;
    queries: number;
    uniqueTopics: number;
    engagement: number;
  }>;
}

export interface PersonalizationEffectiveness {
  beforePersonalization: {
    avgSatisfaction: number;
    avgResponseTime: number;
    avgRelevance: number;
  };
  afterPersonalization: {
    avgSatisfaction: number;
    avgResponseTime: number;
    avgRelevance: number;
  };
  improvement: {
    satisfactionImprovement: number;
    responseTimeImprovement: number;
    relevanceImprovement: number;
  };
}

class PersonalizationService {
  private baseUrl = '/api';

  /**
   * Get user preferences
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