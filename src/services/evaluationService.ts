// Automatic Evaluation Metrics Service
export interface EvaluationMetrics {
  retrievalQuality: {
    mrr: number; // Mean Reciprocal Rank
    recallAtK: Record<number, number>; // Recall@1, Recall@5, etc.
    precisionAtK: Record<number, number>; // Precision@1, Precision@5, etc.
    ndcg: number; // Normalized Discounted Cumulative Gain
  };
  responseQuality: {
    bleuScore: number;
    rougeScore: { rouge1: number; rouge2: number; rougeL: number };
    semanticSimilarity: number;
    factualAccuracy: number;
    coherence: number;
  };
  performance: {
    responseLatency: number;
    tokenUsage: {
      inputTokens: number;
      outputTokens: number;
      totalTokens: number;
    };
    throughput: number; // queries per second
  };
  userSatisfaction: {
    averageRating: number;
    feedbackCount: number;
    positiveRatio: number;
  };
}

export interface QueryEvaluation {
  queryId: string;
  timestamp: Date;
  query: string;
  response: string;
  groundTruth?: string;
  retrievedDocuments: any[];
  relevantDocuments: any[];
  metrics: EvaluationMetrics;
}

export class EvaluationService {
  private evaluations: QueryEvaluation[] = [];
  private performanceLog: any[] = [];

  /**
   * Evaluate a complete RAG query
   */
  async evaluateQuery(
    queryId: string,
    query: string,
    response: string,
    retrievedDocuments: any[],
    relevantDocuments: any[] = [],
    groundTruth?: string
  ): Promise<QueryEvaluation> {
    const startTime = Date.now();
    
    const evaluation: QueryEvaluation = {
      queryId,
      timestamp: new Date(),
      query,
      response,
      groundTruth,
      retrievedDocuments,
      relevantDocuments,
      metrics: {
        retrievalQuality: this.evaluateRetrievalQuality(retrievedDocuments, relevantDocuments),
        responseQuality: await this.evaluateResponseQuality(response, groundTruth),
        performance: this.evaluatePerformance(startTime, response),
        userSatisfaction: this.getUserSatisfactionMetrics(queryId)
      }
    };

    this.evaluations.push(evaluation);
    this.logPerformance(evaluation);
    
    return evaluation;
  }

  /**
   * Get aggregated metrics over time period
   */
  getAggregatedMetrics(timeRange: { start: Date; end: Date }): EvaluationMetrics {
    const relevantEvaluations = this.evaluations.filter(
      evaluation => evaluation.timestamp >= timeRange.start && evaluation.timestamp <= timeRange.end
    );

    if (relevantEvaluations.length === 0) {
      return this.getEmptyMetrics();
    }

    return {
      retrievalQuality: this.aggregateRetrievalMetrics(relevantEvaluations),
      responseQuality: this.aggregateResponseMetrics(relevantEvaluations),
      performance: this.aggregatePerformanceMetrics(relevantEvaluations),
      userSatisfaction: this.aggregateUserSatisfactionMetrics(relevantEvaluations)
    };
  }

  /**
   * Generate evaluation dashboard data
   */
  getDashboardData(): {
    overallScore: number;
    trends: any[];
    topIssues: string[];
    recommendations: string[];
    detailedMetrics: EvaluationMetrics;
  } {
    const last30Days = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const metrics = this.getAggregatedMetrics({ start: last30Days, end: new Date() });
    
    const overallScore = this.calculateOverallScore(metrics);
    const trends = this.calculateTrends();
    const topIssues = this.identifyTopIssues(metrics);
    const recommendations = this.generateRecommendations(metrics, topIssues);

    return {
      overallScore,
      trends,
      topIssues,
      recommendations,
      detailedMetrics: metrics
    };
  }

  /**
   * Evaluate retrieval quality
   */
  private evaluateRetrievalQuality(retrieved: any[], relevant: any[]): EvaluationMetrics['retrievalQuality'] {
    if (relevant.length === 0) {
      // If no ground truth, use heuristic evaluation
      return this.heuristicRetrievalEvaluation(retrieved);
    }

    const relevantIds = new Set(relevant.map(doc => doc.id));
    const retrievedIds = retrieved.map(doc => doc.id);
    
    // Calculate MRR
    let mrr = 0;
    for (let i = 0; i < retrievedIds.length; i++) {
      if (relevantIds.has(retrievedIds[i])) {
        mrr = 1 / (i + 1);
        break;
      }
    }

    // Calculate Recall@K and Precision@K
    const recallAtK: Record<number, number> = {};
    const precisionAtK: Record<number, number> = {};
    
    [1, 3, 5, 10].forEach(k => {
      const topK = retrievedIds.slice(0, k);
      const relevantInTopK = topK.filter(id => relevantIds.has(id)).length;
      
      recallAtK[k] = relevantInTopK / relevant.length;
      precisionAtK[k] = relevantInTopK / k;
    });

    // Calculate NDCG
    const ndcg = this.calculateNDCG(retrievedIds, relevantIds, 10);

    return { mrr, recallAtK, precisionAtK, ndcg };
  }

  /**
   * Heuristic retrieval evaluation when no ground truth available
   */
  private heuristicRetrievalEvaluation(retrieved: any[]): EvaluationMetrics['retrievalQuality'] {
    // Use relevance scores as proxy for quality
    const avgRelevance = retrieved.reduce((sum, doc) => sum + (doc.relevanceScore || 0), 0) / retrieved.length;
    
    return {
      mrr: avgRelevance,
      recallAtK: { 1: avgRelevance, 3: avgRelevance, 5: avgRelevance, 10: avgRelevance },
      precisionAtK: { 1: avgRelevance, 3: avgRelevance, 5: avgRelevance, 10: avgRelevance },
      ndcg: avgRelevance
    };
  }

  /**
   * Calculate NDCG (Normalized Discounted Cumulative Gain)
   */
  private calculateNDCG(retrieved: string[], relevant: Set<string>, k: number): number {
    const dcg = retrieved.slice(0, k).reduce((sum, id, index) => {
      const relevance = relevant.has(id) ? 1 : 0;
      return sum + relevance / Math.log2(index + 2);
    }, 0);

    const idealDcg = Array.from(relevant).slice(0, k).reduce((sum, _, index) => {
      return sum + 1 / Math.log2(index + 2);
    }, 0);

    return idealDcg > 0 ? dcg / idealDcg : 0;
  }

  /**
   * Evaluate response quality
   */
  private async evaluateResponseQuality(
    response: string, 
    groundTruth?: string
  ): Promise<EvaluationMetrics['responseQuality']> {
    const bleuScore = groundTruth ? this.calculateBLEU(response, groundTruth) : 0;
    const rougeScore = groundTruth ? this.calculateROUGE(response, groundTruth) : { rouge1: 0, rouge2: 0, rougeL: 0 };
    const semanticSimilarity = groundTruth ? await this.calculateSemanticSimilarity(response, groundTruth) : 0;
    const factualAccuracy = this.evaluateFactualAccuracy(response);
    const coherence = this.evaluateCoherence(response);

    return {
      bleuScore,
      rougeScore,
      semanticSimilarity,
      factualAccuracy,
      coherence
    };
  }

  /**
   * Calculate BLEU score
   */
  private calculateBLEU(candidate: string, reference: string): number {
    const candidateTokens = candidate.toLowerCase().split(/\s+/);
    const referenceTokens = reference.toLowerCase().split(/\s+/);
    
    // Simplified BLEU-1 calculation
    const candidateSet = new Set(candidateTokens);
    const referenceSet = new Set(referenceTokens);
    
    const intersection = new Set([...candidateSet].filter(x => referenceSet.has(x)));
    const precision = intersection.size / candidateSet.size;
    
    // Brevity penalty
    const bp = candidateTokens.length >= referenceTokens.length ? 1 : 
      Math.exp(1 - referenceTokens.length / candidateTokens.length);
    
    return bp * precision;
  }

  /**
   * Calculate ROUGE scores
   */
  private calculateROUGE(candidate: string, reference: string): { rouge1: number; rouge2: number; rougeL: number } {
    const candidateTokens = candidate.toLowerCase().split(/\s+/);
    const referenceTokens = reference.toLowerCase().split(/\s+/);
    
    // ROUGE-1 (unigram overlap)
    const candidateUnigrams = new Set(candidateTokens);
    const referenceUnigrams = new Set(referenceTokens);
    const unigramOverlap = new Set([...candidateUnigrams].filter(x => referenceUnigrams.has(x)));
    const rouge1 = unigramOverlap.size / referenceUnigrams.size;
    
    // ROUGE-2 (bigram overlap) - simplified
    const candidateBigrams = this.getBigrams(candidateTokens);
    const referenceBigrams = this.getBigrams(referenceTokens);
    const bigramOverlap = candidateBigrams.filter(bg => referenceBigrams.includes(bg));
    const rouge2 = referenceBigrams.length > 0 ? bigramOverlap.length / referenceBigrams.length : 0;
    
    // ROUGE-L (Longest Common Subsequence) - simplified
    const lcs = this.longestCommonSubsequence(candidateTokens, referenceTokens);
    const rougeL = referenceTokens.length > 0 ? lcs / referenceTokens.length : 0;
    
    return { rouge1, rouge2, rougeL };
  }

  /**
   * Get bigrams from tokens
   */
  private getBigrams(tokens: string[]): string[] {
    const bigrams: string[] = [];
    for (let i = 0; i < tokens.length - 1; i++) {
      bigrams.push(`${tokens[i]} ${tokens[i + 1]}`);
    }
    return bigrams;
  }

  /**
   * Calculate longest common subsequence length
   */
  private longestCommonSubsequence(seq1: string[], seq2: string[]): number {
    const dp: number[][] = Array(seq1.length + 1).fill(null).map(() => Array(seq2.length + 1).fill(0));
    
    for (let i = 1; i <= seq1.length; i++) {
      for (let j = 1; j <= seq2.length; j++) {
        if (seq1[i - 1] === seq2[j - 1]) {
          dp[i][j] = dp[i - 1][j - 1] + 1;
        } else {
          dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
        }
      }
    }
    
    return dp[seq1.length][seq2.length];
  }

  /**
   * Calculate semantic similarity (mock implementation)
   */
  private async calculateSemanticSimilarity(text1: string, text2: string): Promise<number> {
    // In production, use actual embedding models
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));
    const intersection = new Set([...words1].filter(x => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    
    return intersection.size / union.size;
  }

  /**
   * Evaluate factual accuracy
   */
  private evaluateFactualAccuracy(response: string): number {
    let accuracy = 0.7; // Base score
    
    // Check for uncertainty markers (good for accuracy)
    const uncertaintyMarkers = ['might', 'could', 'possibly', 'likely', 'according to'];
    if (uncertaintyMarkers.some(marker => response.toLowerCase().includes(marker))) {
      accuracy += 0.1;
    }
    
    // Check for absolute statements without sources (bad for accuracy)
    const absoluteMarkers = ['always', 'never', 'all', 'none', 'definitely'];
    if (absoluteMarkers.some(marker => response.toLowerCase().includes(marker))) {
      accuracy -= 0.1;
    }
    
    return Math.max(0, Math.min(1, accuracy));
  }

  /**
   * Evaluate coherence
   */
  private evaluateCoherence(response: string): number {
    const sentences = response.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length < 2) return 0.5;
    
    let coherence = 0.5;
    
    // Check for transition words
    const transitionWords = ['however', 'therefore', 'furthermore', 'moreover', 'consequently'];
    if (transitionWords.some(word => response.toLowerCase().includes(word))) {
      coherence += 0.2;
    }
    
    // Check sentence length variation
    const lengths = sentences.map(s => s.length);
    const avgLength = lengths.reduce((sum, len) => sum + len, 0) / lengths.length;
    const variance = lengths.reduce((sum, len) => sum + Math.pow(len - avgLength, 2), 0) / lengths.length;
    
    if (variance > 100) coherence += 0.1; // Good variation
    
    return Math.min(1, coherence);
  }

  /**
   * Evaluate performance metrics
   */
  private evaluatePerformance(startTime: number, response: string): EvaluationMetrics['performance'] {
    const responseLatency = Date.now() - startTime;
    const inputTokens = 100; // Mock - would be calculated from actual input
    const outputTokens = response.split(/\s+/).length;
    const totalTokens = inputTokens + outputTokens;
    const throughput = 1000 / responseLatency; // queries per second

    return {
      responseLatency,
      tokenUsage: { inputTokens, outputTokens, totalTokens },
      throughput
    };
  }

  /**
   * Get user satisfaction metrics
   */
  private getUserSatisfactionMetrics(queryId: string): EvaluationMetrics['userSatisfaction'] {
    // Mock implementation - would integrate with actual feedback system
    return {
      averageRating: 4.2,
      feedbackCount: 150,
      positiveRatio: 0.85
    };
  }

  /**
   * Log performance data
   */
  private logPerformance(evaluation: QueryEvaluation): void {
    this.performanceLog.push({
      timestamp: evaluation.timestamp,
      latency: evaluation.metrics.performance.responseLatency,
      tokenUsage: evaluation.metrics.performance.tokenUsage.totalTokens,
      retrievalQuality: evaluation.metrics.retrievalQuality.mrr,
      responseQuality: evaluation.metrics.responseQuality.coherence
    });

    // Keep only last 1000 entries
    if (this.performanceLog.length > 1000) {
      this.performanceLog = this.performanceLog.slice(-1000);
    }
  }

  /**
   * Calculate overall score
   */
  private calculateOverallScore(metrics: EvaluationMetrics): number {
    const weights = {
      retrieval: 0.3,
      response: 0.4,
      performance: 0.2,
      satisfaction: 0.1
    };

    const retrievalScore = metrics.retrievalQuality.mrr;
    const responseScore = (metrics.responseQuality.coherence + metrics.responseQuality.factualAccuracy) / 2;
    const performanceScore = Math.min(1, 5000 / metrics.performance.responseLatency); // 5s target
    const satisfactionScore = metrics.userSatisfaction.positiveRatio;

    return (
      retrievalScore * weights.retrieval +
      responseScore * weights.response +
      performanceScore * weights.performance +
      satisfactionScore * weights.satisfaction
    );
  }

  /**
   * Calculate trends over time
   */
  private calculateTrends(): any[] {
    const last7Days = this.performanceLog.filter(
      log => log.timestamp > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    );

    const dailyMetrics = new Map<string, any[]>();
    
    last7Days.forEach(log => {
      const day = log.timestamp.toISOString().split('T')[0];
      if (!dailyMetrics.has(day)) {
        dailyMetrics.set(day, []);
      }
      dailyMetrics.get(day)!.push(log);
    });

    return Array.from(dailyMetrics.entries()).map(([day, logs]) => ({
      date: day,
      avgLatency: logs.reduce((sum, log) => sum + log.latency, 0) / logs.length,
      avgQuality: logs.reduce((sum, log) => sum + log.retrievalQuality, 0) / logs.length,
      totalQueries: logs.length
    }));
  }

  /**
   * Identify top issues
   */
  private identifyTopIssues(metrics: EvaluationMetrics): string[] {
    const issues: string[] = [];

    if (metrics.performance.responseLatency > 5000) {
      issues.push('High response latency detected');
    }

    if (metrics.retrievalQuality.mrr < 0.5) {
      issues.push('Low retrieval quality - consider improving document indexing');
    }

    if (metrics.responseQuality.coherence < 0.6) {
      issues.push('Response coherence needs improvement');
    }

    if (metrics.userSatisfaction.positiveRatio < 0.7) {
      issues.push('User satisfaction below target');
    }

    return issues;
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(metrics: EvaluationMetrics, issues: string[]): string[] {
    const recommendations: string[] = [];

    if (issues.includes('High response latency detected')) {
      recommendations.push('Consider implementing response caching or optimizing model inference');
    }

    if (issues.includes('Low retrieval quality - consider improving document indexing')) {
      recommendations.push('Review document chunking strategy and embedding quality');
    }

    if (issues.includes('Response coherence needs improvement')) {
      recommendations.push('Experiment with different prompt templates or model parameters');
    }

    if (issues.includes('User satisfaction below target')) {
      recommendations.push('Collect more detailed user feedback and analyze common pain points');
    }

    return recommendations;
  }

  /**
   * Get empty metrics structure
   */
  private getEmptyMetrics(): EvaluationMetrics {
    return {
      retrievalQuality: {
        mrr: 0,
        recallAtK: {},
        precisionAtK: {},
        ndcg: 0
      },
      responseQuality: {
        bleuScore: 0,
        rougeScore: { rouge1: 0, rouge2: 0, rougeL: 0 },
        semanticSimilarity: 0,
        factualAccuracy: 0,
        coherence: 0
      },
      performance: {
        responseLatency: 0,
        tokenUsage: { inputTokens: 0, outputTokens: 0, totalTokens: 0 },
        throughput: 0
      },
      userSatisfaction: {
        averageRating: 0,
        feedbackCount: 0,
        positiveRatio: 0
      }
    };
  }

  // Aggregation methods
  private aggregateRetrievalMetrics(evaluations: QueryEvaluation[]): EvaluationMetrics['retrievalQuality'] {
    const avgMrr = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.retrievalQuality.mrr, 0) / evaluations.length;
    const avgNdcg = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.retrievalQuality.ndcg, 0) / evaluations.length;
    
    const recallAtK: Record<number, number> = {};
    const precisionAtK: Record<number, number> = {};
    
    [1, 3, 5, 10].forEach(k => {
      recallAtK[k] = evaluations.reduce((sum, evaluation) => sum + (evaluation.metrics.retrievalQuality.recallAtK[k] || 0), 0) / evaluations.length;
      precisionAtK[k] = evaluations.reduce((sum, evaluation) => sum + (evaluation.metrics.retrievalQuality.precisionAtK[k] || 0), 0) / evaluations.length;
    });

    return { mrr: avgMrr, recallAtK, precisionAtK, ndcg: avgNdcg };
  }

  private aggregateResponseMetrics(evaluations: QueryEvaluation[]): EvaluationMetrics['responseQuality'] {
    const avgBleu = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.bleuScore, 0) / evaluations.length;
    const avgSemantic = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.semanticSimilarity, 0) / evaluations.length;
    const avgFactual = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.factualAccuracy, 0) / evaluations.length;
    const avgCoherence = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.coherence, 0) / evaluations.length;
    
    const avgRouge = {
      rouge1: evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.rougeScore.rouge1, 0) / evaluations.length,
      rouge2: evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.rougeScore.rouge2, 0) / evaluations.length,
      rougeL: evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.responseQuality.rougeScore.rougeL, 0) / evaluations.length
    };

    return {
      bleuScore: avgBleu,
      rougeScore: avgRouge,
      semanticSimilarity: avgSemantic,
      factualAccuracy: avgFactual,
      coherence: avgCoherence
    };
  }

  private aggregatePerformanceMetrics(evaluations: QueryEvaluation[]): EvaluationMetrics['performance'] {
    const avgLatency = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.performance.responseLatency, 0) / evaluations.length;
    const avgThroughput = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.performance.throughput, 0) / evaluations.length;
    
    const totalTokenUsage = evaluations.reduce((sum, evaluation) => ({
      inputTokens: sum.inputTokens + evaluation.metrics.performance.tokenUsage.inputTokens,
      outputTokens: sum.outputTokens + evaluation.metrics.performance.tokenUsage.outputTokens,
      totalTokens: sum.totalTokens + evaluation.metrics.performance.tokenUsage.totalTokens
    }), { inputTokens: 0, outputTokens: 0, totalTokens: 0 });

    return {
      responseLatency: avgLatency,
      tokenUsage: totalTokenUsage,
      throughput: avgThroughput
    };
  }

  private aggregateUserSatisfactionMetrics(evaluations: QueryEvaluation[]): EvaluationMetrics['userSatisfaction'] {
    const avgRating = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.userSatisfaction.averageRating, 0) / evaluations.length;
    const totalFeedback = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.userSatisfaction.feedbackCount, 0);
    const avgPositiveRatio = evaluations.reduce((sum, evaluation) => sum + evaluation.metrics.userSatisfaction.positiveRatio, 0) / evaluations.length;

    return {
      averageRating: avgRating,
      feedbackCount: totalFeedback,
      positiveRatio: avgPositiveRatio
    };
  }
}

export const evaluationService = new EvaluationService();