#!/usr/bin/env python3
"""
Domain-Specific RAG Specialization
Implements specialized RAG systems for different domains
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
from datetime import datetime

class Domain(Enum):
    ACADEMIC = "academic"
    MEDICAL = "medical"
    LEGAL = "legal"
    BUSINESS = "business"
    TECHNICAL = "technical"
    SCIENTIFIC = "scientific"

@dataclass
class DomainContext:
    domain: Domain
    specialized_vocabulary: List[str]
    citation_format: str
    authority_sources: List[str]
    quality_metrics: Dict[str, float]
    processing_rules: Dict[str, any]

class DomainSpecificRAG(ABC):
    """Abstract base class for domain-specific RAG implementations"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.context = self._initialize_domain_context()
        
    @abstractmethod
    def _initialize_domain_context(self) -> DomainContext:
        """Initialize domain-specific context"""
        pass
    
    @abstractmethod
    def preprocess_document(self, document: str, metadata: Dict) -> Dict:
        """Domain-specific document preprocessing"""
        pass
    
    @abstractmethod
    def extract_domain_entities(self, text: str) -> List[Dict]:
        """Extract domain-specific entities"""
        pass
    
    @abstractmethod
    def calculate_authority_score(self, document: Dict) -> float:
        """Calculate authority/credibility score for domain"""
        pass
    
    @abstractmethod
    def format_response(self, response: str, sources: List[Dict]) -> str:
        """Format response according to domain conventions"""
        pass

class AcademicRAG(DomainSpecificRAG):
    """RAG system specialized for academic research"""
    
    def _initialize_domain_context(self) -> DomainContext:
        return DomainContext(
            domain=Domain.ACADEMIC,
            specialized_vocabulary=[
                'hypothesis', 'methodology', 'literature review', 'peer review',
                'statistical significance', 'correlation', 'causation', 'meta-analysis',
                'empirical', 'theoretical framework', 'research question', 'variables'
            ],
            citation_format='apa',
            authority_sources=[
                'pubmed', 'arxiv', 'google scholar', 'jstor', 'ieee', 'acm',
                'springer', 'elsevier', 'wiley', 'nature', 'science'
            ],
            quality_metrics={
                'peer_reviewed': 1.0,
                'citation_count': 0.8,
                'journal_impact_factor': 0.9,
                'author_h_index': 0.7,
                'recency': 0.6
            },
            processing_rules={
                'extract_citations': True,
                'identify_methodology': True,
                'extract_findings': True,
                'validate_claims': True
            }
        )
    
    def preprocess_document(self, document: str, metadata: Dict) -> Dict:
        """Academic document preprocessing"""
        processed = {
            'original_text': document,
            'metadata': metadata,
            'sections': self._extract_academic_sections(document),
            'citations': self._extract_citations(document),
            'methodology': self._extract_methodology(document),
            'findings': self._extract_findings(document),
            'keywords': self._extract_academic_keywords(document)
        }
        
        # Calculate academic quality score
        processed['quality_score'] = self._calculate_academic_quality(processed, metadata)
        
        return processed
    
    def _extract_academic_sections(self, document: str) -> Dict[str, str]:
        """Extract standard academic paper sections"""
        sections = {}
        
        # Common academic section patterns
        section_patterns = {
            'abstract': r'(?i)abstract\s*:?\s*(.*?)(?=\n\s*(?:introduction|keywords|1\.|background))',
            'introduction': r'(?i)(?:introduction|1\.?\s*introduction)\s*:?\s*(.*?)(?=\n\s*(?:2\.|methodology|methods|literature))',
            'methodology': r'(?i)(?:methodology|methods|2\.?\s*method)\s*:?\s*(.*?)(?=\n\s*(?:3\.|results|findings))',
            'results': r'(?i)(?:results|findings|3\.?\s*results)\s*:?\s*(.*?)(?=\n\s*(?:4\.|discussion|conclusion))',
            'discussion': r'(?i)(?:discussion|4\.?\s*discussion)\s*:?\s*(.*?)(?=\n\s*(?:5\.|conclusion|references))',
            'conclusion': r'(?i)(?:conclusion|5\.?\s*conclusion)\s*:?\s*(.*?)(?=\n\s*(?:references|bibliography))'
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, document, re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()
        
        return sections
    
    def _extract_citations(self, document: str) -> List[Dict]:
        """Extract academic citations"""
        citations = []
        
        # APA style citations
        apa_pattern = r'([A-Z][a-z]+(?:,\s*[A-Z]\.)*)\s*\((\d{4})\)\.\s*([^.]+)\.\s*([^.]+)\.'
        
        for match in re.finditer(apa_pattern, document):
            citations.append({
                'authors': match.group(1),
                'year': match.group(2),
                'title': match.group(3),
                'publication': match.group(4),
                'format': 'apa'
            })
        
        # DOI patterns
        doi_pattern = r'doi:\s*(10\.\d+/[^\s]+)'
        for match in re.finditer(doi_pattern, document):
            citations.append({
                'doi': match.group(1),
                'type': 'doi_reference'
            })
        
        return citations
    
    def _extract_methodology(self, document: str) -> Dict:
        """Extract methodology information"""
        methodology = {}
        
        # Look for methodology keywords
        method_keywords = {
            'quantitative': r'(?i)\b(quantitative|statistical|numerical|survey|experiment)\b',
            'qualitative': r'(?i)\b(qualitative|interview|ethnographic|case study)\b',
            'mixed_methods': r'(?i)\b(mixed methods|triangulation)\b',
            'sample_size': r'(?i)(?:sample size|n\s*=\s*(\d+)|participants?\s*\(n\s*=\s*(\d+)\))',
            'data_collection': r'(?i)\b(data collection|questionnaire|survey|interview)\b'
        }
        
        for method_type, pattern in method_keywords.items():
            if re.search(pattern, document):
                methodology[method_type] = True
                
                # Extract specific values for sample size
                if method_type == 'sample_size':
                    match = re.search(pattern, document)
                    if match:
                        methodology['sample_size_value'] = match.group(1) or match.group(2)
        
        return methodology
    
    def _extract_findings(self, document: str) -> List[str]:
        """Extract key findings from academic text"""
        findings = []
        
        # Look for findings indicators
        finding_patterns = [
            r'(?i)(?:we found|results show|findings indicate|analysis reveals)\s+([^.]+)',
            r'(?i)(?:significant|correlation|association)\s+([^.]+)',
            r'(?i)(?:p\s*<\s*0\.05|statistically significant)\s*([^.]*)'
        ]
        
        for pattern in finding_patterns:
            matches = re.findall(pattern, document)
            findings.extend(matches)
        
        return findings[:5]  # Limit to top 5 findings
    
    def _extract_academic_keywords(self, document: str) -> List[str]:
        """Extract academic keywords"""
        # Look for explicit keywords section
        keywords_match = re.search(r'(?i)keywords?\s*:?\s*([^\n]+)', document)
        if keywords_match:
            keywords_text = keywords_match.group(1)
            return [kw.strip() for kw in re.split(r'[,;]', keywords_text)]
        
        # Extract from specialized vocabulary
        keywords = []
        doc_lower = document.lower()
        for term in self.context.specialized_vocabulary:
            if term in doc_lower:
                keywords.append(term)
        
        return keywords
    
    def _calculate_academic_quality(self, processed_doc: Dict, metadata: Dict) -> float:
        """Calculate academic quality score"""
        score = 0.5  # Base score
        
        # Peer review bonus
        if metadata.get('peer_reviewed', False):
            score += 0.3
        
        # Citation count bonus
        citation_count = metadata.get('citation_count', 0)
        if citation_count > 100:
            score += 0.2
        elif citation_count > 10:
            score += 0.1
        
        # Journal impact factor
        impact_factor = metadata.get('impact_factor', 0)
        if impact_factor > 5:
            score += 0.2
        elif impact_factor > 2:
            score += 0.1
        
        # Methodology presence
        if processed_doc.get('methodology'):
            score += 0.1
        
        # Citations presence
        if processed_doc.get('citations'):
            score += 0.1
        
        return min(score, 1.0)
    
    def extract_domain_entities(self, text: str) -> List[Dict]:
        """Extract academic entities"""
        entities = []
        
        # Research methods
        method_pattern = r'(?i)\b(randomized controlled trial|meta-analysis|systematic review|case study|cohort study)\b'
        for match in re.finditer(method_pattern, text):
            entities.append({
                'text': match.group(0),
                'type': 'research_method',
                'start': match.start(),
                'end': match.end()
            })
        
        # Statistical terms
        stats_pattern = r'(?i)\b(p-value|confidence interval|standard deviation|correlation coefficient)\b'
        for match in re.finditer(stats_pattern, text):
            entities.append({
                'text': match.group(0),
                'type': 'statistical_term',
                'start': match.start(),
                'end': match.end()
            })
        
        # Academic institutions
        institution_pattern = r'\b([A-Z][a-z]+ University|[A-Z][a-z]+ Institute|[A-Z][a-z]+ College)\b'
        for match in re.finditer(institution_pattern, text):
            entities.append({
                'text': match.group(0),
                'type': 'institution',
                'start': match.start(),
                'end': match.end()
            })
        
        return entities
    
    def calculate_authority_score(self, document: Dict) -> float:
        """Calculate authority score for academic document"""
        score = 0.0
        metadata = document.get('metadata', {})
        
        # Journal ranking
        journal = metadata.get('journal', '').lower()
        if any(top_journal in journal for top_journal in ['nature', 'science', 'cell']):
            score += 0.4
        elif any(good_journal in journal for good_journal in ['plos', 'ieee', 'acm']):
            score += 0.3
        
        # Author credentials
        author_h_index = metadata.get('author_h_index', 0)
        if author_h_index > 50:
            score += 0.3
        elif author_h_index > 20:
            score += 0.2
        elif author_h_index > 10:
            score += 0.1
        
        # Citation metrics
        citation_count = metadata.get('citation_count', 0)
        if citation_count > 1000:
            score += 0.2
        elif citation_count > 100:
            score += 0.15
        elif citation_count > 10:
            score += 0.1
        
        # Recency (academic work can be valuable even if older)
        years_old = metadata.get('years_since_publication', 0)
        if years_old < 2:
            score += 0.1
        elif years_old < 5:
            score += 0.05
        
        return min(score, 1.0)
    
    def format_response(self, response: str, sources: List[Dict]) -> str:
        """Format academic response with proper citations"""
        formatted_response = response
        
        # Add citations
        if sources:
            formatted_response += "\n\n**References:**\n"
            for i, source in enumerate(sources, 1):
                citation = self._format_academic_citation(source, i)
                formatted_response += f"{i}. {citation}\n"
        
        # Add methodology note if relevant
        if any('methodology' in source.get('metadata', {}) for source in sources):
            formatted_response += "\n*Note: This response is based on peer-reviewed research with documented methodologies.*"
        
        return formatted_response
    
    def _format_academic_citation(self, source: Dict, number: int) -> str:
        """Format citation in academic style"""
        metadata = source.get('metadata', {})
        
        # Try to construct APA citation
        authors = metadata.get('authors', 'Unknown Author')
        year = metadata.get('year', 'n.d.')
        title = metadata.get('title', 'Untitled')
        journal = metadata.get('journal', '')
        
        citation = f"{authors} ({year}). {title}."
        if journal:
            citation += f" *{journal}*."
        
        # Add DOI if available
        doi = metadata.get('doi')
        if doi:
            citation += f" https://doi.org/{doi}"
        
        return citation

class MedicalRAG(DomainSpecificRAG):
    """RAG system specialized for medical information"""
    
    def _initialize_domain_context(self) -> DomainContext:
        return DomainContext(
            domain=Domain.MEDICAL,
            specialized_vocabulary=[
                'diagnosis', 'treatment', 'symptoms', 'prognosis', 'etiology',
                'pathophysiology', 'clinical trial', 'adverse effects', 'contraindications',
                'dosage', 'pharmacokinetics', 'comorbidity', 'differential diagnosis'
            ],
            citation_format='vancouver',
            authority_sources=[
                'pubmed', 'cochrane', 'uptodate', 'medline', 'nejm', 'jama',
                'bmj', 'lancet', 'who', 'cdc', 'fda', 'ema'
            ],
            quality_metrics={
                'clinical_trial': 1.0,
                'systematic_review': 0.95,
                'peer_reviewed': 0.9,
                'regulatory_approval': 0.85,
                'expert_consensus': 0.8
            },
            processing_rules={
                'extract_medical_entities': True,
                'identify_contraindications': True,
                'extract_dosage_info': True,
                'validate_medical_claims': True,
                'add_disclaimers': True
            }
        )
    
    def preprocess_document(self, document: str, metadata: Dict) -> Dict:
        """Medical document preprocessing"""
        processed = {
            'original_text': document,
            'metadata': metadata,
            'medical_entities': self._extract_medical_entities(document),
            'drug_information': self._extract_drug_info(document),
            'clinical_data': self._extract_clinical_data(document),
            'contraindications': self._extract_contraindications(document),
            'evidence_level': self._determine_evidence_level(document, metadata)
        }
        
        processed['authority_score'] = self.calculate_authority_score({'metadata': metadata})
        
        return processed
    
    def _extract_medical_entities(self, document: str) -> List[Dict]:
        """Extract medical entities like diseases, drugs, procedures"""
        entities = []
        
        # Disease patterns
        disease_pattern = r'\b([A-Z][a-z]+(?:\s+[a-z]+)*(?:\s+(?:disease|syndrome|disorder|condition)))\b'
        for match in re.finditer(disease_pattern, document):
            entities.append({
                'text': match.group(0),
                'type': 'disease',
                'start': match.start(),
                'end': match.end()
            })
        
        # Drug patterns
        drug_pattern = r'\b([A-Z][a-z]+(?:ine|ol|an|ide|ate|um))\b'
        for match in re.finditer(drug_pattern, document):
            entities.append({
                'text': match.group(0),
                'type': 'drug',
                'start': match.start(),
                'end': match.end()
            })
        
        return entities
    
    def _extract_drug_info(self, document: str) -> Dict:
        """Extract drug dosage and administration information"""
        drug_info = {}
        
        # Dosage patterns
        dosage_pattern = r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|units?)\s*(?:per\s+day|daily|bid|tid|qid)?'
        dosages = re.findall(dosage_pattern, document, re.IGNORECASE)
        if dosages:
            drug_info['dosages'] = [f"{dose} {unit}" for dose, unit in dosages]
        
        # Administration routes
        route_pattern = r'(?i)\b(oral|intravenous|intramuscular|subcutaneous|topical|inhalation)\b'
        routes = re.findall(route_pattern, document)
        if routes:
            drug_info['administration_routes'] = list(set(routes))
        
        return drug_info
    
    def _extract_clinical_data(self, document: str) -> Dict:
        """Extract clinical trial and study data"""
        clinical_data = {}
        
        # Sample size
        sample_pattern = r'(?i)(?:n\s*=\s*(\d+)|(\d+)\s+patients?|(\d+)\s+subjects?)'
        sample_match = re.search(sample_pattern, document)
        if sample_match:
            clinical_data['sample_size'] = sample_match.group(1) or sample_match.group(2) or sample_match.group(3)
        
        # Study type
        study_types = ['randomized controlled trial', 'cohort study', 'case-control study', 'meta-analysis']
        for study_type in study_types:
            if study_type in document.lower():
                clinical_data['study_type'] = study_type
                break
        
        # Efficacy data
        efficacy_pattern = r'(?i)(?:efficacy|effectiveness)\s+(?:of\s+)?(\d+(?:\.\d+)?%)'
        efficacy_match = re.search(efficacy_pattern, document)
        if efficacy_match:
            clinical_data['efficacy'] = efficacy_match.group(1)
        
        return clinical_data
    
    def _extract_contraindications(self, document: str) -> List[str]:
        """Extract contraindications and warnings"""
        contraindications = []
        
        # Look for contraindication sections
        contra_pattern = r'(?i)(?:contraindication|warning|caution|adverse effect)s?\s*:?\s*([^.]+)'
        matches = re.findall(contra_pattern, document)
        contraindications.extend(matches)
        
        return contraindications
    
    def _determine_evidence_level(self, document: str, metadata: Dict) -> str:
        """Determine level of medical evidence"""
        doc_lower = document.lower()
        
        if 'systematic review' in doc_lower or 'meta-analysis' in doc_lower:
            return 'Level 1 (Systematic Review/Meta-analysis)'
        elif 'randomized controlled trial' in doc_lower:
            return 'Level 2 (Randomized Controlled Trial)'
        elif 'cohort study' in doc_lower:
            return 'Level 3 (Cohort Study)'
        elif 'case-control' in doc_lower:
            return 'Level 4 (Case-Control Study)'
        elif 'case report' in doc_lower:
            return 'Level 5 (Case Report)'
        else:
            return 'Level 6 (Expert Opinion)'
    
    def extract_domain_entities(self, text: str) -> List[Dict]:
        """Extract medical domain entities"""
        return self._extract_medical_entities(text)
    
    def calculate_authority_score(self, document: Dict) -> float:
        """Calculate authority score for medical document"""
        score = 0.0
        metadata = document.get('metadata', {})
        
        # Source authority
        source = metadata.get('source', '').lower()
        if any(top_source in source for top_source in ['nejm', 'jama', 'bmj', 'lancet']):
            score += 0.4
        elif any(good_source in source for good_source in ['pubmed', 'cochrane', 'uptodate']):
            score += 0.3
        
        # Study type
        study_type = metadata.get('study_type', '').lower()
        if 'systematic review' in study_type or 'meta-analysis' in study_type:
            score += 0.3
        elif 'randomized controlled trial' in study_type:
            score += 0.25
        elif 'cohort study' in study_type:
            score += 0.2
        
        # Regulatory approval
        if metadata.get('fda_approved', False) or metadata.get('ema_approved', False):
            score += 0.2
        
        # Peer review
        if metadata.get('peer_reviewed', False):
            score += 0.1
        
        return min(score, 1.0)
    
    def format_response(self, response: str, sources: List[Dict]) -> str:
        """Format medical response with disclaimers and citations"""
        # Add medical disclaimer
        disclaimer = "\n\n**Medical Disclaimer:** This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare provider for medical decisions."
        
        formatted_response = response + disclaimer
        
        # Add evidence-based citations
        if sources:
            formatted_response += "\n\n**Medical Evidence:**\n"
            for i, source in enumerate(sources, 1):
                evidence_level = source.get('evidence_level', 'Unknown')
                citation = self._format_medical_citation(source, i)
                formatted_response += f"{i}. {citation} (Evidence: {evidence_level})\n"
        
        return formatted_response
    
    def _format_medical_citation(self, source: Dict, number: int) -> str:
        """Format citation in Vancouver style (medical standard)"""
        metadata = source.get('metadata', {})
        
        authors = metadata.get('authors', 'Unknown')
        title = metadata.get('title', 'Untitled')
        journal = metadata.get('journal', '')
        year = metadata.get('year', '')
        volume = metadata.get('volume', '')
        pages = metadata.get('pages', '')
        
        # Vancouver format: Authors. Title. Journal. Year;Volume:Pages.
        citation = f"{authors}. {title}."
        if journal:
            citation += f" {journal}."
        if year:
            citation += f" {year}"
        if volume:
            citation += f";{volume}"
        if pages:
            citation += f":{pages}"
        citation += "."
        
        return citation

# Factory for creating domain-specific RAG systems
class DomainRAGFactory:
    """Factory for creating domain-specific RAG systems"""
    
    _rag_classes = {
        Domain.ACADEMIC: AcademicRAG,
        Domain.MEDICAL: MedicalRAG,
        # Add more domain classes as needed
    }
    
    @classmethod
    def create_rag(cls, domain: Domain) -> DomainSpecificRAG:
        """Create a domain-specific RAG system"""
        if domain not in cls._rag_classes:
            raise ValueError(f"Domain {domain} not supported")
        
        return cls._rag_classes[domain](domain)
    
    @classmethod
    def get_supported_domains(cls) -> List[Domain]:
        """Get list of supported domains"""
        return list(cls._rag_classes.keys())

# Usage example
def implement_domain_specialization():
    """Example implementation of domain-specific RAG"""
    
    # Create academic RAG
    academic_rag = DomainRAGFactory.create_rag(Domain.ACADEMIC)
    
    # Example academic document
    academic_doc = """
    Abstract: This study examines the effectiveness of machine learning algorithms in predicting student performance.
    
    Methodology: We conducted a randomized controlled trial with n=500 students across 10 universities.
    The study used quantitative analysis with statistical significance testing (p<0.05).
    
    Results: Our findings indicate a significant correlation between algorithm predictions and actual performance (r=0.85, p<0.001).
    
    References:
    Smith, J. (2023). Machine Learning in Education. Journal of Educational Technology, 15(3), 45-62.
    """
    
    academic_metadata = {
        'peer_reviewed': True,
        'journal': 'Journal of Educational Technology',
        'impact_factor': 3.2,
        'citation_count': 45,
        'year': 2023
    }
    
    # Process academic document
    processed_academic = academic_rag.preprocess_document(academic_doc, academic_metadata)
    academic_entities = academic_rag.extract_domain_entities(academic_doc)
    academic_authority = academic_rag.calculate_authority_score({'metadata': academic_metadata})
    
    # Create medical RAG
    medical_rag = DomainRAGFactory.create_rag(Domain.MEDICAL)
    
    # Example medical document
    medical_doc = """
    Clinical Trial Results: Aspirin 75mg daily showed significant reduction in cardiovascular events.
    
    Study Design: Randomized controlled trial with n=10,000 patients over 5 years.
    
    Results: 25% reduction in myocardial infarction (p<0.001).
    
    Contraindications: Active bleeding, severe liver disease.
    
    Adverse Effects: Gastrointestinal bleeding in 2% of patients.
    """
    
    medical_metadata = {
        'study_type': 'randomized controlled trial',
        'peer_reviewed': True,
        'source': 'NEJM',
        'fda_approved': True,
        'year': 2023
    }
    
    # Process medical document
    processed_medical = medical_rag.preprocess_document(medical_doc, medical_metadata)
    medical_entities = medical_rag.extract_domain_entities(medical_doc)
    medical_authority = medical_rag.calculate_authority_score({'metadata': medical_metadata})
    
    return {
        'academic_processing': {
            'sections': len(processed_academic.get('sections', {})),
            'citations': len(processed_academic.get('citations', [])),
            'quality_score': processed_academic.get('quality_score', 0),
            'entities': len(academic_entities),
            'authority_score': academic_authority
        },
        'medical_processing': {
            'medical_entities': len(processed_medical.get('medical_entities', [])),
            'drug_info': processed_medical.get('drug_information', {}),
            'evidence_level': processed_medical.get('evidence_level', ''),
            'contraindications': len(processed_medical.get('contraindications', [])),
            'authority_score': medical_authority
        },
        'supported_domains': [domain.value for domain in DomainRAGFactory.get_supported_domains()]
    }

if __name__ == "__main__":
    result = implement_domain_specialization()
    print(json.dumps(result, indent=2))