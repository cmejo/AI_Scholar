/**
 * @fileoverview User Profile and Session Persistence Service
 * Manages user profiles, session data, and conversation history with comprehensive
 * persistence and retrieval capabilities for the AI Scholar application.
 * 
 * @author AI Scholar Team
 * @version 1.0.0
 * @since 2024-01-01
 */

import { User, UserPreferences } from '../types';

/**
 * User session interface
 * Represents an active user session with conversation history and context
 * 
 * @interface UserSession
 */
export interface UserSession {
  id: string;
  userId: string;
  startTime: Date;
  lastActivity: Date;
  conversationHistory: ConversationHistory[];
  context: Record<string, any>;
  preferences: UserPreferences;
}

export interface ConversationHistory {
  id: string;
  sessionId: string;
  timestamp: Date;
  query: string;
  response: string;
  sources: any[];
  feedback?: 'positive' | 'negative';
  tags: string[];
}

export class UserProfileService {
  private users: Map<string, User> = new Map();
  private sessions: Map<string, UserSession> = new Map();
  private conversationHistory: Map<string, ConversationHistory[]> = new Map();

  /**
   * Create or get user profile
   */
  async getOrCreateUser(email: string, name: string): Promise<User> {
    const existingUser = Array.from(this.users.values()).find(u => u.email === email);
    
    if (existingUser) {
      existingUser.lastLogin = new Date();
      return existingUser;
    }

    const newUser: User = {
      id: `user_${Date.now()}`,
      email,
      name,
      role: 'user',
      permissions: [
        { resource: 'documents', actions: ['read'] },
        { resource: 'chat', actions: ['read', 'write'] }
      ],
      preferences: {
        theme: 'dark',
        language: 'en',
        defaultModel: 'mistral',
        responseLength: 'detailed',
        enableVoice: false,
        enableNotifications: true,
        customDashboard: {
          widgets: [],
          layout: 'grid',
          refreshInterval: 30
        }
      },
      createdAt: new Date(),
      lastLogin: new Date()
    };

    this.users.set(newUser.id, newUser);
    return newUser;
  }

  /**
   * Create new session
   */
  createSession(userId: string): UserSession {
    const user = this.users.get(userId);
    if (!user) throw new Error('User not found');

    const session: UserSession = {
      id: `session_${Date.now()}`,
      userId,
      startTime: new Date(),
      lastActivity: new Date(),
      conversationHistory: [],
      context: {},
      preferences: user.preferences
    };

    this.sessions.set(session.id, session);
    return session;
  }

  /**
   * Resume existing session
   */
  resumeSession(sessionId: string): UserSession | null {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.lastActivity = new Date();
      return session;
    }
    return null;
  }

  /**
   * Add conversation to history
   */
  addConversation(sessionId: string, conversation: Omit<ConversationHistory, 'id' | 'sessionId'>): void {
    const session = this.sessions.get(sessionId);
    if (!session) return;

    const historyItem: ConversationHistory = {
      ...conversation,
      id: `conv_${Date.now()}`,
      sessionId
    };

    session.conversationHistory.push(historyItem);
    session.lastActivity = new Date();

    // Also store in user's global history
    if (!this.conversationHistory.has(session.userId)) {
      this.conversationHistory.set(session.userId, []);
    }
    this.conversationHistory.get(session.userId)!.push(historyItem);
  }

  /**
   * Get user's conversation history
   */
  getUserHistory(userId: string, limit: number = 50): ConversationHistory[] {
    const history = this.conversationHistory.get(userId) || [];
    return history
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }

  /**
   * Update user preferences
   */
  updateUserPreferences(userId: string, preferences: Partial<UserPreferences>): void {
    const user = this.users.get(userId);
    if (user) {
      user.preferences = { ...user.preferences, ...preferences };
      
      // Update active sessions
      Array.from(this.sessions.values())
        .filter(session => session.userId === userId)
        .forEach(session => {
          session.preferences = user.preferences;
        });
    }
  }

  /**
   * Get user learning insights
   */
  getUserInsights(userId: string): {
    totalQueries: number;
    favoriteTopics: string[];
    averageSessionLength: number;
    preferredResponseStyle: string;
    learningProgress: any[];
  } {
    const history = this.getUserHistory(userId);
    const sessions = Array.from(this.sessions.values()).filter(s => s.userId === userId);

    // Analyze topics
    const topicFrequency: Map<string, number> = new Map();
    history.forEach(conv => {
      conv.tags.forEach(tag => {
        topicFrequency.set(tag, (topicFrequency.get(tag) || 0) + 1);
      });
    });

    const favoriteTopics = Array.from(topicFrequency.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([topic]) => topic);

    // Calculate average session length
    const avgSessionLength = sessions.length > 0
      ? sessions.reduce((sum, session) => {
          const duration = session.lastActivity.getTime() - session.startTime.getTime();
          return sum + duration;
        }, 0) / sessions.length / (1000 * 60) // Convert to minutes
      : 0;

    return {
      totalQueries: history.length,
      favoriteTopics,
      averageSessionLength: avgSessionLength,
      preferredResponseStyle: this.analyzeResponsePreference(history),
      learningProgress: this.analyzeLearningProgress(history)
    };
  }

  /**
   * Analyze user's response style preference
   */
  private analyzeResponsePreference(history: ConversationHistory[]): string {
    const positiveFeedback = history.filter(h => h.feedback === 'positive');
    
    if (positiveFeedback.length === 0) return 'balanced';
    
    const avgResponseLength = positiveFeedback.reduce(
      (sum, h) => sum + h.response.length, 0
    ) / positiveFeedback.length;

    if (avgResponseLength < 200) return 'concise';
    if (avgResponseLength > 500) return 'detailed';
    return 'balanced';
  }

  /**
   * Analyze learning progress over time
   */
  private analyzeLearningProgress(history: ConversationHistory[]): any[] {
    const monthlyProgress: Map<string, { queries: number; topics: Set<string> }> = new Map();
    
    history.forEach(conv => {
      const monthKey = conv.timestamp.toISOString().substring(0, 7); // YYYY-MM
      
      if (!monthlyProgress.has(monthKey)) {
        monthlyProgress.set(monthKey, { queries: 0, topics: new Set() });
      }
      
      const progress = monthlyProgress.get(monthKey)!;
      progress.queries++;
      conv.tags.forEach(tag => progress.topics.add(tag));
    });

    return Array.from(monthlyProgress.entries()).map(([month, data]) => ({
      month,
      queries: data.queries,
      uniqueTopics: data.topics.size,
      engagement: data.queries * data.topics.size
    }));
  }

  /**
   * Clean up old sessions
   */
  cleanupOldSessions(maxAgeHours: number = 24): void {
    const cutoffTime = new Date(Date.now() - maxAgeHours * 60 * 60 * 1000);
    
    Array.from(this.sessions.entries()).forEach(([sessionId, session]) => {
      if (session.lastActivity < cutoffTime) {
        this.sessions.delete(sessionId);
      }
    });
  }
}

export const userProfileService = new UserProfileService();