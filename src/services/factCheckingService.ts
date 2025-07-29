// Fact Checking and Validation Service
export interface FactCheckResult {
  claim: string;
  verdict: 'supported' | 'contradicted' | 'insufficient_evidence' | 'needs_verification';
  confidence: number;
  evidence: Evidence[];
  explanation: string;
  sources: string[];
}

export interface Evidence {
  text: string;
  source: string;
  relevance: number;
  credibility: number;
  supportType: 'direct' | 'indirect' | 'contradictory';
}

export interface ValidationResult {
  originalText: string;
  validatedText: string;
  issues: ValidationIssue[];
  overallScore: number;
  recommendations: string[];
}

export interface ValidationIssue {
  type: 'unsupported_claim' | 'contradictory_statement' | 'outdated_information' | 'bias_detected';
  severity: 'low' | 'medium' | 'high';
  location: { start: number; end: number };
  description: string;
  suggestion: string;
}

export class FactCheckingService {
  private knowledgeBase: Map<string, any> = new Map();
  private credibleSources: Set<string> = new Set();

  constructor() {
    this.initializeCredibleSources();
  }

  /**
   * Perform comprehensive fact checking on text
   */
  async factCheck(text: string, sources: any[] = []): Promise<FactCheckResult[]> {
    const claims = this.extractClaims(text);
    const results: FactCheckResult[] = [];

    for (const claim of claims) {
      const result = await this.checkSingleClaim(claim, sources);
      results.push(result);
    }

    return results;
  }

  /**
   * Validate entire response for accuracy and reliability
   */
  async validateResponse(
    response: string,
    sources: any[],
    originalQuery: string
  ): Promise<ValidationResult> {
    const issues: ValidationIssue[] = [];
    let validatedText = response;

    // Check for unsupported claims
    const unsupportedClaims = await this.findUnsupportedClaims(response, sources);
    issues.push(...unsupportedClaims);

    // Check for contradictory statements
    const contradictions = this.findContradictions(response);
    issues.push(...contradictions);

    // Check for potential bias
    const biasIssues = this.detectBias(response);
    issues.push(...biasIssues);

    // Check for outdated information
    const outdatedIssues = await this.checkForOutdatedInfo(response, sources);
    issues.push(...outdatedIssues);

    // Generate validated text with corrections
    validatedText = this.applyCorrections(response, issues);

    // Calculate overall score
    const overallScore = this.calculateValidationScore(issues, response.length);

    // Generate recommendations
    const recommendations = this.generateValidationRecommendations(issues);

    return {
      originalText: response,
      validatedText,
      issues,
      overallScore,
      recommendations
    };
  }

  /**
   * Real-time fact checking during response generation
   */
  async realTimeFactCheck(
    partialResponse: string,
    sources: any[]
  ): Promise<{
    warnings: string[];
    suggestions: string[];
    confidence: number;
  }> {
    const warnings: string[] = [];
    const suggestions: string[] = [];
    let confidence = 0.8; // Base confidence

    // Check for absolute statements without evidence
    const absoluteStatements = this.findAbsoluteStatements(partialResponse);
    if (absoluteStatements.length > 0) {
      warnings.push('Contains absolute statements that may need qualification');
      suggestions.push('Consider adding uncertainty markers like "according to" or "likely"');
      confidence -= 0.1;
    }

    // Check for claims that need sources
    const unsubstantiatedClaims = this.findUnsubstantiatedClaims(partialResponse);
    if (unsubstantiatedClaims.length > 0) {
      warnings.push('Contains claims that would benefit from source citations');
      suggestions.push('Add citations to support factual claims');
      confidence -= 0.15;
    }

    // Check for potential contradictions
    const internalContradictions = this.findInternalContradictions(partialResponse);
    if (internalContradictions.length > 0) {
      warnings.push('Potential internal contradictions detected');
      suggestions.push('Review for consistency in statements');
      confidence -= 0.2;
    }

    return {
      warnings,
      suggestions,
      confidence: Math.max(0, confidence)
    };
  }

  /**
   * Extract factual claims from text
   */
  private extractClaims(text: string): string[] {
    const claims: string[] = [];
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);

    sentences.forEach(sentence => {
      const trimmed = sentence.trim();
      
      // Identify factual claims (statements that can be verified)
      if (this.isFactualClaim(trimmed)) {
        claims.push(trimmed);
      }
    });

    return claims;
  }

  /**
   * Check if a sentence contains a factual claim
   */
  private isFactualClaim(sentence: string): boolean {
    const factualIndicators = [
      /\b(is|are|was|were|has|have|had|will|would|can|could|should|must)\b/i,
      /\b(according to|research shows|studies indicate|data suggests)\b/i,
      /\b(percent|percentage|number|amount|rate|ratio)\b/i,
      /\b(increase|decrease|improve|reduce|cause|effect)\b/i
    ];

    return factualIndicators.some(pattern => pattern.test(sentence));
  }

  /**
   * Check a single claim against available evidence
   */
  private async checkSingleClaim(claim: string, sources: any[]): Promise<FactCheckResult> {
    const evidence = this.gatherEvidence(claim, sources);
    const verdict = this.determineVerdict(claim, evidence);
    const confidence = this.calculateConfidence(evidence, verdict);
    const explanation = this.generateExplanation(claim, evidence, verdict);
    const sourceList = evidence.map(e => e.source);

    return {
      claim,
      verdict,
      confidence,
      evidence,
      explanation,
      sources: [...new Set(sourceList)]
    };
  }

  /**
   * Gather evidence for a claim
   */
  private gatherEvidence(claim: string, sources: any[]): Evidence[] {
    const evidence: Evidence[] = [];
    const claimKeywords = this.extractKeywords(claim);

    sources.forEach(source => {
      const relevance = this.calculateRelevance(claim, source.content);
      
      if (relevance > 0.3) {
        const supportType = this.determineSupportType(claim, source.content);
        const credibility = this.assessSourceCredibility(source);

        evidence.push({
          text: source.content.substring(0, 200) + '...',
          source: source.name || 'Unknown source',
          relevance,
          credibility,
          supportType
        });
      }
    });

    return evidence.sort((a, b) => (b.relevance * b.credibility) - (a.relevance * a.credibility));
  }

  /**
   * Determine verdict based on evidence
   */
  private determineVerdict(claim: string, evidence: Evidence[]): FactCheckResult['verdict'] {
    if (evidence.length === 0) {
      return 'insufficient_evidence';
    }

    const supportingEvidence = evidence.filter(e => e.supportType === 'direct');
    const contradictoryEvidence = evidence.filter(e => e.supportType === 'contradictory');

    const supportScore = supportingEvidence.reduce((sum, e) => sum + e.relevance * e.credibility, 0);
    const contradictoryScore = contradictoryEvidence.reduce((sum, e) => sum + e.relevance * e.credibility, 0);

    if (supportScore > contradictoryScore * 1.5) {
      return 'supported';
    } else if (contradictoryScore > supportScore * 1.5) {
      return 'contradicted';
    } else if (supportScore > 0.5 || contradictoryScore > 0.5) {
      return 'needs_verification';
    } else {
      return 'insufficient_evidence';
    }
  }

  /**
   * Calculate confidence in fact check result
   */
  private calculateConfidence(evidence: Evidence[], verdict: FactCheckResult['verdict']): number {
    if (evidence.length === 0) return 0.1;

    const avgCredibility = evidence.reduce((sum, e) => sum + e.credibility, 0) / evidence.length;
    const avgRelevance = evidence.reduce((sum, e) => sum + e.relevance, 0) / evidence.length;
    
    let confidence = (avgCredibility + avgRelevance) / 2;

    // Adjust based on verdict
    switch (verdict) {
      case 'supported':
      case 'contradicted':
        confidence *= 1.2;
        break;
      case 'needs_verification':
        confidence *= 0.8;
        break;
      case 'insufficient_evidence':
        confidence *= 0.5;
        break;
    }

    return Math.min(confidence, 1.0);
  }

  /**
   * Generate explanation for fact check result
   */
  private generateExplanation(claim: string, evidence: Evidence[], verdict: FactCheckResult['verdict']): string {
    switch (verdict) {
      case 'supported':
        return `This claim is supported by ${evidence.length} source(s) with high credibility. The evidence directly corroborates the statement.`;
      
      case 'contradicted':
        const contradictory = evidence.filter(e => e.supportType === 'contradictory');
        return `This claim is contradicted by ${contradictory.length} credible source(s). The available evidence suggests the opposite.`;
      
      case 'needs_verification':
        return `This claim has mixed evidence. Some sources support it while others contradict it. Further verification is recommended.`;
      
      case 'insufficient_evidence':
        return `Insufficient evidence found to verify this claim. More sources or information would be needed for proper fact-checking.`;
      
      default:
        return 'Unable to determine the veracity of this claim.';
    }
  }

  /**
   * Find unsupported claims in response
   */
  private async findUnsupportedClaims(response: string, sources: any[]): Promise<ValidationIssue[]> {
    const issues: ValidationIssue[] = [];
    const claims = this.extractClaims(response);

    for (const claim of claims) {
      const evidence = this.gatherEvidence(claim, sources);
      
      if (evidence.length === 0 || evidence.every(e => e.relevance < 0.5)) {
        const location = this.findTextLocation(response, claim);
        
        issues.push({
          type: 'unsupported_claim',
          severity: 'medium',
          location,
          description: 'This claim lacks supporting evidence from the provided sources',
          suggestion: 'Add a citation or qualify the statement with uncertainty markers'
        });
      }
    }

    return issues;
  }

  /**
   * Find contradictory statements within the text
   */
  private findContradictions(text: string): ValidationIssue[] {
    const issues: ValidationIssue[] = [];
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);

    for (let i = 0; i < sentences.length; i++) {
      for (let j = i + 1; j < sentences.length; j++) {
        if (this.areContradictory(sentences[i], sentences[j])) {
          const location1 = this.findTextLocation(text, sentences[i]);
          const location2 = this.findTextLocation(text, sentences[j]);

          issues.push({
            type: 'contradictory_statement',
            severity: 'high',
            location: location1,
            description: `This statement contradicts another statement in the response`,
            suggestion: 'Review and resolve the contradiction between statements'
          });
        }
      }
    }

    return issues;
  }

  /**
   * Check if two sentences are contradictory
   */
  private areContradictory(sentence1: string, sentence2: string): boolean {
    const contradictionPatterns = [
      { positive: /\bis\s+true\b/gi, negative: /\bis\s+false\b/gi },
      { positive: /\bincreases?\b/gi, negative: /\bdecreases?\b/gi },
      { positive: /\bimproves?\b/gi, negative: /\bworsens?\b/gi },
      { positive: /\bhigher\b/gi, negative: /\blower\b/gi }
    ];

    return contradictionPatterns.some(({ positive, negative }) => {
      const hasPositive1 = positive.test(sentence1);
      const hasNegative1 = negative.test(sentence1);
      const hasPositive2 = positive.test(sentence2);
      const hasNegative2 = negative.test(sentence2);

      return (hasPositive1 && hasNegative2) || (hasNegative1 && hasPositive2);
    });
  }

  /**
   * Detect potential bias in text
   */
  private detectBias(text: string): ValidationIssue[] {
    const issues: ValidationIssue[] = [];
    
    const biasPatterns = [
      {
        pattern: /\b(obviously|clearly|undoubtedly|certainly)\b/gi,
        type: 'certainty_bias',
        description: 'Overconfident language that may indicate bias'
      },
      {
        pattern: /\b(all|every|never|always|none)\s+\w+\s+(are|is|do|does)\b/gi,
        type: 'generalization_bias',
        description: 'Overgeneralization that may not account for exceptions'
      },
      {
        pattern: /\b(should|must|need to|have to)\b/gi,
        type: 'prescriptive_bias',
        description: 'Prescriptive language that may reflect personal opinion'
      }
    ];

    biasPatterns.forEach(({ pattern, type, description }) => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        issues.push({
          type: 'bias_detected',
          severity: 'low',
          location: { start: match.index, end: match.index + match[0].length },
          description,
          suggestion: 'Consider using more neutral language or adding qualifiers'
        });
      }
    });

    return issues;
  }

  /**
   * Check for outdated information
   */
  private async checkForOutdatedInfo(response: string, sources: any[]): Promise<ValidationIssue[]> {
    const issues: ValidationIssue[] = [];
    const currentYear = new Date().getFullYear();

    // Check for date references
    const datePattern = /\b(19|20)\d{2}\b/g;
    let match;

    while ((match = datePattern.exec(response)) !== null) {
      const year = parseInt(match[0]);
      const age = currentYear - year;

      if (age > 5) { // Information older than 5 years
        issues.push({
          type: 'outdated_information',
          severity: age > 10 ? 'high' : 'medium',
          location: { start: match.index, end: match.index + match[0].length },
          description: `Information from ${year} may be outdated (${age} years old)`,
          suggestion: 'Verify if this information is still current or add a note about the date'
        });
      }
    }

    return issues;
  }

  /**
   * Apply corrections to text based on validation issues
   */
  private applyCorrections(text: string, issues: ValidationIssue[]): string {
    let correctedText = text;
    
    // Sort issues by location (reverse order to maintain indices)
    const sortedIssues = issues.sort((a, b) => b.location.start - a.location.start);

    sortedIssues.forEach(issue => {
      const before = correctedText.substring(0, issue.location.start);
      const problematicText = correctedText.substring(issue.location.start, issue.location.end);
      const after = correctedText.substring(issue.location.end);

      let correction = problematicText;

      switch (issue.type) {
        case 'unsupported_claim':
          correction = `[Needs verification] ${problematicText}`;
          break;
        case 'bias_detected':
          correction = this.neutralizeLanguage(problematicText);
          break;
        case 'outdated_information':
          correction = `${problematicText} [Note: This information may be outdated]`;
          break;
      }

      correctedText = before + correction + after;
    });

    return correctedText;
  }

  /**
   * Neutralize biased language
   */
  private neutralizeLanguage(text: string): string {
    const neutralizations = {
      'obviously': 'apparently',
      'clearly': 'seemingly',
      'undoubtedly': 'likely',
      'certainly': 'probably',
      'all': 'most',
      'never': 'rarely',
      'always': 'typically',
      'must': 'should consider',
      'need to': 'might want to'
    };

    let neutralized = text;
    Object.entries(neutralizations).forEach(([biased, neutral]) => {
      neutralized = neutralized.replace(new RegExp(`\\b${biased}\\b`, 'gi'), neutral);
    });

    return neutralized;
  }

  /**
   * Calculate overall validation score
   */
  private calculateValidationScore(issues: ValidationIssue[], textLength: number): number {
    let score = 1.0;
    
    issues.forEach(issue => {
      switch (issue.severity) {
        case 'high':
          score -= 0.2;
          break;
        case 'medium':
          score -= 0.1;
          break;
        case 'low':
          score -= 0.05;
          break;
      }
    });

    // Adjust for text length (longer texts might naturally have more issues)
    const issueRate = issues.length / (textLength / 100); // issues per 100 characters
    if (issueRate > 0.5) score -= 0.1;

    return Math.max(0, score);
  }

  /**
   * Generate validation recommendations
   */
  private generateValidationRecommendations(issues: ValidationIssue[]): string[] {
    const recommendations: string[] = [];
    const issueTypes = new Set(issues.map(i => i.type));

    if (issueTypes.has('unsupported_claim')) {
      recommendations.push('Add citations or source references for factual claims');
    }

    if (issueTypes.has('contradictory_statement')) {
      recommendations.push('Review the response for internal consistency');
    }

    if (issueTypes.has('bias_detected')) {
      recommendations.push('Use more neutral and objective language');
    }

    if (issueTypes.has('outdated_information')) {
      recommendations.push('Verify that all information is current and up-to-date');
    }

    const highSeverityIssues = issues.filter(i => i.severity === 'high').length;
    if (highSeverityIssues > 0) {
      recommendations.push('Address high-severity issues before finalizing the response');
    }

    return recommendations;
  }

  // Helper methods
  private extractKeywords(text: string): string[] {
    return text.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 3);
  }

  private calculateRelevance(claim: string, content: string): number {
    const claimWords = this.extractKeywords(claim);
    const contentWords = this.extractKeywords(content);
    
    const commonWords = claimWords.filter(word => contentWords.includes(word));
    return commonWords.length / claimWords.length;
  }

  private determineSupportType(claim: string, content: string): Evidence['supportType'] {
    const claimSentiment = this.analyzeSentiment(claim);
    const contentSentiment = this.analyzeSentiment(content);
    
    if (Math.abs(claimSentiment - contentSentiment) < 0.3) {
      return 'direct';
    } else if (claimSentiment * contentSentiment < 0) {
      return 'contradictory';
    } else {
      return 'indirect';
    }
  }

  private analyzeSentiment(text: string): number {
    const positiveWords = ['good', 'better', 'best', 'improve', 'increase', 'positive', 'effective'];
    const negativeWords = ['bad', 'worse', 'worst', 'decrease', 'negative', 'ineffective', 'harmful'];
    
    const words = text.toLowerCase().split(/\s+/);
    let sentiment = 0;
    
    words.forEach(word => {
      if (positiveWords.includes(word)) sentiment += 1;
      if (negativeWords.includes(word)) sentiment -= 1;
    });
    
    return sentiment / words.length;
  }

  private assessSourceCredibility(source: any): number {
    let credibility = 0.5; // Base credibility
    
    // Check if source is from credible domain
    if (source.url && this.credibleSources.has(this.extractDomain(source.url))) {
      credibility += 0.3;
    }
    
    // Check for academic indicators
    if (source.content && /\b(doi:|pmid:|arxiv:)\b/i.test(source.content)) {
      credibility += 0.2;
    }
    
    return Math.min(credibility, 1.0);
  }

  private extractDomain(url: string): string {
    try {
      return new URL(url).hostname;
    } catch {
      return '';
    }
  }

  private findTextLocation(text: string, substring: string): { start: number; end: number } {
    const start = text.indexOf(substring);
    return {
      start: start !== -1 ? start : 0,
      end: start !== -1 ? start + substring.length : 0
    };
  }

  private findAbsoluteStatements(text: string): string[] {
    const absolutePatterns = [
      /\b(always|never|all|none|every|no one|everyone|everything|nothing)\b/gi,
      /\b(definitely|certainly|absolutely|undoubtedly|without question)\b/gi
    ];
    
    const statements: string[] = [];
    absolutePatterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) statements.push(...matches);
    });
    
    return statements;
  }

  private findUnsubstantiatedClaims(text: string): string[] {
    const claims = this.extractClaims(text);
    return claims.filter(claim => !this.hasSourceIndicator(claim));
  }

  private hasSourceIndicator(text: string): boolean {
    const sourceIndicators = [
      /according to/i,
      /research shows/i,
      /studies indicate/i,
      /\[source/i,
      /\(.*\d{4}.*\)/i // Year in parentheses
    ];
    
    return sourceIndicators.some(pattern => pattern.test(text));
  }

  private findInternalContradictions(text: string): string[] {
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const contradictions: string[] = [];
    
    for (let i = 0; i < sentences.length - 1; i++) {
      for (let j = i + 1; j < sentences.length; j++) {
        if (this.areContradictory(sentences[i], sentences[j])) {
          contradictions.push(`"${sentences[i]}" contradicts "${sentences[j]}"`);
        }
      }
    }
    
    return contradictions;
  }

  private initializeCredibleSources(): void {
    const credibleDomains = [
      'nature.com',
      'science.org',
      'nejm.org',
      'bmj.com',
      'who.int',
      'cdc.gov',
      'nih.gov',
      'pubmed.ncbi.nlm.nih.gov',
      'arxiv.org',
      'ieee.org',
      'acm.org',
      'springer.com',
      'wiley.com',
      'elsevier.com',
      'cambridge.org',
      'oxford.com'
    ];
    
    credibleDomains.forEach(domain => this.credibleSources.add(domain));
  }
}

export const factCheckingService = new FactCheckingService();