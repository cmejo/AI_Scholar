"""
Reasoning Engine Service for Advanced RAG Features
Implements causal reasoning, analogical reasoning, uncertainty quantification,
and specialized AI agents for fact-checking, summarization, and research.
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from core.config import settings
from models.schemas import ReasoningResult, UncertaintyScore

logger = logging.getLogger(__name__)

class ReasoningType(Enum):
    CAUSAL = "causal"
    ANALOGICAL = "analogical"
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"

@dataclass
class CausalRelation:
    cause: str
    effect: str
    confidence: float
    mechanism: str
    evidence: List[str]

@dataclass
class Analogy:
    source_domain: str
    target_domain: str
    mapping: Dict[str, str]
    similarity_score: float
    explanation: str

class BaseReasoningAgent(ABC):
    """Base class for all reasoning agents"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
    
    @abstractmethod
    async def reason(self, query: str, context: str, **kwargs) -> ReasoningResult:
        """Abstract method for reasoning implementation"""
        pass
    
    async def _call_llm(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
        """Helper method to call the LLM"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "max_tokens": max_tokens
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return "Error: Unable to generate response"
                
        except Exception as e:
            logger.error(f"LLM request error: {str(e)}")
            return "Error: Connection failed"

class CausalReasoningAgent(BaseReasoningAgent):
    """Agent for cause-and-effect analysis"""
    
    async def reason(self, query: str, context: str, **kwargs) -> ReasoningResult:
        """Perform causal reasoning analysis"""
        start_time = time.time()
        
        causal_prompt = f"""
Analyze the following context for causal relationships related to the query.
Identify causes, effects, and the mechanisms that connect them.

Context: {context}

Query: {query}

Please analyze this systematically:

1. DIRECT CAUSAL RELATIONSHIPS:
   - What directly causes what?
   - What are the immediate effects?

2. CAUSAL CHAINS:
   - What are the sequences of cause and effect?
   - Are there intermediate steps?

3. CONTRIBUTING FACTORS:
   - What factors influence the main causal relationships?
   - Are there necessary vs sufficient conditions?

4. CONFIDENCE ASSESSMENT:
   - How certain are these causal claims?
   - What evidence supports them?

Format your response as:
CAUSE: [specific cause]
EFFECT: [specific effect]
MECHANISM: [how the cause leads to the effect]
CONFIDENCE: [0.0-1.0]
EVIDENCE: [supporting evidence from context]

Provide multiple causal relationships if they exist.
"""
        
        response = await self._call_llm(causal_prompt, temperature=0.2)
        
        # Parse causal relationships from response
        causal_relations = self._parse_causal_response(response)
        
        # Calculate overall confidence
        overall_confidence = sum(rel.confidence for rel in causal_relations) / len(causal_relations) if causal_relations else 0.0
        
        processing_time = time.time() - start_time
        
        # Flatten evidence lists into strings
        supporting_evidence = []
        for rel in causal_relations:
            if isinstance(rel.evidence, list):
                supporting_evidence.extend(rel.evidence)
            else:
                supporting_evidence.append(str(rel.evidence))
        
        return ReasoningResult(
            reasoning_type=ReasoningType.CAUSAL.value,
            confidence=overall_confidence,
            explanation=response,
            supporting_evidence=supporting_evidence,
            metadata={
                "causal_relations": [
                    {
                        "cause": rel.cause,
                        "effect": rel.effect,
                        "mechanism": rel.mechanism,
                        "confidence": rel.confidence
                    }
                    for rel in causal_relations
                ],
                "processing_time": processing_time,
                "num_relations": len(causal_relations)
            }
        )
    
    def _parse_causal_response(self, response: str) -> List[CausalRelation]:
        """Parse causal relationships from LLM response"""
        relations = []
        lines = response.split('\n')
        
        current_relation = {}
        for line in lines:
            line = line.strip()
            if line.startswith('CAUSE:'):
                current_relation['cause'] = line.replace('CAUSE:', '').strip()
            elif line.startswith('EFFECT:'):
                current_relation['effect'] = line.replace('EFFECT:', '').strip()
            elif line.startswith('MECHANISM:'):
                current_relation['mechanism'] = line.replace('MECHANISM:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence_str = line.replace('CONFIDENCE:', '').strip()
                    current_relation['confidence'] = float(confidence_str)
                except ValueError:
                    current_relation['confidence'] = 0.5
            elif line.startswith('EVIDENCE:'):
                current_relation['evidence'] = [line.replace('EVIDENCE:', '').strip()]
                
                # If we have all components, create the relation
                if all(key in current_relation for key in ['cause', 'effect', 'mechanism', 'confidence']):
                    relations.append(CausalRelation(
                        cause=current_relation['cause'],
                        effect=current_relation['effect'],
                        confidence=current_relation['confidence'],
                        mechanism=current_relation['mechanism'],
                        evidence=current_relation.get('evidence', [])
                    ))
                    current_relation = {}
        
        return relations

class AnalogicalReasoningAgent(BaseReasoningAgent):
    """Agent for pattern and analogy detection"""
    
    async def reason(self, query: str, context: str, **kwargs) -> ReasoningResult:
        """Perform analogical reasoning analysis"""
        start_time = time.time()
        
        analogical_prompt = f"""
Analyze the following context to find analogies, patterns, and similar structures that relate to the query.
Look for conceptual similarities, structural parallels, and transferable insights.

Context: {context}

Query: {query}

Please analyze this systematically:

1. DIRECT ANALOGIES:
   - What concepts in the context are similar to concepts in the query?
   - What are the key similarities and differences?

2. STRUCTURAL PATTERNS:
   - What underlying patterns or structures are present?
   - How do these patterns relate to the query?

3. CROSS-DOMAIN MAPPINGS:
   - Can concepts from one domain be mapped to another?
   - What insights transfer between domains?

4. PRECEDENTS AND EXAMPLES:
   - Are there historical precedents or similar cases?
   - What can we learn from these examples?

Format your response as:
SOURCE_DOMAIN: [domain being compared from]
TARGET_DOMAIN: [domain being compared to]
MAPPING: [key concept] -> [analogous concept]
SIMILARITY_SCORE: [0.0-1.0]
EXPLANATION: [why this analogy is useful]

Provide multiple analogies if they exist.
"""
        
        response = await self._call_llm(analogical_prompt, temperature=0.4)
        
        # Parse analogies from response
        analogies = self._parse_analogical_response(response)
        
        # Calculate overall confidence based on similarity scores
        overall_confidence = sum(analogy.similarity_score for analogy in analogies) / len(analogies) if analogies else 0.0
        
        processing_time = time.time() - start_time
        
        return ReasoningResult(
            reasoning_type=ReasoningType.ANALOGICAL.value,
            confidence=overall_confidence,
            explanation=response,
            supporting_evidence=[analogy.explanation for analogy in analogies],
            metadata={
                "analogies": [
                    {
                        "source_domain": analogy.source_domain,
                        "target_domain": analogy.target_domain,
                        "mapping": analogy.mapping,
                        "similarity_score": analogy.similarity_score,
                        "explanation": analogy.explanation
                    }
                    for analogy in analogies
                ],
                "processing_time": processing_time,
                "num_analogies": len(analogies)
            }
        )
    
    def _parse_analogical_response(self, response: str) -> List[Analogy]:
        """Parse analogies from LLM response"""
        analogies = []
        lines = response.split('\n')
        
        current_analogy = {}
        for line in lines:
            line = line.strip()
            if line.startswith('SOURCE_DOMAIN:'):
                current_analogy['source_domain'] = line.replace('SOURCE_DOMAIN:', '').strip()
            elif line.startswith('TARGET_DOMAIN:'):
                current_analogy['target_domain'] = line.replace('TARGET_DOMAIN:', '').strip()
            elif line.startswith('MAPPING:'):
                mapping_str = line.replace('MAPPING:', '').strip()
                # Parse simple mapping format "concept1 -> concept2"
                if '->' in mapping_str:
                    parts = mapping_str.split('->')
                    if len(parts) == 2:
                        current_analogy['mapping'] = {parts[0].strip(): parts[1].strip()}
                    else:
                        current_analogy['mapping'] = {"general": mapping_str}
                else:
                    current_analogy['mapping'] = {"general": mapping_str}
            elif line.startswith('SIMILARITY_SCORE:'):
                try:
                    score_str = line.replace('SIMILARITY_SCORE:', '').strip()
                    current_analogy['similarity_score'] = float(score_str)
                except ValueError:
                    current_analogy['similarity_score'] = 0.5
            elif line.startswith('EXPLANATION:'):
                current_analogy['explanation'] = line.replace('EXPLANATION:', '').strip()
                
                # If we have all components, create the analogy
                if all(key in current_analogy for key in ['source_domain', 'target_domain', 'mapping', 'similarity_score']):
                    analogies.append(Analogy(
                        source_domain=current_analogy['source_domain'],
                        target_domain=current_analogy['target_domain'],
                        mapping=current_analogy['mapping'],
                        similarity_score=current_analogy['similarity_score'],
                        explanation=current_analogy.get('explanation', '')
                    ))
                    current_analogy = {}
        
        return analogies

class UncertaintyQuantifier:
    """System for quantifying uncertainty and confidence in responses"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
    
    async def quantify_uncertainty(
        self, 
        response: str, 
        sources: List[Dict[str, Any]], 
        reasoning_results: List[ReasoningResult] = None
    ) -> UncertaintyScore:
        """Quantify uncertainty in a response based on multiple factors"""
        
        # Factor 1: Source quality and consensus
        source_quality = self._assess_source_quality(sources)
        source_consensus = self._assess_source_consensus(sources, response)
        
        # Factor 2: Reasoning confidence
        reasoning_confidence = self._assess_reasoning_confidence(reasoning_results or [])
        
        # Factor 3: Language certainty indicators
        language_confidence = await self._assess_language_confidence(response)
        
        # Factor 4: Factual claim verification
        factual_confidence = await self._assess_factual_confidence(response, sources)
        
        # Combine factors with weights
        weights = {
            'source_quality': 0.25,
            'source_consensus': 0.25,
            'reasoning': 0.20,
            'language': 0.15,
            'factual': 0.15
        }
        
        overall_confidence = (
            source_quality * weights['source_quality'] +
            source_consensus * weights['source_consensus'] +
            reasoning_confidence * weights['reasoning'] +
            language_confidence * weights['language'] +
            factual_confidence * weights['factual']
        )
        
        # Identify uncertainty factors
        uncertainty_factors = []
        if source_quality < 0.7:
            uncertainty_factors.append("Low source quality")
        if source_consensus < 0.6:
            uncertainty_factors.append("Conflicting information in sources")
        if reasoning_confidence < 0.6:
            uncertainty_factors.append("Weak reasoning support")
        if language_confidence < 0.7:
            uncertainty_factors.append("Uncertain language patterns")
        if factual_confidence < 0.6:
            uncertainty_factors.append("Unverified factual claims")
        
        return UncertaintyScore(
            confidence=overall_confidence,
            uncertainty_factors=uncertainty_factors,
            reliability_score=min(source_quality, source_consensus),
            source_quality=source_quality
        )
    
    def _assess_source_quality(self, sources: List[Dict[str, Any]]) -> float:
        """Assess the quality of sources"""
        if not sources:
            return 0.0
        
        quality_scores = []
        for source in sources:
            # Basic quality indicators
            relevance = source.get('relevance', 0.5)
            content_length = len(source.get('content', ''))
            
            # Longer, more relevant content generally indicates higher quality
            length_score = min(content_length / 500, 1.0)  # Normalize to 0-1
            quality_score = (relevance * 0.7) + (length_score * 0.3)
            quality_scores.append(quality_score)
        
        return sum(quality_scores) / len(quality_scores)
    
    def _assess_source_consensus(self, sources: List[Dict[str, Any]], response: str) -> float:
        """Assess how well sources agree with each other and the response"""
        if len(sources) < 2:
            return 0.8  # Single source gets moderate consensus score
        
        # Simple heuristic: count overlapping key terms
        response_terms = set(response.lower().split())
        source_terms = []
        
        for source in sources:
            content = source.get('content', '')
            terms = set(content.lower().split())
            source_terms.append(terms)
        
        # Calculate pairwise similarity between sources
        similarities = []
        for i in range(len(source_terms)):
            for j in range(i + 1, len(source_terms)):
                intersection = len(source_terms[i] & source_terms[j])
                union = len(source_terms[i] | source_terms[j])
                similarity = intersection / union if union > 0 else 0
                similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.5
    
    def _assess_reasoning_confidence(self, reasoning_results: List[ReasoningResult]) -> float:
        """Assess confidence based on reasoning results"""
        if not reasoning_results:
            return 0.5  # Neutral confidence without reasoning
        
        confidences = [result.confidence for result in reasoning_results]
        return sum(confidences) / len(confidences)
    
    async def _assess_language_confidence(self, response: str) -> float:
        """Assess confidence based on language patterns"""
        # Simple heuristic: look for uncertainty indicators
        uncertainty_words = [
            'might', 'could', 'possibly', 'perhaps', 'maybe', 'likely',
            'probably', 'seems', 'appears', 'suggests', 'indicates',
            'uncertain', 'unclear', 'ambiguous', 'potentially'
        ]
        
        confidence_words = [
            'definitely', 'certainly', 'clearly', 'obviously', 'undoubtedly',
            'confirmed', 'established', 'proven', 'demonstrated', 'verified'
        ]
        
        words = response.lower().split()
        uncertainty_count = sum(1 for word in words if any(uw in word for uw in uncertainty_words))
        confidence_count = sum(1 for word in words if any(cw in word for cw in confidence_words))
        
        total_words = len(words)
        if total_words == 0:
            return 0.5
        
        uncertainty_ratio = uncertainty_count / total_words
        confidence_ratio = confidence_count / total_words
        
        # Higher confidence ratio and lower uncertainty ratio = higher confidence
        language_confidence = 0.5 + (confidence_ratio * 0.5) - (uncertainty_ratio * 0.3)
        return max(0.0, min(1.0, language_confidence))
    
    async def _assess_factual_confidence(self, response: str, sources: List[Dict[str, Any]]) -> float:
        """Assess confidence in factual claims"""
        # Simple implementation: check if response claims are supported by sources
        if not sources:
            return 0.3  # Low confidence without sources
        
        # Extract key claims from response (simplified)
        response_sentences = response.split('.')
        source_content = ' '.join([source.get('content', '') for source in sources])
        
        supported_claims = 0
        total_claims = len(response_sentences)
        
        for sentence in response_sentences:
            if len(sentence.strip()) < 10:  # Skip very short sentences
                total_claims -= 1
                continue
            
            # Check if key terms from sentence appear in sources
            sentence_terms = set(sentence.lower().split())
            source_terms = set(source_content.lower().split())
            
            overlap = len(sentence_terms & source_terms)
            if overlap >= 3:  # At least 3 overlapping terms
                supported_claims += 1
        
        if total_claims == 0:
            return 0.5
        
        return supported_claims / total_claims

class FactCheckingAgent(BaseReasoningAgent):
    """Agent for claim verification and fact-checking"""
    
    async def reason(self, query: str, context: str, **kwargs) -> ReasoningResult:
        """Perform fact-checking analysis"""
        start_time = time.time()
        
        # Extract claims from the query or context
        claims = kwargs.get('claims', [])
        if not claims:
            claims = await self._extract_claims(query, context)
        
        fact_check_prompt = f"""
You are a fact-checking agent. Analyze the following claims against the provided context and determine their accuracy.

Context: {context}

Claims to verify:
{chr(10).join([f"- {claim}" for claim in claims])}

For each claim, provide:

1. VERIFICATION STATUS:
   - VERIFIED: The claim is supported by the context
   - PARTIALLY_VERIFIED: The claim is partially supported
   - UNVERIFIED: No evidence found in context
   - CONTRADICTED: The claim contradicts the context

2. EVIDENCE ANALYSIS:
   - What evidence supports or contradicts the claim?
   - How strong is this evidence?

3. CONFIDENCE ASSESSMENT:
   - How confident are you in this verification? (0.0-1.0)

Format your response as:
CLAIM: [original claim]
STATUS: [VERIFIED/PARTIALLY_VERIFIED/UNVERIFIED/CONTRADICTED]
EVIDENCE: [supporting or contradicting evidence]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [detailed reasoning]

Analyze each claim separately.
"""
        
        response = await self._call_llm(fact_check_prompt, temperature=0.1)
        
        # Parse fact-check results
        fact_check_results = self._parse_fact_check_response(response, claims)
        
        # Calculate overall confidence
        overall_confidence = sum(result['confidence'] for result in fact_check_results) / len(fact_check_results) if fact_check_results else 0.0
        
        processing_time = time.time() - start_time
        
        return ReasoningResult(
            reasoning_type="fact_checking",
            confidence=overall_confidence,
            explanation=response,
            supporting_evidence=[result['evidence'] for result in fact_check_results],
            metadata={
                "fact_check_results": fact_check_results,
                "processing_time": processing_time,
                "claims_analyzed": len(claims),
                "verified_claims": len([r for r in fact_check_results if r['status'] == 'VERIFIED']),
                "contradicted_claims": len([r for r in fact_check_results if r['status'] == 'CONTRADICTED'])
            }
        )
    
    async def _extract_claims(self, query: str, context: str) -> List[str]:
        """Extract factual claims from query and context"""
        extraction_prompt = f"""
Extract factual claims from the following text that can be verified or fact-checked.
Focus on specific, verifiable statements rather than opinions or subjective statements.

Text: {query}

Context: {context[:500]}...

List each factual claim on a separate line, starting with "CLAIM:".
Only include claims that make specific, verifiable assertions.
"""
        
        response = await self._call_llm(extraction_prompt, temperature=0.2)
        
        claims = []
        for line in response.split('\n'):
            if line.strip().startswith('CLAIM:'):
                claim = line.replace('CLAIM:', '').strip()
                if claim:
                    claims.append(claim)
        
        return claims[:5]  # Limit to 5 claims for performance
    
    def _parse_fact_check_response(self, response: str, claims: List[str]) -> List[Dict[str, Any]]:
        """Parse fact-check results from LLM response"""
        results = []
        lines = response.split('\n')
        
        current_result = {}
        for line in lines:
            line = line.strip()
            if line.startswith('CLAIM:'):
                current_result['claim'] = line.replace('CLAIM:', '').strip()
            elif line.startswith('STATUS:'):
                current_result['status'] = line.replace('STATUS:', '').strip()
            elif line.startswith('EVIDENCE:'):
                current_result['evidence'] = line.replace('EVIDENCE:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence_str = line.replace('CONFIDENCE:', '').strip()
                    current_result['confidence'] = float(confidence_str)
                except ValueError:
                    current_result['confidence'] = 0.5
            elif line.startswith('EXPLANATION:'):
                current_result['explanation'] = line.replace('EXPLANATION:', '').strip()
                
                # If we have all components, add the result
                if all(key in current_result for key in ['claim', 'status', 'evidence', 'confidence']):
                    results.append(current_result.copy())
                    current_result = {}
        
        return results

class SummarizationAgent(BaseReasoningAgent):
    """Agent for intelligent content summarization"""
    
    async def reason(self, query: str, context: str, **kwargs) -> ReasoningResult:
        """Perform intelligent summarization"""
        start_time = time.time()
        
        summary_type = kwargs.get('summary_type', 'comprehensive')
        max_length = kwargs.get('max_length', 300)
        focus_areas = kwargs.get('focus_areas', [])
        
        summarization_prompt = f"""
You are an intelligent summarization agent. Create a {summary_type} summary of the following content.

Content to summarize: {context}

Query context: {query}

Requirements:
- Maximum length: {max_length} words
- Summary type: {summary_type}
- Focus areas: {', '.join(focus_areas) if focus_areas else 'general overview'}

Provide:

1. MAIN SUMMARY:
   - Key points and main ideas
   - Important details relevant to the query
   - Logical flow and structure

2. KEY INSIGHTS:
   - Most important takeaways
   - Critical information
   - Actionable points

3. RELEVANCE ASSESSMENT:
   - How well does the content address the query?
   - What aspects are most/least relevant?

4. CONFIDENCE METRICS:
   - Completeness: How complete is this summary? (0.0-1.0)
   - Accuracy: How accurately does it represent the source? (0.0-1.0)
   - Relevance: How relevant is it to the query? (0.0-1.0)

Format your response clearly with the sections above.
"""
        
        response = await self._call_llm(summarization_prompt, temperature=0.3, max_tokens=max_length * 2)
        
        # Parse summarization results
        summary_results = self._parse_summarization_response(response)
        
        # Calculate overall confidence
        confidence_metrics = summary_results.get('confidence_metrics', {})
        overall_confidence = sum(confidence_metrics.values()) / len(confidence_metrics) if confidence_metrics else 0.7
        
        processing_time = time.time() - start_time
        
        return ReasoningResult(
            reasoning_type="summarization",
            confidence=overall_confidence,
            explanation=response,
            supporting_evidence=[summary_results.get('main_summary', '')],
            metadata={
                "summary_type": summary_type,
                "max_length": max_length,
                "focus_areas": focus_areas,
                "key_insights": summary_results.get('key_insights', []),
                "relevance_assessment": summary_results.get('relevance_assessment', ''),
                "confidence_metrics": confidence_metrics,
                "processing_time": processing_time,
                "word_count": len(summary_results.get('main_summary', '').split())
            }
        )
    
    def _parse_summarization_response(self, response: str) -> Dict[str, Any]:
        """Parse summarization results from LLM response"""
        result = {
            'main_summary': '',
            'key_insights': [],
            'relevance_assessment': '',
            'confidence_metrics': {}
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'MAIN SUMMARY' in line.upper():
                current_section = 'main_summary'
            elif 'KEY INSIGHTS' in line.upper():
                current_section = 'key_insights'
            elif 'RELEVANCE ASSESSMENT' in line.upper():
                current_section = 'relevance_assessment'
            elif ('CONFIDENCE METRICS' in line.upper() or 
                  ('CONFIDENCE' in line.upper() and ':' not in line)):
                current_section = 'confidence_metrics'
            elif line and ':' in line:
                # Check for standalone confidence metrics anywhere in the response
                if any(metric in line.lower() for metric in ['completeness:', 'accuracy:', 'relevance:']):
                    parts = line.split(':')
                    if len(parts) == 2:
                        metric_name = parts[0].strip().lower()
                        try:
                            metric_value = float(parts[1].strip())
                            result['confidence_metrics'][metric_name] = metric_value
                        except ValueError:
                            pass
                elif current_section == 'confidence_metrics':
                    # Parse confidence metrics in dedicated section
                    parts = line.split(':')
                    if len(parts) == 2:
                        metric_name = parts[0].strip().lower()
                        try:
                            metric_value = float(parts[1].strip())
                            result['confidence_metrics'][metric_name] = metric_value
                        except ValueError:
                            pass
                elif current_section:
                    # Add to current section content
                    if current_section == 'main_summary':
                        result['main_summary'] += line + ' '
                    elif current_section == 'relevance_assessment':
                        result['relevance_assessment'] += line + ' '
            elif line and current_section:
                if current_section == 'main_summary':
                    result['main_summary'] += line + ' '
                elif current_section == 'key_insights':
                    if line.startswith('-') or line.startswith('•'):
                        result['key_insights'].append(line[1:].strip())
                    elif line:
                        result['key_insights'].append(line)
                elif current_section == 'relevance_assessment':
                    result['relevance_assessment'] += line + ' '
        
        # Clean up strings
        result['main_summary'] = result['main_summary'].strip()
        result['relevance_assessment'] = result['relevance_assessment'].strip()
        
        return result

class ResearchAgent(BaseReasoningAgent):
    """Agent for deep topic analysis and research"""
    
    async def reason(self, query: str, context: str, **kwargs) -> ReasoningResult:
        """Perform deep topic research and analysis"""
        start_time = time.time()
        
        research_depth = kwargs.get('research_depth', 'comprehensive')
        research_areas = kwargs.get('research_areas', ['background', 'current_state', 'implications'])
        
        research_prompt = f"""
You are a research agent conducting deep analysis on a topic. Provide comprehensive research insights.

Research Query: {query}

Available Context: {context}

Research Depth: {research_depth}
Focus Areas: {', '.join(research_areas)}

Provide a structured research analysis:

1. BACKGROUND ANALYSIS:
   - Historical context and development
   - Key foundational concepts
   - Important precedents or examples

2. CURRENT STATE ASSESSMENT:
   - Present situation or state of knowledge
   - Recent developments or findings
   - Current debates or controversies

3. KEY RELATIONSHIPS AND CONNECTIONS:
   - How this topic relates to other concepts
   - Interdisciplinary connections
   - Cause-and-effect relationships

4. IMPLICATIONS AND SIGNIFICANCE:
   - Why this topic matters
   - Potential consequences or outcomes
   - Future directions or trends

5. KNOWLEDGE GAPS AND LIMITATIONS:
   - What information is missing or unclear
   - Areas needing further investigation
   - Limitations of current understanding

6. RESEARCH CONFIDENCE:
   - Completeness of analysis (0.0-1.0)
   - Reliability of sources (0.0-1.0)
   - Depth of coverage (0.0-1.0)

Provide detailed, analytical insights for each section.
"""
        
        response = await self._call_llm(research_prompt, temperature=0.4, max_tokens=2048)
        
        # Parse research results
        research_results = self._parse_research_response(response)
        
        # Calculate overall confidence
        confidence_metrics = research_results.get('research_confidence', {})
        overall_confidence = sum(confidence_metrics.values()) / len(confidence_metrics) if confidence_metrics else 0.6
        
        processing_time = time.time() - start_time
        
        return ReasoningResult(
            reasoning_type="research",
            confidence=overall_confidence,
            explanation=response,
            supporting_evidence=[
                research_results.get('background_analysis', ''),
                research_results.get('current_state_assessment', ''),
                research_results.get('implications_significance', '')
            ],
            metadata={
                "research_depth": research_depth,
                "research_areas": research_areas,
                "background_analysis": research_results.get('background_analysis', ''),
                "current_state": research_results.get('current_state_assessment', ''),
                "key_relationships": research_results.get('key_relationships', ''),
                "implications": research_results.get('implications_significance', ''),
                "knowledge_gaps": research_results.get('knowledge_gaps', ''),
                "research_confidence": confidence_metrics,
                "processing_time": processing_time
            }
        )
    
    def _parse_research_response(self, response: str) -> Dict[str, Any]:
        """Parse research results from LLM response"""
        result = {
            'background_analysis': '',
            'current_state_assessment': '',
            'key_relationships': '',
            'implications_significance': '',
            'knowledge_gaps': '',
            'research_confidence': {}
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'BACKGROUND ANALYSIS' in line.upper():
                current_section = 'background_analysis'
            elif 'CURRENT STATE' in line.upper():
                current_section = 'current_state_assessment'
            elif 'KEY RELATIONSHIPS' in line.upper() or 'RELATIONSHIPS AND CONNECTIONS' in line.upper():
                current_section = 'key_relationships'
            elif 'IMPLICATIONS' in line.upper() and 'SIGNIFICANCE' in line.upper():
                current_section = 'implications_significance'
            elif 'KNOWLEDGE GAPS' in line.upper() or 'LIMITATIONS' in line.upper():
                current_section = 'knowledge_gaps'
            elif 'RESEARCH CONFIDENCE' in line.upper() or 'CONFIDENCE' in line.upper():
                current_section = 'research_confidence'
            elif line and current_section:
                if current_section == 'research_confidence':
                    # Parse confidence metrics
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            metric_name = parts[0].strip().lower().replace(' ', '_')
                            try:
                                metric_value = float(parts[1].strip())
                                result['research_confidence'][metric_name] = metric_value
                            except ValueError:
                                pass
                else:
                    result[current_section] += line + ' '
        
        # Clean up strings
        for key in result:
            if isinstance(result[key], str):
                result[key] = result[key].strip()
        
        return result

class AgentCoordinator:
    """Coordinates multiple specialized agents and integrates their results"""
    
    def __init__(self):
        self.fact_checking_agent = FactCheckingAgent()
        self.summarization_agent = SummarizationAgent()
        self.research_agent = ResearchAgent()
    
    async def coordinate_agents(
        self, 
        query: str, 
        context: str, 
        agent_types: List[str] = None,
        **kwargs
    ) -> List[ReasoningResult]:
        """Coordinate multiple agents and integrate their results"""
        
        if agent_types is None:
            agent_types = self._determine_relevant_agents(query)
        
        results = []
        
        # Run fact-checking agent
        if 'fact_checking' in agent_types:
            try:
                fact_check_result = await self.fact_checking_agent.reason(query, context, **kwargs)
                results.append(fact_check_result)
            except Exception as e:
                logger.error(f"Fact-checking agent error: {str(e)}")
        
        # Run summarization agent
        if 'summarization' in agent_types:
            try:
                summary_result = await self.summarization_agent.reason(query, context, **kwargs)
                results.append(summary_result)
            except Exception as e:
                logger.error(f"Summarization agent error: {str(e)}")
        
        # Run research agent
        if 'research' in agent_types:
            try:
                research_result = await self.research_agent.reason(query, context, **kwargs)
                results.append(research_result)
            except Exception as e:
                logger.error(f"Research agent error: {str(e)}")
        
        return results
    
    def _determine_relevant_agents(self, query: str) -> List[str]:
        """Determine which agents are most relevant for a given query"""
        query_lower = query.lower()
        relevant_agents = []
        
        # Fact-checking indicators
        fact_check_indicators = [
            'true', 'false', 'fact', 'verify', 'check', 'accurate', 'correct',
            'claim', 'statement', 'assertion', 'evidence', 'proof'
        ]
        if any(indicator in query_lower for indicator in fact_check_indicators):
            relevant_agents.append('fact_checking')
        
        # Summarization indicators
        summary_indicators = [
            'summarize', 'summary', 'overview', 'brief', 'main points',
            'key points', 'highlights', 'essence', 'gist'
        ]
        if any(indicator in query_lower for indicator in summary_indicators):
            relevant_agents.append('summarization')
        
        # Research indicators
        research_indicators = [
            'research', 'analyze', 'analysis', 'investigate', 'explore',
            'deep dive', 'comprehensive', 'detailed', 'background',
            'implications', 'significance', 'why', 'how', 'what if'
        ]
        if any(indicator in query_lower for indicator in research_indicators):
            relevant_agents.append('research')
        
        # Default to research if no specific indicators
        if not relevant_agents:
            relevant_agents.append('research')
        
        return relevant_agents
    
    async def integrate_results(self, results: List[ReasoningResult]) -> Dict[str, Any]:
        """Integrate results from multiple agents into a coherent response"""
        if not results:
            return {}
        
        integration = {
            'agent_count': len(results),
            'overall_confidence': sum(r.confidence for r in results) / len(results),
            'reasoning_types': [r.reasoning_type for r in results],
            'combined_evidence': [],
            'key_insights': [],
            'metadata_summary': {}
        }
        
        # Combine evidence and insights
        for result in results:
            integration['combined_evidence'].extend(result.supporting_evidence)
            
            # Extract key insights from metadata
            if result.reasoning_type == 'fact_checking':
                fact_results = result.metadata.get('fact_check_results', [])
                verified_claims = [r['claim'] for r in fact_results if r['status'] == 'VERIFIED']
                if verified_claims:
                    integration['key_insights'].extend([f"Verified: {claim}" for claim in verified_claims])
            
            elif result.reasoning_type == 'summarization':
                key_insights = result.metadata.get('key_insights', [])
                integration['key_insights'].extend(key_insights)
            
            elif result.reasoning_type == 'research':
                implications = result.metadata.get('implications', '')
                if implications:
                    integration['key_insights'].append(f"Research insight: {implications[:200]}...")
        
        # Summarize metadata
        for result in results:
            agent_type = result.reasoning_type
            integration['metadata_summary'][agent_type] = {
                'confidence': result.confidence,
                'processing_time': result.metadata.get('processing_time', 0),
                'key_metrics': self._extract_key_metrics(result)
            }
        
        return integration
    
    def _extract_key_metrics(self, result: ReasoningResult) -> Dict[str, Any]:
        """Extract key metrics from a reasoning result"""
        metrics = {}
        
        if result.reasoning_type == 'fact_checking':
            metrics['claims_analyzed'] = result.metadata.get('claims_analyzed', 0)
            metrics['verified_claims'] = result.metadata.get('verified_claims', 0)
            metrics['contradicted_claims'] = result.metadata.get('contradicted_claims', 0)
        
        elif result.reasoning_type == 'summarization':
            metrics['word_count'] = result.metadata.get('word_count', 0)
            metrics['summary_type'] = result.metadata.get('summary_type', 'unknown')
        
        elif result.reasoning_type == 'research':
            metrics['research_depth'] = result.metadata.get('research_depth', 'unknown')
            metrics['research_areas'] = len(result.metadata.get('research_areas', []))
        
        return metrics

class ReasoningEngine:
    """Main reasoning engine that coordinates different reasoning agents"""
    
    def __init__(self):
        self.causal_agent = CausalReasoningAgent()
        self.analogical_agent = AnalogicalReasoningAgent()
        self.uncertainty_quantifier = UncertaintyQuantifier()
        self.agent_coordinator = AgentCoordinator()
    
    async def apply_reasoning(
        self, 
        query: str, 
        context: str, 
        reasoning_types: List[str] = None,
        **kwargs
    ) -> List[ReasoningResult]:
        """Apply multiple types of reasoning to a query and context"""
        
        if reasoning_types is None:
            reasoning_types = [ReasoningType.CAUSAL.value, ReasoningType.ANALOGICAL.value]
        
        results = []
        
        # Apply causal reasoning
        if ReasoningType.CAUSAL.value in reasoning_types:
            try:
                causal_result = await self.causal_agent.reason(query, context, **kwargs)
                results.append(causal_result)
            except Exception as e:
                logger.error(f"Causal reasoning error: {str(e)}")
        
        # Apply analogical reasoning
        if ReasoningType.ANALOGICAL.value in reasoning_types:
            try:
                analogical_result = await self.analogical_agent.reason(query, context, **kwargs)
                results.append(analogical_result)
            except Exception as e:
                logger.error(f"Analogical reasoning error: {str(e)}")
        
        return results
    
    async def apply_specialized_agents(
        self,
        query: str,
        context: str,
        agent_types: List[str] = None,
        **kwargs
    ) -> List[ReasoningResult]:
        """Apply specialized AI agents (fact-checking, summarization, research)"""
        return await self.agent_coordinator.coordinate_agents(query, context, agent_types, **kwargs)
    
    async def fact_check(
        self,
        query: str,
        context: str,
        claims: List[str] = None,
        **kwargs
    ) -> ReasoningResult:
        """Perform fact-checking analysis"""
        if claims:
            kwargs['claims'] = claims
        return await self.agent_coordinator.fact_checking_agent.reason(query, context, **kwargs)
    
    async def summarize(
        self,
        query: str,
        context: str,
        summary_type: str = 'comprehensive',
        max_length: int = 300,
        focus_areas: List[str] = None,
        **kwargs
    ) -> ReasoningResult:
        """Perform intelligent summarization"""
        kwargs.update({
            'summary_type': summary_type,
            'max_length': max_length,
            'focus_areas': focus_areas or []
        })
        return await self.agent_coordinator.summarization_agent.reason(query, context, **kwargs)
    
    async def research(
        self,
        query: str,
        context: str,
        research_depth: str = 'comprehensive',
        research_areas: List[str] = None,
        **kwargs
    ) -> ReasoningResult:
        """Perform deep topic research and analysis"""
        kwargs.update({
            'research_depth': research_depth,
            'research_areas': research_areas or ['background', 'current_state', 'implications']
        })
        return await self.agent_coordinator.research_agent.reason(query, context, **kwargs)
    
    async def integrate_agent_results(self, results: List[ReasoningResult]) -> Dict[str, Any]:
        """Integrate results from multiple specialized agents"""
        return await self.agent_coordinator.integrate_results(results)
    
    async def quantify_uncertainty(
        self, 
        response: str, 
        sources: List[Dict[str, Any]], 
        reasoning_results: List[ReasoningResult] = None
    ) -> UncertaintyScore:
        """Quantify uncertainty in a response"""
        return await self.uncertainty_quantifier.quantify_uncertainty(
            response, sources, reasoning_results
        )
    
    def should_apply_reasoning(self, query: str, complexity_threshold: float = 0.1) -> bool:
        """Determine if reasoning should be applied based on query complexity"""
        # Simple heuristic for query complexity
        complexity_indicators = [
            'why', 'how', 'cause', 'effect', 'because', 'reason', 'explain',
            'compare', 'similar', 'different', 'like', 'analogy', 'relationship',
            'consequence', 'result', 'lead to', 'due to', 'therefore'
        ]
        
        query_lower = query.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        
        # Normalize by query length (use a more lenient threshold)
        query_words = query.split()
        if not query_words:
            return False
            
        normalized_complexity = complexity_score / len(query_words)
        
        return normalized_complexity >= complexity_threshold