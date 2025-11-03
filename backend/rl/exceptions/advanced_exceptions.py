"""Advanced exception classes for RL system components."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class RLSystemError(Exception):
    """Base exception for RL system errors."""
    
    def __init__(self, message: str, error_code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "RL_SYSTEM_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class MultiModalProcessingError(RLSystemError):
    """Exception for multi-modal processing errors."""
    
    def __init__(self, message: str, processing_stage: str = None, 
                 visual_element_type: str = None, **kwargs):
        super().__init__(message, "MULTIMODAL_PROCESSING_ERROR", **kwargs)
        self.processing_stage = processing_stage
        self.visual_element_type = visual_element_type
        
        if processing_stage:
            self.context["processing_stage"] = processing_stage
        if visual_element_type:
            self.context["visual_element_type"] = visual_element_type


class VisualProcessingError(MultiModalProcessingError):
    """Exception for visual content processing errors."""
    
    def __init__(self, message: str, image_format: str = None, 
                 image_size: tuple = None, **kwargs):
        super().__init__(message, "visual_processing", **kwargs)
        self.error_code = "VISUAL_PROCESSING_ERROR"
        self.image_format = image_format
        self.image_size = image_size
        
        if image_format:
            self.context["image_format"] = image_format
        if image_size:
            self.context["image_size"] = image_size


class ChartAnalysisError(MultiModalProcessingError):
    """Exception for chart analysis errors."""
    
    def __init__(self, message: str, chart_type: str = None, 
                 data_extraction_stage: str = None, **kwargs):
        super().__init__(message, "chart_analysis", "chart", **kwargs)
        self.error_code = "CHART_ANALYSIS_ERROR"
        self.chart_type = chart_type
        self.data_extraction_stage = data_extraction_stage
        
        if chart_type:
            self.context["chart_type"] = chart_type
        if data_extraction_stage:
            self.context["data_extraction_stage"] = data_extraction_stage


class DiagramAnalysisError(MultiModalProcessingError):
    """Exception for diagram analysis errors."""
    
    def __init__(self, message: str, diagram_type: str = None, 
                 structure_analysis_stage: str = None, **kwargs):
        super().__init__(message, "diagram_analysis", "diagram", **kwargs)
        self.error_code = "DIAGRAM_ANALYSIS_ERROR"
        self.diagram_type = diagram_type
        self.structure_analysis_stage = structure_analysis_stage
        
        if diagram_type:
            self.context["diagram_type"] = diagram_type
        if structure_analysis_stage:
            self.context["structure_analysis_stage"] = structure_analysis_stage


class FeatureIntegrationError(MultiModalProcessingError):
    """Exception for feature integration errors."""
    
    def __init__(self, message: str, integration_method: str = None, 
                 feature_types: List[str] = None, **kwargs):
        super().__init__(message, "feature_integration", **kwargs)
        self.error_code = "FEATURE_INTEGRATION_ERROR"
        self.integration_method = integration_method
        self.feature_types = feature_types or []
        
        if integration_method:
            self.context["integration_method"] = integration_method
        if feature_types:
            self.context["feature_types"] = feature_types


class PersonalizationError(RLSystemError):
    """Exception for personalization system errors."""
    
    def __init__(self, message: str, user_id: str = None, 
                 personalization_component: str = None, **kwargs):
        super().__init__(message, "PERSONALIZATION_ERROR", **kwargs)
        self.user_id = user_id
        self.personalization_component = personalization_component
        
        if user_id:
            self.context["user_id"] = user_id
        if personalization_component:
            self.context["personalization_component"] = personalization_component


class AdaptationFailureError(PersonalizationError):
    """Exception for adaptation algorithm failures."""
    
    def __init__(self, message: str, adaptation_algorithm: str = None, 
                 failure_reason: str = None, **kwargs):
        super().__init__(message, personalization_component="adaptation", **kwargs)
        self.error_code = "ADAPTATION_FAILURE_ERROR"
        self.adaptation_algorithm = adaptation_algorithm
        self.failure_reason = failure_reason
        
        if adaptation_algorithm:
            self.context["adaptation_algorithm"] = adaptation_algorithm
        if failure_reason:
            self.context["failure_reason"] = failure_reason


class DeepPreferenceLearningError(AdaptationFailureError):
    """Exception for deep preference learning errors."""
    
    def __init__(self, message: str, learning_stage: str = None, 
                 model_parameters: Dict[str, Any] = None, **kwargs):
        super().__init__(message, "deep_preference_learning", **kwargs)
        self.error_code = "DEEP_PREFERENCE_LEARNING_ERROR"
        self.learning_stage = learning_stage
        self.model_parameters = model_parameters or {}
        
        if learning_stage:
            self.context["learning_stage"] = learning_stage
        if model_parameters:
            self.context["model_parameters"] = model_parameters


class ContextualBanditError(AdaptationFailureError):
    """Exception for contextual bandit errors."""
    
    def __init__(self, message: str, bandit_operation: str = None, 
                 action_space_size: int = None, **kwargs):
        super().__init__(message, "contextual_bandit", **kwargs)
        self.error_code = "CONTEXTUAL_BANDIT_ERROR"
        self.bandit_operation = bandit_operation
        self.action_space_size = action_space_size
        
        if bandit_operation:
            self.context["bandit_operation"] = bandit_operation
        if action_space_size:
            self.context["action_space_size"] = action_space_size


class MetaLearningError(AdaptationFailureError):
    """Exception for meta-learning errors."""
    
    def __init__(self, message: str, meta_learning_stage: str = None, 
                 similar_users_count: int = None, **kwargs):
        super().__init__(message, "meta_learning", **kwargs)
        self.error_code = "META_LEARNING_ERROR"
        self.meta_learning_stage = meta_learning_stage
        self.similar_users_count = similar_users_count
        
        if meta_learning_stage:
            self.context["meta_learning_stage"] = meta_learning_stage
        if similar_users_count:
            self.context["similar_users_count"] = similar_users_count


class BehaviorPredictionError(PersonalizationError):
    """Exception for behavior prediction errors."""
    
    def __init__(self, message: str, prediction_type: str = None, 
                 prediction_horizon: str = None, **kwargs):
        super().__init__(message, personalization_component="behavior_prediction", **kwargs)
        self.error_code = "BEHAVIOR_PREDICTION_ERROR"
        self.prediction_type = prediction_type
        self.prediction_horizon = prediction_horizon
        
        if prediction_type:
            self.context["prediction_type"] = prediction_type
        if prediction_horizon:
            self.context["prediction_horizon"] = prediction_horizon


class ResearchAssistantError(RLSystemError):
    """Exception for research assistant mode errors."""
    
    def __init__(self, message: str, workflow_id: str = None, 
                 research_component: str = None, **kwargs):
        super().__init__(message, "RESEARCH_ASSISTANT_ERROR", **kwargs)
        self.workflow_id = workflow_id
        self.research_component = research_component
        
        if workflow_id:
            self.context["workflow_id"] = workflow_id
        if research_component:
            self.context["research_component"] = research_component


class WorkflowOptimizationError(ResearchAssistantError):
    """Exception for workflow optimization errors."""
    
    def __init__(self, message: str, optimization_stage: str = None, 
                 workflow_metrics: Dict[str, float] = None, **kwargs):
        super().__init__(message, research_component="workflow_optimization", **kwargs)
        self.error_code = "WORKFLOW_OPTIMIZATION_ERROR"
        self.optimization_stage = optimization_stage
        self.workflow_metrics = workflow_metrics or {}
        
        if optimization_stage:
            self.context["optimization_stage"] = optimization_stage
        if workflow_metrics:
            self.context["workflow_metrics"] = workflow_metrics


class WorkflowLearningError(ResearchAssistantError):
    """Exception for workflow learning errors."""
    
    def __init__(self, message: str, learning_operation: str = None, 
                 pattern_count: int = None, **kwargs):
        super().__init__(message, research_component="workflow_learning", **kwargs)
        self.error_code = "WORKFLOW_LEARNING_ERROR"
        self.learning_operation = learning_operation
        self.pattern_count = pattern_count
        
        if learning_operation:
            self.context["learning_operation"] = learning_operation
        if pattern_count:
            self.context["pattern_count"] = pattern_count


class ResearchPatternError(ResearchAssistantError):
    """Exception for research pattern analysis errors."""
    
    def __init__(self, message: str, pattern_type: str = None, 
                 analysis_depth: str = None, **kwargs):
        super().__init__(message, research_component="pattern_analysis", **kwargs)
        self.error_code = "RESEARCH_PATTERN_ERROR"
        self.pattern_type = pattern_type
        self.analysis_depth = analysis_depth
        
        if pattern_type:
            self.context["pattern_type"] = pattern_type
        if analysis_depth:
            self.context["analysis_depth"] = analysis_depth


class ConfigurationError(RLSystemError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_section: str = None, 
                 config_parameter: str = None, **kwargs):
        super().__init__(message, "CONFIGURATION_ERROR", **kwargs)
        self.config_section = config_section
        self.config_parameter = config_parameter
        
        if config_section:
            self.context["config_section"] = config_section
        if config_parameter:
            self.context["config_parameter"] = config_parameter


class ValidationError(ConfigurationError):
    """Exception for configuration validation errors."""
    
    def __init__(self, message: str, validation_rule: str = None, 
                 invalid_value: Any = None, **kwargs):
        super().__init__(message, **kwargs)
        self.error_code = "VALIDATION_ERROR"
        self.validation_rule = validation_rule
        self.invalid_value = invalid_value
        
        if validation_rule:
            self.context["validation_rule"] = validation_rule
        if invalid_value is not None:
            self.context["invalid_value"] = str(invalid_value)


class IntegrationError(RLSystemError):
    """Exception for system integration errors."""
    
    def __init__(self, message: str, integration_point: str = None, 
                 component_a: str = None, component_b: str = None, **kwargs):
        super().__init__(message, "INTEGRATION_ERROR", **kwargs)
        self.integration_point = integration_point
        self.component_a = component_a
        self.component_b = component_b
        
        if integration_point:
            self.context["integration_point"] = integration_point
        if component_a:
            self.context["component_a"] = component_a
        if component_b:
            self.context["component_b"] = component_b


class RewardCalculationError(RLSystemError):
    """Exception for reward calculation errors."""
    
    def __init__(self, message: str, reward_component: str = None, 
                 calculation_stage: str = None, **kwargs):
        super().__init__(message, "REWARD_CALCULATION_ERROR", **kwargs)
        self.reward_component = reward_component
        self.calculation_stage = calculation_stage
        
        if reward_component:
            self.context["reward_component"] = reward_component
        if calculation_stage:
            self.context["calculation_stage"] = calculation_stage


class MetricsCollectionError(RLSystemError):
    """Exception for metrics collection errors."""
    
    def __init__(self, message: str, metrics_type: str = None, 
                 collection_stage: str = None, **kwargs):
        super().__init__(message, "METRICS_COLLECTION_ERROR", **kwargs)
        self.metrics_type = metrics_type
        self.collection_stage = collection_stage
        
        if metrics_type:
            self.context["metrics_type"] = metrics_type
        if collection_stage:
            self.context["collection_stage"] = collection_stage


# Exception hierarchy mapping for error handling
EXCEPTION_HIERARCHY = {
    "multimodal": {
        "base": MultiModalProcessingError,
        "visual": VisualProcessingError,
        "chart": ChartAnalysisError,
        "diagram": DiagramAnalysisError,
        "integration": FeatureIntegrationError
    },
    "personalization": {
        "base": PersonalizationError,
        "adaptation": AdaptationFailureError,
        "deep_learning": DeepPreferenceLearningError,
        "bandit": ContextualBanditError,
        "meta_learning": MetaLearningError,
        "behavior": BehaviorPredictionError
    },
    "research_assistant": {
        "base": ResearchAssistantError,
        "optimization": WorkflowOptimizationError,
        "learning": WorkflowLearningError,
        "patterns": ResearchPatternError
    },
    "system": {
        "config": ConfigurationError,
        "validation": ValidationError,
        "integration": IntegrationError,
        "rewards": RewardCalculationError,
        "metrics": MetricsCollectionError
    }
}


def get_exception_class(category: str, subcategory: str = "base") -> type:
    """Get appropriate exception class for error category."""
    if category in EXCEPTION_HIERARCHY:
        if subcategory in EXCEPTION_HIERARCHY[category]:
            return EXCEPTION_HIERARCHY[category][subcategory]
        return EXCEPTION_HIERARCHY[category]["base"]
    return RLSystemError


def create_error_context(component: str, operation: str, **kwargs) -> Dict[str, Any]:
    """Create standardized error context."""
    context = {
        "component": component,
        "operation": operation,
        "timestamp": datetime.now().isoformat()
    }
    context.update(kwargs)
    return context