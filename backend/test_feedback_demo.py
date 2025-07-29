"""
Demo script for Feedback Processing System

This script demonstrates the feedback processing capabilities including:
- Thumbs up/down feedback collection
- Detailed rating feedback
- Correction feedback processing
- Preference feedback handling
- Feedback analysis and trends
- System improvement cycles
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from core.database import Base, get_db
from core.config import settings
from services.feedback_processor import FeedbackProcessor, FeedbackAnalyzer, FeedbackLoop
from services.user_profile_service import UserProfileManager
from models.schemas import FeedbackType, UserPreferences
from core.database import User, Message, Conversation, UserProfile, UserFeedback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackProcessingDemo:
    """Demo class for feedback processing system."""
    
    def __init__(self):
        """Initialize demo with database connection."""
        self.engine = create_engine(settings.DATABASE_URL, echo=False)
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        self.feedback_processor = FeedbackProcessor(self.db)
        self.feedback_analyzer = FeedbackAnalyzer(self.db)
        self.feedback_loop = FeedbackLoop(self.db)
        self.profile_manager = UserProfileManager(self.db)
    
    async def setup_demo_data(self):
        """Set up demo users, conversations, and messages."""
        try:
            logger.info("Setting up demo data...")
            
            # Create demo users
            demo_users = [
                User(
                    id="demo-user-1",
                    email="alice@example.com",
                    name="Alice Johnson",
                    hashed_password="hashed_password_1",
                    is_active=True
                ),
                User(
                    id="demo-user-2", 
                    email="bob@example.com",
                    name="Bob Smith",
                    hashed_password="hashed_password_2",
                    is_active=True
                )
            ]
            
            for user in demo_users:
                existing_user = self.db.query(User).filter(User.id == user.id).first()
                if not existing_user:
                    self.db.add(user)
            
            # Create demo conversations
            demo_conversations = [
                Conversation(
                    id="demo-conv-1",
                    user_id="demo-user-1",
                    title="Machine Learning Discussion"
                ),
                Conversation(
                    id="demo-conv-2",
                    user_id="demo-user-2",
                    title="Data Science Questions"
                )
            ]
            
            for conv in demo_conversations:
                existing_conv = self.db.query(Conversation).filter(Conversation.id == conv.id).first()
                if not existing_conv:
                    self.db.add(conv)
            
            # Create demo messages
            demo_messages = [
                Message(
                    id="demo-msg-1",
                    conversation_id="demo-conv-1",
                    role="user",
                    content="What is machine learning?"
                ),
                Message(
                    id="demo-msg-2",
                    conversation_id="demo-conv-1",
                    role="assistant",
                    content="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                    sources=json.dumps([
                        {"document_id": "doc-1", "relevance": 0.9, "snippet": "ML definition"},
                        {"document_id": "doc-2", "relevance": 0.7, "snippet": "AI overview"}
                    ])
                ),
                Message(
                    id="demo-msg-3",
                    conversation_id="demo-conv-2",
                    role="user",
                    content="How does deep learning work?"
                ),
                Message(
                    id="demo-msg-4",
                    conversation_id="demo-conv-2",
                    role="assistant",
                    content="Deep learning uses neural networks with multiple layers to process data and extract patterns.",
                    sources=json.dumps([
                        {"document_id": "doc-3", "relevance": 0.8, "snippet": "Deep learning basics"}
                    ])
                )
            ]
            
            for msg in demo_messages:
                existing_msg = self.db.query(Message).filter(Message.id == msg.id).first()
                if not existing_msg:
                    self.db.add(msg)
            
            # Create user profiles
            await self.profile_manager.create_user_profile(
                user_id="demo-user-1",
                preferences=UserPreferences(
                    response_style="detailed",
                    domain_focus=["technology", "science"],
                    reasoning_display=True
                )
            )
            
            await self.profile_manager.create_user_profile(
                user_id="demo-user-2",
                preferences=UserPreferences(
                    response_style="concise",
                    domain_focus=["business", "technology"],
                    reasoning_display=False
                )
            )
            
            self.db.commit()
            logger.info("Demo data setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up demo data: {str(e)}")
            self.db.rollback()
            raise
    
    async def demo_thumbs_feedback(self):
        """Demonstrate thumbs up/down feedback processing."""
        logger.info("\n=== Thumbs Feedback Demo ===")
        
        try:
            # Positive thumbs feedback
            logger.info("Processing thumbs up feedback...")
            thumbs_up = await self.feedback_processor.process_thumbs_feedback(
                user_id="demo-user-1",
                message_id="demo-msg-2",
                is_positive=True,
                context={"query": "What is machine learning?"}
            )
            
            logger.info(f"Thumbs up processed: {thumbs_up.id}")
            logger.info(f"Rating: {thumbs_up.feedback_value['rating']}")
            
            # Negative thumbs feedback
            logger.info("Processing thumbs down feedback...")
            thumbs_down = await self.feedback_processor.process_thumbs_feedback(
                user_id="demo-user-2",
                message_id="demo-msg-4",
                is_positive=False,
                context={"query": "How does deep learning work?"}
            )
            
            logger.info(f"Thumbs down processed: {thumbs_down.id}")
            logger.info(f"Rating: {thumbs_down.feedback_value['rating']}")
            
        except Exception as e:
            logger.error(f"Error in thumbs feedback demo: {str(e)}")
    
    async def demo_detailed_rating(self):
        """Demonstrate detailed rating feedback processing."""
        logger.info("\n=== Detailed Rating Demo ===")
        
        try:
            # High-quality detailed rating
            logger.info("Processing detailed positive rating...")
            detailed_rating = await self.feedback_processor.process_detailed_rating(
                user_id="demo-user-1",
                message_id="demo-msg-2",
                rating=0.9,
                aspects={
                    "accuracy": 0.95,
                    "relevance": 0.9,
                    "completeness": 0.85,
                    "clarity": 0.9
                },
                comment="Excellent explanation of machine learning concepts!",
                context={"response_time": 2.3, "sources_count": 2}
            )
            
            logger.info(f"Detailed rating processed: {detailed_rating.id}")
            logger.info(f"Overall rating: {detailed_rating.feedback_value['rating']}")
            logger.info(f"Aspects: {detailed_rating.feedback_value['aspects']}")
            
            # Poor quality detailed rating
            logger.info("Processing detailed negative rating...")
            poor_rating = await self.feedback_processor.process_detailed_rating(
                user_id="demo-user-2",
                message_id="demo-msg-4",
                rating=0.4,
                aspects={
                    "accuracy": 0.6,
                    "relevance": 0.3,
                    "completeness": 0.2,
                    "clarity": 0.5
                },
                comment="Response was too vague and didn't answer my specific question.",
                context={"response_time": 1.8, "sources_count": 1}
            )
            
            logger.info(f"Poor rating processed: {poor_rating.id}")
            logger.info(f"Overall rating: {poor_rating.feedback_value['rating']}")
            logger.info(f"Poor aspects: {[k for k, v in poor_rating.feedback_value['aspects'].items() if v < 0.5]}")
            
        except Exception as e:
            logger.error(f"Error in detailed rating demo: {str(e)}")
    
    async def demo_correction_feedback(self):
        """Demonstrate correction feedback processing."""
        logger.info("\n=== Correction Feedback Demo ===")
        
        try:
            # Factual correction
            logger.info("Processing factual correction...")
            correction = await self.feedback_processor.process_feedback(
                user_id="demo-user-1",
                feedback_type=FeedbackType.CORRECTION,
                feedback_value={
                    "correction": "Machine learning is actually a subset of AI, not the other way around.",
                    "original": "AI is a subset of machine learning",
                    "type": "factual"
                },
                message_id="demo-msg-2",
                context={"correction_confidence": 0.9}
            )
            
            logger.info(f"Correction processed: {correction.id}")
            logger.info(f"Correction type: {correction.feedback_value['type']}")
            
            # Formatting correction
            logger.info("Processing formatting correction...")
            format_correction = await self.feedback_processor.process_feedback(
                user_id="demo-user-2",
                feedback_type=FeedbackType.CORRECTION,
                feedback_value={
                    "correction": "Please use bullet points for better readability",
                    "original": "Long paragraph format",
                    "type": "formatting"
                },
                message_id="demo-msg-4"
            )
            
            logger.info(f"Format correction processed: {format_correction.id}")
            
        except Exception as e:
            logger.error(f"Error in correction feedback demo: {str(e)}")
    
    async def demo_preference_feedback(self):
        """Demonstrate preference feedback processing."""
        logger.info("\n=== Preference Feedback Demo ===")
        
        try:
            # Response style preference
            logger.info("Processing response style preference...")
            style_pref = await self.feedback_processor.process_feedback(
                user_id="demo-user-1",
                feedback_type=FeedbackType.PREFERENCE,
                feedback_value={
                    "type": "response_style",
                    "value": "concise",
                    "strength": 0.8
                },
                context={"trigger": "user_request"}
            )
            
            logger.info(f"Style preference processed: {style_pref.id}")
            
            # Domain focus preference
            logger.info("Processing domain focus preference...")
            domain_pref = await self.feedback_processor.process_feedback(
                user_id="demo-user-2",
                feedback_type=FeedbackType.PREFERENCE,
                feedback_value={
                    "type": "domain_focus",
                    "value": ["machine_learning", "data_science"],
                    "strength": 0.9
                },
                context={"inferred_from": "query_patterns"}
            )
            
            logger.info(f"Domain preference processed: {domain_pref.id}")
            
            # Citation format preference
            logger.info("Processing citation preference...")
            citation_pref = await self.feedback_processor.process_feedback(
                user_id="demo-user-1",
                feedback_type=FeedbackType.PREFERENCE,
                feedback_value={
                    "type": "citation_format",
                    "value": "footnote",
                    "strength": 0.7
                }
            )
            
            logger.info(f"Citation preference processed: {citation_pref.id}")
            
        except Exception as e:
            logger.error(f"Error in preference feedback demo: {str(e)}")
    
    async def demo_relevance_feedback(self):
        """Demonstrate relevance feedback processing."""
        logger.info("\n=== Relevance Feedback Demo ===")
        
        try:
            # Source-specific relevance feedback
            logger.info("Processing relevance feedback...")
            relevance = await self.feedback_processor.process_feedback(
                user_id="demo-user-1",
                feedback_type=FeedbackType.RELEVANCE,
                feedback_value={
                    "relevance": 0.7,
                    "sources": {
                        "doc-1": 0.9,  # Very relevant
                        "doc-2": 0.5   # Somewhat relevant
                    },
                    "query": "What is machine learning?"
                },
                message_id="demo-msg-2",
                context={"search_method": "semantic"}
            )
            
            logger.info(f"Relevance feedback processed: {relevance.id}")
            logger.info(f"Overall relevance: {relevance.feedback_value['relevance']}")
            logger.info(f"Source relevance: {relevance.feedback_value['sources']}")
            
            # Poor relevance feedback
            logger.info("Processing poor relevance feedback...")
            poor_relevance = await self.feedback_processor.process_feedback(
                user_id="demo-user-2",
                feedback_type=FeedbackType.RELEVANCE,
                feedback_value={
                    "relevance": 0.3,
                    "sources": {
                        "doc-3": 0.2  # Not relevant
                    },
                    "query": "How does deep learning work?"
                },
                message_id="demo-msg-4"
            )
            
            logger.info(f"Poor relevance processed: {poor_relevance.id}")
            
        except Exception as e:
            logger.error(f"Error in relevance feedback demo: {str(e)}")
    
    async def demo_feedback_analysis(self):
        """Demonstrate feedback analysis and trends."""
        logger.info("\n=== Feedback Analysis Demo ===")
        
        try:
            # Analyze overall feedback trends
            logger.info("Analyzing overall feedback trends...")
            overall_trends = await self.feedback_analyzer.analyze_feedback_trends(
                time_range=30
            )
            
            logger.info(f"Total feedback entries: {overall_trends.get('total_feedback', 0)}")
            if 'feedback_by_type' in overall_trends:
                logger.info(f"Feedback distribution: {overall_trends['feedback_by_type']['distribution']}")
            if 'rating_trends' in overall_trends:
                rating_trends = overall_trends['rating_trends']
                if 'average_rating' in rating_trends:
                    logger.info(f"Average rating: {rating_trends['average_rating']:.2f}")
                if 'rating_distribution' in rating_trends:
                    logger.info(f"Rating distribution: {rating_trends['rating_distribution']}")
            
            # Analyze user-specific trends
            logger.info("Analyzing user-specific trends...")
            user_trends = await self.feedback_analyzer.analyze_feedback_trends(
                user_id="demo-user-1",
                time_range=7
            )
            
            logger.info(f"User 1 feedback count: {user_trends.get('total_feedback', 0)}")
            
            # Analyze specific feedback types
            logger.info("Analyzing rating feedback only...")
            rating_only_trends = await self.feedback_analyzer.analyze_feedback_trends(
                feedback_types=["rating"],
                time_range=30
            )
            
            logger.info(f"Rating-only feedback count: {rating_only_trends.get('total_feedback', 0)}")
            
        except Exception as e:
            logger.error(f"Error in feedback analysis demo: {str(e)}")
    
    async def demo_improvement_cycle(self):
        """Demonstrate system improvement cycle."""
        logger.info("\n=== Improvement Cycle Demo ===")
        
        try:
            logger.info("Running improvement cycle...")
            cycle_result = await self.feedback_loop.run_improvement_cycle()
            
            logger.info(f"Cycle completed at: {cycle_result.get('cycle_timestamp')}")
            logger.info(f"Improvements identified: {cycle_result.get('improvements_identified', 0)}")
            logger.info(f"Improvements applied: {cycle_result.get('improvements_applied', 0)}")
            
            if 'feedback_analysis' in cycle_result:
                analysis = cycle_result['feedback_analysis']
                logger.info(f"Analysis covered {analysis.get('total_feedback', 0)} feedback entries")
            
        except Exception as e:
            logger.error(f"Error in improvement cycle demo: {str(e)}")
    
    async def demo_user_profile_impact(self):
        """Demonstrate how feedback impacts user profiles."""
        logger.info("\n=== User Profile Impact Demo ===")
        
        try:
            # Get user profile before feedback
            logger.info("User profile before feedback processing...")
            profile_before = await self.profile_manager.get_user_profile("demo-user-1")
            if profile_before:
                logger.info(f"Satisfaction history entries: {len(profile_before.interaction_history.get('satisfaction_history', []))}")
                logger.info(f"Average satisfaction: {profile_before.interaction_history.get('avg_satisfaction', 'N/A')}")
            
            # Process some feedback
            await self.feedback_processor.process_detailed_rating(
                user_id="demo-user-1",
                message_id="demo-msg-2",
                rating=0.85,
                aspects={"accuracy": 0.9, "relevance": 0.8}
            )
            
            # Get user profile after feedback
            logger.info("User profile after feedback processing...")
            profile_after = await self.profile_manager.get_user_profile("demo-user-1")
            if profile_after:
                logger.info(f"Satisfaction history entries: {len(profile_after.interaction_history.get('satisfaction_history', []))}")
                logger.info(f"Average satisfaction: {profile_after.interaction_history.get('avg_satisfaction', 'N/A')}")
                
                # Show recent satisfaction entry
                satisfaction_history = profile_after.interaction_history.get('satisfaction_history', [])
                if satisfaction_history:
                    recent = satisfaction_history[-1]
                    logger.info(f"Most recent satisfaction: {recent.get('overall_rating', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error in user profile impact demo: {str(e)}")
    
    async def run_complete_demo(self):
        """Run the complete feedback processing demo."""
        logger.info("Starting Feedback Processing System Demo")
        logger.info("=" * 50)
        
        try:
            # Setup demo data
            await self.setup_demo_data()
            
            # Run all demo scenarios
            await self.demo_thumbs_feedback()
            await self.demo_detailed_rating()
            await self.demo_correction_feedback()
            await self.demo_preference_feedback()
            await self.demo_relevance_feedback()
            await self.demo_feedback_analysis()
            await self.demo_improvement_cycle()
            await self.demo_user_profile_impact()
            
            logger.info("\n" + "=" * 50)
            logger.info("Feedback Processing System Demo completed successfully!")
            
            # Show final statistics
            await self.show_final_statistics()
            
        except Exception as e:
            logger.error(f"Error in complete demo: {str(e)}")
            raise
        finally:
            self.db.close()
    
    async def show_final_statistics(self):
        """Show final statistics from the demo."""
        logger.info("\n=== Final Statistics ===")
        
        try:
            # Count total feedback entries
            total_feedback = self.db.query(UserFeedback).count()
            logger.info(f"Total feedback entries created: {total_feedback}")
            
            # Count by type
            feedback_by_type = {}
            for feedback_type in ["rating", "correction", "preference", "relevance"]:
                count = self.db.query(UserFeedback).filter(
                    UserFeedback.feedback_type == feedback_type
                ).count()
                feedback_by_type[feedback_type] = count
            
            logger.info(f"Feedback by type: {feedback_by_type}")
            
            # Count processed feedback
            processed_count = self.db.query(UserFeedback).filter(
                UserFeedback.processed == True
            ).count()
            logger.info(f"Processed feedback entries: {processed_count}")
            
            # Show user profiles updated
            profiles_with_satisfaction = self.db.query(UserProfile).filter(
                UserProfile.interaction_history.contains('"satisfaction_history"')
            ).count()
            logger.info(f"User profiles with satisfaction data: {profiles_with_satisfaction}")
            
        except Exception as e:
            logger.error(f"Error showing final statistics: {str(e)}")

async def main():
    """Main function to run the demo."""
    demo = FeedbackProcessingDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())