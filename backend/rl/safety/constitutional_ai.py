"""
Constitutional AI implementation for the RL system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import torch
import torch.nn as nn

from ..core.config import RLConfig, SafetyConfig
from ..models.conversation_models import ConversationState, Action, ActionType

logger = logging.getLogger(__name__)


class PrincipleType(Enum):
    """Types of constitutional principles."""
    HELPFULNESS = "helpfulness"
    HARMLESSNESS = "harmlessness"
    HONESTY = "honesty"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"
    TRANSPARENCY = "transparency"


@dataclass
class ConstitutionalPrinciple:
    """Represents a constitutional AI principle."""
    principle_id: str
    principle_type: PrincipleType
    description: str
    weight: float = 1.0
    threshold: float = 0.5
    violation_penalty: float = -0.5
    
    def evaluate(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Evaluate if response violates this principle.
        
        Returns:
            is_violation: Whether principle is violated
            confidence: Confidence in the evaluation (0-1)
            explanation: Explanation of the evaluation
        """
        
        if self.principle_type == PrincipleType.HELPFULNESS:
            return self._evaluate_helpfulness(response_text, context)
        elif self.principle_type == PrincipleType.HARMLESSNESS:
            return self._evaluate_harmlessness(response_text, context)
        elif self.principle_type == PrincipleType.HONESTY:
            return self._evaluate_honesty(response_text, context)
        elif self.principle_type == PrincipleType.PRIVACY:
            return self._evaluate_privacy(response_text, context)
        elif self.principle_type == PrincipleType.FAIRNESS:
            return self._evaluate_fairness(response_text, context)
        elif self.principle_type == PrincipleType.TRANSPARENCY:
            return self._evaluate_transparency(response_text, context)
        else:
            return False, 0.0, "Unknown principle type"
    
    def _evaluate_helpfulness(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate helpfulness principle."""
        
        # Simple heuristics for helpfulness
        response_lower = response_text.lower()
        
        # Check for unhelpful responses
        unhelpful_patterns = [
            "i don't know", "i can't help", "that's not my job",
            "figure it out yourself", "i won't help", "not my problem"
        ]
        
        for pattern in unhelpful_patterns:
            if pattern in response_lower:
                return True, 0.8, f"Response contains unhelpful pattern: '{pattern}'"
        
        # Check for minimal effort responses
        if len(response_text.strip()) < 10:
            return True, 0.6, "Response is too short to be helpful"
        
        # Check for helpful indicators
        helpful_patterns = [
            "here's how", "let me help", "i can assist", "here are some options",
            "you might try", "consider", "suggestion", "recommendation"
        ]
        
        helpful_count = sum(1 for pattern in helpful_patterns if pattern in response_lower)
        
        if helpful_count == 0 and len(response_text) < 50:
            return True, 0.4, "Response lacks helpful indicators and is brief"
        
        return False, 0.9, "Response appears helpful"
    
    def _evaluate_harmlessness(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate harmlessness principle."""
        
        response_lower = response_text.lower()
        
        # Check for harmful content
        harmful_patterns = [
            "violence", "harm", "hurt", "kill", "destroy", "attack",
            "illegal", "criminal", "fraud", "scam", "steal",
            "hate", "discrimination", "racist", "sexist", "offensive"
        ]
        
        for pattern in harmful_patterns:
            if pattern in response_lower:
                return True, 0.9, f"Response contains potentially harmful content: '{pattern}'"
        
        # Check for encouraging dangerous behavior
        dangerous_patterns = [
            "you should break", "ignore safety", "bypass security",
            "don't tell anyone", "keep this secret", "hide this"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in response_lower:
                return True, 0.8, f"Response encourages dangerous behavior: '{pattern}'"
        
        return False, 0.9, "Response appears harmless"
    
    def _evaluate_honesty(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate honesty principle."""
        
        response_lower = response_text.lower()
        
        # Check for dishonest patterns
        dishonest_patterns = [
            "i'm certain", "definitely", "absolutely sure", "100% correct",
            "always true", "never wrong", "guaranteed"
        ]
        
        # Only flag if making strong claims without evidence
        strong_claims = sum(1 for pattern in dishonest_patterns if pattern in response_lower)
        
        if strong_claims > 0:
            # Check if response provides evidence or caveats
            evidence_patterns = [
                "according to", "research shows", "studies indicate",
                "however", "but", "might", "could", "possibly"
            ]
            
            evidence_count = sum(1 for pattern in evidence_patterns if pattern in response_lower)
            
            if evidence_count == 0:
                return True, 0.7, "Response makes strong claims without evidence or caveats"
        
        # Check for uncertainty acknowledgment when appropriate
        if "i don't know" in response_lower or "i'm not sure" in response_lower:
            return False, 0.9, "Response honestly acknowledges uncertainty"
        
        return False, 0.8, "Response appears honest"
    
    def _evaluate_privacy(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate privacy principle."""
        
        response_lower = response_text.lower()
        
        # Check for requests for personal information
        personal_info_patterns = [
            "what's your address", "phone number", "social security",
            "credit card", "password", "personal details",
            "where do you live", "full name", "date of birth"
        ]
        
        for pattern in personal_info_patterns:
            if pattern in response_lower:
                return True, 0.9, f"Response requests personal information: '{pattern}'"
        
        # Check for sharing personal information (if any in context)
        if context.get("contains_personal_info", False):
            sharing_patterns = [
                "let me share", "here's their", "their address is",
                "their phone", "personal information"
            ]
            
            for pattern in sharing_patterns:
                if pattern in response_lower:
                    return True, 0.8, f"Response may share personal information: '{pattern}'"
        
        return False, 0.9, "Response respects privacy"
    
    def _evaluate_fairness(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate fairness principle."""
        
        response_lower = response_text.lower()
        
        # Check for biased language
        biased_patterns = [
            "all [group] are", "typical [group]", "[group] always",
            "men are better", "women can't", "people from [place] are"
        ]
        
        # Simple bias detection (would be more sophisticated in practice)
        bias_indicators = [
            "all women", "all men", "typical woman", "typical man",
            "always", "never", "all people from"
        ]
        
        for indicator in bias_indicators:
            if indicator in response_lower:
                return True, 0.6, f"Response contains potentially biased language: '{indicator}'"
        
        # Check for stereotyping
        stereotype_patterns = [
            "stereotype", "generalization", "assumption about"
        ]
        
        for pattern in stereotype_patterns:
            if pattern in response_lower:
                # This might be discussing stereotypes, which could be educational
                if "avoid" in response_lower or "don't" in response_lower:
                    return False, 0.8, "Response discusses avoiding stereotypes"
                else:
                    return True, 0.5, f"Response may contain stereotyping: '{pattern}'"
        
        return False, 0.8, "Response appears fair and unbiased"
    
    def _evaluate_transparency(self, response_text: str, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate transparency principle."""
        
        response_lower = response_text.lower()
        
        # Check if AI acknowledges its limitations when appropriate
        if context.get("complex_question", False):
            limitation_acknowledgments = [
                "i'm an ai", "as an ai", "i don't have access to",
                "i can't", "my knowledge", "i'm not able to"
            ]
            
            has_acknowledgment = any(ack in response_lower for ack in limitation_acknowledgments)
            
            if not has_acknowledgment and len(response_text) > 100:
                return True, 0.6, "Response doesn't acknowledge AI limitations for complex question"
        
        # Check for transparency about uncertainty
        if context.get("uncertain_domain", False):
            uncertainty_indicators = [
                "might", "could", "possibly", "uncertain", "not sure",
                "depends", "varies", "it's possible"
            ]
            
            has_uncertainty = any(ind in response_lower for ind in uncertainty_indicators)
            
            if not has_uncertainty:
                return True, 0.5, "Response doesn't acknowledge uncertainty in uncertain domain"
        
        return False, 0.8, "Response is appropriately transparent"


class SafetyValidator:
    """Validates responses against constitutional principles."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.principles = self._initialize_principles()
        self.violation_history: List[Dict[str, Any]] = []
    
    def _initialize_principles(self) -> List[ConstitutionalPrinciple]:
        """Initialize constitutional principles."""
        
        principles = [
            ConstitutionalPrinciple(
                principle_id="helpfulness_1",
                principle_type=PrincipleType.HELPFULNESS,
                description="Responses should be helpful and constructive",
                weight=1.0,
                threshold=0.5
            ),
            ConstitutionalPrinciple(
                principle_id="harmlessness_1",
                principle_type=PrincipleType.HARMLESSNESS,
                description="Responses should not cause harm or encourage harmful behavior",
                weight=1.5,  # Higher weight for safety
                threshold=0.3,  # Lower threshold (more sensitive)
                violation_penalty=-1.0
            ),
            ConstitutionalPrinciple(
                principle_id="honesty_1",
                principle_type=PrincipleType.HONESTY,
                description="Responses should be honest and acknowledge uncertainty",
                weight=1.2,
                threshold=0.4
            ),
            ConstitutionalPrinciple(
                principle_id="privacy_1",
                principle_type=PrincipleType.PRIVACY,
                description="Responses should respect privacy and not request personal information",
                weight=1.3,
                threshold=0.4,
                violation_penalty=-0.8
            ),
            ConstitutionalPrinciple(
                principle_id="fairness_1",
                principle_type=PrincipleType.FAIRNESS,
                description="Responses should be fair and avoid bias or discrimination",
                weight=1.1,
                threshold=0.5
            ),
            ConstitutionalPrinciple(
                principle_id="transparency_1",
                principle_type=PrincipleType.TRANSPARENCY,
                description="Responses should be transparent about AI limitations",
                weight=0.8,
                threshold=0.6
            )
        ]
        
        return principles
    
    async def validate_response(
        self,
        response_text: str,
        conversation_state: ConversationState,
        action: Action
    ) -> Tuple[bool, float, List[str]]:
        """
        Validate response against all constitutional principles.
        
        Returns:
            is_safe: Whether response passes all safety checks
            safety_score: Overall safety score (0-1)
            violations: List of violation descriptions
        """
        
        violations = []
        safety_scores = []
        
        # Prepare context for evaluation
        context = {
            "conversation_length": len(conversation_state.conversation_history),
            "domain": conversation_state.domain_context,
            "action_type": action.action_type.value if action.action_type else "unknown",
            "complex_question": len(conversation_state.current_user_input) > 100,
            "uncertain_domain": "research" in conversation_state.domain_context.lower()
        }
        
        # Evaluate against each principle
        for principle in self.principles:
            is_violation, confidence, explanation = principle.evaluate(response_text, context)
            
            if is_violation and confidence >= principle.threshold:
                violations.append(f"{principle.principle_type.value}: {explanation}")
                safety_scores.append(0.0)  # Violation gets 0 score
                
                # Record violation
                self._record_violation(principle, response_text, explanation, confidence)
            else:
                # Calculate safety score for this principle
                principle_score = 1.0 - (confidence if is_violation else 0.0)
                safety_scores.append(principle_score)
        
        # Calculate overall safety score (weighted average)
        if safety_scores:
            weights = [p.weight for p in self.principles]
            weighted_score = sum(score * weight for score, weight in zip(safety_scores, weights))
            total_weight = sum(weights)
            overall_safety_score = weighted_score / total_weight
        else:
            overall_safety_score = 1.0
        
        is_safe = len(violations) == 0 and overall_safety_score >= self.config.safety_alert_threshold
        
        return is_safe, overall_safety_score, violations
    
    def _record_violation(
        self,
        principle: ConstitutionalPrinciple,
        response_text: str,
        explanation: str,
        confidence: float
    ) -> None:
        """Record a principle violation for analysis."""
        
        violation_record = {
            "timestamp": datetime.now(),
            "principle_id": principle.principle_id,
            "principle_type": principle.principle_type.value,
            "response_text": response_text[:200],  # Truncate for storage
            "explanation": explanation,
            "confidence": confidence,
            "severity": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
        }
        
        self.violation_history.append(violation_record)
        
        # Keep only recent violations
        if len(self.violation_history) > 1000:
            self.violation_history = self.violation_history[-500:]
        
        logger.warning(f"Constitutional violation detected: {explanation}")
    
    def get_violation_statistics(self) -> Dict[str, Any]:
        """Get statistics about constitutional violations."""
        
        if not self.violation_history:
            return {"total_violations": 0}
        
        # Count violations by type
        violation_counts = {}
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        
        for violation in self.violation_history:
            principle_type = violation["principle_type"]
            violation_counts[principle_type] = violation_counts.get(principle_type, 0) + 1
            severity_counts[violation["severity"]] += 1
        
        # Calculate recent trend
        recent_violations = [v for v in self.violation_history if 
                           (datetime.now() - v["timestamp"]).days <= 7]
        
        return {
            "total_violations": len(self.violation_history),
            "recent_violations": len(recent_violations),
            "violations_by_type": violation_counts,
            "violations_by_severity": severity_counts,
            "most_common_violation": max(violation_counts, key=violation_counts.get) if violation_counts else None
        }


class ContentFilter:
    """Filters content for harmful or inappropriate material."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.blocked_patterns = self._initialize_blocked_patterns()
        self.warning_patterns = self._initialize_warning_patterns()
    
    def _initialize_blocked_patterns(self) -> List[str]:
        """Initialize patterns that should be blocked."""
        
        return [
            # Violence and harm
            r'\b(kill|murder|violence|harm|hurt|attack|destroy)\b',
            
            # Illegal activities
            r'\b(illegal|criminal|fraud|scam|steal|hack|piracy)\b',
            
            # Hate speech
            r'\b(hate|racist|sexist|discrimination|offensive)\b',
            
            # Personal information requests
            r'\b(social security|credit card|password|address|phone number)\b',
            
            # Dangerous instructions
            r'\b(how to make (bomb|weapon|poison|drug))\b'
        ]
    
    def _initialize_warning_patterns(self) -> List[str]:
        """Initialize patterns that should trigger warnings."""
        
        return [
            # Potentially sensitive topics
            r'\b(politics|religion|controversial|sensitive)\b',
            
            # Medical advice
            r'\b(medical advice|diagnosis|treatment|medication)\b',
            
            # Financial advice
            r'\b(investment advice|financial planning|stock tips)\b',
            
            # Legal advice
            r'\b(legal advice|lawsuit|court|attorney)\b'
        ]
    
    async def filter_content(self, text: str) -> Tuple[bool, str, List[str]]:
        """
        Filter content for safety issues.
        
        Returns:
            is_safe: Whether content passes filter
            filtered_text: Text with any modifications
            warnings: List of warnings or issues found
        """
        
        warnings = []
        filtered_text = text
        is_safe = True
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                is_safe = False
                warnings.append(f"Blocked content detected: {pattern}")
                # Replace with placeholder
                filtered_text = re.sub(pattern, "[FILTERED]", filtered_text, flags=re.IGNORECASE)
        
        # Check for warning patterns
        for pattern in self.warning_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append(f"Potentially sensitive content: {pattern}")
        
        return is_safe, filtered_text, warnings


class ConstitutionalAI:
    """Main constitutional AI system that coordinates all safety components."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.safety_validator = SafetyValidator(config)
        self.content_filter = ContentFilter(config)
        self.enabled = config.enable_constitutional_ai
    
    async def evaluate_response(
        self,
        response_text: str,
        conversation_state: ConversationState,
        action: Action
    ) -> Tuple[bool, float, str, List[str]]:
        """
        Comprehensive evaluation of response safety.
        
        Returns:
            is_safe: Whether response is safe to use
            safety_score: Overall safety score (0-1)
            filtered_response: Response with any necessary filtering
            issues: List of safety issues found
        """
        
        if not self.enabled:
            return True, 1.0, response_text, []
        
        all_issues = []
        
        # Content filtering
        content_safe, filtered_text, content_warnings = await self.content_filter.filter_content(response_text)
        all_issues.extend(content_warnings)
        
        # Constitutional validation
        principles_safe, safety_score, principle_violations = await self.safety_validator.validate_response(
            filtered_text, conversation_state, action
        )
        all_issues.extend(principle_violations)
        
        # Overall safety determination
        is_safe = content_safe and principles_safe and safety_score >= self.config.safety_alert_threshold
        
        return is_safe, safety_score, filtered_text, all_issues
    
    def get_safety_statistics(self) -> Dict[str, Any]:
        """Get comprehensive safety statistics."""
        
        violation_stats = self.safety_validator.get_violation_statistics()
        
        return {
            "constitutional_ai_enabled": self.enabled,
            "safety_threshold": self.config.safety_alert_threshold,
            "violation_statistics": violation_stats,
            "total_principles": len(self.safety_validator.principles)
        }