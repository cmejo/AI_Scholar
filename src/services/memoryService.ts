// Memory and Context Management Service
import { ConversationMemory, MemoryItem, User } from '../types';

export class MemoryService {
  private memories: Map<string, ConversationMemory> = new Map();
  private maxShortTermItems = 50;
  private maxLongTermItems = 200;

  /**
   * Get or create memory for user
   */
  getMemory(userId: string): ConversationMemory {
    if (!this.memories.has(userId)) {
      this.memories.set(userId, {
        id: `memory_${userId}`,
        userId,
        shortTermMemory: [],
        longTermMemory: [],
        contextSummary: '',
        preferences: {
          responseStyle: 'balanced',
          topicInterests: [],
          preferredSources: [],
          languageLevel: 'intermediate'
        },
        lastUpdated: new Date()
      });
    }
    
    return this.memories.get(userId)!;
  }

  /**
   * Add memory item
   */
  addMemory(userId: string, item: Omit<MemoryItem, 'id' | 'timestamp'>): void {
    const memory = this.getMemory(userId);
    
    const memoryItem: MemoryItem = {
      ...item,
      id: `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };

    // Add to short-term memory
    memory.shortTermMemory.unshift(memoryItem);
    
    // Maintain size limits
    if (memory.shortTermMemory.length > this.maxShortTermItems) {
      const oldItems = memory.shortTermMemory.splice(this.maxShortTermItems);
      
      // Move important items to long-term memory
      const importantItems = oldItems.filter(item => item.importance > 0.7);
      memory.longTermMemory.push(...importantItems);
      
      // Maintain long-term memory size
      if (memory.longTermMemory.length > this.maxLongTermItems) {
        memory.longTermMemory = memory.longTermMemory
          .sort((a, b) => b.importance - a.importance)
          .slice(0, this.maxLongTermItems);
      }
    }
    
    memory.lastUpdated = new Date();
    this.updateContextSummary(memory);
  }

  /**
   * Retrieve relevant memories for query
   */
  getRelevantMemories(userId: string, query: string, limit: number = 10): MemoryItem[] {
    const memory = this.getMemory(userId);
    const allMemories = [...memory.shortTermMemory, ...memory.longTermMemory];
    
    // Score memories based on relevance to query
    const scoredMemories = allMemories.map(item => ({
      item,
      score: this.calculateRelevanceScore(item, query)
    }));
    
    return scoredMemories
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(scored => scored.item);
  }

  /**
   * Update user preferences based on interactions
   */
  updatePreferences(userId: string, interaction: {
    query: string;
    response: string;
    feedback?: 'positive' | 'negative';
    topics: string[];
  }): void {
    const memory = this.getMemory(userId);
    
    // Update topic interests
    interaction.topics.forEach(topic => {
      const existing = memory.preferences.topicInterests.find(t => t.topic === topic);
      if (existing) {
        existing.interest += interaction.feedback === 'positive' ? 0.1 : -0.05;
        existing.interest = Math.max(0, Math.min(1, existing.interest));
      } else {
        memory.preferences.topicInterests.push({
          topic,
          interest: interaction.feedback === 'positive' ? 0.7 : 0.3
        });
      }
    });
    
    // Learn response style preferences
    if (interaction.feedback === 'positive') {
      const responseLength = interaction.response.length;
      if (responseLength < 200) {
        memory.preferences.responseStyle = 'concise';
      } else if (responseLength > 500) {
        memory.preferences.responseStyle = 'detailed';
      }
    }
    
    memory.lastUpdated = new Date();
  }

  /**
   * Compress conversation context
   */
  compressContext(userId: string, conversation: any[]): string {
    const memory = this.getMemory(userId);
    
    // Extract key points from conversation
    const keyPoints = this.extractKeyPoints(conversation);
    
    // Combine with existing context
    const combinedContext = [memory.contextSummary, ...keyPoints].join(' ');
    
    // Summarize if too long
    if (combinedContext.length > 1000) {
      return this.summarizeContext(combinedContext);
    }
    
    return combinedContext;
  }

  /**
   * Get conversation context for new queries
   */
  getConversationContext(userId: string): string {
    const memory = this.getMemory(userId);
    const recentMemories = memory.shortTermMemory.slice(0, 5);
    
    const context = [
      memory.contextSummary,
      ...recentMemories.map(item => `${item.type}: ${item.content}`)
    ].filter(Boolean).join('\n');
    
    return context;
  }

  /**
   * Calculate relevance score for memory item
   */
  private calculateRelevanceScore(item: MemoryItem, query: string): number {
    let score = 0;
    
    // Content similarity (simple keyword matching)
    const queryWords = query.toLowerCase().split(/\s+/);
    const itemWords = item.content.toLowerCase().split(/\s+/);
    const commonWords = queryWords.filter(word => itemWords.includes(word));
    score += (commonWords.length / queryWords.length) * 0.4;
    
    // Recency boost
    const daysSince = (Date.now() - item.timestamp.getTime()) / (1000 * 60 * 60 * 24);
    score += Math.max(0, (7 - daysSince) / 7) * 0.3;
    
    // Importance boost
    score += item.importance * 0.3;
    
    return score;
  }

  /**
   * Update context summary
   */
  private updateContextSummary(memory: ConversationMemory): void {
    const recentItems = memory.shortTermMemory.slice(0, 10);
    const keyFacts = recentItems
      .filter(item => item.type === 'fact' && item.importance > 0.5)
      .map(item => item.content)
      .join('. ');
    
    memory.contextSummary = keyFacts.length > 0 
      ? `Recent context: ${keyFacts}`
      : 'No significant context available';
  }

  /**
   * Extract key points from conversation
   */
  private extractKeyPoints(conversation: any[]): string[] {
    return conversation
      .filter(msg => msg.role === 'user')
      .map(msg => msg.content)
      .slice(-3); // Last 3 user messages
  }

  /**
   * Summarize context when it gets too long
   */
  private summarizeContext(context: string): string {
    // Simple summarization - in production, use a summarization model
    const sentences = context.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const importantSentences = sentences
      .filter(sentence => {
        const words = sentence.toLowerCase().split(/\s+/);
        return words.some(word => 
          ['important', 'key', 'main', 'significant', 'critical'].includes(word)
        );
      })
      .slice(0, 3);
    
    return importantSentences.join('. ') + '.';
  }

  /**
   * Clear old memories
   */
  clearOldMemories(userId: string, daysOld: number = 30): void {
    const memory = this.getMemory(userId);
    const cutoffDate = new Date(Date.now() - daysOld * 24 * 60 * 60 * 1000);
    
    memory.shortTermMemory = memory.shortTermMemory.filter(
      item => item.timestamp > cutoffDate
    );
    
    memory.longTermMemory = memory.longTermMemory.filter(
      item => item.timestamp > cutoffDate || item.importance > 0.8
    );
    
    memory.lastUpdated = new Date();
  }
}

export const memoryService = new MemoryService();