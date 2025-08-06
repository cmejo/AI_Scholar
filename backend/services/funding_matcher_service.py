"""
Funding Matcher Service

This service implements AI-powered funding opportunity discovery and matching
with relevance scoring based on research profiles and interests.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from core.database import (
    get_db, ResearchProfile, FundingOpportunity, FundingMatch, 
    FundingAlert, FundingNotification, GrantDatabase, User
)

logger = logging.getLogger(__name__)

@dataclass
class FundingMatchResult:
    """Result of funding opportunity matching"""
    opportunity_id: str
    title: str
    funding_agency: str
    relevance_score: float
    match_reasons: List[str]
    eligibility_status: str
    recommendation_strength: str
    application_deadline: Optional[datetime]
    funding_amount_range: Tuple[Optional[float], Optional[float]]

@dataclass
class RelevanceFactors:
    """Factors used in relevance scoring"""
    keyword_match_score: float
    domain_match_score: float
    career_stage_match: float
    funding_amount_match: float
    geographic_match: float
    eligibility_match: float
    deadline_urgency: float

class FundingMatcherService:
    """Service for AI-powered funding opportunity matching"""
    
    def __init__(self):
        self.keyword_weights = {
            'exact_match': 1.0,
            'partial_match': 0.7,
            'semantic_match': 0.5,
            'domain_match': 0.8
        }
        self.relevance_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    async def discover_funding_opportunities(
        self, 
        user_id: str, 
        limit: int = 50,
        min_relevance: float = 0.4
    ) -> List[FundingMatchResult]:
        """
        Discover and match funding opportunities for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of opportunities to return
            min_relevance: Minimum relevance score threshold
            
        Returns:
            List of matched funding opportunities
        """
        try:
            db = next(get_db())
            
            # Get user's research profile
            research_profile = db.query(ResearchProfile).filter(
                ResearchProfile.user_id == user_id
            ).first()
            
            if not research_profile:
                logger.warning(f"No research profile found for user {user_id}")
                return []
            
            # Get active funding opportunities
            opportunities = db.query(FundingOpportunity).filter(
                and_(
                    FundingOpportunity.is_active == True,
                    FundingOpportunity.application_deadline > datetime.now()
                )
            ).all()
            
            # Calculate relevance scores for each opportunity
            matches = []
            for opportunity in opportunities:
                relevance_score, match_reasons, eligibility = await self._calculate_relevance_score(
                    research_profile, opportunity
                )
                
                if relevance_score >= min_relevance:
                    recommendation_strength = self._get_recommendation_strength(relevance_score)
                    
                    match_result = FundingMatchResult(
                        opportunity_id=opportunity.id,
                        title=opportunity.title,
                        funding_agency=opportunity.funding_agency,
                        relevance_score=relevance_score,
                        match_reasons=match_reasons,
                        eligibility_status=eligibility,
                        recommendation_strength=recommendation_strength,
                        application_deadline=opportunity.application_deadline,
                        funding_amount_range=(opportunity.funding_amount_min, opportunity.funding_amount_max)
                    )
                    matches.append(match_result)
            
            # Sort by relevance score and limit results
            matches.sort(key=lambda x: x.relevance_score, reverse=True)
            matches = matches[:limit]
            
            # Store matches in database
            await self._store_funding_matches(db, user_id, matches)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error discovering funding opportunities: {str(e)}")
            raise
        finally:
            db.close()
    
    async def _calculate_relevance_score(
        self, 
        research_profile: ResearchProfile, 
        opportunity: FundingOpportunity
    ) -> Tuple[float, List[str], str]:
        """
        Calculate relevance score between research profile and funding opportunity
        
        Args:
            research_profile: User's research profile
            opportunity: Funding opportunity
            
        Returns:
            Tuple of (relevance_score, match_reasons, eligibility_status)
        """
        factors = RelevanceFactors(
            keyword_match_score=0.0,
            domain_match_score=0.0,
            career_stage_match=0.0,
            funding_amount_match=0.0,
            geographic_match=0.0,
            eligibility_match=0.0,
            deadline_urgency=0.0
        )
        
        match_reasons = []
        
        # Keyword matching
        factors.keyword_match_score, keyword_reasons = self._calculate_keyword_match(
            research_profile.research_interests or [],
            opportunity.keywords or []
        )
        match_reasons.extend(keyword_reasons)
        
        # Domain matching
        factors.domain_match_score, domain_reasons = self._calculate_domain_match(
            research_profile.research_domains or [],
            opportunity.research_areas or []
        )
        match_reasons.extend(domain_reasons)
        
        # Career stage matching
        factors.career_stage_match = self._calculate_career_stage_match(
            research_profile.career_stage,
            opportunity.eligibility_criteria or {}
        )
        
        # Funding amount matching
        factors.funding_amount_match = self._calculate_funding_amount_match(
            research_profile.funding_amount_range or {},
            opportunity.funding_amount_min,
            opportunity.funding_amount_max
        )
        
        # Geographic matching
        factors.geographic_match = self._calculate_geographic_match(
            research_profile.geographic_preferences or [],
            opportunity.restrictions or {}
        )
        
        # Eligibility matching
        factors.eligibility_match, eligibility_status = self._calculate_eligibility_match(
            research_profile,
            opportunity.eligibility_criteria or {}
        )
        
        # Deadline urgency (bonus for approaching deadlines)
        factors.deadline_urgency = self._calculate_deadline_urgency(
            opportunity.application_deadline
        )
        
        # Calculate weighted relevance score
        relevance_score = (
            factors.keyword_match_score * 0.25 +
            factors.domain_match_score * 0.20 +
            factors.career_stage_match * 0.15 +
            factors.funding_amount_match * 0.15 +
            factors.geographic_match * 0.10 +
            factors.eligibility_match * 0.10 +
            factors.deadline_urgency * 0.05
        )
        
        return min(relevance_score, 1.0), match_reasons, eligibility_status
    
    def _calculate_keyword_match(
        self, 
        research_interests: List[str], 
        opportunity_keywords: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate keyword matching score"""
        if not research_interests or not opportunity_keywords:
            return 0.0, []
        
        # Convert to lowercase for comparison
        interests_lower = [interest.lower() for interest in research_interests]
        keywords_lower = [keyword.lower() for keyword in opportunity_keywords]
        
        exact_matches = []
        partial_matches = []
        
        for interest in interests_lower:
            for keyword in keywords_lower:
                if interest == keyword:
                    exact_matches.append(interest)
                elif interest in keyword or keyword in interest:
                    partial_matches.append(f"{interest} ~ {keyword}")
        
        # Calculate score based on matches
        exact_score = len(exact_matches) * self.keyword_weights['exact_match']
        partial_score = len(partial_matches) * self.keyword_weights['partial_match']
        
        total_score = (exact_score + partial_score) / max(len(research_interests), 1)
        normalized_score = min(total_score, 1.0)
        
        reasons = []
        if exact_matches:
            reasons.append(f"Exact keyword matches: {', '.join(exact_matches)}")
        if partial_matches:
            reasons.append(f"Partial keyword matches: {', '.join(partial_matches[:3])}")
        
        return normalized_score, reasons
    
    def _calculate_domain_match(
        self, 
        research_domains: List[str], 
        opportunity_areas: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate research domain matching score"""
        if not research_domains or not opportunity_areas:
            return 0.0, []
        
        domains_lower = [domain.lower() for domain in research_domains]
        areas_lower = [area.lower() for area in opportunity_areas]
        
        matches = []
        for domain in domains_lower:
            for area in areas_lower:
                if domain == area or domain in area or area in domain:
                    matches.append(domain)
                    break
        
        score = len(matches) / len(research_domains)
        reasons = []
        if matches:
            reasons.append(f"Research domain matches: {', '.join(matches)}")
        
        return score, reasons
    
    def _calculate_career_stage_match(
        self, 
        career_stage: str, 
        eligibility_criteria: Dict[str, Any]
    ) -> float:
        """Calculate career stage matching score"""
        if not career_stage or not eligibility_criteria:
            return 0.5  # Neutral score if no information
        
        eligible_stages = eligibility_criteria.get('career_stages', [])
        if not eligible_stages:
            return 0.5
        
        career_stage_lower = career_stage.lower()
        eligible_stages_lower = [stage.lower() for stage in eligible_stages]
        
        if career_stage_lower in eligible_stages_lower:
            return 1.0
        
        # Partial matches for related stages
        stage_mappings = {
            'undergraduate': ['student', 'undergrad'],
            'graduate': ['student', 'grad', 'phd', 'masters'],
            'postdoc': ['postdoctoral', 'early_career'],
            'faculty': ['professor', 'academic', 'researcher']
        }
        
        for eligible_stage in eligible_stages_lower:
            if eligible_stage in stage_mappings.get(career_stage_lower, []):
                return 0.8
        
        return 0.2
    
    def _calculate_funding_amount_match(
        self, 
        preferred_range: Dict[str, float], 
        min_amount: Optional[float], 
        max_amount: Optional[float]
    ) -> float:
        """Calculate funding amount matching score"""
        if not preferred_range or (not min_amount and not max_amount):
            return 0.5  # Neutral score if no information
        
        pref_min = preferred_range.get('min', 0)
        pref_max = preferred_range.get('max', float('inf'))
        
        opp_min = min_amount or 0
        opp_max = max_amount or float('inf')
        
        # Check for overlap
        overlap_start = max(pref_min, opp_min)
        overlap_end = min(pref_max, opp_max)
        
        if overlap_start <= overlap_end:
            # Calculate overlap percentage
            pref_range_size = pref_max - pref_min
            overlap_size = overlap_end - overlap_start
            
            if pref_range_size > 0:
                return min(overlap_size / pref_range_size, 1.0)
            else:
                return 1.0  # Perfect match if preferred range is a point
        
        return 0.0  # No overlap
    
    def _calculate_geographic_match(
        self, 
        geographic_preferences: List[str], 
        restrictions: Dict[str, Any]
    ) -> float:
        """Calculate geographic matching score"""
        if not geographic_preferences:
            return 1.0  # No preference means all locations are acceptable
        
        geographic_restrictions = restrictions.get('geographic', [])
        if not geographic_restrictions:
            return 1.0  # No restrictions means all locations are eligible
        
        preferences_lower = [pref.lower() for pref in geographic_preferences]
        restrictions_lower = [rest.lower() for rest in geographic_restrictions]
        
        # Check for matches
        for pref in preferences_lower:
            for restriction in restrictions_lower:
                if pref in restriction or restriction in pref:
                    return 1.0
        
        return 0.3  # Low score if no geographic match
    
    def _calculate_eligibility_match(
        self, 
        research_profile: ResearchProfile, 
        eligibility_criteria: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Calculate eligibility matching score"""
        if not eligibility_criteria:
            return 1.0, "eligible"
        
        # Check various eligibility factors
        eligibility_score = 1.0
        status = "eligible"
        
        # Institution type requirements
        if 'institution_types' in eligibility_criteria:
            required_types = eligibility_criteria['institution_types']
            # This would need to be checked against actual institution data
            # For now, assume eligible
            pass
        
        # Citizenship requirements
        if 'citizenship' in eligibility_criteria:
            # This would need to be checked against user profile
            # For now, assume potentially eligible
            eligibility_score *= 0.8
            status = "potentially_eligible"
        
        # Experience requirements
        if 'min_experience_years' in eligibility_criteria:
            # This would need to be calculated from user profile
            # For now, assume eligible
            pass
        
        if eligibility_score < 0.5:
            status = "not_eligible"
        elif eligibility_score < 0.8:
            status = "potentially_eligible"
        
        return eligibility_score, status
    
    def _calculate_deadline_urgency(self, deadline: Optional[datetime]) -> float:
        """Calculate deadline urgency bonus"""
        if not deadline:
            return 0.0
        
        days_until_deadline = (deadline - datetime.now()).days
        
        if days_until_deadline < 0:
            return 0.0  # Past deadline
        elif days_until_deadline <= 30:
            return 0.3  # High urgency
        elif days_until_deadline <= 90:
            return 0.2  # Medium urgency
        elif days_until_deadline <= 180:
            return 0.1  # Low urgency
        else:
            return 0.0  # No urgency bonus
    
    def _get_recommendation_strength(self, relevance_score: float) -> str:
        """Get recommendation strength based on relevance score"""
        if relevance_score >= self.relevance_thresholds['high']:
            return 'high'
        elif relevance_score >= self.relevance_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    async def _store_funding_matches(
        self, 
        db: Session, 
        user_id: str, 
        matches: List[FundingMatchResult]
    ):
        """Store funding matches in database"""
        try:
            # Remove existing matches for this user
            db.query(FundingMatch).filter(FundingMatch.user_id == user_id).delete()
            
            # Add new matches
            for match in matches:
                funding_match = FundingMatch(
                    user_id=user_id,
                    funding_opportunity_id=match.opportunity_id,
                    relevance_score=match.relevance_score,
                    match_reasons=match.match_reasons,
                    eligibility_status=match.eligibility_status,
                    recommendation_strength=match.recommendation_strength,
                    match_metadata={
                        'funding_amount_range': match.funding_amount_range,
                        'application_deadline': match.application_deadline.isoformat() if match.application_deadline else None
                    }
                )
                db.add(funding_match)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing funding matches: {str(e)}")
            raise
    
    async def create_funding_alert(
        self, 
        user_id: str, 
        alert_name: str, 
        search_criteria: Dict[str, Any],
        notification_frequency: str = 'weekly'
    ) -> str:
        """
        Create a funding alert for automatic opportunity notifications
        
        Args:
            user_id: User identifier
            alert_name: Name for the alert
            search_criteria: Criteria for matching opportunities
            notification_frequency: How often to send notifications
            
        Returns:
            Alert ID
        """
        try:
            db = next(get_db())
            
            funding_alert = FundingAlert(
                user_id=user_id,
                alert_name=alert_name,
                search_criteria=search_criteria,
                notification_frequency=notification_frequency,
                is_active=True
            )
            
            db.add(funding_alert)
            db.commit()
            db.refresh(funding_alert)
            
            return funding_alert.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating funding alert: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_funding_matches(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get stored funding matches for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of matches to return
            
        Returns:
            List of funding matches with opportunity details
        """
        try:
            db = next(get_db())
            
            matches = db.query(FundingMatch, FundingOpportunity).join(
                FundingOpportunity, FundingMatch.funding_opportunity_id == FundingOpportunity.id
            ).filter(
                FundingMatch.user_id == user_id
            ).order_by(
                desc(FundingMatch.relevance_score)
            ).limit(limit).all()
            
            result = []
            for match, opportunity in matches:
                result.append({
                    'match_id': match.id,
                    'relevance_score': match.relevance_score,
                    'match_reasons': match.match_reasons,
                    'eligibility_status': match.eligibility_status,
                    'recommendation_strength': match.recommendation_strength,
                    'opportunity': {
                        'id': opportunity.id,
                        'title': opportunity.title,
                        'description': opportunity.description,
                        'funding_agency': opportunity.funding_agency,
                        'program_name': opportunity.program_name,
                        'opportunity_type': opportunity.opportunity_type,
                        'funding_amount_min': opportunity.funding_amount_min,
                        'funding_amount_max': opportunity.funding_amount_max,
                        'duration_months': opportunity.duration_months,
                        'application_deadline': opportunity.application_deadline,
                        'application_url': opportunity.application_url,
                        'success_rate': opportunity.success_rate
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting funding matches: {str(e)}")
            raise
        finally:
            db.close()
    
    async def search_grant_databases(
        self, 
        keywords: List[str], 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search multiple grant databases for funding opportunities
        
        Args:
            keywords: Search keywords
            filters: Additional search filters
            
        Returns:
            List of funding opportunities from various databases
        """
        try:
            db = next(get_db())
            
            # Get active grant databases
            databases = db.query(GrantDatabase).filter(
                GrantDatabase.is_active == True
            ).all()
            
            all_opportunities = []
            
            for database in databases:
                try:
                    # This would integrate with actual grant database APIs
                    # For now, return mock data
                    opportunities = await self._search_database(database, keywords, filters)
                    all_opportunities.extend(opportunities)
                    
                except Exception as e:
                    logger.warning(f"Error searching database {database.name}: {str(e)}")
                    continue
            
            return all_opportunities
            
        except Exception as e:
            logger.error(f"Error searching grant databases: {str(e)}")
            raise
        finally:
            db.close()
    
    async def _search_database(
        self, 
        database: GrantDatabase, 
        keywords: List[str], 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Search a specific grant database with enhanced AI-powered matching"""
        try:
            # Enhanced database-specific search implementations
            if database.name.lower() == 'nsf':
                return await self._search_nsf_database(keywords, filters)
            elif database.name.lower() == 'nih':
                return await self._search_nih_database(keywords, filters)
            elif database.name.lower() == 'grants.gov':
                return await self._search_grants_gov_database(keywords, filters)
            elif database.name.lower() == 'doe':
                return await self._search_doe_database(keywords, filters)
            elif database.name.lower() == 'nasa':
                return await self._search_nasa_database(keywords, filters)
            else:
                # Generic search for other databases
                return await self._search_generic_database(database, keywords, filters)
                
        except Exception as e:
            logger.warning(f"Error searching database {database.name}: {str(e)}")
            return []
    
    async def _search_nsf_database(self, keywords: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search NSF database with AI-enhanced keyword expansion"""
        # AI-powered keyword expansion for better matching
        expanded_keywords = await self._expand_keywords_with_ai(keywords, domain="nsf")
        
        # Mock NSF opportunities with realistic data
        nsf_opportunities = [
            {
                'title': 'Computer and Information Science and Engineering (CISE) Core Programs',
                'description': 'Supports investigator-initiated research in all areas of computer and information science and engineering',
                'funding_agency': 'National Science Foundation',
                'program_name': 'CISE Core Programs',
                'opportunity_type': 'grant',
                'funding_amount_min': 100000,
                'funding_amount_max': 500000,
                'duration_months': 36,
                'application_deadline': datetime.now() + timedelta(days=45),
                'source': 'nsf',
                'keywords': ['computer science', 'artificial intelligence', 'machine learning', 'data science'],
                'success_rate': 0.18,
                'eligibility_criteria': {
                    'career_stages': ['faculty', 'postdoc'],
                    'institution_types': ['university', 'research_institute']
                }
            },
            {
                'title': 'Faculty Early Career Development Program (CAREER)',
                'description': 'NSF\'s most prestigious award for early-career faculty',
                'funding_agency': 'National Science Foundation',
                'program_name': 'CAREER',
                'opportunity_type': 'grant',
                'funding_amount_min': 400000,
                'funding_amount_max': 600000,
                'duration_months': 60,
                'application_deadline': datetime.now() + timedelta(days=120),
                'source': 'nsf',
                'keywords': ['early career', 'education', 'research integration'],
                'success_rate': 0.12,
                'eligibility_criteria': {
                    'career_stages': ['faculty'],
                    'experience_years': {'max': 7}
                }
            }
        ]
        
        # Filter based on keyword matches
        matched_opportunities = []
        for opp in nsf_opportunities:
            if self._matches_keywords(opp.get('keywords', []), expanded_keywords):
                matched_opportunities.append(opp)
        
        return matched_opportunities
    
    async def _search_nih_database(self, keywords: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search NIH database with biomedical focus"""
        expanded_keywords = await self._expand_keywords_with_ai(keywords, domain="biomedical")
        
        nih_opportunities = [
            {
                'title': 'Research Project Grant (R01)',
                'description': 'Support for discrete, specified, circumscribed research projects',
                'funding_agency': 'National Institutes of Health',
                'program_name': 'R01',
                'opportunity_type': 'grant',
                'funding_amount_min': 250000,
                'funding_amount_max': 500000,
                'duration_months': 60,
                'application_deadline': datetime.now() + timedelta(days=75),
                'source': 'nih',
                'keywords': ['biomedical research', 'health', 'disease', 'clinical'],
                'success_rate': 0.20,
                'eligibility_criteria': {
                    'career_stages': ['faculty', 'postdoc'],
                    'fields': ['biomedical', 'health sciences']
                }
            },
            {
                'title': 'Small Business Innovation Research (SBIR)',
                'description': 'Support for small businesses to engage in R&D with commercialization potential',
                'funding_agency': 'National Institutes of Health',
                'program_name': 'SBIR',
                'opportunity_type': 'grant',
                'funding_amount_min': 50000,
                'funding_amount_max': 1500000,
                'duration_months': 24,
                'application_deadline': datetime.now() + timedelta(days=90),
                'source': 'nih',
                'keywords': ['innovation', 'commercialization', 'small business', 'technology transfer'],
                'success_rate': 0.15,
                'eligibility_criteria': {
                    'organization_type': ['small_business'],
                    'employee_limit': 500
                }
            }
        ]
        
        matched_opportunities = []
        for opp in nih_opportunities:
            if self._matches_keywords(opp.get('keywords', []), expanded_keywords):
                matched_opportunities.append(opp)
        
        return matched_opportunities
    
    async def _search_grants_gov_database(self, keywords: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search Grants.gov database"""
        # This would implement actual Grants.gov API integration
        # For now, return diverse federal opportunities
        return [
            {
                'title': 'Department of Energy Office of Science Research',
                'description': 'Basic research in physical sciences and advanced computing',
                'funding_agency': 'Department of Energy',
                'program_name': 'Office of Science',
                'opportunity_type': 'grant',
                'funding_amount_min': 100000,
                'funding_amount_max': 1000000,
                'duration_months': 36,
                'application_deadline': datetime.now() + timedelta(days=60),
                'source': 'grants.gov',
                'keywords': ['energy', 'physics', 'computing', 'materials science'],
                'success_rate': 0.22
            }
        ]
    
    async def _search_doe_database(self, keywords: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search Department of Energy database"""
        return [
            {
                'title': 'Advanced Scientific Computing Research',
                'description': 'Research in computational science and high-performance computing',
                'funding_agency': 'Department of Energy',
                'program_name': 'ASCR',
                'opportunity_type': 'grant',
                'funding_amount_min': 200000,
                'funding_amount_max': 800000,
                'duration_months': 36,
                'application_deadline': datetime.now() + timedelta(days=85),
                'source': 'doe',
                'keywords': ['computing', 'simulation', 'algorithms', 'mathematics'],
                'success_rate': 0.25
            }
        ]
    
    async def _search_nasa_database(self, keywords: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search NASA database"""
        return [
            {
                'title': 'NASA Research Opportunities in Space and Earth Sciences',
                'description': 'Research opportunities in space science, Earth science, and astrophysics',
                'funding_agency': 'NASA',
                'program_name': 'ROSES',
                'opportunity_type': 'grant',
                'funding_amount_min': 75000,
                'funding_amount_max': 400000,
                'duration_months': 36,
                'application_deadline': datetime.now() + timedelta(days=95),
                'source': 'nasa',
                'keywords': ['space science', 'earth science', 'astrophysics', 'planetary science'],
                'success_rate': 0.28
            }
        ]
    
    async def _search_generic_database(self, database: GrantDatabase, keywords: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generic search for other databases"""
        return [
            {
                'title': f'Research Opportunity from {database.name}',
                'description': f'Research funding opportunity matching keywords: {", ".join(keywords)}',
                'funding_agency': database.name,
                'funding_amount_min': 50000,
                'funding_amount_max': 500000,
                'application_deadline': datetime.now() + timedelta(days=90),
                'source': database.name.lower().replace(' ', '_')
            }
        ]
    
    async def _expand_keywords_with_ai(self, keywords: List[str], domain: str = "general") -> List[str]:
        """Use AI to expand keywords for better matching"""
        expanded = set(keywords)
        
        # Domain-specific keyword expansion
        keyword_expansions = {
            "nsf": {
                "machine learning": ["artificial intelligence", "deep learning", "neural networks", "data mining"],
                "computer science": ["computing", "algorithms", "software engineering", "cybersecurity"],
                "artificial intelligence": ["AI", "machine learning", "robotics", "natural language processing"]
            },
            "biomedical": {
                "machine learning": ["bioinformatics", "computational biology", "medical AI", "health informatics"],
                "artificial intelligence": ["medical AI", "clinical decision support", "diagnostic AI", "precision medicine"],
                "data science": ["biostatistics", "epidemiology", "health analytics", "clinical data"]
            },
            "general": {
                "AI": ["artificial intelligence", "machine learning", "deep learning"],
                "ML": ["machine learning", "artificial intelligence", "data science"],
                "NLP": ["natural language processing", "text mining", "computational linguistics"]
            }
        }
        
        domain_expansions = keyword_expansions.get(domain, keyword_expansions["general"])
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in domain_expansions:
                expanded.update(domain_expansions[keyword_lower])
        
        return list(expanded)
    
    def _matches_keywords(self, opportunity_keywords: List[str], search_keywords: List[str]) -> bool:
        """Check if opportunity keywords match search keywords"""
        opp_keywords_lower = [k.lower() for k in opportunity_keywords]
        search_keywords_lower = [k.lower() for k in search_keywords]
        
        # Check for exact matches or partial matches
        for search_kw in search_keywords_lower:
            for opp_kw in opp_keywords_lower:
                if search_kw in opp_kw or opp_kw in search_kw:
                    return True
        
        return False
    
    async def send_funding_notifications(self, user_id: str):
        """Send funding opportunity notifications to user"""
        try:
            db = next(get_db())
            
            # Get user's active alerts
            alerts = db.query(FundingAlert).filter(
                and_(
                    FundingAlert.user_id == user_id,
                    FundingAlert.is_active == True
                )
            ).all()
            
            for alert in alerts:
                # Check if it's time to send notification based on frequency
                should_send = self._should_send_notification(alert)
                
                if should_send:
                    # Find new opportunities matching alert criteria
                    new_opportunities = await self._find_opportunities_for_alert(alert)
                    
                    if new_opportunities:
                        # Create notifications
                        for opportunity in new_opportunities:
                            notification = FundingNotification(
                                user_id=user_id,
                                funding_opportunity_id=opportunity['id'],
                                alert_id=alert.id,
                                notification_type='new_opportunity',
                                message=f"New funding opportunity matching your alert '{alert.alert_name}': {opportunity['title']}"
                            )
                            db.add(notification)
                        
                        # Update alert last triggered time
                        alert.last_triggered = datetime.now()
                        
                        db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error sending funding notifications: {str(e)}")
            raise
        finally:
            db.close()
    
    def _should_send_notification(self, alert: FundingAlert) -> bool:
        """Check if notification should be sent based on frequency"""
        if not alert.last_triggered:
            return True
        
        now = datetime.now()
        time_since_last = now - alert.last_triggered
        
        if alert.notification_frequency == 'immediate':
            return True
        elif alert.notification_frequency == 'daily':
            return time_since_last.days >= 1
        elif alert.notification_frequency == 'weekly':
            return time_since_last.days >= 7
        
        return False
    
    async def _find_opportunities_for_alert(self, alert: FundingAlert) -> List[Dict[str, Any]]:
        """Find new opportunities matching alert criteria"""
        # This would implement the actual search logic based on alert criteria
        # For now, return empty list
        return []
    
    async def get_funding_analytics(
        self, 
        user_id: str,
        time_range_days: int = 365
    ) -> Dict[str, Any]:
        """
        Get funding opportunity analytics and success rate data
        
        Args:
            user_id: User identifier
            time_range_days: Time range for analytics in days
            
        Returns:
            Analytics data including success rates and recommendations
        """
        try:
            db = next(get_db())
            
            # Get user's applications from grant applications table
            from core.database import GrantApplication
            
            cutoff_date = datetime.now() - timedelta(days=time_range_days)
            
            applications = db.query(GrantApplication).filter(
                and_(
                    GrantApplication.user_id == user_id,
                    GrantApplication.created_at >= cutoff_date
                )
            ).all()
            
            # Calculate success metrics
            total_applications = len(applications)
            awarded_applications = len([app for app in applications if app.status == 'awarded'])
            rejected_applications = len([app for app in applications if app.status == 'rejected'])
            pending_applications = len([app for app in applications if app.status in ['submitted', 'under_review']])
            
            success_rate = (awarded_applications / total_applications * 100) if total_applications > 0 else 0
            
            # Calculate funding amounts
            total_requested = sum(app.requested_amount or 0 for app in applications)
            total_awarded = sum(app.award_amount or 0 for app in applications if app.status == 'awarded')
            
            # Get opportunity type breakdown
            opportunity_types = {}
            for app in applications:
                # Get opportunity details
                opportunity = db.query(FundingOpportunity).filter(
                    FundingOpportunity.id == app.funding_opportunity_id
                ).first()
                
                if opportunity:
                    opp_type = opportunity.opportunity_type
                    if opp_type not in opportunity_types:
                        opportunity_types[opp_type] = {'count': 0, 'success_rate': 0, 'awarded': 0}
                    
                    opportunity_types[opp_type]['count'] += 1
                    if app.status == 'awarded':
                        opportunity_types[opp_type]['awarded'] += 1
            
            # Calculate success rates by type
            for opp_type in opportunity_types:
                count = opportunity_types[opp_type]['count']
                awarded = opportunity_types[opp_type]['awarded']
                opportunity_types[opp_type]['success_rate'] = (awarded / count * 100) if count > 0 else 0
            
            # Generate recommendations
            recommendations = []
            
            if success_rate < 20:
                recommendations.append("Consider applying to opportunities with higher acceptance rates")
            
            if total_applications < 5:
                recommendations.append("Increase application volume to improve chances of success")
            
            if len(opportunity_types) == 1:
                recommendations.append("Diversify application types to spread risk")
            
            analytics = {
                'time_range_days': time_range_days,
                'total_applications': total_applications,
                'success_rate': success_rate,
                'awarded_applications': awarded_applications,
                'rejected_applications': rejected_applications,
                'pending_applications': pending_applications,
                'total_requested_amount': total_requested,
                'total_awarded_amount': total_awarded,
                'opportunity_types': opportunity_types,
                'recommendations': recommendations,
                'average_award_amount': total_awarded / awarded_applications if awarded_applications > 0 else 0,
                'roi_ratio': total_awarded / total_requested if total_requested > 0 else 0
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting funding analytics: {str(e)}")
            raise
        finally:
            db.close()
    
    async def optimize_application_strategy(
        self, 
        user_id: str,
        target_success_rate: float = 0.3
    ) -> Dict[str, Any]:
        """
        Provide AI-powered application optimization recommendations
        
        Args:
            user_id: User identifier
            target_success_rate: Desired success rate (0.0 to 1.0)
            
        Returns:
            Optimization recommendations and strategy
        """
        try:
            db = next(get_db())
            
            # Get user's research profile
            research_profile = db.query(ResearchProfile).filter(
                ResearchProfile.user_id == user_id
            ).first()
            
            if not research_profile:
                return {"error": "No research profile found"}
            
            # Get user's application history
            from core.database import GrantApplication
            applications = db.query(GrantApplication).filter(
                GrantApplication.user_id == user_id
            ).all()
            
            # Analyze current performance
            try:
                current_analytics = await self.get_funding_analytics(user_id)
                current_success_rate = current_analytics.get('success_rate', 0) / 100
            except:
                # If analytics fail, use defaults
                current_analytics = {
                    'success_rate': 0,
                    'total_applications': 0,
                    'opportunity_types': {},
                    'total_requested_amount': 0,
                    'total_awarded_amount': 0
                }
                current_success_rate = 0
            
            # Generate optimization recommendations
            recommendations = []
            strategy_changes = []
            
            # Success rate analysis
            if current_success_rate < target_success_rate:
                gap = target_success_rate - current_success_rate
                
                if gap > 0.2:
                    recommendations.append({
                        'type': 'strategy_overhaul',
                        'priority': 'high',
                        'title': 'Major Strategy Revision Needed',
                        'description': f'Current success rate ({current_success_rate:.1%}) is significantly below target ({target_success_rate:.1%})',
                        'actions': [
                            'Focus on opportunities with higher acceptance rates (>25%)',
                            'Apply to more opportunities to increase volume',
                            'Consider collaborating with established researchers',
                            'Seek mentorship for proposal writing'
                        ]
                    })
                elif gap > 0.1:
                    recommendations.append({
                        'type': 'moderate_adjustment',
                        'priority': 'medium',
                        'title': 'Strategy Refinement Recommended',
                        'description': f'Success rate can be improved from {current_success_rate:.1%} to {target_success_rate:.1%}',
                        'actions': [
                            'Diversify application portfolio',
                            'Target opportunities with better fit scores',
                            'Improve proposal quality through peer review'
                        ]
                    })
            
            # Portfolio diversification analysis
            opportunity_types = current_analytics.get('opportunity_types', {})
            if len(opportunity_types) < 3:
                recommendations.append({
                    'type': 'diversification',
                    'priority': 'medium',
                    'title': 'Diversify Opportunity Types',
                    'description': 'Applying to diverse opportunity types reduces risk',
                    'actions': [
                        'Consider fellowships in addition to grants',
                        'Look into industry partnerships',
                        'Explore international funding opportunities'
                    ]
                })
            
            # Funding amount optimization
            funding_range = research_profile.funding_amount_range or {}
            avg_requested = current_analytics.get('total_requested_amount', 0) / max(current_analytics.get('total_applications', 1), 1)
            
            if avg_requested > funding_range.get('max', float('inf')):
                recommendations.append({
                    'type': 'amount_optimization',
                    'priority': 'medium',
                    'title': 'Consider Smaller Grant Amounts',
                    'description': 'Smaller grants often have higher success rates',
                    'actions': [
                        'Target grants in the $50K-$200K range for higher success probability',
                        'Build track record with smaller grants before pursuing larger ones',
                        'Consider pilot grants and seed funding opportunities'
                    ]
                })
            
            # Timing optimization
            recommendations.append({
                'type': 'timing',
                'priority': 'low',
                'title': 'Optimize Application Timing',
                'description': 'Strategic timing can improve success rates',
                'actions': [
                    'Apply early in funding cycles when possible',
                    'Avoid last-minute submissions',
                    'Plan for multiple submission deadlines per year'
                ]
            })
            
            # AI-powered opportunity matching
            current_matches = await self.discover_funding_opportunities(
                user_id=user_id,
                limit=20,
                min_relevance=0.5
            )
            
            high_potential_opportunities = [
                match for match in current_matches 
                if match.relevance_score > 0.7 and match.eligibility_status == 'eligible'
            ]
            
            # Generate strategic recommendations
            strategy = {
                'recommended_applications_per_year': max(8, int(target_success_rate * 20)),
                'target_success_rate': target_success_rate,
                'current_success_rate': current_success_rate,
                'improvement_needed': max(0, target_success_rate - current_success_rate),
                'high_potential_opportunities': len(high_potential_opportunities),
                'recommended_opportunity_mix': {
                    'high_success_rate_opportunities': 0.4,  # 40% of applications
                    'medium_success_rate_opportunities': 0.4,  # 40% of applications
                    'high_reward_opportunities': 0.2  # 20% of applications (higher risk, higher reward)
                }
            }
            
            optimization_result = {
                'user_id': user_id,
                'current_performance': current_analytics,
                'target_success_rate': target_success_rate,
                'recommendations': recommendations,
                'strategy': strategy,
                'high_potential_opportunities': [
                    {
                        'title': opp.title,
                        'agency': opp.funding_agency,
                        'relevance_score': opp.relevance_score,
                        'deadline': opp.application_deadline.isoformat() if opp.application_deadline else None
                    }
                    for opp in high_potential_opportunities[:5]
                ],
                'next_steps': [
                    'Review and implement high-priority recommendations',
                    'Apply to identified high-potential opportunities',
                    'Set up funding alerts for relevant opportunities',
                    'Schedule regular strategy reviews (quarterly)'
                ]
            }
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing application strategy: {str(e)}")
            raise
        finally:
            db.close()
    
    async def setup_default_grant_databases(self):
        """Set up default grant databases for enhanced searching"""
        try:
            db = next(get_db())
            
            default_databases = [
                {
                    'name': 'NSF',
                    'description': 'National Science Foundation funding opportunities',
                    'base_url': 'https://www.nsf.gov',
                    'api_endpoint': 'https://api.nsf.gov/services/v1/awards.json',
                    'authentication_type': 'none',
                    'supported_fields': ['title', 'abstract', 'investigator', 'institution', 'program'],
                    'rate_limit': {'requests_per_hour': 1000}
                },
                {
                    'name': 'NIH',
                    'description': 'National Institutes of Health funding opportunities',
                    'base_url': 'https://www.nih.gov',
                    'api_endpoint': 'https://api.reporter.nih.gov/v2/projects/search',
                    'authentication_type': 'none',
                    'supported_fields': ['title', 'abstract', 'pi_names', 'org_name', 'activity_code'],
                    'rate_limit': {'requests_per_hour': 500}
                },
                {
                    'name': 'Grants.gov',
                    'description': 'Federal government grant opportunities',
                    'base_url': 'https://www.grants.gov',
                    'api_endpoint': 'https://www.grants.gov/grantsws/rest/opportunities/search',
                    'authentication_type': 'api_key',
                    'supported_fields': ['title', 'description', 'agency', 'category', 'eligibility'],
                    'rate_limit': {'requests_per_hour': 200}
                },
                {
                    'name': 'DOE',
                    'description': 'Department of Energy funding opportunities',
                    'base_url': 'https://www.energy.gov',
                    'api_endpoint': 'https://www.energy.gov/science/funding-opportunities',
                    'authentication_type': 'none',
                    'supported_fields': ['title', 'description', 'program', 'deadline'],
                    'rate_limit': {'requests_per_hour': 300}
                },
                {
                    'name': 'NASA',
                    'description': 'NASA research opportunities',
                    'base_url': 'https://www.nasa.gov',
                    'api_endpoint': 'https://nspires.nasaprs.com/external/solicitations/solicitations.do',
                    'authentication_type': 'none',
                    'supported_fields': ['title', 'description', 'program', 'deadline'],
                    'rate_limit': {'requests_per_hour': 250}
                }
            ]
            
            for db_info in default_databases:
                existing_db = db.query(GrantDatabase).filter(
                    GrantDatabase.name == db_info['name']
                ).first()
                
                if not existing_db:
                    grant_db = GrantDatabase(
                        name=db_info['name'],
                        description=db_info['description'],
                        base_url=db_info['base_url'],
                        api_endpoint=db_info['api_endpoint'],
                        authentication_type=db_info['authentication_type'],
                        supported_fields=db_info['supported_fields'],
                        rate_limit=db_info['rate_limit'],
                        is_active=True,
                        sync_frequency_hours=24
                    )
                    db.add(grant_db)
            
            db.commit()
            logger.info("Default grant databases set up successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting up default grant databases: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_trending_opportunities(
        self, 
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending funding opportunities based on AI analysis
        
        Args:
            user_id: User identifier
            limit: Maximum number of opportunities to return
            
        Returns:
            List of trending opportunities with trend analysis
        """
        try:
            db = next(get_db())
            
            # Get user's research profile for personalization
            research_profile = db.query(ResearchProfile).filter(
                ResearchProfile.user_id == user_id
            ).first()
            
            # Get recent funding opportunities
            recent_opportunities = db.query(FundingOpportunity).filter(
                and_(
                    FundingOpportunity.is_active == True,
                    FundingOpportunity.application_deadline > datetime.now(),
                    FundingOpportunity.created_at > datetime.now() - timedelta(days=30)
                )
            ).all()
            
            # AI-powered trend analysis
            trending_opportunities = []
            
            for opportunity in recent_opportunities:
                # Calculate trend score based on multiple factors
                trend_score = 0.0
                trend_factors = []
                
                # Recency factor (newer opportunities get higher scores)
                days_since_posted = (datetime.now() - opportunity.created_at).days
                recency_score = max(0, 1 - (days_since_posted / 30))
                trend_score += recency_score * 0.3
                trend_factors.append(f"Recently posted ({days_since_posted} days ago)")
                
                # Success rate factor
                if opportunity.success_rate and opportunity.success_rate > 0.2:
                    trend_score += 0.2
                    trend_factors.append(f"High success rate ({opportunity.success_rate:.1%})")
                
                # Funding amount attractiveness
                if opportunity.funding_amount_max and opportunity.funding_amount_max > 200000:
                    trend_score += 0.2
                    trend_factors.append(f"Substantial funding (up to ${opportunity.funding_amount_max:,.0f})")
                
                # Keyword relevance to current research trends
                trending_keywords = ['artificial intelligence', 'machine learning', 'climate change', 
                                   'sustainability', 'quantum computing', 'biotechnology', 'cybersecurity']
                
                if opportunity.keywords:
                    keyword_matches = sum(1 for kw in opportunity.keywords 
                                        if any(trend_kw in kw.lower() for trend_kw in trending_keywords))
                    if keyword_matches > 0:
                        trend_score += min(keyword_matches * 0.1, 0.3)
                        trend_factors.append(f"Trending research areas ({keyword_matches} matches)")
                
                # Personal relevance if user profile exists
                if research_profile:
                    relevance_score, _, _ = await self._calculate_relevance_score(research_profile, opportunity)
                    if relevance_score > 0.6:
                        trend_score += 0.2
                        trend_factors.append(f"High personal relevance ({relevance_score:.2f})")
                
                if trend_score > 0.4:  # Threshold for trending
                    trending_opportunities.append({
                        'opportunity': {
                            'id': opportunity.id,
                            'title': opportunity.title,
                            'funding_agency': opportunity.funding_agency,
                            'funding_amount_min': opportunity.funding_amount_min,
                            'funding_amount_max': opportunity.funding_amount_max,
                            'application_deadline': opportunity.application_deadline,
                            'success_rate': opportunity.success_rate,
                            'opportunity_type': opportunity.opportunity_type
                        },
                        'trend_score': trend_score,
                        'trend_factors': trend_factors,
                        'days_until_deadline': (opportunity.application_deadline - datetime.now()).days if opportunity.application_deadline else None
                    })
            
            # Sort by trend score and limit results
            trending_opportunities.sort(key=lambda x: x['trend_score'], reverse=True)
            trending_opportunities = trending_opportunities[:limit]
            
            return trending_opportunities
            
        except Exception as e:
            logger.error(f"Error getting trending opportunities: {str(e)}")
            raise
        finally:
            db.close()
    
