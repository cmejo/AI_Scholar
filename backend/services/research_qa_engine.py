"""
Research Quality Assurance Engine
Automated validation of research methodology, statistical analysis, bias detection,
and citation verification to ensure research integrity and quality.
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from core.database import get_db
from core.advanced_research_models import QAReport, ReproducibilityRecord

logger = logging.getLogger(__name__)

class QAReportType(str, Enum):
    """QA report types"""
    METHODOLOGY = "methodology"
    STATISTICAL = "statistical"
    BIAS = "bias"
    CITATION = "citation"
    COMPREHENSIVE = "comprehensive"

class ValidationSeverity(str, Enum):
    """Validation issue severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Validation issue details"""
    id: str
    issue_type: str
    severity: ValidationSeverity
    title: str
    description: str
    location: str
    recommendation: str
    auto_fixable: bool

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    report_id: str
    report_type: QAReportType
    project_id: str
    overall_score: float
    methodology_score: float
    statistical_score: float
    bias_score: float
    citation_score: float
    issues_found: List[ValidationIssue]
    recommendations: List[str]
    best_practices_alignment: float
    confidence_score: float
    generated_at: datetime

@dataclass
class StatisticalAnalysis:
    """Statistical analysis structure"""
    analysis_type: str
    data_description: Dict[str, Any]
    methods_used: List[str]
    assumptions: List[str]
    results: Dict[str, Any]
    interpretation: str

@dataclass
class ResearchMethodology:
    """Research methodology structure"""
    research_design: str
    data_collection_methods: List[str]
    sampling_strategy: str
    variables: Dict[str, Any]
    procedures: List[str]
    ethical_considerations: List[str]

class ResearchQAEngine:
    """Main research quality assurance engine"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # QA rule sets
        self.methodology_rules = self._initialize_methodology_rules()
        self.statistical_rules = self._initialize_statistical_rules()
        self.bias_detection_rules = self._initialize_bias_rules()
        self.citation_rules = self._initialize_citation_rules()
        
        # Best practice databases
        self.best_practices = self._load_best_practices()
        self.common_issues = self._load_common_issues()

    async def validate_methodology(
        self,
        project_id: str,
        methodology: ResearchMethodology
    ) -> ValidationReport:
        """Validate research methodology against best practices"""
        try:
            logger.info(f"Validating methodology for project {project_id}")
            
            issues = []
            recommendations = []
            
            # Validate research design
            design_issues = await self._validate_research_design(methodology.research_design)
            issues.extend(design_issues)
            
            # Validate data collection methods
            collection_issues = await self._validate_data_collection(methodology.data_collection_methods)
            issues.extend(collection_issues)
            
            # Validate sampling strategy
            sampling_issues = await self._validate_sampling_strategy(methodology.sampling_strategy)
            issues.extend(sampling_issues)
            
            # Validate variables
            variable_issues = await self._validate_variables(methodology.variables)
            issues.extend(variable_issues)
            
            # Validate ethical considerations
            ethics_issues = await self._validate_ethics_considerations(methodology.ethical_considerations)
            issues.extend(ethics_issues)
            
            # Calculate methodology score
            methodology_score = await self._calculate_methodology_score(issues)
            
            # Generate recommendations
            recommendations = await self._generate_methodology_recommendations(issues, methodology)
            
            # Create validation report
            report = ValidationReport(
                report_id=str(uuid.uuid4()),
                report_type=QAReportType.METHODOLOGY,
                project_id=project_id,
                overall_score=methodology_score,
                methodology_score=methodology_score,
                statistical_score=0.0,
                bias_score=0.0,
                citation_score=0.0,
                issues_found=issues,
                recommendations=recommendations,
                best_practices_alignment=await self._calculate_best_practices_alignment(methodology),
                confidence_score=0.85,
                generated_at=datetime.utcnow()
            )
            
            # Save to database
            await self._save_qa_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error validating methodology: {str(e)}")
            raise

    async def check_statistical_analysis(
        self,
        project_id: str,
        analysis: StatisticalAnalysis
    ) -> ValidationReport:
        """Validate statistical analysis for correctness and appropriateness"""
        try:
            logger.info(f"Checking statistical analysis for project {project_id}")
            
            issues = []
            recommendations = []
            
            # Validate analysis type appropriateness
            type_issues = await self._validate_analysis_type(analysis)
            issues.extend(type_issues)
            
            # Check statistical assumptions
            assumption_issues = await self._check_statistical_assumptions(analysis)
            issues.extend(assumption_issues)
            
            # Validate sample size
            sample_issues = await self._validate_sample_size(analysis)
            issues.extend(sample_issues)
            
            # Check for common statistical errors
            error_issues = await self._check_common_statistical_errors(analysis)
            issues.extend(error_issues)
            
            # Validate result interpretation
            interpretation_issues = await self._validate_interpretation(analysis)
            issues.extend(interpretation_issues)
            
            # Calculate statistical score
            statistical_score = await self._calculate_statistical_score(issues)
            
            # Generate recommendations
            recommendations = await self._generate_statistical_recommendations(issues, analysis)
            
            report = ValidationReport(
                report_id=str(uuid.uuid4()),
                report_type=QAReportType.STATISTICAL,
                project_id=project_id,
                overall_score=statistical_score,
                methodology_score=0.0,
                statistical_score=statistical_score,
                bias_score=0.0,
                citation_score=0.0,
                issues_found=issues,
                recommendations=recommendations,
                best_practices_alignment=await self._calculate_statistical_best_practices(analysis),
                confidence_score=0.80,
                generated_at=datetime.utcnow()
            )
            
            await self._save_qa_report(report)
            return report
            
        except Exception as e:
            logger.error(f"Error checking statistical analysis: {str(e)}")
            raise

    async def assess_bias_risk(
        self,
        project_id: str,
        research_design: Dict[str, Any]
    ) -> ValidationReport:
        """Assess potential biases in research design"""
        try:
            logger.info(f"Assessing bias risk for project {project_id}")
            
            issues = []
            recommendations = []
            
            # Check for selection bias
            selection_issues = await self._check_selection_bias(research_design)
            issues.extend(selection_issues)
            
            # Check for confirmation bias
            confirmation_issues = await self._check_confirmation_bias(research_design)
            issues.extend(confirmation_issues)
            
            # Check for measurement bias
            measurement_issues = await self._check_measurement_bias(research_design)
            issues.extend(measurement_issues)
            
            # Check for reporting bias
            reporting_issues = await self._check_reporting_bias(research_design)
            issues.extend(reporting_issues)
            
            # Check for cultural/demographic bias
            demographic_issues = await self._check_demographic_bias(research_design)
            issues.extend(demographic_issues)
            
            # Calculate bias risk score
            bias_score = await self._calculate_bias_score(issues)
            
            # Generate bias mitigation recommendations
            recommendations = await self._generate_bias_recommendations(issues, research_design)
            
            report = ValidationReport(
                report_id=str(uuid.uuid4()),
                report_type=QAReportType.BIAS,
                project_id=project_id,
                overall_score=bias_score,
                methodology_score=0.0,
                statistical_score=0.0,
                bias_score=bias_score,
                citation_score=0.0,
                issues_found=issues,
                recommendations=recommendations,
                best_practices_alignment=await self._calculate_bias_best_practices(research_design),
                confidence_score=0.75,
                generated_at=datetime.utcnow()
            )
            
            await self._save_qa_report(report)
            return report
            
        except Exception as e:
            logger.error(f"Error assessing bias risk: {str(e)}")
            raise

    async def verify_citations(
        self,
        project_id: str,
        citations: List[Dict[str, Any]]
    ) -> ValidationReport:
        """Verify citation accuracy and completeness"""
        try:
            logger.info(f"Verifying citations for project {project_id}")
            
            issues = []
            recommendations = []
            
            for citation in citations:
                # Check citation format
                format_issues = await self._check_citation_format(citation)
                issues.extend(format_issues)
                
                # Check citation completeness
                completeness_issues = await self._check_citation_completeness(citation)
                issues.extend(completeness_issues)
                
                # Check for duplicate citations
                duplicate_issues = await self._check_duplicate_citations(citation, citations)
                issues.extend(duplicate_issues)
                
                # Validate DOI/URL if present
                link_issues = await self._validate_citation_links(citation)
                issues.extend(link_issues)
            
            # Check citation diversity
            diversity_issues = await self._check_citation_diversity(citations)
            issues.extend(diversity_issues)
            
            # Check for recent citations
            recency_issues = await self._check_citation_recency(citations)
            issues.extend(recency_issues)
            
            # Calculate citation score
            citation_score = await self._calculate_citation_score(issues, len(citations))
            
            # Generate citation recommendations
            recommendations = await self._generate_citation_recommendations(issues, citations)
            
            report = ValidationReport(
                report_id=str(uuid.uuid4()),
                report_type=QAReportType.CITATION,
                project_id=project_id,
                overall_score=citation_score,
                methodology_score=0.0,
                statistical_score=0.0,
                bias_score=0.0,
                citation_score=citation_score,
                issues_found=issues,
                recommendations=recommendations,
                best_practices_alignment=await self._calculate_citation_best_practices(citations),
                confidence_score=0.90,
                generated_at=datetime.utcnow()
            )
            
            await self._save_qa_report(report)
            return report
            
        except Exception as e:
            logger.error(f"Error verifying citations: {str(e)}")
            raise

    async def generate_reproducibility_checklist(
        self,
        project_id: str,
        research_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate reproducibility checklist for research project"""
        try:
            checklist = {
                "methodology_documentation": [
                    {
                        "item": "Research design clearly described",
                        "status": "pending",
                        "importance": "critical",
                        "description": "Detailed description of research design and rationale"
                    },
                    {
                        "item": "Data collection procedures documented",
                        "status": "pending",
                        "importance": "critical",
                        "description": "Step-by-step data collection procedures"
                    },
                    {
                        "item": "Sampling strategy explained",
                        "status": "pending",
                        "importance": "high",
                        "description": "Clear explanation of sampling methodology"
                    }
                ],
                "data_management": [
                    {
                        "item": "Raw data preserved",
                        "status": "pending",
                        "importance": "critical",
                        "description": "Original data files stored securely"
                    },
                    {
                        "item": "Data processing steps documented",
                        "status": "pending",
                        "importance": "critical",
                        "description": "All data transformations and cleaning steps recorded"
                    },
                    {
                        "item": "Data dictionary provided",
                        "status": "pending",
                        "importance": "high",
                        "description": "Variable definitions and coding schemes"
                    }
                ],
                "analysis_documentation": [
                    {
                        "item": "Analysis code available",
                        "status": "pending",
                        "importance": "critical",
                        "description": "Complete analysis scripts with comments"
                    },
                    {
                        "item": "Software versions documented",
                        "status": "pending",
                        "importance": "high",
                        "description": "Versions of all software and packages used"
                    },
                    {
                        "item": "Statistical assumptions checked",
                        "status": "pending",
                        "importance": "high",
                        "description": "Documentation of assumption testing"
                    }
                ],
                "reporting": [
                    {
                        "item": "Complete methodology section",
                        "status": "pending",
                        "importance": "critical",
                        "description": "Sufficient detail for replication"
                    },
                    {
                        "item": "Results fully reported",
                        "status": "pending",
                        "importance": "critical",
                        "description": "All results including non-significant findings"
                    },
                    {
                        "item": "Limitations discussed",
                        "status": "pending",
                        "importance": "high",
                        "description": "Honest discussion of study limitations"
                    }
                ]
            }
            
            # Calculate completion percentage
            total_items = sum(len(section) for section in checklist.values())
            completed_items = 0  # Would be calculated based on actual status
            
            checklist["summary"] = {
                "total_items": total_items,
                "completed_items": completed_items,
                "completion_percentage": (completed_items / total_items) * 100,
                "critical_items_pending": sum(
                    1 for section in checklist.values() 
                    if isinstance(section, list)
                    for item in section 
                    if item["importance"] == "critical" and item["status"] == "pending"
                )
            }
            
            return checklist
            
        except Exception as e:
            logger.error(f"Error generating reproducibility checklist: {str(e)}")
            return {}

    # Helper methods for validation rules
    def _initialize_methodology_rules(self) -> Dict[str, Any]:
        """Initialize methodology validation rules"""
        return {
            "required_components": [
                "research_design", "data_collection", "sampling", "variables"
            ],
            "design_types": [
                "experimental", "quasi-experimental", "observational", 
                "descriptive", "correlational", "case_study"
            ],
            "sampling_methods": [
                "random", "stratified", "cluster", "convenience", 
                "purposive", "snowball"
            ]
        }

    def _initialize_statistical_rules(self) -> Dict[str, Any]:
        """Initialize statistical validation rules"""
        return {
            "common_tests": {
                "t_test": {"min_sample": 30, "assumptions": ["normality", "independence"]},
                "anova": {"min_sample": 20, "assumptions": ["normality", "homogeneity", "independence"]},
                "chi_square": {"min_expected": 5, "assumptions": ["independence", "expected_frequency"]},
                "regression": {"min_sample": 50, "assumptions": ["linearity", "independence", "normality"]}
            },
            "effect_sizes": ["cohen_d", "eta_squared", "r_squared", "odds_ratio"],
            "power_analysis": {"min_power": 0.8, "alpha": 0.05}
        }

    def _initialize_bias_rules(self) -> Dict[str, Any]:
        """Initialize bias detection rules"""
        return {
            "selection_bias": [
                "non_representative_sample", "volunteer_bias", "survivorship_bias"
            ],
            "measurement_bias": [
                "observer_bias", "recall_bias", "social_desirability"
            ],
            "confirmation_bias": [
                "cherry_picking", "p_hacking", "harking"
            ]
        }

    def _initialize_citation_rules(self) -> Dict[str, Any]:
        """Initialize citation validation rules"""
        return {
            "required_fields": ["author", "title", "year"],
            "formats": ["apa", "mla", "chicago", "ieee"],
            "recency_threshold": 5,  # years
            "diversity_threshold": 0.7  # minimum diversity score
        }

    def _load_best_practices(self) -> Dict[str, Any]:
        """Load research best practices database"""
        return {
            "methodology": {
                "sample_size_guidelines": "Use power analysis for sample size determination",
                "control_groups": "Include appropriate control groups for experimental designs",
                "randomization": "Use proper randomization techniques to reduce bias"
            },
            "statistics": {
                "effect_sizes": "Always report effect sizes with statistical tests",
                "confidence_intervals": "Report confidence intervals for key estimates",
                "multiple_comparisons": "Adjust for multiple comparisons when appropriate"
            }
        }

    def _load_common_issues(self) -> Dict[str, Any]:
        """Load common research issues database"""
        return {
            "methodology": [
                "Inadequate sample size",
                "Lack of control group",
                "Poor randomization"
            ],
            "statistics": [
                "P-hacking",
                "Assumption violations",
                "Missing effect sizes"
            ]
        }

    # Validation implementation methods (simplified for brevity)
    async def _validate_research_design(self, design: str) -> List[ValidationIssue]:
        """Validate research design"""
        issues = []
        if not design or design.lower() not in self.methodology_rules["design_types"]:
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                issue_type="methodology",
                severity=ValidationSeverity.ERROR,
                title="Invalid Research Design",
                description=f"Research design '{design}' is not recognized or missing",
                location="methodology.research_design",
                recommendation="Specify a valid research design (experimental, observational, etc.)",
                auto_fixable=False
            ))
        return issues

    async def _calculate_methodology_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate methodology quality score"""
        if not issues:
            return 1.0
        
        penalty = 0.0
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                penalty += 0.3
            elif issue.severity == ValidationSeverity.ERROR:
                penalty += 0.2
            elif issue.severity == ValidationSeverity.WARNING:
                penalty += 0.1
            else:  # INFO
                penalty += 0.05
        
        return max(0.0, 1.0 - penalty)

    async def _save_qa_report(self, report: ValidationReport):
        """Save QA report to database"""
        try:
            qa_record = QAReport(
                project_id=report.project_id,
                report_type=report.report_type.value,
                methodology_score=report.methodology_score,
                statistical_validity_score=report.statistical_score,
                bias_risk_score=1.0 - report.bias_score,  # Invert for risk
                citation_accuracy_score=report.citation_score,
                overall_quality_score=report.overall_score,
                issues_identified=[asdict(issue) for issue in report.issues_found],
                recommendations=report.recommendations,
                validation_details={
                    "best_practices_alignment": report.best_practices_alignment,
                    "confidence_score": report.confidence_score,
                    "generated_at": report.generated_at.isoformat()
                }
            )
            
            self.db.add(qa_record)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving QA report: {str(e)}")
            self.db.rollback()

    # Placeholder implementations for other validation methods
    async def _validate_data_collection(self, methods: List[str]) -> List[ValidationIssue]:
        return []
    
    async def _validate_sampling_strategy(self, strategy: str) -> List[ValidationIssue]:
        return []
    
    async def _validate_variables(self, variables: Dict[str, Any]) -> List[ValidationIssue]:
        return []
    
    async def _validate_ethics_considerations(self, considerations: List[str]) -> List[ValidationIssue]:
        return []
    
    async def _generate_methodology_recommendations(self, issues: List[ValidationIssue], methodology: ResearchMethodology) -> List[str]:
        return ["Consider strengthening methodology documentation"]
    
    async def _calculate_best_practices_alignment(self, methodology: ResearchMethodology) -> float:
        return 0.8

# Export classes
__all__ = [
    'ResearchQAEngine',
    'ValidationReport',
    'ValidationIssue',
    'StatisticalAnalysis',
    'ResearchMethodology',
    'QAReportType',
    'ValidationSeverity'
]