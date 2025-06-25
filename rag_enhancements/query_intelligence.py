#!/usr/bin/env python3
"""
Advanced Query Understanding for RAG
Implements intent recognition, query expansion, and contextual understanding
"""

import spacy
import re
from typing import Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass
from transformers import pipeline

class QueryIntent(Enum):
    FACTUAL = "factual"
    COMPARATIVE = "comparative"
    ANALYTICAL = "analytical"
    PROCEDURAL = "procedural"
    DEFINITIONAL = "definitional"
    CAUSAL = "causal"
    TEMPORAL = "temporal"
    QUANTITATIVE = "quantitative"

@dataclass
class QueryAnalysis:
    original_query: str
    intent: QueryIntent
    entities: List[Dict]
    keywords: List[str]
    expanded_query: str
    context_requirements: List[str]
    complexity_score: float
    domain: str

class AdvancedQueryProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
        # Intent classification patterns
        self.intent_patterns = {
            QueryIntent.FACTUAL: [
                r'\b(what|who|where|when|which)\b',
                r'\bis\b.*\?',
                r'\bfact\b',
                r'\binformation about\b'
            ],
            QueryIntent.COMPARATIVE: [
                r'\b(compare|versus|vs|difference|similar|different)\b',
                r'\bbetter than\b',
                r'\bcompared to\b'
            ],
            QueryIntent.ANALYTICAL: [
                r'\b(analyze|analysis|examine|evaluate|assess)\b',
                r'\bwhy\b.*\?',
                r'\bhow does.*affect\b',
                r'\bimpact of\b'
            ],
            QueryIntent.PROCEDURAL: [
                r'\bhow to\b',
                r'\bsteps\b',
                r'\bprocess\b',
                r'\bmethod\b',
                r'\bprocedure\b'
            ],
            QueryIntent.DEFINITIONAL: [
                r'\bdefine\b',
                r'\bdefinition\b',
                r'\bmeaning of\b',
                r'\bwhat is\b'
            ],
            QueryIntent.CAUSAL: [
                r'\bcause\b',
                r'\breason\b',
                r'\bwhy\b',
                r'\bdue to\b',
                r'\bresult of\b'
            ],
            QueryIntent.TEMPORAL: [
                r'\bwhen\b',
                r'\btimeline\b',
                r'\bhistory\b',
                r'\bevolution\b',
                r'\bover time\b'
            ],
            QueryIntent.QUANTITATIVE: [
                r'\bhow much\b',
                r'\bhow many\b',
                r'\bstatistics\b',
                r'\bnumber\b',
                r'\bpercentage\b'
            ]
        }
        
        # Domain classification keywords
        self.domain_keywords = {
            'academic': ['research', 'study', 'paper', 'journal', 'academic', 'scholar', 'university'],
            'business': ['market', 'revenue', 'profit', 'strategy', 'company', 'business', 'finance'],
            'technical': ['algorithm', 'code', 'programming', 'software', 'system', 'technical'],
            'medical': ['health', 'medical', 'disease', 'treatment', 'patient', 'clinical'],
            'legal': ['law', 'legal', 'court', 'regulation', 'compliance', 'contract'],
            'general': []
        }
    
    def analyze_query(self, query: str, conversation_context: List[str] = None) -> QueryAnalysis:
        """Comprehensive query analysis"""
        doc = self.nlp(query)
        
        # Extract entities and keywords
        entities = self._extract_entities(doc)
        keywords = self._extract_keywords(doc)
        
        # Determine intent
        intent = self._classify_intent(query)
        
        # Expand query
        expanded_query = self._expand_query(query, entities, keywords, conversation_context)
        
        # Determine context requirements
        context_requirements = self._determine_context_requirements(intent, entities)
        
        # Calculate complexity
        complexity_score = self._calculate_complexity(doc, intent, entities)
        
        # Classify domain
        domain = self._classify_domain(query, keywords)
        
        return QueryAnalysis(
            original_query=query,
            intent=intent,
            entities=entities,
            keywords=keywords,
            expanded_query=expanded_query,
            context_requirements=context_requirements,
            complexity_score=complexity_score,
            domain=domain
        )
    
    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of the query"""
        query_lower = query.lower()
        
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            intent_scores[intent] = score
        
        # Return intent with highest score, default to FACTUAL
        if max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        return QueryIntent.FACTUAL
    
    def _extract_entities(self, doc) -> List[Dict]:
        """Extract named entities with enhanced information"""
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'start': ent.start_char,
                'end': ent.end_char,
                'importance': self._calculate_entity_importance(ent)
            })
        return entities
    
    def _extract_keywords(self, doc) -> List[str]:
        """Extract important keywords from the query"""
        keywords = []
        
        # Extract nouns and adjectives
        for token in doc:
            if (token.pos_ in ['NOUN', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.lemma_.lower())
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1:
                keywords.append(chunk.text.lower())
        
        return list(set(keywords))
    
    def _expand_query(self, query: str, entities: List[Dict], keywords: List[str], 
                     context: List[str] = None) -> str:
        """Expand query with synonyms and related terms"""
        expanded_terms = []
        
        # Add original query
        expanded_terms.append(query)
        
        # Add entity variations
        for entity in entities:
            if entity['label'] in ['PERSON', 'ORG', 'GPE']:
                expanded_terms.append(f"about {entity['text']}")
                expanded_terms.append(f"related to {entity['text']}")
        
        # Add keyword variations
        keyword_expansions = {
            'machine learning': ['ML', 'artificial intelligence', 'AI', 'deep learning'],
            'artificial intelligence': ['AI', 'machine learning', 'ML', 'neural networks'],
            'data science': ['analytics', 'big data', 'data analysis'],
            'programming': ['coding', 'software development', 'development'],
            'research': ['study', 'investigation', 'analysis', 'examination']
        }
        
        for keyword in keywords:
            if keyword in keyword_expansions:
                expanded_terms.extend(keyword_expansions[keyword])
        
        # Add context from conversation history
        if context:
            # Extract relevant terms from recent context
            for ctx in context[-3:]:  # Last 3 context items
                ctx_doc = self.nlp(ctx)
                for token in ctx_doc:
                    if token.pos_ in ['NOUN', 'ADJ'] and not token.is_stop:
                        expanded_terms.append(token.lemma_.lower())
        
        return " ".join(expanded_terms)
    
    def _determine_context_requirements(self, intent: QueryIntent, entities: List[Dict]) -> List[str]:
        """Determine what type of context is needed for this query"""
        requirements = []
        
        # Intent-based requirements
        intent_requirements = {
            QueryIntent.COMPARATIVE: ['multiple_sources', 'contrasting_viewpoints'],
            QueryIntent.ANALYTICAL: ['detailed_analysis', 'supporting_evidence'],
            QueryIntent.PROCEDURAL: ['step_by_step', 'sequential_information'],
            QueryIntent.TEMPORAL: ['chronological_order', 'historical_context'],
            QueryIntent.QUANTITATIVE: ['numerical_data', 'statistics'],
            QueryIntent.CAUSAL: ['cause_effect_relationships', 'explanatory_content']
        }
        
        if intent in intent_requirements:
            requirements.extend(intent_requirements[intent])
        
        # Entity-based requirements
        for entity in entities:
            if entity['label'] == 'PERSON':
                requirements.append('biographical_information')
            elif entity['label'] == 'ORG':
                requirements.append('organizational_information')
            elif entity['label'] == 'DATE':
                requirements.append('temporal_context')
            elif entity['label'] == 'MONEY':
                requirements.append('financial_context')
        
        return list(set(requirements))
    
    def _calculate_complexity(self, doc, intent: QueryIntent, entities: List[Dict]) -> float:
        """Calculate query complexity score (0-1)"""
        complexity = 0.0
        
        # Base complexity from query length
        complexity += min(len(doc) / 50, 0.3)
        
        # Intent complexity
        intent_complexity = {
            QueryIntent.FACTUAL: 0.2,
            QueryIntent.DEFINITIONAL: 0.3,
            QueryIntent.PROCEDURAL: 0.5,
            QueryIntent.COMPARATIVE: 0.7,
            QueryIntent.ANALYTICAL: 0.8,
            QueryIntent.CAUSAL: 0.9
        }
        complexity += intent_complexity.get(intent, 0.5)
        
        # Entity complexity
        complexity += min(len(entities) * 0.1, 0.3)
        
        # Syntactic complexity
        complexity += min(len(list(doc.noun_chunks)) * 0.05, 0.2)
        
        return min(complexity, 1.0)
    
    def _classify_domain(self, query: str, keywords: List[str]) -> str:
        """Classify the domain of the query"""
        query_lower = query.lower()
        all_terms = keywords + query_lower.split()
        
        domain_scores = {}
        for domain, domain_keywords in self.domain_keywords.items():
            score = sum(1 for term in all_terms if term in domain_keywords)
            domain_scores[domain] = score
        
        # Return domain with highest score, default to general
        if max(domain_scores.values()) > 0:
            return max(domain_scores, key=domain_scores.get)
        return 'general'
    
    def _calculate_entity_importance(self, entity) -> float:
        """Calculate importance score for an entity"""
        # Entity type importance
        type_importance = {
            'PERSON': 0.8,
            'ORG': 0.7,
            'GPE': 0.6,
            'DATE': 0.5,
            'MONEY': 0.6,
            'PERCENT': 0.5
        }
        
        base_score = type_importance.get(entity.label_, 0.3)
        
        # Length bonus (longer entities often more specific)
        length_bonus = min(len(entity.text.split()) * 0.1, 0.3)
        
        return min(base_score + length_bonus, 1.0)

class ContextualRetrieval:
    """Enhanced retrieval system that uses query analysis"""
    
    def __init__(self, query_processor: AdvancedQueryProcessor):
        self.query_processor = query_processor
        
    def retrieve_with_intent(self, query: str, documents: List[Dict], 
                           conversation_context: List[str] = None) -> Dict:
        """Retrieve documents based on query intent and analysis"""
        
        # Analyze the query
        analysis = self.query_processor.analyze_query(query, conversation_context)
        
        # Adjust retrieval strategy based on intent
        retrieval_strategy = self._get_retrieval_strategy(analysis.intent)
        
        # Perform retrieval
        results = self._execute_retrieval(analysis, documents, retrieval_strategy)
        
        # Post-process results based on context requirements
        processed_results = self._post_process_results(results, analysis)
        
        return {
            'query_analysis': analysis,
            'retrieval_strategy': retrieval_strategy,
            'results': processed_results,
            'confidence_score': self._calculate_confidence(analysis, processed_results)
        }
    
    def _get_retrieval_strategy(self, intent: QueryIntent) -> Dict:
        """Get retrieval strategy based on intent"""
        strategies = {
            QueryIntent.FACTUAL: {
                'method': 'semantic_search',
                'top_k': 5,
                'diversity_threshold': 0.3
            },
            QueryIntent.COMPARATIVE: {
                'method': 'multi_perspective',
                'top_k': 8,
                'diversity_threshold': 0.7
            },
            QueryIntent.ANALYTICAL: {
                'method': 'comprehensive_search',
                'top_k': 10,
                'diversity_threshold': 0.5
            },
            QueryIntent.PROCEDURAL: {
                'method': 'sequential_search',
                'top_k': 6,
                'diversity_threshold': 0.2
            },
            QueryIntent.TEMPORAL: {
                'method': 'chronological_search',
                'top_k': 7,
                'diversity_threshold': 0.4
            }
        }
        
        return strategies.get(intent, strategies[QueryIntent.FACTUAL])
    
    def _execute_retrieval(self, analysis: QueryAnalysis, documents: List[Dict], 
                          strategy: Dict) -> List[Dict]:
        """Execute retrieval based on strategy"""
        # This would integrate with your existing RAG system
        # For now, a simplified implementation
        
        if strategy['method'] == 'semantic_search':
            return self._semantic_search(analysis.expanded_query, documents, strategy['top_k'])
        elif strategy['method'] == 'multi_perspective':
            return self._multi_perspective_search(analysis, documents, strategy['top_k'])
        elif strategy['method'] == 'comprehensive_search':
            return self._comprehensive_search(analysis, documents, strategy['top_k'])
        else:
            return self._semantic_search(analysis.expanded_query, documents, strategy['top_k'])
    
    def _semantic_search(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """Basic semantic search implementation"""
        # This would use your existing embedding-based search
        # Placeholder implementation
        return documents[:top_k]
    
    def _multi_perspective_search(self, analysis: QueryAnalysis, documents: List[Dict], 
                                 top_k: int) -> List[Dict]:
        """Search for multiple perspectives on a topic"""
        # Search for contrasting viewpoints
        perspectives = []
        
        # Add original query results
        main_results = self._semantic_search(analysis.original_query, documents, top_k // 2)
        perspectives.extend(main_results)
        
        # Add alternative perspective results
        alt_query = f"alternative view {analysis.original_query}"
        alt_results = self._semantic_search(alt_query, documents, top_k // 2)
        perspectives.extend(alt_results)
        
        return perspectives
    
    def _comprehensive_search(self, analysis: QueryAnalysis, documents: List[Dict], 
                             top_k: int) -> List[Dict]:
        """Comprehensive search for analytical queries"""
        results = []
        
        # Search with original query
        results.extend(self._semantic_search(analysis.original_query, documents, top_k // 3))
        
        # Search with entity-focused queries
        for entity in analysis.entities[:2]:  # Top 2 entities
            entity_query = f"{entity['text']} {analysis.original_query}"
            results.extend(self._semantic_search(entity_query, documents, top_k // 3))
        
        # Search with keyword combinations
        if len(analysis.keywords) >= 2:
            keyword_query = " ".join(analysis.keywords[:3])
            results.extend(self._semantic_search(keyword_query, documents, top_k // 3))
        
        return results[:top_k]
    
    def _post_process_results(self, results: List[Dict], analysis: QueryAnalysis) -> List[Dict]:
        """Post-process results based on context requirements"""
        processed = []
        
        for result in results:
            # Add relevance score based on query analysis
            relevance_score = self._calculate_relevance(result, analysis)
            result['relevance_score'] = relevance_score
            result['query_intent'] = analysis.intent.value
            result['domain_match'] = analysis.domain
            
            processed.append(result)
        
        # Sort by relevance score
        processed.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return processed
    
    def _calculate_relevance(self, result: Dict, analysis: QueryAnalysis) -> float:
        """Calculate relevance score for a result"""
        score = 0.5  # Base score
        
        # Entity matching bonus
        result_text = result.get('text', '').lower()
        for entity in analysis.entities:
            if entity['text'].lower() in result_text:
                score += 0.1 * entity['importance']
        
        # Keyword matching bonus
        for keyword in analysis.keywords:
            if keyword in result_text:
                score += 0.05
        
        # Domain matching bonus
        if analysis.domain in result.get('metadata', {}).get('domain', ''):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_confidence(self, analysis: QueryAnalysis, results: List[Dict]) -> float:
        """Calculate confidence in the retrieval results"""
        if not results:
            return 0.0
        
        # Base confidence from query complexity (inverse relationship)
        confidence = 1.0 - analysis.complexity_score * 0.3
        
        # Boost confidence if we have high-relevance results
        avg_relevance = sum(r.get('relevance_score', 0) for r in results) / len(results)
        confidence += avg_relevance * 0.3
        
        # Boost confidence if we have enough results
        if len(results) >= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)

# Usage example
def implement_query_intelligence():
    """Example implementation of advanced query processing"""
    processor = AdvancedQueryProcessor()
    retrieval = ContextualRetrieval(processor)
    
    # Example queries
    queries = [
        "What is machine learning?",  # Definitional
        "Compare supervised and unsupervised learning",  # Comparative
        "How does gradient descent work?",  # Procedural
        "Why is overfitting a problem in ML?",  # Causal
        "Analyze the impact of AI on healthcare"  # Analytical
    ]
    
    results = {}
    for query in queries:
        analysis = processor.analyze_query(query)
        results[query] = {
            'intent': analysis.intent.value,
            'complexity': analysis.complexity_score,
            'domain': analysis.domain,
            'entities': analysis.entities,
            'keywords': analysis.keywords
        }
    
    return results