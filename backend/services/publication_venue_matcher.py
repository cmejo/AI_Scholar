"""
Publication Venue Matcher Service

This service implements journal and conference recommendation system with venue ranking,
impact factor analysis, and submission timeline tracking.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from core.database import (
    get_db, PublicationVenue, PublicationDeadline, PublicationMatch, 
    SubmissionTracker, ResearchProfile, User
)

logger = logging.getLogger(__name__)

@dataclass
class VenueRecommendation:
    """Result of venue recommendation"""
    venue_id: str
    name: str
    venue_type: str
    publisher: str
    relevance_score: float
    fit_score: float
    success_probability: float
    match_reasons: List[str]
    recommendation_strength: str
    impact_factor: Optional[float]
    acceptance_rate: Optional[float]
    next_deadline: Optional[datetime]
    average_review_time: Optional[int]

@dataclass
class VenueAnalytics:
    """Analytics for venue performance"""
    venue_id: str
    name: str
    total_submissions: int
    acceptance_rate: float
    average_review_time: int
    impact_metrics: Dict[str, float]
    recent_trends: Dict[str, Any]

class PublicationVenueMatcherService:
    """Service for publication venue matching and recommendation"""
    
    def __init__(self):
        self.venue_weights = {
            'keyword_match': 0.25,
            'research_area_match': 0.20,
            'impact_factor': 0.15,
            'acceptance_rate': 0.15,
            'review_time': 0.10,
            'open_access': 0.05,
            'geographic_scope': 0.05,
            'publication_fee': 0.05
        }
        
        self.recommendation_thresholds = {
            'high': 0.75,
            'medium': 0.55,
            'low': 0.35
        }
    
    async def recommend_venues(
        self, 
        user_id: str,
        paper_abstract: str,
        venue_type: Optional[str] = None,
        max_recommendations: int = 20,
        min_fit_score: float = 0.3
    ) -> List[VenueRecommendation]:
        """
        Recommend publication venues based on paper abstract and user profile
        
        Args:
            user_id: User identifier
            paper_abstract: Abstract of the paper
            venue_type: Filter by venue type ('journal', 'conference', 'workshop')
            max_recommendations: Maximum number of recommendations
            min_fit_score: Minimum fit score threshold
            
        Returns:
            List of venue recommendations
        """
        try:
            db = next(get_db())
            
            # Get user's research profile
            research_profile = db.query(ResearchProfile).filter(
                ResearchProfile.user_id == user_id
            ).first()
            
            # Get active publication venues
            query = db.query(PublicationVenue).filter(
                PublicationVenue.is_active == True
            )
            
            if venue_type:
                query = query.filter(PublicationVenue.venue_type == venue_type)
            
            venues = query.all()
            
            # Extract keywords and topics from abstract
            abstract_keywords = self._extract_keywords_from_abstract(paper_abstract)
            abstract_topics = self._extract_research_topics(paper_abstract)
            
            recommendations = []
            for venue in venues:
                # Calculate fit score
                fit_score, match_reasons = await self._calculate_venue_fit_score(
                    venue, paper_abstract, abstract_keywords, abstract_topics, research_profile
                )
                
                if fit_score >= min_fit_score:
                    # Calculate success probability
                    success_probability = await self._calculate_success_probability(
                        venue, paper_abstract, research_profile
                    )
                    
                    # Get next deadline
                    next_deadline = await self._get_next_deadline(db, venue.id)
                    
                    # Determine recommendation strength
                    recommendation_strength = self._get_recommendation_strength(fit_score)
                    
                    recommendation = VenueRecommendation(
                        venue_id=venue.id,
                        name=venue.name,
                        venue_type=venue.venue_type,
                        publisher=venue.publisher or "Unknown",
                        relevance_score=fit_score,
                        fit_score=fit_score,
                        success_probability=success_probability,
                        match_reasons=match_reasons,
                        recommendation_strength=recommendation_strength,
                        impact_factor=venue.impact_factor,
                        acceptance_rate=venue.acceptance_rate,
                        next_deadline=next_deadline,
                        average_review_time=venue.average_review_time_days
                    )
                    recommendations.append(recommendation)
            
            # Sort by fit score and limit results
            recommendations.sort(key=lambda x: x.fit_score, reverse=True)
            recommendations = recommendations[:max_recommendations]
            
            # Store matches in database
            await self._store_publication_matches(db, user_id, paper_abstract, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error recommending venues: {str(e)}")
            raise
        finally:
            db.close()
    
    def _extract_keywords_from_abstract(self, abstract: str) -> List[str]:
        """Extract keywords from paper abstract"""
        # Simple keyword extraction - in practice, this would use NLP techniques
        # Remove common words and extract meaningful terms
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'we', 'our', 
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'cannot', 'paper', 'study', 'research', 'work', 'approach',
            'method', 'results', 'conclusion', 'abstract', 'introduction'
        }
        
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', abstract.lower())
        keywords = [word for word in words if word not in common_words]
        
        # Get unique keywords and their frequency
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Return top keywords
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, freq in sorted_keywords[:20]]
    
    def _extract_research_topics(self, abstract: str) -> List[str]:
        """Extract research topics from abstract using pattern matching"""
        # Common research topic patterns
        topic_patterns = {
            'machine learning': r'\b(machine learning|ml|artificial intelligence|ai)\b',
            'deep learning': r'\b(deep learning|neural networks|cnn|rnn|lstm)\b',
            'natural language processing': r'\b(natural language processing|nlp|text mining|language models)\b',
            'computer vision': r'\b(computer vision|image processing|object detection|image recognition)\b',
            'data mining': r'\b(data mining|knowledge discovery|pattern recognition)\b',
            'algorithms': r'\b(algorithms|optimization|computational complexity)\b',
            'software engineering': r'\b(software engineering|software development|programming)\b',
            'cybersecurity': r'\b(cybersecurity|security|cryptography|privacy)\b',
            'databases': r'\b(databases|data management|sql|nosql)\b',
            'networks': r'\b(networks|networking|distributed systems|cloud computing)\b',
            'human-computer interaction': r'\b(hci|human computer interaction|user interface|ux)\b',
            'bioinformatics': r'\b(bioinformatics|computational biology|genomics)\b'
        }
        
        abstract_lower = abstract.lower()
        detected_topics = []
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, abstract_lower):
                detected_topics.append(topic)
        
        return detected_topics
    
    async def _calculate_venue_fit_score(
        self,
        venue: PublicationVenue,
        abstract: str,
        abstract_keywords: List[str],
        abstract_topics: List[str],
        research_profile: Optional[ResearchProfile]
    ) -> Tuple[float, List[str]]:
        """Calculate how well a paper fits a venue"""
        score = 0.0
        match_reasons = []
        
        # Keyword matching
        venue_keywords = venue.keywords or []
        keyword_matches = []
        for keyword in abstract_keywords:
            for venue_keyword in venue_keywords:
                if keyword.lower() in venue_keyword.lower() or venue_keyword.lower() in keyword.lower():
                    keyword_matches.append(keyword)
                    break
        
        if keyword_matches:
            keyword_score = min(len(keyword_matches) / max(len(abstract_keywords), 1), 1.0)
            score += keyword_score * self.venue_weights['keyword_match']
            match_reasons.append(f"Keyword matches: {', '.join(keyword_matches[:3])}")
        
        # Research area matching
        venue_areas = venue.research_areas or []
        area_matches = []
        for topic in abstract_topics:
            for area in venue_areas:
                if topic.lower() in area.lower() or area.lower() in topic.lower():
                    area_matches.append(topic)
                    break
        
        if area_matches:
            area_score = min(len(area_matches) / max(len(abstract_topics), 1), 1.0)
            score += area_score * self.venue_weights['research_area_match']
            match_reasons.append(f"Research area matches: {', '.join(area_matches[:2])}")
        
        # Impact factor bonus
        if venue.impact_factor:
            # Normalize impact factor (assuming max of 50 for normalization)
            impact_score = min(venue.impact_factor / 50.0, 1.0)
            score += impact_score * self.venue_weights['impact_factor']
            match_reasons.append(f"Impact factor: {venue.impact_factor}")
        
        # Acceptance rate consideration (higher acceptance rate = better for authors)
        if venue.acceptance_rate:
            acceptance_score = venue.acceptance_rate / 100.0  # Convert percentage to 0-1
            score += acceptance_score * self.venue_weights['acceptance_rate']
            match_reasons.append(f"Acceptance rate: {venue.acceptance_rate}%")
        
        # Review time consideration (shorter review time = better)
        if venue.average_review_time_days:
            # Normalize review time (assuming 365 days as max for normalization)
            review_time_score = max(0, 1.0 - (venue.average_review_time_days / 365.0))
            score += review_time_score * self.venue_weights['review_time']
            match_reasons.append(f"Average review time: {venue.average_review_time_days} days")
        
        # Open access bonus
        if venue.open_access:
            score += 1.0 * self.venue_weights['open_access']
            match_reasons.append("Open access publication")
        
        # Geographic scope consideration
        if venue.geographic_scope == 'international':
            score += 1.0 * self.venue_weights['geographic_scope']
            match_reasons.append("International scope")
        elif venue.geographic_scope == 'national':
            score += 0.7 * self.venue_weights['geographic_scope']
        
        # Publication fee consideration (lower fee = better)
        if venue.publication_fee is not None:
            if venue.publication_fee == 0:
                score += 1.0 * self.venue_weights['publication_fee']
                match_reasons.append("No publication fee")
            else:
                # Normalize fee (assuming $5000 as high fee for normalization)
                fee_score = max(0, 1.0 - (venue.publication_fee / 5000.0))
                score += fee_score * self.venue_weights['publication_fee']
        
        return min(score, 1.0), match_reasons
    
    async def _calculate_success_probability(
        self,
        venue: PublicationVenue,
        abstract: str,
        research_profile: Optional[ResearchProfile]
    ) -> float:
        """Calculate probability of acceptance at this venue"""
        base_probability = venue.acceptance_rate / 100.0 if venue.acceptance_rate else 0.2
        
        # Adjust based on research profile if available
        if research_profile:
            # Consider previous publications and expertise
            publications = research_profile.publications or []
            if publications:
                # Higher success probability if user has publications
                publication_bonus = min(len(publications) * 0.05, 0.2)
                base_probability += publication_bonus
        
        # Consider venue prestige (higher impact factor = lower acceptance probability)
        if venue.impact_factor:
            prestige_factor = min(venue.impact_factor / 10.0, 1.0)
            base_probability *= (1.0 - prestige_factor * 0.3)
        
        return min(base_probability, 1.0)
    
    async def _get_next_deadline(self, db: Session, venue_id: str) -> Optional[datetime]:
        """Get the next submission deadline for a venue"""
        next_deadline = db.query(PublicationDeadline).filter(
            and_(
                PublicationDeadline.venue_id == venue_id,
                PublicationDeadline.deadline_date > datetime.now(),
                PublicationDeadline.is_active == True
            )
        ).order_by(PublicationDeadline.deadline_date).first()
        
        return next_deadline.deadline_date if next_deadline else None
    
    def _get_recommendation_strength(self, fit_score: float) -> str:
        """Get recommendation strength based on fit score"""
        if fit_score >= self.recommendation_thresholds['high']:
            return 'high'
        elif fit_score >= self.recommendation_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    async def _store_publication_matches(
        self,
        db: Session,
        user_id: str,
        paper_abstract: str,
        recommendations: List[VenueRecommendation]
    ):
        """Store publication matches in database"""
        try:
            # Remove existing matches for this user and abstract
            db.query(PublicationMatch).filter(
                and_(
                    PublicationMatch.user_id == user_id,
                    PublicationMatch.paper_abstract == paper_abstract
                )
            ).delete()
            
            # Add new matches
            for rec in recommendations:
                match = PublicationMatch(
                    user_id=user_id,
                    venue_id=rec.venue_id,
                    paper_abstract=paper_abstract,
                    relevance_score=rec.relevance_score,
                    match_reasons=rec.match_reasons,
                    fit_score=rec.fit_score,
                    success_probability=rec.success_probability,
                    recommendation_strength=rec.recommendation_strength,
                    match_metadata={
                        'impact_factor': rec.impact_factor,
                        'acceptance_rate': rec.acceptance_rate,
                        'next_deadline': rec.next_deadline.isoformat() if rec.next_deadline else None,
                        'average_review_time': rec.average_review_time
                    }
                )
                db.add(match)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing publication matches: {str(e)}")
            raise
    
    async def get_venue_rankings(
        self,
        research_area: Optional[str] = None,
        venue_type: Optional[str] = None,
        sort_by: str = 'impact_factor',
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get ranked list of publication venues
        
        Args:
            research_area: Filter by research area
            venue_type: Filter by venue type
            sort_by: Sort criteria ('impact_factor', 'acceptance_rate', 'h_index')
            limit: Maximum number of venues to return
            
        Returns:
            List of ranked venues
        """
        try:
            db = next(get_db())
            
            query = db.query(PublicationVenue).filter(
                PublicationVenue.is_active == True
            )
            
            if venue_type:
                query = query.filter(PublicationVenue.venue_type == venue_type)
            
            if research_area:
                # Filter by research area (this would need proper JSON querying in production)
                venues = query.all()
                filtered_venues = []
                for venue in venues:
                    if venue.research_areas and any(
                        research_area.lower() in area.lower() 
                        for area in venue.research_areas
                    ):
                        filtered_venues.append(venue)
                venues = filtered_venues
            else:
                venues = query.all()
            
            # Sort venues
            if sort_by == 'impact_factor':
                venues.sort(key=lambda x: x.impact_factor or 0, reverse=True)
            elif sort_by == 'acceptance_rate':
                venues.sort(key=lambda x: x.acceptance_rate or 0, reverse=True)
            elif sort_by == 'h_index':
                venues.sort(key=lambda x: x.h_index or 0, reverse=True)
            
            # Limit results
            venues = venues[:limit]
            
            # Format results
            results = []
            for venue in venues:
                next_deadline = await self._get_next_deadline(db, venue.id)
                
                results.append({
                    'id': venue.id,
                    'name': venue.name,
                    'venue_type': venue.venue_type,
                    'publisher': venue.publisher,
                    'impact_factor': venue.impact_factor,
                    'h_index': venue.h_index,
                    'acceptance_rate': venue.acceptance_rate,
                    'research_areas': venue.research_areas,
                    'open_access': venue.open_access,
                    'publication_fee': venue.publication_fee,
                    'average_review_time_days': venue.average_review_time_days,
                    'geographic_scope': venue.geographic_scope,
                    'website_url': venue.website_url,
                    'next_deadline': next_deadline.isoformat() if next_deadline else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting venue rankings: {str(e)}")
            raise
        finally:
            db.close()
    
    async def track_submission(
        self,
        user_id: str,
        venue_id: str,
        paper_title: str,
        paper_abstract: str,
        deadline_id: Optional[str] = None,
        submission_date: Optional[datetime] = None
    ) -> str:
        """
        Track a paper submission
        
        Args:
            user_id: User identifier
            venue_id: Venue identifier
            paper_title: Title of the paper
            paper_abstract: Abstract of the paper
            deadline_id: Associated deadline ID
            submission_date: Date of submission
            
        Returns:
            Submission tracker ID
        """
        try:
            db = next(get_db())
            
            submission = SubmissionTracker(
                user_id=user_id,
                venue_id=venue_id,
                paper_title=paper_title,
                paper_abstract=paper_abstract,
                deadline_id=deadline_id,
                submission_date=submission_date or datetime.now(),
                status='submitted'
            )
            
            db.add(submission)
            db.commit()
            db.refresh(submission)
            
            return submission.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error tracking submission: {str(e)}")
            raise
        finally:
            db.close()
    
    async def update_submission_status(
        self,
        submission_id: str,
        status: str,
        decision_date: Optional[datetime] = None,
        final_decision: Optional[str] = None,
        review_comments: Optional[str] = None
    ):
        """Update submission status"""
        try:
            db = next(get_db())
            
            submission = db.query(SubmissionTracker).filter(
                SubmissionTracker.id == submission_id
            ).first()
            
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            submission.status = status
            if decision_date:
                submission.decision_date = decision_date
            if final_decision:
                submission.final_decision = final_decision
            if review_comments:
                submission.review_comments = review_comments
            
            submission.updated_at = datetime.now()
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating submission status: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_user_submissions(
        self,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's submission history"""
        try:
            db = next(get_db())
            
            query = db.query(SubmissionTracker, PublicationVenue).join(
                PublicationVenue, SubmissionTracker.venue_id == PublicationVenue.id
            ).filter(SubmissionTracker.user_id == user_id)
            
            if status_filter:
                query = query.filter(SubmissionTracker.status == status_filter)
            
            submissions = query.order_by(
                desc(SubmissionTracker.submission_date)
            ).all()
            
            results = []
            for submission, venue in submissions:
                results.append({
                    'id': submission.id,
                    'paper_title': submission.paper_title,
                    'venue_name': venue.name,
                    'venue_type': venue.venue_type,
                    'submission_date': submission.submission_date,
                    'status': submission.status,
                    'decision_date': submission.decision_date,
                    'final_decision': submission.final_decision,
                    'review_comments': submission.review_comments,
                    'venue_impact_factor': venue.impact_factor,
                    'venue_acceptance_rate': venue.acceptance_rate
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user submissions: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_venue_analytics(self, venue_id: str) -> VenueAnalytics:
        """Get analytics for a specific venue"""
        try:
            db = next(get_db())
            
            venue = db.query(PublicationVenue).filter(
                PublicationVenue.id == venue_id
            ).first()
            
            if not venue:
                raise ValueError(f"Venue {venue_id} not found")
            
            # Get submission statistics
            total_submissions = db.query(SubmissionTracker).filter(
                SubmissionTracker.venue_id == venue_id
            ).count()
            
            accepted_submissions = db.query(SubmissionTracker).filter(
                and_(
                    SubmissionTracker.venue_id == venue_id,
                    SubmissionTracker.final_decision == 'accepted'
                )
            ).count()
            
            calculated_acceptance_rate = (
                (accepted_submissions / total_submissions * 100) 
                if total_submissions > 0 else venue.acceptance_rate or 0
            )
            
            # Calculate average review time from submissions
            review_times = db.query(SubmissionTracker).filter(
                and_(
                    SubmissionTracker.venue_id == venue_id,
                    SubmissionTracker.submission_date.isnot(None),
                    SubmissionTracker.decision_date.isnot(None)
                )
            ).all()
            
            avg_review_time = venue.average_review_time_days or 0
            if review_times:
                total_days = sum([
                    (sub.decision_date - sub.submission_date).days 
                    for sub in review_times
                ])
                avg_review_time = total_days / len(review_times)
            
            analytics = VenueAnalytics(
                venue_id=venue_id,
                name=venue.name,
                total_submissions=total_submissions,
                acceptance_rate=calculated_acceptance_rate,
                average_review_time=int(avg_review_time),
                impact_metrics={
                    'impact_factor': venue.impact_factor or 0,
                    'h_index': venue.h_index or 0,
                    'publication_fee': venue.publication_fee or 0
                },
                recent_trends={
                    'submission_trend': 'stable',  # This would be calculated from historical data
                    'acceptance_trend': 'stable'
                }
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting venue analytics: {str(e)}")
            raise
        finally:
            db.close()