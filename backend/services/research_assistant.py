"""
Research Assistant Service
Provides advanced research assistance capabilities including literature reviews,
research proposals, methodology suggestions, and data analysis guidance.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import uuid
import re

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from core.database import (
    get_db, Document, DocumentChunk, User, DocumentTag,
    KnowledgeGraphEntity, KnowledgeGraphRelationship,
    AnalyticsEvent
)
from services.multimodal_processor import MultiModalProcessor, ContentType
# from services.topic_modeling_service import TopicModelingService
from services.knowledge_graph import EnhancedKnowledgeGraphService
from models.schemas import AnalyticsEventCreate

logger = logging.getLogger(__name__)

class ResearchType(str, Enum):
    """Types of research methodologies"""
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    MIXED_METHODS = "mixed_methods"
    EXPERIMENTAL = "experimental"
    OBSERVATIONAL = "observational"
    THEORETICAL = "theoretical"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"

class ResearchDomain(str, Enum):
    """Research domains and fields"""
    COMPUTER_SCIENCE = "computer_science"
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    MATHEMATICS = "mathematics"
    PSYCHOLOGY = "psychology"
    SOCIAL_SCIENCES = "social_sciences"
    BUSINESS = "business"
    EDUCATION = "education"
    HUMANITIES = "humanities"

@dataclass
class LiteratureReviewSection:
    """A section of a literature review"""
    title: str
    content: str
    citations: List[str]
    key_findings: List[str]
    gaps_identified: List[str]
    section_type: str  # introduction, methodology, findings, discussion, conclusion

@dataclass
class ResearchProposal:
    """A structured research proposal"""
    title: str
    abstract: str
    introduction: str
    literature_review: str
    methodology: str
    expected_outcomes: str
    timeline: Dict[str, str]
    budget_estimate: Optional[str]
    references: List[str]
    research_questions: List[str]
    hypotheses: List[str]

@dataclass
class MethodologyRecommendation:
    """A methodology recommendation for research"""
    method_name: str
    description: str
    advantages: List[str]
    disadvantages: List[str]
    applicability_score: float
    required_resources: List[str]
    estimated_duration: str
    complexity_level: str  # beginner, intermediate, advanced
    references: List[str]

@dataclass
class DataAnalysisGuidance:
    """Guidance for data analysis"""
    analysis_type: str
    statistical_methods: List[str]
    software_recommendations: List[str]
    step_by_step_guide: List[str]
    interpretation_guidelines: str
    common_pitfalls: List[str]
    validation_methods: List[str]
    reporting_standards: List[str]

class ResearchAssistant:
    """Main research assistant service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.multimodal_processor = MultiModalProcessor(db)
        # self.topic_service = TopicModelingService(db)
        self.kg_service = EnhancedKnowledgeGraphService()
        
        # Research templates and patterns
        self.research_templates = self._load_research_templates()
        self.methodology_database = self._load_methodology_database()
        self.analysis_patterns = self._load_analysis_patterns()
    
    def _load_research_templates(self) -> Dict[str, Any]:
        """Load research proposal and literature review templates"""
        return {
            "literature_review": {
                "sections": [
                    "Introduction and Background",
                    "Theoretical Framework", 
                    "Current State of Research",
                    "Methodological Approaches",
                    "Key Findings and Trends",
                    "Research Gaps and Limitations",
                    "Future Directions",
                    "Conclusion"
                ],
                "structure": {
                    "introduction_percentage": 15,
                    "body_percentage": 70,
                    "conclusion_percentage": 15
                }
            },
            "research_proposal": {
                "sections": [
                    "Title and Abstract",
                    "Introduction and Problem Statement",
                    "Literature Review",
                    "Research Questions and Hypotheses",
                    "Methodology",
                    "Expected Outcomes and Significance",
                    "Timeline and Milestones",
                    "Budget and Resources",
                    "References"
                ],
                "word_limits": {
                    "abstract": 300,
                    "introduction": 1000,
                    "literature_review": 2000,
                    "methodology": 1500,
                    "total": 8000
                }
            }
        }
    
    def _load_methodology_database(self) -> Dict[str, Any]:
        """Load database of research methodologies"""
        return {
            ResearchType.QUANTITATIVE: {
                "methods": [
                    "Survey Research", "Experimental Design", "Quasi-Experimental",
                    "Correlational Studies", "Longitudinal Studies", "Cross-sectional Studies"
                ],
                "analysis_types": ["Descriptive Statistics", "Inferential Statistics", 
                                 "Regression Analysis", "ANOVA", "Factor Analysis"],
                "software": ["SPSS", "R", "Python", "SAS", "Stata"]
            },
            ResearchType.QUALITATIVE: {
                "methods": [
                    "Ethnography", "Case Study", "Grounded Theory", 
                    "Phenomenology", "Narrative Research", "Action Research"
                ],
                "analysis_types": ["Thematic Analysis", "Content Analysis", 
                                 "Discourse Analysis", "Narrative Analysis"],
                "software": ["NVivo", "Atlas.ti", "MAXQDA", "Dedoose"]
            },
            ResearchType.MIXED_METHODS: {
                "methods": [
                    "Convergent Parallel", "Explanatory Sequential", 
                    "Exploratory Sequential", "Embedded Design"
                ],
                "analysis_types": ["Joint Displays", "Meta-Inferences", 
                                 "Mixed Methods Matrix"],
                "software": ["R", "Python", "NVivo", "SPSS"]
            }
        }
    
    def _load_analysis_patterns(self) -> Dict[str, Any]:
        """Load common data analysis patterns and guidelines"""
        return {
            "statistical_tests": {
                "comparison": {
                    "two_groups": ["t-test", "Mann-Whitney U", "Chi-square"],
                    "multiple_groups": ["ANOVA", "Kruskal-Wallis", "Chi-square"],
                    "paired_data": ["Paired t-test", "Wilcoxon signed-rank"]
                },
                "relationship": {
                    "correlation": ["Pearson", "Spearman", "Kendall"],
                    "regression": ["Linear", "Logistic", "Multiple", "Polynomial"]
                },
                "prediction": {
                    "classification": ["Logistic Regression", "SVM", "Random Forest"],
                    "regression": ["Linear Regression", "Ridge", "Lasso", "Neural Networks"]
                }
            },
            "sample_size": {
                "small": {"n": "< 30", "methods": ["Non-parametric tests", "Bootstrap"]},
                "medium": {"n": "30-100", "methods": ["Parametric tests", "Standard methods"]},
                "large": {"n": "> 100", "methods": ["Advanced methods", "Machine learning"]}
            }
        }
    
    async def generate_literature_review(
        self,
        topic: str,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        review_type: str = "comprehensive",
        max_length: int = 5000
    ) -> LiteratureReviewSection:
        """
        Generate a comprehensive literature review on a given topic
        """
        try:
            logger.info(f"Generating literature review for topic: {topic}")
            
            # Get relevant documents
            documents = await self._get_relevant_documents(topic, user_id, document_ids)
            
            if not documents:
                raise ValueError("No relevant documents found for the topic")
            
            # Analyze documents for key themes and findings
            themes = await self._extract_research_themes(documents)
            
            # Perform topic modeling to identify key areas
            topic_result = await self.topic_service.analyze_document_topics(
                user_id=user_id,
                document_ids=[doc.id for doc in documents],
                n_topics=min(8, len(documents)),
                update_tags=False
            )
            
            # Extract key findings and methodologies
            findings = await self._extract_key_findings(documents)
            methodologies = await self._identify_methodologies(documents)
            
            # Identify research gaps
            gaps = await self._identify_research_gaps(documents, themes)
            
            # Generate structured review sections
            sections = []
            
            # Introduction section
            intro_section = await self._generate_introduction_section(
                topic, themes, len(documents)
            )
            sections.append(intro_section)
            
            # Thematic analysis sections
            for theme in themes[:5]:  # Top 5 themes
                theme_section = await self._generate_theme_section(
                    theme, documents, findings
                )
                sections.append(theme_section)
            
            # Methodology section
            methodology_section = await self._generate_methodology_section(
                methodologies, documents
            )
            sections.append(methodology_section)
            
            # Research gaps section
            gaps_section = await self._generate_gaps_section(gaps, themes)
            sections.append(gaps_section)
            
            # Conclusion section
            conclusion_section = await self._generate_conclusion_section(
                topic, themes, gaps, findings
            )
            sections.append(conclusion_section)
            
            # Combine sections into final review
            full_content = self._combine_review_sections(sections, max_length)
            
            # Extract all citations
            all_citations = []
            for section in sections:
                all_citations.extend(section.citations)
            
            # Track analytics
            await self._track_research_event(
                user_id, "literature_review_generated", {
                    "topic": topic,
                    "documents_analyzed": len(documents),
                    "sections_generated": len(sections),
                    "word_count": len(full_content.split())
                }
            )
            
            return LiteratureReviewSection(
                title=f"Literature Review: {topic}",
                content=full_content,
                citations=list(set(all_citations)),  # Remove duplicates
                key_findings=[finding["text"] for finding in findings[:10]],
                gaps_identified=[gap["description"] for gap in gaps[:5]],
                section_type="complete_review"
            )
            
        except Exception as e:
            logger.error(f"Error generating literature review: {str(e)}")
            raise

    async def create_research_proposal(
        self,
        research_idea: str,
        user_id: str,
        research_type: ResearchType,
        domain: ResearchDomain,
        duration_months: int = 12
    ) -> ResearchProposal:
        """
        Create a structured research proposal based on a research idea
        """
        try:
            logger.info(f"Creating research proposal for: {research_idea}")
            
            # Analyze the research idea
            idea_analysis = await self._analyze_research_idea(research_idea, domain)
            
            # Get relevant literature
            relevant_docs = await self._get_relevant_documents(
                research_idea, user_id, limit=20
            )
            
            # Generate research questions
            research_questions = await self._generate_research_questions(
                research_idea, idea_analysis, research_type
            )
            
            # Generate hypotheses
            hypotheses = await self._generate_hypotheses(
                research_questions, research_type, domain
            )
            
            # Suggest methodology
            methodology = await self._suggest_methodology(
                research_questions, research_type, domain
            )
            
            # Create timeline
            timeline = await self._create_research_timeline(
                methodology, duration_months
            )
            
            # Generate proposal sections
            title = await self._generate_proposal_title(research_idea, domain)
            abstract = await self._generate_abstract(
                research_idea, research_questions, methodology
            )
            introduction = await self._generate_introduction(
                research_idea, idea_analysis, relevant_docs
            )
            literature_review = await self._generate_proposal_literature_review(
                research_idea, relevant_docs
            )
            methodology_section = await self._generate_methodology_section_proposal(
                methodology, research_type
            )
            expected_outcomes = await self._generate_expected_outcomes(
                research_questions, hypotheses, domain
            )
            
            # Extract references
            references = await self._extract_references(relevant_docs)
            
            # Track analytics
            await self._track_research_event(
                user_id, "research_proposal_created", {
                    "research_type": research_type.value,
                    "domain": domain.value,
                    "duration_months": duration_months,
                    "questions_generated": len(research_questions),
                    "hypotheses_generated": len(hypotheses)
                }
            )
            
            return ResearchProposal(
                title=title,
                abstract=abstract,
                introduction=introduction,
                literature_review=literature_review,
                methodology=methodology_section,
                expected_outcomes=expected_outcomes,
                timeline=timeline,
                budget_estimate=None,  # Could be enhanced later
                references=references,
                research_questions=research_questions,
                hypotheses=hypotheses
            )
            
        except Exception as e:
            logger.error(f"Error creating research proposal: {str(e)}")
            raise

    async def suggest_methodology(
        self,
        research_questions: List[str],
        research_type: ResearchType,
        domain: ResearchDomain,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[MethodologyRecommendation]:
        """
        Suggest appropriate research methodologies based on research questions
        """
        try:
            logger.info(f"Suggesting methodologies for {research_type} research in {domain}")
            
            recommendations = []
            
            # Get methodology database for the research type
            method_db = self.methodology_database.get(research_type, {})
            available_methods = method_db.get("methods", [])
            
            # Analyze research questions to determine best methods
            for method in available_methods:
                # Calculate applicability score
                applicability = await self._calculate_method_applicability(
                    method, research_questions, domain, constraints
                )
                
                if applicability > 0.3:  # Only include relevant methods
                    # Get method details
                    method_details = await self._get_method_details(
                        method, research_type, domain
                    )
                    
                    recommendation = MethodologyRecommendation(
                        method_name=method,
                        description=method_details["description"],
                        advantages=method_details["advantages"],
                        disadvantages=method_details["disadvantages"],
                        applicability_score=applicability,
                        required_resources=method_details["resources"],
                        estimated_duration=method_details["duration"],
                        complexity_level=method_details["complexity"],
                        references=method_details["references"]
                    )
                    
                    recommendations.append(recommendation)
            
            # Sort by applicability score
            recommendations.sort(key=lambda x: x.applicability_score, reverse=True)
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error suggesting methodology: {str(e)}")
            raise

    async def provide_data_analysis_guidance(
        self,
        data_description: str,
        research_questions: List[str],
        data_type: str = "mixed",
        sample_size: Optional[int] = None
    ) -> DataAnalysisGuidance:
        """
        Provide guidance for data analysis based on research context
        """
        try:
            logger.info(f"Providing data analysis guidance for {data_type} data")
            
            # Determine analysis type based on research questions and data
            analysis_type = await self._determine_analysis_type(
                research_questions, data_description, data_type
            )
            
            # Suggest statistical methods
            statistical_methods = await self._suggest_statistical_methods(
                analysis_type, data_type, sample_size
            )
            
            # Recommend software
            software_recommendations = await self._recommend_analysis_software(
                statistical_methods, data_type, analysis_type
            )
            
            # Create step-by-step guide
            step_guide = await self._create_analysis_guide(
                statistical_methods, software_recommendations[0] if software_recommendations else "R"
            )
            
            # Generate interpretation guidelines
            interpretation = await self._generate_interpretation_guidelines(
                analysis_type, statistical_methods
            )
            
            # Identify common pitfalls
            pitfalls = await self._identify_analysis_pitfalls(
                analysis_type, data_type, sample_size
            )
            
            # Suggest validation methods
            validation_methods = await self._suggest_validation_methods(
                analysis_type, statistical_methods
            )
            
            # Provide reporting standards
            reporting_standards = await self._get_reporting_standards(
                analysis_type, statistical_methods
            )
            
            return DataAnalysisGuidance(
                analysis_type=analysis_type,
                statistical_methods=statistical_methods,
                software_recommendations=software_recommendations,
                step_by_step_guide=step_guide,
                interpretation_guidelines=interpretation,
                common_pitfalls=pitfalls,
                validation_methods=validation_methods,
                reporting_standards=reporting_standards
            )
            
        except Exception as e:
            logger.error(f"Error providing data analysis guidance: {str(e)}")
            raise    
# Helper methods for document analysis and content generation
    
    async def _get_relevant_documents(
        self,
        topic: str,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Document]:
        """Get documents relevant to the research topic"""
        try:
            query = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.status == "completed"
            )
            
            if document_ids:
                query = query.filter(Document.id.in_(document_ids))
            else:
                # Search by topic in document name and content
                query = query.filter(
                    Document.name.contains(topic)
                )
            
            documents = query.limit(limit).all()
            
            # If no direct matches, try semantic search through chunks
            if not documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.content.contains(topic)
                ).limit(limit).all()
                
                doc_ids = list(set([chunk.document_id for chunk in chunks]))
                documents = self.db.query(Document).filter(
                    Document.id.in_(doc_ids),
                    Document.user_id == user_id
                ).all()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting relevant documents: {str(e)}")
            return []

    async def _extract_research_themes(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract key research themes from documents"""
        try:
            # Use topic modeling to identify themes
            if documents:
                doc_ids = [doc.id for doc in documents]
                topic_result = await self.topic_service.analyze_document_topics(
                    document_ids=doc_ids,
                    n_topics=min(10, len(documents)),
                    update_tags=False
                )
                
                themes = []
                for topic in topic_result.topics:
                    themes.append({
                        "name": topic.name,
                        "keywords": topic.keywords,
                        "weight": topic.weight,
                        "description": topic.description,
                        "document_count": topic.document_count
                    })
                
                return themes
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting research themes: {str(e)}")
            return []

    async def _extract_key_findings(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract key findings from research documents"""
        try:
            findings = []
            
            # Keywords that often indicate findings
            finding_keywords = [
                "found that", "results show", "demonstrated", "revealed",
                "concluded", "evidence suggests", "indicates", "significant"
            ]
            
            for doc in documents:
                # Get document chunks
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                for chunk in chunks:
                    content = chunk.content.lower()
                    
                    # Look for sentences with finding keywords
                    sentences = content.split('.')
                    for sentence in sentences:
                        for keyword in finding_keywords:
                            if keyword in sentence and len(sentence.strip()) > 50:
                                findings.append({
                                    "text": sentence.strip(),
                                    "document": doc.name,
                                    "document_id": doc.id,
                                    "confidence": 0.7  # Basic confidence score
                                })
                                break
            
            # Sort by confidence and remove duplicates
            unique_findings = []
            seen_texts = set()
            
            for finding in sorted(findings, key=lambda x: x["confidence"], reverse=True):
                if finding["text"] not in seen_texts:
                    unique_findings.append(finding)
                    seen_texts.add(finding["text"])
            
            return unique_findings[:20]  # Return top 20 findings
            
        except Exception as e:
            logger.error(f"Error extracting key findings: {str(e)}")
            return []

    async def _identify_methodologies(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Identify research methodologies used in documents"""
        try:
            methodologies = []
            
            # Common methodology keywords
            method_keywords = {
                "survey": ["survey", "questionnaire", "poll"],
                "experiment": ["experiment", "experimental", "control group", "randomized"],
                "case_study": ["case study", "case analysis"],
                "interview": ["interview", "qualitative interview", "semi-structured"],
                "observation": ["observation", "ethnography", "field study"],
                "meta_analysis": ["meta-analysis", "systematic review"],
                "statistical": ["regression", "anova", "correlation", "statistical analysis"]
            }
            
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                doc_content = " ".join([chunk.content.lower() for chunk in chunks])
                
                for method_type, keywords in method_keywords.items():
                    for keyword in keywords:
                        if keyword in doc_content:
                            methodologies.append({
                                "type": method_type,
                                "keyword": keyword,
                                "document": doc.name,
                                "document_id": doc.id
                            })
                            break
            
            # Count methodology frequency
            method_counts = {}
            for method in methodologies:
                method_type = method["type"]
                if method_type not in method_counts:
                    method_counts[method_type] = {
                        "count": 0,
                        "documents": [],
                        "keywords": []
                    }
                method_counts[method_type]["count"] += 1
                method_counts[method_type]["documents"].append(method["document"])
                method_counts[method_type]["keywords"].append(method["keyword"])
            
            # Convert to list format
            result = []
            for method_type, data in method_counts.items():
                result.append({
                    "methodology": method_type,
                    "frequency": data["count"],
                    "documents": list(set(data["documents"])),
                    "keywords": list(set(data["keywords"]))
                })
            
            return sorted(result, key=lambda x: x["frequency"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error identifying methodologies: {str(e)}")
            return []

    async def _identify_research_gaps(
        self,
        documents: List[Document],
        themes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify potential research gaps"""
        try:
            gaps = []
            
            # Gap indicator phrases
            gap_indicators = [
                "further research", "future work", "limitation", "not addressed",
                "remains unclear", "needs investigation", "unexplored", "gap in"
            ]
            
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                for chunk in chunks:
                    content = chunk.content.lower()
                    sentences = content.split('.')
                    
                    for sentence in sentences:
                        for indicator in gap_indicators:
                            if indicator in sentence and len(sentence.strip()) > 30:
                                gaps.append({
                                    "description": sentence.strip(),
                                    "document": doc.name,
                                    "document_id": doc.id,
                                    "indicator": indicator,
                                    "confidence": 0.6
                                })
                                break
            
            # Add thematic gaps (areas with few documents)
            if themes:
                total_docs = len(documents)
                for theme in themes:
                    if theme["document_count"] < total_docs * 0.2:  # Less than 20% coverage
                        gaps.append({
                            "description": f"Limited research on {theme['name']} - only {theme['document_count']} documents address this theme",
                            "document": "thematic_analysis",
                            "document_id": None,
                            "indicator": "low_coverage",
                            "confidence": 0.8,
                            "theme": theme["name"]
                        })
            
            return gaps[:10]  # Return top 10 gaps
            
        except Exception as e:
            logger.error(f"Error identifying research gaps: {str(e)}")
            return []

    async def _generate_introduction_section(
        self,
        topic: str,
        themes: List[Dict[str, Any]],
        doc_count: int
    ) -> LiteratureReviewSection:
        """Generate introduction section for literature review"""
        
        content = f"""
        This literature review examines the current state of research on {topic}. 
        Based on an analysis of {doc_count} relevant documents, this review identifies 
        key themes, methodological approaches, and research gaps in the field.
        
        The analysis reveals {len(themes)} major research themes, including:
        {', '.join([theme['name'] for theme in themes[:5]])}.
        
        This review aims to synthesize current knowledge, identify methodological 
        trends, and highlight areas requiring further investigation.
        """
        
        return LiteratureReviewSection(
            title="Introduction",
            content=content.strip(),
            citations=[],
            key_findings=[],
            gaps_identified=[],
            section_type="introduction"
        )

    async def _track_research_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Track research assistant analytics events"""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking research event: {str(e)}")

    # Additional helper methods would continue here...
    # For brevity, I'll implement the core structure and key methods

    async def _generate_expected_outcomes(self, topic: ResearchTopic) -> List[str]:
        """Generate expected research outcomes"""
        outcomes = [
            f"Enhanced understanding of {topic.keywords[0]} in {topic.domain}",
            f"Empirical evidence addressing {topic.research_questions[0] if topic.research_questions else 'key research questions'}",
            "Theoretical contributions to the field",
            "Practical implications for practitioners",
            "Recommendations for future research"
        ]
        
        # Add topic-specific outcomes
        if "technology" in topic.domain.lower():
            outcomes.append("Technical innovations or improvements")
        
        if "education" in topic.domain.lower():
            outcomes.append("Educational practice improvements")
        
        return outcomes

    async def _identify_research_limitations(self, topic: ResearchTopic, methodology: Dict[str, Any]) -> List[str]:
        """Identify potential research limitations"""
        limitations = []
        
        # Sample limitations
        limitations.append("Sample size may limit generalizability of findings")
        limitations.append("Cross-sectional design limits causal inferences")
        
        # Methodology-specific limitations
        approach = methodology.get("approach", "")
        if "qualitative" in approach:
            limitations.extend([
                "Findings may not be generalizable to broader populations",
                "Researcher bias may influence data interpretation"
            ])
        
        if "quantitative" in approach:
            limitations.extend([
                "May not capture contextual nuances",
                "Measurement instruments may have limitations"
            ])
        
        # Domain-specific limitations
        if "technology" in topic.domain.lower():
            limitations.append("Rapid technological changes may affect relevance")
        
        # Resource limitations
        limitations.extend([
            "Time constraints may limit depth of investigation",
            "Budget constraints may affect sample size or scope"
        ])
        
        return limitations[:7]  # Limit to 7 limitations

    async def _generate_ethical_considerations(self, topic: ResearchTopic) -> str:
        """Generate ethical considerations section"""
        considerations = []
        
        considerations.append(
            "This research will be conducted in accordance with institutional ethical guidelines "
            "and relevant professional standards."
        )
        
        considerations.append(
            "Informed consent will be obtained from all participants, clearly explaining the "
            "purpose, procedures, risks, and benefits of the research."
        )
        
        considerations.append(
            "Participant confidentiality and anonymity will be maintained throughout the study. "
            "All data will be stored securely and accessed only by authorized research personnel."
        )
        
        considerations.append(
            "Participants will have the right to withdraw from the study at any time without "
            "penalty or loss of benefits."
        )
        
        # Domain-specific considerations
        if "medicine" in topic.domain.lower() or "health" in topic.domain.lower():
            considerations.append(
                "Additional medical ethics protocols will be followed, including potential "
                "risks to participant health and wellbeing."
            )
        
        if "education" in topic.domain.lower():
            considerations.append(
                "Special consideration will be given to vulnerable populations, particularly "
                "if minors are involved in the research."
            )
        
        considerations.append(
            "The research will undergo institutional review board (IRB) approval before "
            "data collection begins."
        )
        
        return " ".join(considerations)

    async def _generate_hypotheses(self, topic: ResearchTopic) -> List[str]:
        """Generate research hypotheses"""
        hypotheses = []
        
        if topic.research_questions:
            for question in topic.research_questions[:3]:  # Max 3 hypotheses
                # Convert question to hypothesis format
                if question.lower().startswith("how"):
                    hypothesis = f"There is a significant relationship between {topic.keywords[0]} and {topic.keywords[1] if len(topic.keywords) > 1 else 'related factors'}"
                elif question.lower().startswith("what"):
                    hypothesis = f"{topic.keywords[0].title()} significantly influences outcomes in {topic.domain}"
                elif question.lower().startswith("why"):
                    hypothesis = f"The observed effects of {topic.keywords[0]} can be explained by underlying mechanisms"
                else:
                    hypothesis = f"There are measurable effects of {topic.keywords[0]} in the context of {topic.domain}"
                
                hypotheses.append(hypothesis)
        
        # Add null hypotheses
        if hypotheses:
            null_hypothesis = f"There is no significant relationship between {topic.keywords[0]} and the measured outcomes"
            hypotheses.append(f"Null hypothesis: {null_hypothesis}")
        
        return hypotheses

    async def _classify_research_question(self, research_question: str) -> str:
        """Classify research question type"""
        question_lower = research_question.lower()
        
        if any(word in question_lower for word in ["how many", "what percentage", "measure", "quantify"]):
            return "quantitative_descriptive"
        elif any(word in question_lower for word in ["compare", "difference", "versus", "between"]):
            return "comparative"
        elif any(word in question_lower for word in ["cause", "effect", "influence", "impact"]):
            return "causal"
        elif any(word in question_lower for word in ["relationship", "association", "correlation"]):
            return "relational"
        elif any(word in question_lower for word in ["how", "why", "experience", "meaning"]):
            return "qualitative_exploratory"
        else:
            return "exploratory"

# Additional service classes for Phase 2

class LiteratureSearchService:
    """Service for literature search and analysis"""
    
    def __init__(self, db: Session):
        self.db = db
        self.research_assistant = ResearchAssistant(db)
    
    async def search_literature(
        self,
        user_id: str,
        query: str,
        databases: List[str] = None,
        date_range: Dict[str, int] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """Search literature based on query"""
        try:
            # Search user's document collection
            relevant_docs = await self._search_user_documents(user_id, query, max_results)
            
            # Analyze search results
            analysis = await self._analyze_search_results(relevant_docs, query)
            
            # Generate search insights
            insights = await self._generate_search_insights(analysis, query)
            
            return {
                "query": query,
                "results": relevant_docs,
                "analysis": analysis,
                "insights": insights,
                "total_results": len(relevant_docs),
                "search_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in literature search: {str(e)}")
            raise
    
    async def _search_user_documents(self, user_id: str, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search user's documents for relevant literature"""
        # Extract search terms
        search_terms = query.lower().split()
        
        # Search documents
        documents = []
        for term in search_terms[:5]:  # Use top 5 terms
            docs = self.db.query(Document).join(DocumentChunk).filter(
                Document.user_id == user_id,
                Document.status == "completed",
                or_(
                    Document.name.contains(term),
                    DocumentChunk.content.contains(term)
                )
            ).distinct().limit(max_results // len(search_terms[:5])).all()
            
            for doc in docs:
                doc_data = {
                    "id": doc.id,
                    "title": doc.name,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "size": doc.size,
                    "content_type": doc.content_type,
                    "relevance_score": 0.8,  # Would be calculated based on term matching
                    "search_term": term
                }
                documents.append(doc_data)
        
        # Remove duplicates and sort by relevance
        unique_docs = list({doc["id"]: doc for doc in documents}.values())
        return sorted(unique_docs, key=lambda x: x["relevance_score"], reverse=True)[:max_results]
    
    async def _analyze_search_results(self, documents: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Analyze search results for patterns and insights"""
        if not documents:
            return {"message": "No documents found"}
        
        # Analyze document types
        content_types = Counter([doc["content_type"] for doc in documents])
        
        # Analyze temporal distribution
        years = []
        for doc in documents:
            if doc["created_at"]:
                try:
                    year = datetime.fromisoformat(doc["created_at"]).year
                    years.append(year)
                except:
                    pass
        
        year_distribution = Counter(years) if years else {}
        
        # Calculate average relevance
        avg_relevance = sum(doc["relevance_score"] for doc in documents) / len(documents)
        
        return {
            "total_documents": len(documents),
            "content_type_distribution": dict(content_types),
            "year_distribution": dict(year_distribution),
            "average_relevance": avg_relevance,
            "date_range": {
                "earliest": min(years) if years else None,
                "latest": max(years) if years else None
            }
        }
    
    async def _generate_search_insights(self, analysis: Dict[str, Any], query: str) -> List[str]:
        """Generate insights from search analysis"""
        insights = []
        
        total_docs = analysis.get("total_documents", 0)
        if total_docs == 0:
            return ["No relevant documents found in your collection"]
        
        insights.append(f"Found {total_docs} relevant documents in your collection")
        
        # Content type insights
        content_types = analysis.get("content_type_distribution", {})
        if content_types:
            most_common_type = max(content_types.items(), key=lambda x: x[1])
            insights.append(f"Most common document type: {most_common_type[0]} ({most_common_type[1]} documents)")
        
        # Temporal insights
        year_dist = analysis.get("year_distribution", {})
        if year_dist:
            recent_years = [year for year in year_dist.keys() if year >= datetime.now().year - 3]
            recent_count = sum(year_dist[year] for year in recent_years)
            insights.append(f"{recent_count} documents from the last 3 years")
        
        # Relevance insights
        avg_relevance = analysis.get("average_relevance", 0)
        if avg_relevance > 0.7:
            insights.append("High relevance match - documents closely align with your query")
        elif avg_relevance > 0.5:
            insights.append("Moderate relevance match - some documents may be tangentially related")
        else:
            insights.append("Lower relevance match - consider refining your search terms")
        
        return insights

class ResearchProposalGenerator:
    """Service for generating research proposals"""
    
    def __init__(self, db: Session):
        self.db = db
        self.research_assistant = ResearchAssistant(db)
    
    async def generate_proposal_outline(
        self,
        user_id: str,
        topic: str,
        research_questions: List[str],
        methodology_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a research proposal outline"""
        try:
            # Create research topic
            research_topic = await self._create_research_topic(topic, research_questions)
            
            # Generate literature review
            literature_review = await self.research_assistant.generate_literature_review(
                user_id, topic, research_questions, max_sources=20
            )
            
            # Generate methodology recommendations
            methodology_recs = await self.research_assistant.suggest_methodology(
                research_questions, research_topic.domain, "available", 12, ["basic_resources"]
            )
            
            # Select methodology
            selected_methodology = None
            if methodology_preference:
                selected_methodology = ResearchMethodology(methodology_preference)
            elif methodology_recs:
                selected_methodology = methodology_recs[0].methodology
            
            # Generate full proposal
            proposal = await self.research_assistant.generate_research_proposal(
                user_id, research_topic, literature_review, selected_methodology
            )
            
            return {
                "proposal": proposal,
                "literature_review": literature_review,
                "methodology_recommendations": methodology_recs,
                "research_topic": research_topic
            }
            
        except Exception as e:
            logger.error(f"Error generating proposal outline: {str(e)}")
            raise
    
    async def _create_research_topic(self, topic: str, research_questions: List[str]) -> ResearchTopic:
        """Create a research topic from basic information"""
        # Extract keywords from topic and questions
        text = f"{topic} {' '.join(research_questions)}"
        keywords = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        keywords = list(set(keywords))[:10]  # Top 10 unique keywords
        
        # Infer domain
        domain = self._infer_domain_from_text(text)
        
        return ResearchTopic(
            id=str(uuid.uuid4()),
            title=topic,
            description=f"Research investigating {topic} and related factors",
            keywords=keywords,
            domain=domain,
            research_questions=research_questions,
            significance=f"This research contributes to understanding of {topic}",
            novelty_score=0.7,
            feasibility_score=0.8,
            impact_potential=0.6,
            related_topics=keywords[:5],
            suggested_methodologies=[ResearchMethodology.MIXED_METHODS, ResearchMethodology.QUANTITATIVE],
            estimated_timeline={"literature_review": 2, "methodology": 1, "data_collection": 4, "analysis": 2, "writing": 3},
            resources_needed=["literature access", "data collection tools", "analysis software"]
        )
    
    def _infer_domain_from_text(self, text: str) -> str:
        """Infer research domain from text"""
        text_lower = text.lower()
        
        domain_keywords = {
            "Computer Science": ["algorithm", "software", "programming", "artificial intelligence", "machine learning", "data"],
            "Medicine": ["health", "medical", "clinical", "patient", "treatment", "diagnosis", "therapy"],
            "Psychology": ["behavior", "cognitive", "mental", "psychological", "emotion", "personality"],
            "Education": ["learning", "teaching", "student", "curriculum", "pedagogy", "educational"],
            "Business": ["management", "marketing", "finance", "organization", "strategy", "business"],
            "Engineering": ["design", "system", "technical", "engineering", "construction", "mechanical"],
            "Social Sciences": ["social", "society", "culture", "community", "policy", "sociology"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return domain
        
        return "Interdisciplinary"

class MethodologyAdvisor:
    """Service for providing methodology advice"""
    
    def __init__(self, db: Session):
        self.db = db
        self.research_assistant = ResearchAssistant(db)
    
    async def get_methodology_advice(
        self,
        research_questions: List[str],
        domain: str,
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get comprehensive methodology advice"""
        try:
            # Analyze research questions
            question_analysis = await self.research_assistant._analyze_research_questions(research_questions)
            
            # Get methodology recommendations
            recommendations = await self.research_assistant.suggest_methodology(
                research_questions,
                domain,
                constraints.get("data_availability", "available"),
                constraints.get("timeline_months", 12),
                constraints.get("resources", ["basic_resources"])
            )
            
            # Generate detailed advice
            advice = await self._generate_detailed_advice(
                question_analysis, recommendations, constraints
            )
            
            return {
                "question_analysis": question_analysis,
                "recommendations": recommendations,
                "detailed_advice": advice,
                "constraints_considered": constraints
            }
            
        except Exception as e:
            logger.error(f"Error getting methodology advice: {str(e)}")
            raise
    
    async def _generate_detailed_advice(
        self,
        question_analysis: Dict[str, Any],
        recommendations: List[MethodologyRecommendation],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed methodology advice"""
        advice = {
            "overview": "",
            "top_recommendation": None,
            "considerations": [],
            "next_steps": [],
            "resources_needed": [],
            "timeline_guidance": {}
        }
        
        if not recommendations:
            advice["overview"] = "No suitable methodologies found for the given constraints."
            return advice
        
        top_rec = recommendations[0]
        advice["top_recommendation"] = {
            "methodology": top_rec.methodology.value,
            "rationale": top_rec.rationale,
            "suitability_score": top_rec.suitability_score
        }
        
        advice["overview"] = (
            f"Based on your research questions and constraints, {top_rec.methodology.value} "
            f"methodology is recommended with a suitability score of {top_rec.suitability_score:.2f}. "
            f"{top_rec.rationale}"
        )
        
        # Generate considerations
        advice["considerations"] = [
            f"Advantages: {', '.join(top_rec.advantages)}",
            f"Disadvantages: {', '.join(top_rec.disadvantages)}",
            f"Complexity level: {top_rec.complexity_level}",
            f"Estimated duration: {top_rec.estimated_duration} months"
        ]
        
        # Generate next steps
        advice["next_steps"] = [
            "Refine research questions based on methodology selection",
            "Develop detailed research design",
            "Identify and prepare data collection instruments",
            "Plan participant recruitment strategy",
            "Prepare ethics approval application"
        ]
        
        # Resources needed
        advice["resources_needed"] = top_rec.requirements + top_rec.tools_recommended
        
        # Timeline guidance
        advice["timeline_guidance"] = {
            "preparation": "1-2 months",
            "data_collection": f"{top_rec.estimated_duration // 2} months",
            "analysis": f"{top_rec.estimated_duration // 3} months",
            "writing": "2-3 months"
        }
        
        return advice

# Export the services
__all__ = [
    'ResearchAssistant',
    'LiteratureSearchService', 
    'ResearchProposalGenerator',
    'MethodologyAdvisor',
    'ResearchTopic',
    'LiteratureReview',
    'ResearchProposal',
    'MethodologyRecommendation',
    'DataAnalysisGuidance',
    'ResearchPhase',
    'ResearchMethodology',
    'DataAnalysisMethod'
]