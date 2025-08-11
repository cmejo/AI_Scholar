/**
 * Type definitions for reasoning and chain of thought functionality
 */

// Query Analysis Types
export interface QueryAnalysis {
  complexity: 'simple' | 'moderate' | 'complex' | 'very_complex';
  intent: QueryIntent;
  entities: ExtractedEntity[];
  topics: string[];
  confidence: number;
  requiresDecomposition: boolean;
  suggestedStrategy: ReasoningStrategy;
}

export interface QueryIntent {
  primary: IntentType;
  secondary?: IntentType[];
  confidence: number;
  parameters: IntentParameters;
}

export type IntentType = 
  | 'search'
  | 'question'
  | 'comparison'
  | 'analysis'
  | 'summarization'
  | 'explanation'
  | 'definition'
  | 'calculation'
  | 'recommendation';

export interface IntentParameters {
  searchTerms?: string[];
  comparisonItems?: string[];
  analysisType?: 'statistical' | 'qualitative' | 'trend' | 'causal';
  summaryLength?: 'brief' | 'detailed' | 'comprehensive';
  explanationLevel?: 'basic' | 'intermediate' | 'advanced';
  [key: string]: unknown;
}

export interface ExtractedEntity {
  text: string;
  type: EntityType;
  confidence: number;
  startIndex: number;
  endIndex: number;
  metadata?: EntityMetadata;
}

export type EntityType = 
  | 'person'
  | 'organization'
  | 'location'
  | 'date'
  | 'number'
  | 'concept'
  | 'technology'
  | 'method'
  | 'product';

export interface EntityMetadata {
  canonicalForm?: string;
  aliases?: string[];
  category?: string;
  description?: string;
  [key: string]: unknown;
}

// Reasoning Strategy Types
export interface ReasoningStrategy {
  type: StrategyType;
  steps: ReasoningStep[];
  estimatedComplexity: number;
  estimatedTime: number;
  requiredResources: string[];
}

export type StrategyType = 
  | 'direct_retrieval'
  | 'multi_step_reasoning'
  | 'comparative_analysis'
  | 'synthesis'
  | 'deductive'
  | 'inductive'
  | 'abductive';

export interface ReasoningStep {
  id: string;
  type: StepType;
  description: string;
  input: StepInput;
  expectedOutput: StepOutput;
  dependencies: string[];
  confidence: number;
  status: StepStatus;
  result?: StepResult;
}

export type StepType = 
  | 'retrieve'
  | 'analyze'
  | 'compare'
  | 'synthesize'
  | 'validate'
  | 'rank'
  | 'filter'
  | 'transform';

export interface StepInput {
  query?: string;
  documents?: string[];
  previousResults?: unknown[];
  parameters?: Record<string, unknown>;
}

export interface StepOutput {
  type: 'documents' | 'analysis' | 'ranking' | 'synthesis' | 'validation';
  format: 'text' | 'structured' | 'numeric' | 'boolean';
  expectedFields?: string[];
}

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface StepResult {
  data: unknown;
  confidence: number;
  executionTime: number;
  metadata?: Record<string, unknown>;
  errors?: string[];
}

// Thought Process Types
export interface ThoughtProcess {
  id: string;
  query: string;
  strategy: ReasoningStrategy;
  steps: CompletedReasoningStep[];
  finalAnswer: ReasoningAnswer;
  metadata: ThoughtProcessMetadata;
}

export interface CompletedReasoningStep extends ReasoningStep {
  result: StepResult;
  startTime: Date;
  endTime: Date;
  logs: StepLog[];
}

export interface StepLog {
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  timestamp: Date;
  data?: unknown;
}

export interface ReasoningAnswer {
  mainAnswer: string;
  confidence: number;
  supportingEvidence: Evidence[];
  alternativeAnswers?: AlternativeAnswer[];
  limitations?: string[];
  sources: SourceReference[];
}

export interface Evidence {
  type: 'direct_quote' | 'paraphrase' | 'inference' | 'calculation';
  content: string;
  source: SourceReference;
  relevanceScore: number;
  confidence: number;
}

export interface AlternativeAnswer {
  answer: string;
  confidence: number;
  reasoning: string;
  evidence: Evidence[];
}

export interface SourceReference {
  documentId: string;
  title?: string;
  author?: string;
  section?: string;
  pageNumber?: number;
  url?: string;
  accessDate?: Date;
}

export interface ThoughtProcessMetadata {
  totalExecutionTime: number;
  stepsExecuted: number;
  stepsSkipped: number;
  averageStepConfidence: number;
  resourcesUsed: string[];
  createdAt: Date;
  version: string;
}

// Validation Types
export interface ValidationResult {
  isValid: boolean;
  confidence: number;
  issues: ValidationIssue[];
  suggestions: ValidationSuggestion[];
  score: ValidationScore;
}

export interface ValidationIssue {
  type: 'inconsistency' | 'missing_evidence' | 'low_confidence' | 'contradiction';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affectedSteps: string[];
  suggestedFix?: string;
}

export interface ValidationSuggestion {
  type: 'additional_search' | 'alternative_approach' | 'clarification' | 'verification';
  description: string;
  priority: number;
  estimatedImpact: 'low' | 'medium' | 'high';
}

export interface ValidationScore {
  overall: number;
  consistency: number;
  completeness: number;
  reliability: number;
  relevance: number;
}

// Context and Memory Types
export interface ReasoningContext {
  conversationHistory: ConversationTurn[];
  userProfile?: UserProfile;
  domainKnowledge: DomainKnowledge;
  preferences: ReasoningPreferences;
  constraints: ReasoningConstraints;
}

export interface ConversationTurn {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

export interface UserProfile {
  id: string;
  expertiseLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  domains: string[];
  preferences: UserPreferences;
  history: QueryHistory[];
}

export interface UserPreferences {
  explanationStyle: 'concise' | 'detailed' | 'step_by_step';
  evidenceLevel: 'minimal' | 'moderate' | 'comprehensive';
  technicalLevel: 'layperson' | 'technical' | 'expert';
  responseFormat: 'text' | 'structured' | 'visual';
}

export interface QueryHistory {
  query: string;
  timestamp: Date;
  satisfaction?: number;
  feedback?: string;
}

export interface DomainKnowledge {
  domains: Domain[];
  relationships: DomainRelationship[];
  lastUpdated: Date;
}

export interface Domain {
  id: string;
  name: string;
  description: string;
  concepts: Concept[];
  methods: Method[];
  experts: Expert[];
}

export interface Concept {
  id: string;
  name: string;
  definition: string;
  aliases: string[];
  relatedConcepts: string[];
  importance: number;
}

export interface Method {
  id: string;
  name: string;
  description: string;
  applicability: string[];
  complexity: number;
  reliability: number;
}

export interface Expert {
  id: string;
  name: string;
  expertise: string[];
  credibility: number;
  publications?: Publication[];
}

export interface Publication {
  title: string;
  year: number;
  venue: string;
  citations: number;
  relevance: number;
}

export interface DomainRelationship {
  source: string;
  target: string;
  type: 'subset' | 'overlap' | 'dependency' | 'similarity';
  strength: number;
}

export interface ReasoningPreferences {
  maxSteps: number;
  timeoutMs: number;
  confidenceThreshold: number;
  evidenceRequirement: 'minimal' | 'moderate' | 'strong';
  allowSpeculation: boolean;
  preferredSources: string[];
}

export interface ReasoningConstraints {
  maxExecutionTime: number;
  maxDocuments: number;
  requiredConfidence: number;
  forbiddenSources?: string[];
  requiredSources?: string[];
  ethicalGuidelines: string[];
}