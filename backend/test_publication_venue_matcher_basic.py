"""
Basic test for Publication Venue Matcher Service

This test verifies the core functionality of the publication venue recommendation system.
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db, init_db, User, ResearchProfile, PublicationVenue, PublicationDeadline
from services.publication_venue_matcher import PublicationVenueMatcherService

class TestPublicationVenueMatcherService:
    """Test class for publication venue matcher service"""
    
    def __init__(self):
        self.venue_service = PublicationVenueMatcherService()
        self.test_user_id = "test_user_venue_123"
        self.test_venues = []
    
    async def setup_test_data(self):
        """Set up test data for publication venue matcher tests"""
        try:
            db = next(get_db())
            
            # Create test user if not exists
            existing_user = db.query(User).filter(User.id == self.test_user_id).first()
            if not existing_user:
                test_user = User(
                    id=self.test_user_id,
                    email="test_venue@example.com",
                    name="Test Venue User",
                    hashed_password="hashed_password_123"
                )
                db.add(test_user)
            
            # Create test research profile
            existing_profile = db.query(ResearchProfile).filter(
                ResearchProfile.user_id == self.test_user_id
            ).first()
            
            if existing_profile:
                # Update existing profile
                existing_profile.research_interests = [
                    "machine learning",
                    "artificial intelligence", 
                    "natural language processing",
                    "computer vision"
                ]
                existing_profile.research_domains = [
                    "computer science",
                    "artificial intelligence"
                ]
                existing_profile.publications = [
                    {
                        "title": "Deep Learning for NLP",
                        "year": 2023,
                        "venue": "AAAI",
                        "citations": 15
                    }
                ]
                existing_profile.updated_at = datetime.now()
            else:
                research_profile = ResearchProfile(
                    user_id=self.test_user_id,
                    research_interests=[
                        "machine learning",
                        "artificial intelligence", 
                        "natural language processing",
                        "computer vision"
                    ],
                    research_domains=[
                        "computer science",
                        "artificial intelligence"
                    ],
                    career_stage="graduate",
                    publications=[
                        {
                            "title": "Deep Learning for NLP",
                            "year": 2023,
                            "venue": "AAAI",
                            "citations": 15
                        }
                    ]
                )
                db.add(research_profile)
            
            # Create test publication venues
            venues_data = [
                {
                    "name": "Journal of Machine Learning Research",
                    "venue_type": "journal",
                    "publisher": "JMLR",
                    "issn": "1532-4435",
                    "impact_factor": 4.3,
                    "h_index": 180,
                    "acceptance_rate": 25.0,
                    "research_areas": ["machine learning", "artificial intelligence", "statistics"],
                    "keywords": ["machine learning", "deep learning", "neural networks", "AI"],
                    "submission_frequency": "continuous",
                    "review_process": "peer_review",
                    "open_access": True,
                    "publication_fee": 0.0,
                    "average_review_time_days": 120,
                    "geographic_scope": "international",
                    "website_url": "https://jmlr.org"
                },
                {
                    "name": "Conference on Neural Information Processing Systems",
                    "venue_type": "conference",
                    "publisher": "NeurIPS Foundation",
                    "impact_factor": 8.1,
                    "h_index": 220,
                    "acceptance_rate": 20.0,
                    "research_areas": ["machine learning", "neural networks", "deep learning"],
                    "keywords": ["neural networks", "deep learning", "ML", "AI", "NeurIPS"],
                    "submission_frequency": "annual",
                    "review_process": "peer_review",
                    "open_access": False,
                    "publication_fee": 500.0,
                    "average_review_time_days": 90,
                    "geographic_scope": "international",
                    "website_url": "https://neurips.cc"
                },
                {
                    "name": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
                    "venue_type": "journal",
                    "publisher": "IEEE",
                    "issn": "0162-8828",
                    "impact_factor": 17.7,
                    "h_index": 350,
                    "acceptance_rate": 15.0,
                    "research_areas": ["computer vision", "pattern recognition", "machine learning"],
                    "keywords": ["computer vision", "pattern recognition", "image processing", "PAMI"],
                    "submission_frequency": "monthly",
                    "review_process": "peer_review",
                    "open_access": False,
                    "publication_fee": 1750.0,
                    "average_review_time_days": 180,
                    "geographic_scope": "international",
                    "website_url": "https://ieee.org/tpami"
                },
                {
                    "name": "International Conference on Learning Representations",
                    "venue_type": "conference",
                    "publisher": "ICLR",
                    "impact_factor": 7.2,
                    "h_index": 95,
                    "acceptance_rate": 22.0,
                    "research_areas": ["deep learning", "representation learning", "machine learning"],
                    "keywords": ["deep learning", "representation learning", "neural networks", "ICLR"],
                    "submission_frequency": "annual",
                    "review_process": "open_review",
                    "open_access": True,
                    "publication_fee": 0.0,
                    "average_review_time_days": 75,
                    "geographic_scope": "international",
                    "website_url": "https://iclr.cc"
                },
                {
                    "name": "ACL: Association for Computational Linguistics",
                    "venue_type": "conference",
                    "publisher": "ACL",
                    "impact_factor": 4.8,
                    "h_index": 140,
                    "acceptance_rate": 25.0,
                    "research_areas": ["natural language processing", "computational linguistics"],
                    "keywords": ["NLP", "natural language processing", "computational linguistics", "text mining"],
                    "submission_frequency": "annual",
                    "review_process": "peer_review",
                    "open_access": True,
                    "publication_fee": 300.0,
                    "average_review_time_days": 85,
                    "geographic_scope": "international",
                    "website_url": "https://aclweb.org"
                }
            ]
            
            # Add venues to database
            for venue_data in venues_data:
                # Check if venue already exists
                existing_venue = db.query(PublicationVenue).filter(
                    PublicationVenue.name == venue_data["name"]
                ).first()
                
                if not existing_venue:
                    venue = PublicationVenue(
                        name=venue_data["name"],
                        venue_type=venue_data["venue_type"],
                        publisher=venue_data["publisher"],
                        issn=venue_data.get("issn"),
                        impact_factor=venue_data["impact_factor"],
                        h_index=venue_data["h_index"],
                        acceptance_rate=venue_data["acceptance_rate"],
                        research_areas=venue_data["research_areas"],
                        keywords=venue_data["keywords"],
                        submission_frequency=venue_data["submission_frequency"],
                        review_process=venue_data["review_process"],
                        open_access=venue_data["open_access"],
                        publication_fee=venue_data["publication_fee"],
                        average_review_time_days=venue_data["average_review_time_days"],
                        geographic_scope=venue_data["geographic_scope"],
                        website_url=venue_data["website_url"],
                        is_active=True
                    )
                    db.add(venue)
                    self.test_venues.append(venue)
            
            # Create some test deadlines
            db.commit()
            
            # Get venue IDs for creating deadlines
            venues = db.query(PublicationVenue).filter(
                PublicationVenue.venue_type == "conference"
            ).all()
            
            for venue in venues[:2]:  # Add deadlines for first 2 conferences
                deadline = PublicationDeadline(
                    venue_id=venue.id,
                    deadline_type="full_paper",
                    deadline_date=datetime.now() + timedelta(days=60),
                    notification_date=datetime.now() + timedelta(days=120),
                    publication_date=datetime.now() + timedelta(days=180),
                    submission_url=f"{venue.website_url}/submit",
                    is_active=True
                )
                
                # Check if deadline already exists
                existing_deadline = db.query(PublicationDeadline).filter(
                    PublicationDeadline.venue_id == venue.id
                ).first()
                
                if not existing_deadline:
                    db.add(deadline)
            
            db.commit()
            print("✅ Test data setup completed successfully")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error setting up test data: {str(e)}")
            raise
        finally:
            db.close()
    
    async def test_venue_recommendations(self):
        """Test venue recommendation functionality"""
        try:
            print("\n🔍 Testing venue recommendations...")
            
            # Test paper abstract
            paper_abstract = """
            This paper presents a novel deep learning approach for natural language processing tasks.
            We propose a transformer-based architecture that achieves state-of-the-art performance
            on sentiment analysis and text classification. Our method uses attention mechanisms
            and pre-trained language models to improve accuracy. Experimental results on benchmark
            datasets demonstrate significant improvements over existing approaches.
            """
            
            # Get venue recommendations
            recommendations = await self.venue_service.recommend_venues(
                user_id=self.test_user_id,
                paper_abstract=paper_abstract,
                max_recommendations=10,
                min_fit_score=0.2
            )
            
            print(f"Found {len(recommendations)} venue recommendations")
            
            # Verify recommendations
            assert len(recommendations) > 0, "Should find at least one venue recommendation"
            
            # Check recommendation structure
            for rec in recommendations:
                assert hasattr(rec, 'venue_id'), "Recommendation should have venue_id"
                assert hasattr(rec, 'name'), "Recommendation should have name"
                assert hasattr(rec, 'fit_score'), "Recommendation should have fit_score"
                assert hasattr(rec, 'success_probability'), "Recommendation should have success_probability"
                assert hasattr(rec, 'match_reasons'), "Recommendation should have match_reasons"
                assert hasattr(rec, 'recommendation_strength'), "Recommendation should have recommendation_strength"
                
                # Verify score ranges
                assert 0.0 <= rec.fit_score <= 1.0, f"Fit score should be between 0 and 1, got {rec.fit_score}"
                assert 0.0 <= rec.success_probability <= 1.0, f"Success probability should be between 0 and 1, got {rec.success_probability}"
                
                # Verify recommendation strength
                valid_strengths = ['high', 'medium', 'low']
                assert rec.recommendation_strength in valid_strengths, f"Invalid recommendation strength: {rec.recommendation_strength}"
                
                print(f"  📋 {rec.name}")
                print(f"     Type: {rec.venue_type}")
                print(f"     Publisher: {rec.publisher}")
                print(f"     Fit Score: {rec.fit_score:.3f}")
                print(f"     Success Probability: {rec.success_probability:.3f}")
                print(f"     Strength: {rec.recommendation_strength}")
                print(f"     Impact Factor: {rec.impact_factor}")
                print(f"     Acceptance Rate: {rec.acceptance_rate}%")
                print(f"     Reasons: {', '.join(rec.match_reasons[:2])}")
                print()
            
            # Test that recommendations are sorted by fit score
            fit_scores = [rec.fit_score for rec in recommendations]
            assert fit_scores == sorted(fit_scores, reverse=True), "Recommendations should be sorted by fit score"
            
            print("✅ Venue recommendations test passed")
            return True
            
        except Exception as e:
            print(f"❌ Venue recommendations test failed: {str(e)}")
            return False
    
    async def test_venue_type_filtering(self):
        """Test venue type filtering"""
        try:
            print("\n🎯 Testing venue type filtering...")
            
            paper_abstract = "A machine learning approach for computer vision tasks."
            
            # Test journal filtering
            journal_recs = await self.venue_service.recommend_venues(
                user_id=self.test_user_id,
                paper_abstract=paper_abstract,
                venue_type="journal",
                max_recommendations=10,
                min_fit_score=0.1
            )
            
            # Test conference filtering
            conference_recs = await self.venue_service.recommend_venues(
                user_id=self.test_user_id,
                paper_abstract=paper_abstract,
                venue_type="conference",
                max_recommendations=10,
                min_fit_score=0.1
            )
            
            # Verify filtering works
            for rec in journal_recs:
                assert rec.venue_type == "journal", f"Journal filter failed: got {rec.venue_type}"
            
            for rec in conference_recs:
                assert rec.venue_type == "conference", f"Conference filter failed: got {rec.venue_type}"
            
            print(f"Journal recommendations: {len(journal_recs)}")
            print(f"Conference recommendations: {len(conference_recs)}")
            
            print("✅ Venue type filtering test passed")
            return True
            
        except Exception as e:
            print(f"❌ Venue type filtering test failed: {str(e)}")
            return False
    
    async def test_venue_rankings(self):
        """Test venue ranking functionality"""
        try:
            print("\n📊 Testing venue rankings...")
            
            # Test rankings by impact factor
            impact_rankings = await self.venue_service.get_venue_rankings(
                sort_by="impact_factor",
                limit=10
            )
            
            # Test rankings by acceptance rate
            acceptance_rankings = await self.venue_service.get_venue_rankings(
                sort_by="acceptance_rate",
                limit=10
            )
            
            # Verify rankings
            assert len(impact_rankings) > 0, "Should have impact factor rankings"
            assert len(acceptance_rankings) > 0, "Should have acceptance rate rankings"
            
            # Check sorting
            if len(impact_rankings) > 1:
                impact_factors = [v.get('impact_factor', 0) for v in impact_rankings]
                assert impact_factors == sorted(impact_factors, reverse=True), "Impact factor rankings should be sorted"
            
            if len(acceptance_rankings) > 1:
                acceptance_rates = [v.get('acceptance_rate', 0) for v in acceptance_rankings]
                assert acceptance_rates == sorted(acceptance_rates, reverse=True), "Acceptance rate rankings should be sorted"
            
            print(f"Impact factor rankings: {len(impact_rankings)} venues")
            for venue in impact_rankings[:3]:
                print(f"  📋 {venue['name']} - Impact Factor: {venue.get('impact_factor', 'N/A')}")
            
            print(f"Acceptance rate rankings: {len(acceptance_rankings)} venues")
            for venue in acceptance_rankings[:3]:
                print(f"  📋 {venue['name']} - Acceptance Rate: {venue.get('acceptance_rate', 'N/A')}%")
            
            print("✅ Venue rankings test passed")
            return True
            
        except Exception as e:
            print(f"❌ Venue rankings test failed: {str(e)}")
            return False
    
    async def test_submission_tracking(self):
        """Test submission tracking functionality"""
        try:
            print("\n📝 Testing submission tracking...")
            
            # Get a test venue
            db = next(get_db())
            venue = db.query(PublicationVenue).first()
            db.close()
            
            if not venue:
                print("⚠️  No venues available for submission tracking test")
                return True
            
            # Track a submission
            submission_id = await self.venue_service.track_submission(
                user_id=self.test_user_id,
                venue_id=venue.id,
                paper_title="Test Paper: Deep Learning for NLP",
                paper_abstract="This is a test paper abstract for submission tracking.",
                submission_date=datetime.now()
            )
            
            assert submission_id is not None, "Submission ID should not be None"
            assert isinstance(submission_id, str), "Submission ID should be a string"
            
            print(f"Created submission with ID: {submission_id}")
            
            # Update submission status
            await self.venue_service.update_submission_status(
                submission_id=submission_id,
                status="under_review",
                decision_date=datetime.now() + timedelta(days=90),
                final_decision="under_review"
            )
            
            # Get user submissions
            submissions = await self.venue_service.get_user_submissions(
                user_id=self.test_user_id
            )
            
            assert len(submissions) > 0, "Should have at least one submission"
            
            # Find our test submission
            test_submission = None
            for sub in submissions:
                if sub['id'] == submission_id:
                    test_submission = sub
                    break
            
            assert test_submission is not None, "Should find the test submission"
            assert test_submission['status'] == "under_review", "Status should be updated"
            
            print(f"Submission status: {test_submission['status']}")
            print(f"Venue: {test_submission['venue_name']}")
            
            print("✅ Submission tracking test passed")
            return True
            
        except Exception as e:
            print(f"❌ Submission tracking test failed: {str(e)}")
            return False
    
    async def test_venue_analytics(self):
        """Test venue analytics functionality"""
        try:
            print("\n📈 Testing venue analytics...")
            
            # Get a test venue
            db = next(get_db())
            venue = db.query(PublicationVenue).first()
            db.close()
            
            if not venue:
                print("⚠️  No venues available for analytics test")
                return True
            
            # Get venue analytics
            analytics = await self.venue_service.get_venue_analytics(venue.id)
            
            assert analytics is not None, "Analytics should not be None"
            assert hasattr(analytics, 'venue_id'), "Analytics should have venue_id"
            assert hasattr(analytics, 'name'), "Analytics should have name"
            assert hasattr(analytics, 'total_submissions'), "Analytics should have total_submissions"
            assert hasattr(analytics, 'acceptance_rate'), "Analytics should have acceptance_rate"
            assert hasattr(analytics, 'average_review_time'), "Analytics should have average_review_time"
            assert hasattr(analytics, 'impact_metrics'), "Analytics should have impact_metrics"
            
            print(f"Venue: {analytics.name}")
            print(f"Total submissions: {analytics.total_submissions}")
            print(f"Acceptance rate: {analytics.acceptance_rate}%")
            print(f"Average review time: {analytics.average_review_time} days")
            print(f"Impact metrics: {analytics.impact_metrics}")
            
            print("✅ Venue analytics test passed")
            return True
            
        except Exception as e:
            print(f"❌ Venue analytics test failed: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all publication venue matcher tests"""
        print("🚀 Starting Publication Venue Matcher Service Tests")
        print("=" * 60)
        
        # Initialize database
        await init_db()
        
        # Setup test data
        await self.setup_test_data()
        
        # Run tests
        tests = [
            self.test_venue_recommendations,
            self.test_venue_type_filtering,
            self.test_venue_rankings,
            self.test_submission_tracking,
            self.test_venue_analytics
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All publication venue matcher tests passed!")
        else:
            print(f"⚠️  {total - passed} tests failed")
        
        return passed == total

async def main():
    """Main test function"""
    test_suite = TestPublicationVenueMatcherService()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)