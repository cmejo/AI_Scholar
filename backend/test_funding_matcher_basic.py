"""
Basic test for Funding Matcher Service

This test verifies the core functionality of the funding opportunity matching system.
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db, init_db, User, ResearchProfile, FundingOpportunity
from services.funding_matcher_service import FundingMatcherService

class TestFundingMatcherService:
    """Test class for funding matcher service"""
    
    def __init__(self):
        self.funding_service = FundingMatcherService()
        self.test_user_id = "test_user_funding_123"
        self.test_opportunities = []
    
    async def setup_test_data(self):
        """Set up test data for funding matcher tests"""
        try:
            db = next(get_db())
            
            # Create test user
            test_user = User(
                id=self.test_user_id,
                email="test_funding@example.com",
                name="Test Funding User",
                hashed_password="hashed_password_123"
            )
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.id == self.test_user_id).first()
            if not existing_user:
                db.add(test_user)
            
            # Create test research profile
            research_profile = ResearchProfile(
                user_id=self.test_user_id,
                research_interests=[
                    "machine learning",
                    "artificial intelligence",
                    "natural language processing",
                    "computer vision"
                ],
                expertise_areas={
                    "machine_learning": 0.9,
                    "deep_learning": 0.8,
                    "nlp": 0.7,
                    "computer_vision": 0.6
                },
                research_domains=[
                    "computer science",
                    "artificial intelligence",
                    "data science"
                ],
                career_stage="graduate",
                institution_affiliation="Test University",
                previous_funding=[
                    {
                        "agency": "NSF",
                        "amount": 50000,
                        "year": 2022,
                        "title": "ML Research Grant"
                    }
                ],
                publications=[
                    {
                        "title": "Deep Learning for NLP",
                        "year": 2023,
                        "citations": 25
                    }
                ],
                collaborators=["Dr. Smith", "Dr. Johnson"],
                geographic_preferences=["United States", "North America"],
                funding_amount_range={
                    "min": 25000,
                    "max": 500000
                }
            )
            
            # Check if profile already exists
            existing_profile = db.query(ResearchProfile).filter(
                ResearchProfile.user_id == self.test_user_id
            ).first()
            if existing_profile:
                # Update existing profile
                existing_profile.research_interests = research_profile.research_interests
                existing_profile.expertise_areas = research_profile.expertise_areas
                existing_profile.research_domains = research_profile.research_domains
                existing_profile.career_stage = research_profile.career_stage
                existing_profile.institution_affiliation = research_profile.institution_affiliation
                existing_profile.previous_funding = research_profile.previous_funding
                existing_profile.publications = research_profile.publications
                existing_profile.collaborators = research_profile.collaborators
                existing_profile.geographic_preferences = research_profile.geographic_preferences
                existing_profile.funding_amount_range = research_profile.funding_amount_range
                existing_profile.updated_at = datetime.now()
            else:
                db.add(research_profile)
            
            # Create test funding opportunities
            opportunities = [
                {
                    "title": "NSF AI Research Grant",
                    "description": "Funding for artificial intelligence and machine learning research",
                    "funding_agency": "National Science Foundation",
                    "program_name": "AI Research Initiative",
                    "opportunity_type": "grant",
                    "funding_amount_min": 100000,
                    "funding_amount_max": 500000,
                    "duration_months": 36,
                    "eligibility_criteria": {
                        "career_stages": ["graduate", "postdoc", "faculty"],
                        "institution_types": ["university", "research_institute"]
                    },
                    "research_areas": ["artificial intelligence", "machine learning", "computer science"],
                    "keywords": ["AI", "machine learning", "deep learning", "neural networks"],
                    "application_deadline": datetime.now() + timedelta(days=60),
                    "application_url": "https://nsf.gov/ai-grant",
                    "requirements": {
                        "documents": ["proposal", "cv", "budget"],
                        "eligibility": "US citizens or permanent residents"
                    },
                    "restrictions": {
                        "geographic": ["United States"],
                        "institutional": ["accredited universities"]
                    },
                    "success_rate": 0.15,
                    "average_award_amount": 300000,
                    "source": "nsf"
                },
                {
                    "title": "NIH Biomedical AI Fellowship",
                    "description": "Fellowship for AI applications in biomedical research",
                    "funding_agency": "National Institutes of Health",
                    "program_name": "Biomedical AI Program",
                    "opportunity_type": "fellowship",
                    "funding_amount_min": 50000,
                    "funding_amount_max": 75000,
                    "duration_months": 24,
                    "eligibility_criteria": {
                        "career_stages": ["graduate", "postdoc"],
                        "fields": ["biomedical", "computer science"]
                    },
                    "research_areas": ["biomedical informatics", "artificial intelligence", "healthcare"],
                    "keywords": ["biomedical AI", "healthcare", "medical imaging", "bioinformatics"],
                    "application_deadline": datetime.now() + timedelta(days=90),
                    "application_url": "https://nih.gov/biomedical-ai",
                    "requirements": {
                        "documents": ["research plan", "transcripts", "references"],
                        "gpa_minimum": 3.5
                    },
                    "restrictions": {
                        "geographic": ["United States"],
                        "citizenship": ["US citizen", "permanent resident"]
                    },
                    "success_rate": 0.25,
                    "average_award_amount": 62500,
                    "source": "nih"
                },
                {
                    "title": "Google Research Award",
                    "description": "Industry funding for computer science research",
                    "funding_agency": "Google",
                    "program_name": "Faculty Research Awards",
                    "opportunity_type": "award",
                    "funding_amount_min": 25000,
                    "funding_amount_max": 150000,
                    "duration_months": 12,
                    "eligibility_criteria": {
                        "career_stages": ["faculty"],
                        "fields": ["computer science", "engineering"]
                    },
                    "research_areas": ["machine learning", "natural language processing", "computer vision"],
                    "keywords": ["NLP", "computer vision", "ML", "deep learning"],
                    "application_deadline": datetime.now() + timedelta(days=45),
                    "application_url": "https://research.google.com/awards",
                    "requirements": {
                        "documents": ["proposal", "cv"],
                        "collaboration": "Google researcher collaboration preferred"
                    },
                    "restrictions": {
                        "geographic": ["Global"],
                        "institutional": ["universities only"]
                    },
                    "success_rate": 0.20,
                    "average_award_amount": 87500,
                    "source": "google"
                },
                {
                    "title": "European Research Council Grant",
                    "description": "European funding for frontier research",
                    "funding_agency": "European Research Council",
                    "program_name": "Starting Grants",
                    "opportunity_type": "grant",
                    "funding_amount_min": 1000000,
                    "funding_amount_max": 1500000,
                    "duration_months": 60,
                    "eligibility_criteria": {
                        "career_stages": ["early_career", "faculty"],
                        "experience_years": {"min": 2, "max": 7}
                    },
                    "research_areas": ["any field", "frontier research"],
                    "keywords": ["innovation", "breakthrough", "frontier research"],
                    "application_deadline": datetime.now() + timedelta(days=120),
                    "application_url": "https://erc.europa.eu/starting-grants",
                    "requirements": {
                        "documents": ["detailed proposal", "cv", "track record"],
                        "host_institution": "European institution required"
                    },
                    "restrictions": {
                        "geographic": ["European Union", "Associated Countries"],
                        "institutional": ["European research institutions"]
                    },
                    "success_rate": 0.12,
                    "average_award_amount": 1250000,
                    "source": "erc"
                }
            ]
            
            # Add funding opportunities to database
            for opp_data in opportunities:
                opportunity = FundingOpportunity(
                    title=opp_data["title"],
                    description=opp_data["description"],
                    funding_agency=opp_data["funding_agency"],
                    program_name=opp_data["program_name"],
                    opportunity_type=opp_data["opportunity_type"],
                    funding_amount_min=opp_data["funding_amount_min"],
                    funding_amount_max=opp_data["funding_amount_max"],
                    duration_months=opp_data["duration_months"],
                    eligibility_criteria=opp_data["eligibility_criteria"],
                    research_areas=opp_data["research_areas"],
                    keywords=opp_data["keywords"],
                    application_deadline=opp_data["application_deadline"],
                    application_url=opp_data["application_url"],
                    requirements=opp_data["requirements"],
                    restrictions=opp_data["restrictions"],
                    success_rate=opp_data["success_rate"],
                    average_award_amount=opp_data["average_award_amount"],
                    is_active=True,
                    source=opp_data["source"]
                )
                
                # Check if opportunity already exists
                existing_opp = db.query(FundingOpportunity).filter(
                    FundingOpportunity.title == opp_data["title"]
                ).first()
                if not existing_opp:
                    db.add(opportunity)
                    self.test_opportunities.append(opportunity)
            
            db.commit()
            print("✅ Test data setup completed successfully")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error setting up test data: {str(e)}")
            raise
        finally:
            db.close()
    
    async def test_funding_opportunity_discovery(self):
        """Test funding opportunity discovery and matching"""
        try:
            print("\n🔍 Testing funding opportunity discovery...")
            
            # Discover funding opportunities
            matches = await self.funding_service.discover_funding_opportunities(
                user_id=self.test_user_id,
                limit=10,
                min_relevance=0.3
            )
            
            print(f"Found {len(matches)} funding matches")
            
            # Verify matches
            assert len(matches) > 0, "Should find at least one funding match"
            
            # Check match structure
            for match in matches:
                assert hasattr(match, 'opportunity_id'), "Match should have opportunity_id"
                assert hasattr(match, 'title'), "Match should have title"
                assert hasattr(match, 'relevance_score'), "Match should have relevance_score"
                assert hasattr(match, 'match_reasons'), "Match should have match_reasons"
                assert hasattr(match, 'eligibility_status'), "Match should have eligibility_status"
                assert hasattr(match, 'recommendation_strength'), "Match should have recommendation_strength"
                
                # Verify relevance score is valid
                assert 0.0 <= match.relevance_score <= 1.0, f"Relevance score should be between 0 and 1, got {match.relevance_score}"
                
                # Verify eligibility status is valid
                valid_statuses = ['eligible', 'potentially_eligible', 'not_eligible']
                assert match.eligibility_status in valid_statuses, f"Invalid eligibility status: {match.eligibility_status}"
                
                # Verify recommendation strength is valid
                valid_strengths = ['high', 'medium', 'low']
                assert match.recommendation_strength in valid_strengths, f"Invalid recommendation strength: {match.recommendation_strength}"
                
                print(f"  📋 {match.title}")
                print(f"     Agency: {match.funding_agency}")
                print(f"     Relevance: {match.relevance_score:.3f}")
                print(f"     Eligibility: {match.eligibility_status}")
                print(f"     Strength: {match.recommendation_strength}")
                print(f"     Reasons: {', '.join(match.match_reasons[:2])}")
                print()
            
            # Test that matches are sorted by relevance score
            relevance_scores = [match.relevance_score for match in matches]
            assert relevance_scores == sorted(relevance_scores, reverse=True), "Matches should be sorted by relevance score"
            
            print("✅ Funding opportunity discovery test passed")
            return True
            
        except Exception as e:
            print(f"❌ Funding opportunity discovery test failed: {str(e)}")
            return False
    
    async def test_relevance_scoring(self):
        """Test relevance scoring algorithm"""
        try:
            print("\n🎯 Testing relevance scoring...")
            
            # Get matches with different relevance thresholds
            high_relevance_matches = await self.funding_service.discover_funding_opportunities(
                user_id=self.test_user_id,
                limit=10,
                min_relevance=0.7
            )
            
            medium_relevance_matches = await self.funding_service.discover_funding_opportunities(
                user_id=self.test_user_id,
                limit=10,
                min_relevance=0.4
            )
            
            low_relevance_matches = await self.funding_service.discover_funding_opportunities(
                user_id=self.test_user_id,
                limit=10,
                min_relevance=0.1
            )
            
            # Verify filtering works
            assert len(high_relevance_matches) <= len(medium_relevance_matches), "High relevance should have fewer or equal matches"
            assert len(medium_relevance_matches) <= len(low_relevance_matches), "Medium relevance should have fewer or equal matches"
            
            # Verify all high relevance matches have high scores
            for match in high_relevance_matches:
                assert match.relevance_score >= 0.7, f"High relevance match has low score: {match.relevance_score}"
            
            print(f"High relevance (≥0.7): {len(high_relevance_matches)} matches")
            print(f"Medium relevance (≥0.4): {len(medium_relevance_matches)} matches")
            print(f"Low relevance (≥0.1): {len(low_relevance_matches)} matches")
            
            print("✅ Relevance scoring test passed")
            return True
            
        except Exception as e:
            print(f"❌ Relevance scoring test failed: {str(e)}")
            return False
    
    async def test_funding_alert_creation(self):
        """Test funding alert creation and management"""
        try:
            print("\n🔔 Testing funding alert creation...")
            
            # Create a funding alert
            alert_id = await self.funding_service.create_funding_alert(
                user_id=self.test_user_id,
                alert_name="AI Research Opportunities",
                search_criteria={
                    "keywords": ["artificial intelligence", "machine learning"],
                    "funding_amount_min": 50000,
                    "opportunity_types": ["grant", "fellowship"]
                },
                notification_frequency="weekly"
            )
            
            assert alert_id is not None, "Alert ID should not be None"
            assert isinstance(alert_id, str), "Alert ID should be a string"
            
            print(f"Created funding alert with ID: {alert_id}")
            
            # Test alert retrieval
            from core.database import get_db, FundingAlert
            db = next(get_db())
            
            alert = db.query(FundingAlert).filter(FundingAlert.id == alert_id).first()
            assert alert is not None, "Alert should exist in database"
            assert alert.user_id == self.test_user_id, "Alert should belong to test user"
            assert alert.alert_name == "AI Research Opportunities", "Alert name should match"
            assert alert.is_active == True, "Alert should be active"
            
            db.close()
            
            print("✅ Funding alert creation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Funding alert creation test failed: {str(e)}")
            return False
    
    async def test_stored_matches_retrieval(self):
        """Test retrieval of stored funding matches"""
        try:
            print("\n📊 Testing stored matches retrieval...")
            
            # First discover opportunities to store matches
            await self.funding_service.discover_funding_opportunities(
                user_id=self.test_user_id,
                limit=5,
                min_relevance=0.3
            )
            
            # Retrieve stored matches
            stored_matches = await self.funding_service.get_funding_matches(
                user_id=self.test_user_id,
                limit=10
            )
            
            assert len(stored_matches) > 0, "Should have stored matches"
            
            # Verify match structure
            for match in stored_matches:
                assert 'match_id' in match, "Match should have match_id"
                assert 'relevance_score' in match, "Match should have relevance_score"
                assert 'match_reasons' in match, "Match should have match_reasons"
                assert 'opportunity' in match, "Match should have opportunity details"
                
                opportunity = match['opportunity']
                assert 'id' in opportunity, "Opportunity should have id"
                assert 'title' in opportunity, "Opportunity should have title"
                assert 'funding_agency' in opportunity, "Opportunity should have funding_agency"
                
                print(f"  📋 Stored match: {opportunity['title']}")
                print(f"     Relevance: {match['relevance_score']:.3f}")
                print(f"     Agency: {opportunity['funding_agency']}")
            
            print("✅ Stored matches retrieval test passed")
            return True
            
        except Exception as e:
            print(f"❌ Stored matches retrieval test failed: {str(e)}")
            return False
    
    async def test_grant_database_search(self):
        """Test grant database search functionality"""
        try:
            print("\n🔍 Testing grant database search...")
            
            # Set up default grant databases first
            await self.funding_service.setup_default_grant_databases()
            
            # Search grant databases
            search_results = await self.funding_service.search_grant_databases(
                keywords=["machine learning", "AI"],
                filters={
                    "funding_amount_min": 25000,
                    "opportunity_type": "grant"
                }
            )
            
            # Note: This will return mock data since we don't have real API integrations
            assert isinstance(search_results, list), "Search results should be a list"
            
            print(f"Found {len(search_results)} opportunities from grant databases")
            
            for result in search_results:
                print(f"  📋 {result.get('title', 'Unknown Title')}")
                print(f"     Source: {result.get('source', 'Unknown')}")
                print(f"     Amount: ${result.get('funding_amount_min', 0):,} - ${result.get('funding_amount_max', 0):,}")
            
            print("✅ Grant database search test passed")
            return True
            
        except Exception as e:
            print(f"❌ Grant database search test failed: {str(e)}")
            return False
    
    async def test_application_optimization(self):
        """Test application optimization recommendations"""
        try:
            print("\n🎯 Testing application optimization...")
            
            # Get optimization recommendations
            optimization = await self.funding_service.optimize_application_strategy(
                user_id=self.test_user_id,
                target_success_rate=0.3
            )
            
            print(f"Optimization result keys: {list(optimization.keys())}")
            print(f"Optimization result: {optimization}")
            
            assert isinstance(optimization, dict), "Optimization should return a dictionary"
            assert 'recommendations' in optimization, "Should include recommendations"
            assert 'strategy' in optimization, "Should include strategy"
            assert 'current_performance' in optimization, "Should include current performance"
            
            print(f"Generated {len(optimization['recommendations'])} recommendations")
            
            for rec in optimization['recommendations']:
                print(f"  🎯 {rec['title']} (Priority: {rec['priority']})")
                print(f"     {rec['description']}")
                print(f"     Actions: {len(rec['actions'])} suggested")
            
            strategy = optimization['strategy']
            print(f"\n📊 Strategy Summary:")
            print(f"  Recommended applications per year: {strategy['recommended_applications_per_year']}")
            print(f"  Target success rate: {strategy['target_success_rate']:.1%}")
            print(f"  Current success rate: {strategy['current_success_rate']:.1%}")
            
            print("✅ Application optimization test passed")
            return True
            
        except Exception as e:
            print(f"❌ Application optimization test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_trending_opportunities(self):
        """Test trending opportunities discovery"""
        try:
            print("\n📈 Testing trending opportunities...")
            
            # Get trending opportunities
            trending = await self.funding_service.get_trending_opportunities(
                user_id=self.test_user_id,
                limit=5
            )
            
            assert isinstance(trending, list), "Trending should return a list"
            
            print(f"Found {len(trending)} trending opportunities")
            
            for trend in trending:
                opp = trend['opportunity']
                print(f"  📈 {opp['title']}")
                print(f"     Agency: {opp['funding_agency']}")
                print(f"     Trend Score: {trend['trend_score']:.3f}")
                print(f"     Factors: {', '.join(trend['trend_factors'][:2])}")
                if trend['days_until_deadline']:
                    print(f"     Deadline: {trend['days_until_deadline']} days")
                print()
            
            print("✅ Trending opportunities test passed")
            return True
            
        except Exception as e:
            print(f"❌ Trending opportunities test failed: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all funding matcher tests"""
        print("🚀 Starting Funding Matcher Service Tests")
        print("=" * 50)
        
        # Initialize database
        await init_db()
        
        # Setup test data
        await self.setup_test_data()
        
        # Run tests
        tests = [
            self.test_funding_opportunity_discovery,
            self.test_relevance_scoring,
            self.test_funding_alert_creation,
            self.test_stored_matches_retrieval,
            self.test_grant_database_search,
            self.test_application_optimization,
            self.test_trending_opportunities
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
        
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All funding matcher tests passed!")
        else:
            print(f"⚠️  {total - passed} tests failed")
        
        return passed == total

async def main():
    """Main test function"""
    test_suite = TestFundingMatcherService()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)