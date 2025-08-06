"""
Spaced Repetition Service for Educational Enhancement System

This service implements a SuperMemo-based spaced repetition algorithm with adaptive scheduling
based on user performance and retention. It manages review sessions with optimal timing
calculations and provides performance analytics and retention rate tracking.
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core.database import get_db, SpacedRepetitionItem as SRItemModel, StudySession as StudySessionModel

logger = logging.getLogger(__name__)

class ReviewQuality(int, Enum):
    """Review quality ratings based on SuperMemo algorithm"""
    BLACKOUT = 0      # Complete blackout
    INCORRECT = 1     # Incorrect response with correct answer seeming familiar
    DIFFICULT = 2     # Correct response with serious difficulty
    HESITANT = 3      # Correct response with hesitation
    EASY = 4          # Correct response with some hesitation
    PERFECT = 5       # Perfect response

class ContentType(str, Enum):
    """Types of content that can be scheduled for review"""
    QUIZ_QUESTION = "quiz_question"
    CONCEPT = "concept"
    FACT = "fact"
    DEFINITION = "definition"
    FORMULA = "formula"

@dataclass
class SpacedRepetitionItem:
    """Represents an item in the spaced repetition system"""
    id: str
    user_id: str
    content_id: str
    content_type: ContentType
    difficulty: float = 2.5  # SuperMemo difficulty factor
    interval: int = 1  # Days until next review
    repetitions: int = 0
    ease_factor: float = 2.5  # SuperMemo ease factor
    next_review_date: datetime = None
    last_reviewed: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.next_review_date is None:
            self.next_review_date = datetime.now() + timedelta(days=self.interval)
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ReviewSession:
    """Represents a review session"""
    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    items_reviewed: List[str] = None
    performance_scores: List[float] = None
    session_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.items_reviewed is None:
            self.items_reviewed = []
        if self.performance_scores is None:
            self.performance_scores = []
        if self.session_metadata is None:
            self.session_metadata = {}

@dataclass
class PerformanceMetrics:
    """Performance metrics for spaced repetition"""
    total_reviews: int
    correct_reviews: int
    accuracy_rate: float
    average_ease_factor: float
    retention_rate: float
    streak_count: int
    last_review_date: Optional[datetime] = None

class SpacedRepetitionService:
    """Service for managing spaced repetition learning"""
    
    def __init__(self):
        # SuperMemo algorithm constants
        self.MIN_EASE_FACTOR = 1.3
        self.INITIAL_EASE_FACTOR = 2.5
        self.EASE_FACTOR_BONUS = 0.1
        self.EASE_FACTOR_PENALTY = 0.2
        self.MIN_INTERVAL = 1
        self.GRADUATION_INTERVAL = 4  # Days to graduate from learning phase

    async def add_item_to_review(
        self,
        user_id: str,
        content_id: str,
        content_type: ContentType,
        initial_difficulty: float = 2.5,
        metadata: Dict[str, Any] = None
    ) -> SpacedRepetitionItem:
        """Add a new item to the spaced repetition system"""
        try:
            item = SpacedRepetitionItem(
                id=f"sr_{content_type.value}_{content_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                difficulty=initial_difficulty,
                metadata=metadata or {}
            )
            
            await self._store_sr_item(item)
            logger.info(f"Added item {content_id} to spaced repetition for user {user_id}")
            return item
            
        except Exception as e:
            logger.error(f"Error adding item to spaced repetition: {str(e)}")
            raise

    async def get_due_items(
        self,
        user_id: str,
        limit: int = 20,
        content_types: List[ContentType] = None
    ) -> List[SpacedRepetitionItem]:
        """Get items that are due for review"""
        try:
            db = next(get_db())
            try:
                query = db.query(SRItemModel).filter(
                    SRItemModel.user_id == user_id,
                    SRItemModel.next_review_date <= datetime.now()
                )
                
                if content_types:
                    query = query.filter(SRItemModel.content_type.in_([ct.value for ct in content_types]))
                
                db_items = query.order_by(SRItemModel.next_review_date).limit(limit).all()
                
                items = []
                for db_item in db_items:
                    items.append(self._db_item_to_sr_item(db_item))
                
                logger.info(f"Found {len(items)} due items for user {user_id}")
                return items
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting due items: {str(e)}")
            return []

    async def record_review(
        self,
        item_id: str,
        user_id: str,
        quality: ReviewQuality,
        response_time_seconds: int = None
    ) -> SpacedRepetitionItem:
        """Record a review and update the item's scheduling"""
        try:
            # Get the current item
            item = await self.get_sr_item_by_id(item_id, user_id)
            if not item:
                raise ValueError(f"Spaced repetition item {item_id} not found")
            
            # Calculate new scheduling parameters using SuperMemo algorithm
            new_ease_factor, new_interval, new_repetitions = self._calculate_supermemo_parameters(
                current_ease_factor=item.ease_factor,
                current_interval=item.interval,
                current_repetitions=item.repetitions,
                quality=quality
            )
            
            # Update item
            item.ease_factor = new_ease_factor
            item.interval = new_interval
            item.repetitions = new_repetitions
            item.last_reviewed = datetime.now()
            item.next_review_date = datetime.now() + timedelta(days=new_interval)
            
            # Add review metadata
            if 'review_history' not in item.metadata:
                item.metadata['review_history'] = []
            
            item.metadata['review_history'].append({
                'date': datetime.now().isoformat(),
                'quality': quality.value,
                'response_time_seconds': response_time_seconds,
                'ease_factor': new_ease_factor,
                'interval': new_interval
            })
            
            # Update in database
            await self._update_sr_item(item)
            
            logger.info(f"Recorded review for item {item_id}: quality={quality.value}, new_interval={new_interval}")
            return item
            
        except Exception as e:
            logger.error(f"Error recording review: {str(e)}")
            raise

    async def start_review_session(self, user_id: str) -> ReviewSession:
        """Start a new review session"""
        try:
            session = ReviewSession(
                id=f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                started_at=datetime.now()
            )
            
            await self._store_review_session(session)
            logger.info(f"Started review session {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error starting review session: {str(e)}")
            raise

    async def end_review_session(
        self,
        session_id: str,
        user_id: str,
        items_reviewed: List[str],
        performance_scores: List[float]
    ) -> ReviewSession:
        """End a review session and record performance"""
        try:
            session = await self.get_review_session(session_id, user_id)
            if not session:
                raise ValueError(f"Review session {session_id} not found")
            
            session.ended_at = datetime.now()
            session.items_reviewed = items_reviewed
            session.performance_scores = performance_scores
            
            # Calculate session statistics
            session.session_metadata.update({
                'duration_minutes': (session.ended_at - session.started_at).total_seconds() / 60,
                'items_count': len(items_reviewed),
                'average_score': sum(performance_scores) / len(performance_scores) if performance_scores else 0,
                'accuracy_rate': len([s for s in performance_scores if s >= 3]) / len(performance_scores) if performance_scores else 0
            })
            
            await self._update_review_session(session)
            logger.info(f"Ended review session {session_id} with {len(items_reviewed)} items reviewed")
            return session
            
        except Exception as e:
            logger.error(f"Error ending review session: {str(e)}")
            raise

    async def get_performance_metrics(self, user_id: str, days_back: int = 30) -> PerformanceMetrics:
        """Get performance metrics for a user"""
        try:
            db = next(get_db())
            try:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                # Get all items for user (not just recently reviewed ones)
                all_items = db.query(SRItemModel).filter(SRItemModel.user_id == user_id).all()
                
                if not all_items:
                    return PerformanceMetrics(
                        total_reviews=0,
                        correct_reviews=0,
                        accuracy_rate=0.0,
                        average_ease_factor=self.INITIAL_EASE_FACTOR,
                        retention_rate=0.0,
                        streak_count=0
                    )
                
                # Calculate metrics
                total_reviews = 0
                correct_reviews = 0
                ease_factors = []
                last_review_date = None
                items_with_recent_reviews = 0
                
                for item in all_items:
                    ease_factors.append(item.ease_factor)
                    
                    if item.sr_metadata and 'review_history' in item.sr_metadata:
                        reviews = item.sr_metadata['review_history']
                        has_recent_review = False
                        
                        for review in reviews:
                            review_date = datetime.fromisoformat(review['date'])
                            if review_date >= cutoff_date:
                                total_reviews += 1
                                has_recent_review = True
                                if review['quality'] >= 3:  # Correct threshold
                                    correct_reviews += 1
                                
                                if not last_review_date or review_date > last_review_date:
                                    last_review_date = review_date
                        
                        if has_recent_review:
                            items_with_recent_reviews += 1
                
                accuracy_rate = correct_reviews / total_reviews if total_reviews > 0 else 0.0
                average_ease_factor = sum(ease_factors) / len(ease_factors) if ease_factors else self.INITIAL_EASE_FACTOR
                
                # Enhanced retention rate calculation
                # Items with ease factor >= initial are considered "retained"
                # Also consider items that haven't been reviewed recently but have high ease factors
                retained_items = 0
                for item in all_items:
                    if item.ease_factor >= self.INITIAL_EASE_FACTOR:
                        retained_items += 1
                    elif item.repetitions >= 3 and item.ease_factor >= self.MIN_EASE_FACTOR + 0.3:
                        # Items that have been reviewed multiple times and maintain decent ease factor
                        retained_items += 1
                
                retention_rate = retained_items / len(all_items) if all_items else 0.0
                
                # Calculate streak (consecutive days with reviews)
                streak_count = await self._calculate_review_streak(user_id)
                
                return PerformanceMetrics(
                    total_reviews=total_reviews,
                    correct_reviews=correct_reviews,
                    accuracy_rate=accuracy_rate,
                    average_ease_factor=average_ease_factor,
                    retention_rate=retention_rate,
                    streak_count=streak_count,
                    last_review_date=last_review_date
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return PerformanceMetrics(
                total_reviews=0,
                correct_reviews=0,
                accuracy_rate=0.0,
                average_ease_factor=self.INITIAL_EASE_FACTOR,
                retention_rate=0.0,
                streak_count=0
            )

    async def get_review_schedule(self, user_id: str, days_ahead: int = 7) -> Dict[str, List[SpacedRepetitionItem]]:
        """Get review schedule for upcoming days"""
        try:
            db = next(get_db())
            try:
                end_date = datetime.now() + timedelta(days=days_ahead)
                
                items = db.query(SRItemModel).filter(
                    SRItemModel.user_id == user_id,
                    SRItemModel.next_review_date <= end_date
                ).order_by(SRItemModel.next_review_date).all()
                
                # Group by date
                schedule = {}
                for item in items:
                    date_key = item.next_review_date.date().isoformat()
                    if date_key not in schedule:
                        schedule[date_key] = []
                    schedule[date_key].append(self._db_item_to_sr_item(item))
                
                return schedule
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting review schedule: {str(e)}")
            return {}

    async def optimize_review_timing(self, user_id: str) -> Dict[str, Any]:
        """Optimize review timing based on user performance patterns"""
        try:
            # Get user's performance metrics
            metrics = await self.get_performance_metrics(user_id)
            
            # Get all user's items
            db = next(get_db())
            try:
                items = db.query(SRItemModel).filter(SRItemModel.user_id == user_id).all()
                
                optimizations = {
                    'total_items': len(items),
                    'adjustments_made': 0,
                    'recommendations': [],
                    'performance_analysis': {
                        'high_performers': 0,
                        'struggling_items': 0,
                        'stable_items': 0,
                        'new_items': 0
                    },
                    'timing_adjustments': {
                        'ease_factor_increases': 0,
                        'ease_factor_decreases': 0,
                        'interval_adjustments': 0
                    }
                }
                
                for item in items:
                    # Analyze item performance
                    if item.sr_metadata and 'review_history' in item.sr_metadata:
                        reviews = item.sr_metadata['review_history']
                        recent_reviews = reviews[-5:]  # Last 5 reviews
                        
                        if len(recent_reviews) >= 3:
                            recent_qualities = [r['quality'] for r in recent_reviews]
                            avg_quality = sum(recent_qualities) / len(recent_qualities)
                            quality_variance = sum((q - avg_quality) ** 2 for q in recent_qualities) / len(recent_qualities)
                            
                            # Advanced performance analysis
                            if avg_quality >= 4.0 and quality_variance < 0.5:
                                # Consistently high performance with low variance
                                optimizations['performance_analysis']['high_performers'] += 1
                                if item.ease_factor < 3.5:
                                    new_ease_factor = min(3.5, item.ease_factor + 0.15)
                                    await self._update_item_ease_factor(item.id, new_ease_factor)
                                    optimizations['adjustments_made'] += 1
                                    optimizations['timing_adjustments']['ease_factor_increases'] += 1
                                    optimizations['recommendations'].append(
                                        f"Increased ease factor for item {item.content_id} to {new_ease_factor:.2f} due to consistent excellent performance"
                                    )
                            
                            elif avg_quality <= 2.5 and item.ease_factor > self.MIN_EASE_FACTOR:
                                # Consistently poor performance
                                optimizations['performance_analysis']['struggling_items'] += 1
                                new_ease_factor = max(self.MIN_EASE_FACTOR, item.ease_factor - 0.2)
                                await self._update_item_ease_factor(item.id, new_ease_factor)
                                optimizations['adjustments_made'] += 1
                                optimizations['timing_adjustments']['ease_factor_decreases'] += 1
                                optimizations['recommendations'].append(
                                    f"Decreased ease factor for item {item.content_id} to {new_ease_factor:.2f} due to consistent difficulty"
                                )
                                
                                # Also adjust interval if it's too long
                                if item.interval > 7:
                                    new_interval = max(3, item.interval // 2)
                                    await self._update_item_interval(item.id, new_interval)
                                    optimizations['timing_adjustments']['interval_adjustments'] += 1
                                    optimizations['recommendations'].append(
                                        f"Reduced interval for struggling item {item.content_id} to {new_interval} days"
                                    )
                            
                            elif quality_variance > 1.0:
                                # High variance in performance - needs stabilization
                                if item.ease_factor > 2.0:
                                    new_ease_factor = max(2.0, item.ease_factor - 0.1)
                                    await self._update_item_ease_factor(item.id, new_ease_factor)
                                    optimizations['adjustments_made'] += 1
                                    optimizations['timing_adjustments']['ease_factor_decreases'] += 1
                                    optimizations['recommendations'].append(
                                        f"Stabilized ease factor for inconsistent item {item.content_id} to {new_ease_factor:.2f}"
                                    )
                            
                            else:
                                optimizations['performance_analysis']['stable_items'] += 1
                        
                        elif len(reviews) < 3:
                            optimizations['performance_analysis']['new_items'] += 1
                    else:
                        optimizations['performance_analysis']['new_items'] += 1
                
                # Add adaptive scheduling recommendations
                if metrics.accuracy_rate < 0.7:
                    optimizations['recommendations'].append(
                        "Consider reducing daily review load to improve focus and retention"
                    )
                elif metrics.accuracy_rate > 0.9:
                    optimizations['recommendations'].append(
                        "Excellent performance! Consider adding more challenging content"
                    )
                
                # Retention-based recommendations
                if metrics.retention_rate < 0.6:
                    optimizations['recommendations'].append(
                        "Low retention detected. Consider more frequent reviews for struggling items"
                    )
                
                return optimizations
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error optimizing review timing: {str(e)}")
            return {'error': str(e)}

    def _calculate_supermemo_parameters(
        self,
        current_ease_factor: float,
        current_interval: int,
        current_repetitions: int,
        quality: ReviewQuality
    ) -> Tuple[float, int, int]:
        """Calculate new SuperMemo parameters based on review quality"""
        
        # Update ease factor
        new_ease_factor = current_ease_factor
        if quality.value >= 3:
            new_ease_factor = current_ease_factor + (0.1 - (5 - quality.value) * (0.08 + (5 - quality.value) * 0.02))
        else:
            new_ease_factor = current_ease_factor - 0.2
        
        # Ensure ease factor stays within bounds
        new_ease_factor = max(self.MIN_EASE_FACTOR, new_ease_factor)
        
        # Update repetitions and interval
        if quality.value < 3:
            # Reset if quality is poor
            new_repetitions = 0
            new_interval = self.MIN_INTERVAL
        else:
            new_repetitions = current_repetitions + 1
            
            if new_repetitions == 1:
                new_interval = 1
            elif new_repetitions == 2:
                new_interval = 6
            else:
                new_interval = int(current_interval * new_ease_factor)
        
        # Ensure minimum interval
        new_interval = max(self.MIN_INTERVAL, new_interval)
        
        return new_ease_factor, new_interval, new_repetitions

    async def _store_sr_item(self, item: SpacedRepetitionItem):
        """Store spaced repetition item in database"""
        try:
            db = next(get_db())
            try:
                db_item = SRItemModel(
                    id=item.id,
                    user_id=item.user_id,
                    content_id=item.content_id,
                    content_type=item.content_type.value,
                    difficulty=item.difficulty,
                    interval=item.interval,
                    repetitions=item.repetitions,
                    ease_factor=item.ease_factor,
                    next_review_date=item.next_review_date,
                    last_reviewed=item.last_reviewed,
                    sr_metadata=item.metadata
                )
                db.add(db_item)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error storing SR item: {str(e)}")
            raise

    async def _update_sr_item(self, item: SpacedRepetitionItem):
        """Update spaced repetition item in database"""
        try:
            db = next(get_db())
            try:
                db_item = db.query(SRItemModel).filter(SRItemModel.id == item.id).first()
                if db_item:
                    db_item.difficulty = item.difficulty
                    db_item.interval = item.interval
                    db_item.repetitions = item.repetitions
                    db_item.ease_factor = item.ease_factor
                    db_item.next_review_date = item.next_review_date
                    db_item.last_reviewed = item.last_reviewed
                    db_item.sr_metadata = item.metadata
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating SR item: {str(e)}")
            raise

    async def get_sr_item_by_id(self, item_id: str, user_id: str) -> Optional[SpacedRepetitionItem]:
        """Get spaced repetition item by ID"""
        try:
            db = next(get_db())
            try:
                db_item = db.query(SRItemModel).filter(
                    SRItemModel.id == item_id,
                    SRItemModel.user_id == user_id
                ).first()
                
                if db_item:
                    return self._db_item_to_sr_item(db_item)
                return None
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting SR item: {str(e)}")
            return None

    def _db_item_to_sr_item(self, db_item: SRItemModel) -> SpacedRepetitionItem:
        """Convert database item to SpacedRepetitionItem"""
        return SpacedRepetitionItem(
            id=db_item.id,
            user_id=db_item.user_id,
            content_id=db_item.content_id,
            content_type=ContentType(db_item.content_type),
            difficulty=db_item.difficulty,
            interval=db_item.interval,
            repetitions=db_item.repetitions,
            ease_factor=db_item.ease_factor,
            next_review_date=db_item.next_review_date,
            last_reviewed=db_item.last_reviewed,
            metadata=db_item.sr_metadata or {}
        )

    async def _store_review_session(self, session: ReviewSession):
        """Store review session in database"""
        try:
            db = next(get_db())
            try:
                db_session = StudySessionModel(
                    id=session.id,
                    user_id=session.user_id,
                    session_type="spaced_repetition",
                    started_at=session.started_at,
                    ended_at=session.ended_at,
                    items_studied=len(session.items_reviewed),
                    performance_score=sum(session.performance_scores) / len(session.performance_scores) if session.performance_scores else 0,
                    session_metadata=session.session_metadata
                )
                db.add(db_session)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error storing review session: {str(e)}")
            raise

    async def _update_review_session(self, session: ReviewSession):
        """Update review session in database"""
        try:
            db = next(get_db())
            try:
                db_session = db.query(StudySessionModel).filter(StudySessionModel.id == session.id).first()
                if db_session:
                    db_session.ended_at = session.ended_at
                    db_session.items_studied = len(session.items_reviewed)
                    db_session.performance_score = sum(session.performance_scores) / len(session.performance_scores) if session.performance_scores else 0
                    db_session.session_metadata = session.session_metadata
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating review session: {str(e)}")
            raise

    async def get_review_session(self, session_id: str, user_id: str) -> Optional[ReviewSession]:
        """Get review session by ID"""
        try:
            db = next(get_db())
            try:
                db_session = db.query(StudySessionModel).filter(
                    StudySessionModel.id == session_id,
                    StudySessionModel.user_id == user_id
                ).first()
                
                if db_session:
                    return ReviewSession(
                        id=db_session.id,
                        user_id=db_session.user_id,
                        started_at=db_session.started_at,
                        ended_at=db_session.ended_at,
                        items_reviewed=[],  # Would need to store this separately
                        performance_scores=[],  # Would need to store this separately
                        session_metadata=db_session.session_metadata or {}
                    )
                return None
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting review session: {str(e)}")
            return None

    async def _calculate_review_streak(self, user_id: str) -> int:
        """Calculate consecutive days with reviews"""
        try:
            db = next(get_db())
            try:
                # Get review sessions ordered by date
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id,
                    StudySessionModel.session_type == "spaced_repetition"
                ).order_by(StudySessionModel.started_at.desc()).all()
                
                if not sessions:
                    return 0
                
                streak = 0
                current_date = datetime.now().date()
                
                # Check each day backwards
                for i in range(365):  # Max 1 year streak
                    check_date = current_date - timedelta(days=i)
                    
                    # Check if there's a session on this date
                    has_session = any(
                        session.started_at.date() == check_date 
                        for session in sessions
                    )
                    
                    if has_session:
                        streak += 1
                    else:
                        break
                
                return streak
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error calculating review streak: {str(e)}")
            return 0

    async def _update_item_ease_factor(self, item_id: str, new_ease_factor: float):
        """Update ease factor for a specific item"""
        try:
            db = next(get_db())
            try:
                db_item = db.query(SRItemModel).filter(SRItemModel.id == item_id).first()
                if db_item:
                    db_item.ease_factor = new_ease_factor
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating ease factor: {str(e)}")
            raise

    async def _update_item_interval(self, item_id: str, new_interval: int):
        """Update interval for a specific item"""
        try:
            db = next(get_db())
            try:
                db_item = db.query(SRItemModel).filter(SRItemModel.id == item_id).first()
                if db_item:
                    db_item.interval = new_interval
                    db_item.next_review_date = datetime.now() + timedelta(days=new_interval)
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating interval: {str(e)}")
            raise

    async def get_optimal_session_timing(self, user_id: str) -> Dict[str, Any]:
        """Calculate optimal session timing based on user patterns and performance"""
        try:
            db = next(get_db())
            try:
                # Get user's session history
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id,
                    StudySessionModel.session_type == "spaced_repetition",
                    StudySessionModel.ended_at.isnot(None)
                ).order_by(StudySessionModel.started_at.desc()).limit(30).all()
                
                if not sessions:
                    return {
                        'recommended_session_length': 20,  # Default 20 minutes
                        'recommended_items_per_session': 15,
                        'optimal_time_of_day': 'morning',
                        'confidence': 'low',
                        'reasoning': 'No session history available, using defaults'
                    }
                
                # Analyze session patterns
                session_durations = []
                session_performances = []
                session_times = []
                items_per_session = []
                
                for session in sessions:
                    if session.ended_at and session.started_at:
                        duration = (session.ended_at - session.started_at).total_seconds() / 60
                        session_durations.append(duration)
                        session_performances.append(session.performance_score or 0)
                        session_times.append(session.started_at.hour)
                        items_per_session.append(session.items_studied or 0)
                
                # Find optimal session length (best performance vs duration)
                optimal_duration = 20  # Default
                if session_durations and session_performances:
                    # Group by duration ranges and find best performing range
                    duration_performance = {}
                    for duration, performance in zip(session_durations, session_performances):
                        duration_range = int(duration // 10) * 10  # Group by 10-minute ranges
                        if duration_range not in duration_performance:
                            duration_performance[duration_range] = []
                        duration_performance[duration_range].append(performance)
                    
                    # Find range with best average performance
                    best_range = max(duration_performance.keys(), 
                                   key=lambda x: sum(duration_performance[x]) / len(duration_performance[x]))
                    optimal_duration = min(max(best_range + 5, 10), 45)  # Cap between 10-45 minutes
                
                # Find optimal items per session
                optimal_items = 15  # Default
                if items_per_session and session_performances:
                    # Find correlation between items and performance
                    items_performance = {}
                    for items, performance in zip(items_per_session, session_performances):
                        items_range = int(items // 5) * 5  # Group by 5-item ranges
                        if items_range not in items_performance:
                            items_performance[items_range] = []
                        items_performance[items_range].append(performance)
                    
                    if items_performance:
                        best_items_range = max(items_performance.keys(),
                                             key=lambda x: sum(items_performance[x]) / len(items_performance[x]))
                        optimal_items = min(max(best_items_range + 2, 5), 30)  # Cap between 5-30 items
                
                # Find optimal time of day
                optimal_time = 'morning'  # Default
                if session_times and session_performances:
                    time_performance = {}
                    for time_hour, performance in zip(session_times, session_performances):
                        time_period = self._get_time_period(time_hour)
                        if time_period not in time_performance:
                            time_performance[time_period] = []
                        time_performance[time_period].append(performance)
                    
                    if time_performance:
                        optimal_time = max(time_performance.keys(),
                                         key=lambda x: sum(time_performance[x]) / len(time_performance[x]))
                
                # Calculate confidence based on data availability
                confidence = 'high' if len(sessions) >= 10 else 'medium' if len(sessions) >= 5 else 'low'
                
                return {
                    'recommended_session_length': optimal_duration,
                    'recommended_items_per_session': optimal_items,
                    'optimal_time_of_day': optimal_time,
                    'confidence': confidence,
                    'reasoning': f'Based on analysis of {len(sessions)} recent sessions',
                    'session_analysis': {
                        'average_duration': sum(session_durations) / len(session_durations) if session_durations else 0,
                        'average_performance': sum(session_performances) / len(session_performances) if session_performances else 0,
                        'sessions_analyzed': len(sessions)
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error calculating optimal session timing: {str(e)}")
            return {'error': str(e)}

    def _get_time_period(self, hour: int) -> str:
        """Convert hour to time period"""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

    async def get_advanced_retention_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get advanced retention analytics with forgetting curves and predictions"""
        try:
            db = next(get_db())
            try:
                items = db.query(SRItemModel).filter(SRItemModel.user_id == user_id).all()
                
                if not items:
                    return {'error': 'No items found for analysis'}
                
                analytics = {
                    'forgetting_curve_analysis': {},
                    'retention_by_content_type': {},
                    'difficulty_progression': {},
                    'predicted_retention': {},
                    'recommendations': []
                }
                
                # Analyze forgetting curves by content type
                content_type_data = {}
                for item in items:
                    ct = item.content_type
                    if ct not in content_type_data:
                        content_type_data[ct] = {'items': [], 'reviews': []}
                    
                    content_type_data[ct]['items'].append(item)
                    
                    if item.sr_metadata and 'review_history' in item.sr_metadata:
                        content_type_data[ct]['reviews'].extend(item.sr_metadata['review_history'])
                
                # Calculate retention rates by content type
                for ct, data in content_type_data.items():
                    items_list = data['items']
                    reviews = data['reviews']
                    
                    if items_list:
                        avg_ease_factor = sum(item.ease_factor for item in items_list) / len(items_list)
                        retention_rate = len([item for item in items_list if item.ease_factor >= self.INITIAL_EASE_FACTOR]) / len(items_list)
                        
                        analytics['retention_by_content_type'][ct] = {
                            'item_count': len(items_list),
                            'average_ease_factor': avg_ease_factor,
                            'retention_rate': retention_rate,
                            'total_reviews': len(reviews)
                        }
                
                # Analyze difficulty progression over time
                all_reviews = []
                for item in items:
                    if item.sr_metadata and 'review_history' in item.sr_metadata:
                        for review in item.sr_metadata['review_history']:
                            review['content_type'] = item.content_type
                            all_reviews.append(review)
                
                # Sort reviews by date
                all_reviews.sort(key=lambda x: x['date'])
                
                # Calculate moving average of performance
                if len(all_reviews) >= 10:
                    window_size = min(10, len(all_reviews) // 3)
                    moving_avg = []
                    for i in range(window_size, len(all_reviews)):
                        window_reviews = all_reviews[i-window_size:i]
                        avg_quality = sum(r['quality'] for r in window_reviews) / len(window_reviews)
                        moving_avg.append({
                            'date': all_reviews[i]['date'],
                            'average_quality': avg_quality
                        })
                    
                    analytics['difficulty_progression'] = {
                        'trend': 'improving' if moving_avg[-1]['average_quality'] > moving_avg[0]['average_quality'] else 'declining',
                        'data_points': len(moving_avg),
                        'latest_average': moving_avg[-1]['average_quality'] if moving_avg else 0
                    }
                
                # Predict future retention
                current_time = datetime.now()
                future_predictions = {}
                
                for days_ahead in [7, 14, 30]:
                    future_date = current_time + timedelta(days=days_ahead)
                    items_due = [item for item in items if item.next_review_date <= future_date]
                    
                    # Estimate retention based on ease factors and intervals
                    predicted_retention = 0
                    for item in items_due:
                        # Simple retention prediction based on ease factor and time since last review
                        if item.last_reviewed:
                            days_since_review = (current_time - item.last_reviewed).days
                            retention_probability = min(1.0, item.ease_factor / 2.5 * (1 - days_since_review / (item.interval * 2)))
                            predicted_retention += max(0, retention_probability)
                    
                    future_predictions[f'{days_ahead}_days'] = {
                        'items_due': len(items_due),
                        'predicted_retention_rate': predicted_retention / len(items_due) if items_due else 0
                    }
                
                analytics['predicted_retention'] = future_predictions
                
                # Generate recommendations
                if analytics['retention_by_content_type']:
                    worst_performing_type = min(analytics['retention_by_content_type'].keys(),
                                              key=lambda x: analytics['retention_by_content_type'][x]['retention_rate'])
                    analytics['recommendations'].append(
                        f"Focus on {worst_performing_type} content - showing lowest retention rate"
                    )
                
                if analytics['difficulty_progression'].get('trend') == 'declining':
                    analytics['recommendations'].append(
                        "Performance trend is declining - consider reducing session difficulty or frequency"
                    )
                
                return analytics
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting advanced retention analytics: {str(e)}")
            return {'error': str(e)}

    async def get_user_sr_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive spaced repetition statistics for user"""
        try:
            db = next(get_db())
            try:
                # Get all items
                items = db.query(SRItemModel).filter(SRItemModel.user_id == user_id).all()
                
                # Get sessions
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id,
                    StudySessionModel.session_type == "spaced_repetition"
                ).all()
                
                # Calculate statistics
                total_items = len(items)
                due_items = len([item for item in items if item.next_review_date <= datetime.now()])
                overdue_items = len([item for item in items if item.next_review_date < datetime.now() - timedelta(days=1)])
                
                # Content type distribution
                content_type_dist = {}
                for item in items:
                    content_type_dist[item.content_type] = content_type_dist.get(item.content_type, 0) + 1
                
                # Average ease factor
                avg_ease_factor = sum(item.ease_factor for item in items) / len(items) if items else self.INITIAL_EASE_FACTOR
                
                # Session statistics
                total_sessions = len(sessions)
                total_study_time = sum(
                    (session.ended_at - session.started_at).total_seconds() / 60
                    for session in sessions if session.ended_at
                )
                
                # Advanced statistics
                mature_items = len([item for item in items if item.repetitions >= 3])
                learning_items = len([item for item in items if item.repetitions < 3])
                
                # Interval distribution
                interval_dist = {}
                for item in items:
                    interval_range = f"{item.interval}-{item.interval + 6}" if item.interval < 30 else "30+"
                    interval_dist[interval_range] = interval_dist.get(interval_range, 0) + 1
                
                return {
                    'total_items': total_items,
                    'due_items': due_items,
                    'overdue_items': overdue_items,
                    'mature_items': mature_items,
                    'learning_items': learning_items,
                    'content_type_distribution': content_type_dist,
                    'interval_distribution': interval_dist,
                    'average_ease_factor': avg_ease_factor,
                    'total_sessions': total_sessions,
                    'total_study_time_minutes': total_study_time,
                    'average_session_duration': total_study_time / total_sessions if total_sessions > 0 else 0,
                    'streak_count': await self._calculate_review_streak(user_id),
                    'generated_at': datetime.now().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting SR stats: {str(e)}")
            return {'error': str(e)}