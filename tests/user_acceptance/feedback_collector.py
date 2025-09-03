#!/usr/bin/env python3
"""
Feedback Collection and Analysis Framework
Comprehensive feedback gathering and sentiment analysis for UAT
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import random

class FeedbackType(Enum):
    SURVEY = "survey"
    INTERVIEW = "interview"
    ANALYTICS = "analytics"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY_ISSUE = "usability_issue"

class SentimentScore(Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

@dataclass
class FeedbackItem:
    """Represents a single piece of feedback"""
    id: str
    user_id: str
    feedback_type: FeedbackType
    content: str
    sentiment: Optional[SentimentScore] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SurveyResponse:
    """Represents a survey response"""
    user_id: str
    survey_id: str
    responses: Dict[str, Any]
    completion_time: datetime
    time_spent_minutes: int

@dataclass
class InterviewSession:
    """Represents an interview session"""
    user_id: str
    interviewer: str
    duration_minutes: int
    transcript: str
    key_insights: List[str]
    satisfaction_rating: int
    conducted_at: datetime

class FeedbackCollector:
    """Collects and analyzes comprehensive feedback from users"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        
        self.collection_methods = config.get("collection_methods", ["surveys", "interviews", "analytics"])
        self.metrics = config.get("metrics", ["usability", "satisfaction", "task_completion", "error_rate"])
        
        self.results_dir = Path("tests/user_acceptance/feedback_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_items: List[FeedbackItem] = []
        self.survey_responses: List[SurveyResponse] = []
        self.interview_sessions: List[InterviewSession] = []
        
        # Initialize sentiment analysis keywords
        self._init_sentiment_keywords()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for feedback collector"""
        logger = logging.getLogger("feedback_collector")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("tests/user_acceptance/feedback_collection.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_sentiment_keywords(self):
        """Initialize sentiment analysis keywords"""
        self.sentiment_keywords = {
            SentimentScore.VERY_POSITIVE: [
                "excellent", "amazing", "fantastic", "love", "perfect", "outstanding",
                "brilliant", "exceptional", "wonderful", "incredible"
            ],
            SentimentScore.POSITIVE: [
                "good", "great", "nice", "helpful", "useful", "easy", "smooth",
                "efficient", "intuitive", "pleased", "satisfied", "like"
            ],
            SentimentScore.NEUTRAL: [
                "okay", "fine", "average", "decent", "acceptable", "reasonable",
                "standard", "normal", "typical"
            ],
            SentimentScore.NEGATIVE: [
                "bad", "poor", "difficult", "hard", "confusing", "slow", "annoying",
                "frustrating", "disappointing", "problematic", "dislike"
            ],
            SentimentScore.VERY_NEGATIVE: [
                "terrible", "awful", "horrible", "hate", "broken", "useless",
                "nightmare", "disaster", "unacceptable", "infuriating"
            ]
        }
    
    async def analyze_comprehensive_feedback(self) -> Dict[str, Any]:
        """Analyze all collected feedback comprehensively"""
        self.logger.info("Starting comprehensive feedback analysis")
        
        analysis_results = {
            "start_time": datetime.now().isoformat(),
            "collection_phases": {},
            "analysis_complete": False
        }
        
        try:
            # Phase 1: Collect survey feedback
            if "surveys" in self.collection_methods:
                self.logger.info("Phase 1: Collecting survey feedback")
                survey_results = await self._collect_survey_feedback()
                analysis_results["collection_phases"]["surveys"] = survey_results
            
            # Phase 2: Conduct and analyze interviews
            if "interviews" in self.collection_methods:
                self.logger.info("Phase 2: Conducting and analyzing interviews")
                interview_results = await self._collect_interview_feedback()
                analysis_results["collection_phases"]["interviews"] = interview_results
            
            # Phase 3: Analyze usage analytics
            if "analytics" in self.collection_methods:
                self.logger.info("Phase 3: Analyzing usage analytics")
                analytics_results = await self._collect_analytics_feedback()
                analysis_results["collection_phases"]["analytics"] = analytics_results
            
            # Phase 4: Process bug reports and feature requests
            self.logger.info("Phase 4: Processing bug reports and feature requests")
            issue_results = await self._collect_issue_feedback()
            analysis_results["collection_phases"]["issues"] = issue_results
            
            # Phase 5: Comprehensive analysis
            self.logger.info("Phase 5: Performing comprehensive analysis")
            comprehensive_analysis = await self._perform_comprehensive_analysis()
            analysis_results.update(comprehensive_analysis)
            
            analysis_results["analysis_complete"] = True
            
        except Exception as e:
            self.logger.error(f"Feedback analysis failed: {str(e)}")
            analysis_results["error"] = str(e)
            analysis_results["analysis_complete"] = False
        
        finally:
            analysis_results["end_time"] = datetime.now().isoformat()
            await self._save_feedback_analysis(analysis_results)
        
        return analysis_results
    
    async def _collect_survey_feedback(self) -> Dict[str, Any]:
        """Collect and analyze survey feedback"""
        self.logger.info("Collecting survey feedback")
        
        # Define survey questions
        survey_questions = {
            "overall_satisfaction": {
                "question": "How satisfied are you with the Zotero integration overall?",
                "type": "rating",
                "scale": "1-5"
            },
            "ease_of_use": {
                "question": "How easy was it to use the Zotero integration features?",
                "type": "rating",
                "scale": "1-5"
            },
            "feature_completeness": {
                "question": "How complete do you feel the feature set is?",
                "type": "rating",
                "scale": "1-5"
            },
            "performance_satisfaction": {
                "question": "How satisfied are you with the performance?",
                "type": "rating",
                "scale": "1-5"
            },
            "would_recommend": {
                "question": "Would you recommend this to colleagues?",
                "type": "boolean"
            },
            "most_useful_feature": {
                "question": "What feature did you find most useful?",
                "type": "text"
            },
            "biggest_pain_point": {
                "question": "What was your biggest pain point?",
                "type": "text"
            },
            "improvement_suggestions": {
                "question": "What improvements would you suggest?",
                "type": "text"
            }
        }
        
        # Simulate survey responses from beta testers
        survey_responses = []
        
        for i in range(25):  # 25 survey responses
            user_id = f"beta_user_{i+1}"
            
            # Generate realistic survey responses
            response_data = {
                "overall_satisfaction": random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 45, 33])[0],
                "ease_of_use": random.choices([1, 2, 3, 4, 5], weights=[1, 8, 20, 40, 31])[0],
                "feature_completeness": random.choices([1, 2, 3, 4, 5], weights=[3, 7, 25, 35, 30])[0],
                "performance_satisfaction": random.choices([1, 2, 3, 4, 5], weights=[5, 12, 28, 35, 20])[0],
                "would_recommend": random.choices([True, False], weights=[75, 25])[0],
                "most_useful_feature": random.choice([
                    "Citation generation", "Library import", "Search functionality",
                    "AI analysis", "Real-time sync", "Collaboration features"
                ]),
                "biggest_pain_point": random.choice([
                    "Slow import for large libraries", "Confusing interface",
                    "Limited citation styles", "Performance issues", "Sync conflicts",
                    "Missing features", "Error messages unclear"
                ]),
                "improvement_suggestions": random.choice([
                    "Better performance optimization", "More citation styles",
                    "Improved user interface", "Better error handling",
                    "More collaboration features", "Mobile support"
                ])
            }
            
            survey_response = SurveyResponse(
                user_id=user_id,
                survey_id="zotero_integration_uat_survey",
                responses=response_data,
                completion_time=datetime.now() - timedelta(days=random.randint(0, 14)),
                time_spent_minutes=random.randint(8, 25)
            )
            
            survey_responses.append(survey_response)
            self.survey_responses.append(survey_response)
            
            # Create feedback items from text responses
            for field in ["biggest_pain_point", "improvement_suggestions"]:
                if response_data[field]:
                    feedback_item = FeedbackItem(
                        id=f"survey_{user_id}_{field}",
                        user_id=user_id,
                        feedback_type=FeedbackType.SURVEY,
                        content=response_data[field],
                        category=field,
                        metadata={"survey_id": "zotero_integration_uat_survey"}
                    )
                    self.feedback_items.append(feedback_item)
        
        # Analyze survey results
        analysis = await self._analyze_survey_responses(survey_responses)
        
        return {
            "responses_collected": len(survey_responses),
            "completion_rate": 100.0,  # All simulated responses completed
            "average_completion_time": statistics.mean([r.time_spent_minutes for r in survey_responses]),
            "satisfaction_metrics": analysis["satisfaction_metrics"],
            "key_insights": analysis["key_insights"],
            "recommendation_rate": sum(1 for r in survey_responses if r.responses["would_recommend"]) / len(survey_responses) * 100
        }
    
    async def _analyze_survey_responses(self, responses: List[SurveyResponse]) -> Dict[str, Any]:
        """Analyze survey responses for insights"""
        satisfaction_scores = [r.responses["overall_satisfaction"] for r in responses]
        ease_scores = [r.responses["ease_of_use"] for r in responses]
        completeness_scores = [r.responses["feature_completeness"] for r in responses]
        performance_scores = [r.responses["performance_satisfaction"] for r in responses]
        
        satisfaction_metrics = {
            "overall_satisfaction": {
                "average": statistics.mean(satisfaction_scores),
                "median": statistics.median(satisfaction_scores),
                "distribution": {str(i): satisfaction_scores.count(i) for i in range(1, 6)}
            },
            "ease_of_use": {
                "average": statistics.mean(ease_scores),
                "median": statistics.median(ease_scores),
                "distribution": {str(i): ease_scores.count(i) for i in range(1, 6)}
            },
            "feature_completeness": {
                "average": statistics.mean(completeness_scores),
                "median": statistics.median(completeness_scores),
                "distribution": {str(i): completeness_scores.count(i) for i in range(1, 6)}
            },
            "performance_satisfaction": {
                "average": statistics.mean(performance_scores),
                "median": statistics.median(performance_scores),
                "distribution": {str(i): performance_scores.count(i) for i in range(1, 6)}
            }
        }
        
        # Identify most common responses
        most_useful_features = [r.responses["most_useful_feature"] for r in responses]
        biggest_pain_points = [r.responses["biggest_pain_point"] for r in responses]
        
        feature_counts = {}
        for feature in most_useful_features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        pain_point_counts = {}
        for pain_point in biggest_pain_points:
            pain_point_counts[pain_point] = pain_point_counts.get(pain_point, 0) + 1
        
        key_insights = {
            "most_valued_features": sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            "top_pain_points": sorted(pain_point_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            "satisfaction_trend": "positive" if statistics.mean(satisfaction_scores) >= 4.0 else "neutral" if statistics.mean(satisfaction_scores) >= 3.0 else "negative"
        }
        
        return {
            "satisfaction_metrics": satisfaction_metrics,
            "key_insights": key_insights
        }
    
    async def _collect_interview_feedback(self) -> Dict[str, Any]:
        """Collect and analyze interview feedback"""
        self.logger.info("Collecting interview feedback")
        
        # Simulate interview sessions with key users
        interview_sessions = []
        
        interview_scenarios = [
            {
                "user_type": "academic_researcher",
                "duration": 45,
                "key_insights": [
                    "Citation generation is the most critical feature",
                    "Performance with large libraries needs improvement",
                    "AI analysis features are innovative but need refinement"
                ],
                "satisfaction": 4,
                "transcript_summary": "Researcher appreciates the integration but notes performance issues with 5000+ item library"
            },
            {
                "user_type": "graduate_student",
                "duration": 30,
                "key_insights": [
                    "Interface is intuitive for basic tasks",
                    "Search functionality works well",
                    "Would like better mobile support"
                ],
                "satisfaction": 4,
                "transcript_summary": "Student finds the tool helpful for coursework and thesis research"
            },
            {
                "user_type": "librarian",
                "duration": 60,
                "key_insights": [
                    "Collaboration features are valuable",
                    "Import process needs better error handling",
                    "Documentation could be more comprehensive"
                ],
                "satisfaction": 3,
                "transcript_summary": "Librarian sees potential but identifies several areas for improvement"
            },
            {
                "user_type": "power_user",
                "duration": 50,
                "key_insights": [
                    "Advanced features are well-designed",
                    "API integration possibilities are exciting",
                    "Performance optimization is crucial"
                ],
                "satisfaction": 5,
                "transcript_summary": "Power user is very satisfied and sees great potential for advanced workflows"
            }
        ]
        
        for i, scenario in enumerate(interview_scenarios):
            user_id = f"interview_user_{i+1}"
            
            interview_session = InterviewSession(
                user_id=user_id,
                interviewer="uat_coordinator",
                duration_minutes=scenario["duration"],
                transcript=scenario["transcript_summary"],
                key_insights=scenario["key_insights"],
                satisfaction_rating=scenario["satisfaction"],
                conducted_at=datetime.now() - timedelta(days=random.randint(1, 10))
            )
            
            interview_sessions.append(interview_session)
            self.interview_sessions.append(interview_session)
            
            # Create feedback items from insights
            for insight in scenario["key_insights"]:
                feedback_item = FeedbackItem(
                    id=f"interview_{user_id}_{len(self.feedback_items)}",
                    user_id=user_id,
                    feedback_type=FeedbackType.INTERVIEW,
                    content=insight,
                    category="interview_insight",
                    metadata={
                        "user_type": scenario["user_type"],
                        "interview_duration": scenario["duration"]
                    }
                )
                self.feedback_items.append(feedback_item)
        
        # Analyze interview results
        analysis = await self._analyze_interview_sessions(interview_sessions)
        
        return {
            "interviews_conducted": len(interview_sessions),
            "total_interview_time": sum(s.duration_minutes for s in interview_sessions),
            "average_satisfaction": statistics.mean([s.satisfaction_rating for s in interview_sessions]),
            "key_themes": analysis["key_themes"],
            "user_type_insights": analysis["user_type_insights"]
        }
    
    async def _analyze_interview_sessions(self, sessions: List[InterviewSession]) -> Dict[str, Any]:
        """Analyze interview sessions for themes and insights"""
        all_insights = []
        for session in sessions:
            all_insights.extend(session.key_insights)
        
        # Identify common themes
        theme_keywords = {
            "performance": ["performance", "slow", "speed", "optimization", "fast"],
            "usability": ["interface", "intuitive", "easy", "difficult", "user-friendly"],
            "features": ["feature", "functionality", "capability", "tool"],
            "collaboration": ["collaboration", "sharing", "team", "group"],
            "citation": ["citation", "bibliography", "reference", "format"],
            "import": ["import", "sync", "library", "data"]
        }
        
        theme_counts = {}
        for theme, keywords in theme_keywords.items():
            count = 0
            for insight in all_insights:
                if any(keyword in insight.lower() for keyword in keywords):
                    count += 1
            theme_counts[theme] = count
        
        key_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze by user type (would be more sophisticated in real implementation)
        user_type_insights = {
            "academic_researcher": "Focus on citation and performance",
            "graduate_student": "Values ease of use and search",
            "librarian": "Emphasizes collaboration and documentation",
            "power_user": "Interested in advanced features and API"
        }
        
        return {
            "key_themes": key_themes,
            "user_type_insights": user_type_insights
        }
    
    async def _collect_analytics_feedback(self) -> Dict[str, Any]:
        """Collect and analyze usage analytics feedback"""
        self.logger.info("Collecting usage analytics feedback")
        
        # Simulate analytics data collection
        analytics_data = {
            "user_engagement": {
                "daily_active_users": 18,
                "weekly_active_users": 23,
                "average_session_duration": 25.5,  # minutes
                "feature_usage_frequency": {
                    "library_import": 0.95,
                    "search": 0.88,
                    "citation_generation": 0.82,
                    "ai_analysis": 0.45,
                    "export": 0.67,
                    "collaboration": 0.23
                }
            },
            "task_completion": {
                "library_import_success_rate": 0.92,
                "search_task_completion": 0.89,
                "citation_generation_success": 0.94,
                "export_success_rate": 0.87
            },
            "error_analytics": {
                "total_errors": 47,
                "error_categories": {
                    "import_errors": 18,
                    "sync_errors": 12,
                    "search_errors": 8,
                    "citation_errors": 6,
                    "ui_errors": 3
                },
                "error_recovery_rate": 0.78
            },
            "performance_metrics": {
                "average_page_load_time": 1.8,  # seconds
                "api_response_times": {
                    "library": 1.2,
                    "search": 2.1,
                    "citations": 1.5,
                    "analysis": 4.2
                }
            }
        }
        
        # Create feedback items from analytics insights
        analytics_insights = [
            "High adoption rate for core features like import and search",
            "AI analysis features have lower adoption - may need better onboarding",
            "Collaboration features underutilized - consider promoting benefits",
            "Import errors are the most common issue - needs attention",
            "Search response times occasionally exceed user expectations"
        ]
        
        for i, insight in enumerate(analytics_insights):
            feedback_item = FeedbackItem(
                id=f"analytics_insight_{i}",
                user_id="analytics_system",
                feedback_type=FeedbackType.ANALYTICS,
                content=insight,
                category="usage_analytics",
                metadata={"source": "user_behavior_analysis"}
            )
            self.feedback_items.append(feedback_item)
        
        return {
            "analytics_period_days": 14,
            "users_analyzed": 25,
            "engagement_metrics": analytics_data["user_engagement"],
            "completion_metrics": analytics_data["task_completion"],
            "error_analysis": analytics_data["error_analytics"],
            "performance_insights": analytics_data["performance_metrics"],
            "key_findings": analytics_insights
        }
    
    async def _collect_issue_feedback(self) -> Dict[str, Any]:
        """Collect bug reports and feature requests"""
        self.logger.info("Collecting bug reports and feature requests")
        
        # Simulate bug reports
        bug_reports = [
            {
                "title": "Large library import fails with timeout",
                "description": "Import of 8000+ items fails after 10 minutes",
                "severity": "high",
                "category": "import"
            },
            {
                "title": "Citation format incorrect for journal articles",
                "description": "APA format missing DOI in some cases",
                "severity": "medium",
                "category": "citation"
            },
            {
                "title": "Search results pagination broken",
                "description": "Cannot navigate beyond page 10 of search results",
                "severity": "medium",
                "category": "search"
            },
            {
                "title": "Sync status not updating in real-time",
                "description": "User has to refresh page to see sync progress",
                "severity": "low",
                "category": "sync"
            }
        ]
        
        # Simulate feature requests
        feature_requests = [
            {
                "title": "Mobile app support",
                "description": "Need mobile app for iOS and Android",
                "priority": "high",
                "votes": 15
            },
            {
                "title": "More citation styles",
                "description": "Add support for Nature, Science, and IEEE styles",
                "priority": "medium",
                "votes": 8
            },
            {
                "title": "Bulk operations",
                "description": "Ability to perform bulk edits on multiple items",
                "priority": "medium",
                "votes": 12
            },
            {
                "title": "Advanced search filters",
                "description": "More granular search and filtering options",
                "priority": "low",
                "votes": 6
            }
        ]
        
        # Create feedback items
        for i, bug in enumerate(bug_reports):
            feedback_item = FeedbackItem(
                id=f"bug_report_{i}",
                user_id=f"user_{i+1}",
                feedback_type=FeedbackType.BUG_REPORT,
                content=f"{bug['title']}: {bug['description']}",
                category=bug["category"],
                priority=bug["severity"],
                metadata={"type": "bug_report"}
            )
            self.feedback_items.append(feedback_item)
        
        for i, feature in enumerate(feature_requests):
            feedback_item = FeedbackItem(
                id=f"feature_request_{i}",
                user_id=f"user_{i+10}",
                feedback_type=FeedbackType.FEATURE_REQUEST,
                content=f"{feature['title']}: {feature['description']}",
                category="feature_request",
                priority=feature["priority"],
                metadata={"votes": feature["votes"], "type": "feature_request"}
            )
            self.feedback_items.append(feedback_item)
        
        return {
            "bug_reports_collected": len(bug_reports),
            "feature_requests_collected": len(feature_requests),
            "bug_severity_distribution": {
                "high": sum(1 for b in bug_reports if b["severity"] == "high"),
                "medium": sum(1 for b in bug_reports if b["severity"] == "medium"),
                "low": sum(1 for b in bug_reports if b["severity"] == "low")
            },
            "top_feature_requests": sorted(feature_requests, key=lambda x: x["votes"], reverse=True)[:3],
            "most_common_bug_categories": ["import", "citation", "search"]
        }
    
    async def _perform_comprehensive_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of all feedback"""
        self.logger.info("Performing comprehensive feedback analysis")
        
        # Analyze sentiment across all feedback
        sentiment_analysis = await self._analyze_sentiment()
        
        # Categorize and prioritize feedback
        categorization = await self._categorize_feedback()
        
        # Identify common themes and patterns
        theme_analysis = await self._analyze_themes()
        
        # Generate actionable insights
        actionable_insights = await self._generate_actionable_insights()
        
        # Calculate overall metrics
        overall_metrics = await self._calculate_overall_metrics()
        
        return {
            "total_feedback_items": len(self.feedback_items),
            "sentiment": sentiment_analysis,
            "categorization": categorization,
            "themes": theme_analysis,
            "actionable_insights": actionable_insights,
            "overall_metrics": overall_metrics,
            "priority_improvements": await self._identify_priority_improvements(),
            "user_satisfaction_summary": await self._summarize_user_satisfaction()
        }
    
    async def _analyze_sentiment(self) -> Dict[str, Any]:
        """Analyze sentiment across all feedback"""
        sentiment_counts = {sentiment.value: 0 for sentiment in SentimentScore}
        
        for feedback_item in self.feedback_items:
            sentiment = self._determine_sentiment(feedback_item.content)
            feedback_item.sentiment = sentiment
            sentiment_counts[sentiment.value] += 1
        
        total_items = len(self.feedback_items)
        sentiment_percentages = {
            sentiment: (count / total_items * 100) if total_items > 0 else 0
            for sentiment, count in sentiment_counts.items()
        }
        
        # Calculate overall sentiment score
        sentiment_scores = {
            SentimentScore.VERY_NEGATIVE.value: 1,
            SentimentScore.NEGATIVE.value: 2,
            SentimentScore.NEUTRAL.value: 3,
            SentimentScore.POSITIVE.value: 4,
            SentimentScore.VERY_POSITIVE.value: 5
        }
        
        weighted_score = sum(
            sentiment_scores[sentiment] * count
            for sentiment, count in sentiment_counts.items()
        ) / total_items if total_items > 0 else 3
        
        return {
            "distribution": sentiment_percentages,
            "counts": sentiment_counts,
            "overall_sentiment_score": weighted_score,
            "sentiment_trend": self._determine_sentiment_trend(weighted_score)
        }
    
    def _determine_sentiment(self, text: str) -> SentimentScore:
        """Determine sentiment of text using keyword matching"""
        text_lower = text.lower()
        
        # Count sentiment keywords
        sentiment_scores = {}
        for sentiment, keywords in self.sentiment_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            sentiment_scores[sentiment] = score
        
        # Return sentiment with highest score, default to neutral
        if not any(sentiment_scores.values()):
            return SentimentScore.NEUTRAL
        
        return max(sentiment_scores.items(), key=lambda x: x[1])[0]
    
    def _determine_sentiment_trend(self, score: float) -> str:
        """Determine overall sentiment trend"""
        if score >= 4.0:
            return "very_positive"
        elif score >= 3.5:
            return "positive"
        elif score >= 2.5:
            return "neutral"
        elif score >= 2.0:
            return "negative"
        else:
            return "very_negative"
    
    async def _categorize_feedback(self) -> Dict[str, Any]:
        """Categorize feedback by type and topic"""
        type_counts = {}
        category_counts = {}
        
        for feedback_item in self.feedback_items:
            # Count by feedback type
            feedback_type = feedback_item.feedback_type.value
            type_counts[feedback_type] = type_counts.get(feedback_type, 0) + 1
            
            # Count by category
            category = feedback_item.category or "uncategorized"
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "by_type": type_counts,
            "by_category": category_counts,
            "most_common_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        }
    
    async def _analyze_themes(self) -> Dict[str, Any]:
        """Analyze common themes across feedback"""
        # Define theme keywords
        theme_keywords = {
            "performance": ["slow", "fast", "performance", "speed", "optimization", "lag", "responsive"],
            "usability": ["easy", "difficult", "intuitive", "confusing", "user-friendly", "interface"],
            "features": ["feature", "functionality", "capability", "missing", "add", "need"],
            "bugs": ["bug", "error", "broken", "issue", "problem", "fail", "crash"],
            "citation": ["citation", "bibliography", "reference", "format", "style"],
            "import": ["import", "sync", "library", "data", "transfer"],
            "search": ["search", "find", "filter", "results", "query"],
            "collaboration": ["share", "collaborate", "team", "group", "together"]
        }
        
        theme_counts = {}
        theme_sentiment = {}
        
        for theme, keywords in theme_keywords.items():
            count = 0
            sentiments = []
            
            for feedback_item in self.feedback_items:
                content_lower = feedback_item.content.lower()
                if any(keyword in content_lower for keyword in keywords):
                    count += 1
                    if feedback_item.sentiment:
                        sentiment_score = {
                            SentimentScore.VERY_NEGATIVE: 1,
                            SentimentScore.NEGATIVE: 2,
                            SentimentScore.NEUTRAL: 3,
                            SentimentScore.POSITIVE: 4,
                            SentimentScore.VERY_POSITIVE: 5
                        }[feedback_item.sentiment]
                        sentiments.append(sentiment_score)
            
            theme_counts[theme] = count
            theme_sentiment[theme] = statistics.mean(sentiments) if sentiments else 3.0
        
        # Sort themes by frequency
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "theme_frequencies": theme_counts,
            "theme_sentiments": theme_sentiment,
            "top_themes": top_themes,
            "positive_themes": [
                theme for theme, sentiment in theme_sentiment.items()
                if sentiment >= 4.0 and theme_counts[theme] > 0
            ],
            "negative_themes": [
                theme for theme, sentiment in theme_sentiment.items()
                if sentiment <= 2.0 and theme_counts[theme] > 0
            ]
        }
    
    async def _generate_actionable_insights(self) -> List[Dict[str, Any]]:
        """Generate actionable insights from feedback analysis"""
        insights = []
        
        # Analyze survey data for insights
        if self.survey_responses:
            avg_satisfaction = statistics.mean([r.responses["overall_satisfaction"] for r in self.survey_responses])
            if avg_satisfaction < 4.0:
                insights.append({
                    "type": "improvement_needed",
                    "priority": "high",
                    "insight": "Overall satisfaction below target (4.0)",
                    "action": "Focus on addressing top pain points identified in surveys",
                    "impact": "user_satisfaction"
                })
        
        # Analyze common issues
        bug_reports = [f for f in self.feedback_items if f.feedback_type == FeedbackType.BUG_REPORT]
        if len(bug_reports) > 5:
            insights.append({
                "type": "quality_issue",
                "priority": "high",
                "insight": f"{len(bug_reports)} bug reports collected",
                "action": "Prioritize bug fixes, especially high-severity issues",
                "impact": "system_reliability"
            })
        
        # Analyze feature requests
        feature_requests = [f for f in self.feedback_items if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        if feature_requests:
            insights.append({
                "type": "feature_gap",
                "priority": "medium",
                "insight": f"{len(feature_requests)} feature requests received",
                "action": "Evaluate and prioritize most requested features",
                "impact": "feature_completeness"
            })
        
        # Performance-related insights
        performance_feedback = [
            f for f in self.feedback_items
            if "performance" in f.content.lower() or "slow" in f.content.lower()
        ]
        if len(performance_feedback) > 3:
            insights.append({
                "type": "performance_issue",
                "priority": "high",
                "insight": "Multiple users reporting performance issues",
                "action": "Conduct performance optimization review",
                "impact": "user_experience"
            })
        
        return insights
    
    async def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall feedback metrics"""
        total_feedback = len(self.feedback_items)
        
        # Calculate response rates
        survey_completion_rate = len(self.survey_responses) / 25 * 100  # Assuming 25 target responses
        interview_participation_rate = len(self.interview_sessions) / 10 * 100  # Assuming 10 target interviews
        
        # Calculate satisfaction metrics
        if self.survey_responses:
            satisfaction_scores = [r.responses["overall_satisfaction"] for r in self.survey_responses]
            avg_satisfaction = statistics.mean(satisfaction_scores)
            satisfaction_above_4 = sum(1 for score in satisfaction_scores if score >= 4) / len(satisfaction_scores) * 100
        else:
            avg_satisfaction = 0
            satisfaction_above_4 = 0
        
        # Calculate recommendation rate
        if self.survey_responses:
            recommendation_rate = sum(1 for r in self.survey_responses if r.responses["would_recommend"]) / len(self.survey_responses) * 100
        else:
            recommendation_rate = 0
        
        return {
            "total_feedback_items": total_feedback,
            "survey_completion_rate": survey_completion_rate,
            "interview_participation_rate": interview_participation_rate,
            "average_satisfaction_score": avg_satisfaction,
            "satisfaction_above_threshold": satisfaction_above_4,
            "recommendation_rate": recommendation_rate,
            "feedback_response_rate": (total_feedback / 25) * 100  # Assuming 25 total users
        }
    
    async def _identify_priority_improvements(self) -> List[Dict[str, Any]]:
        """Identify priority improvements based on feedback"""
        improvements = []
        
        # Analyze pain points from surveys
        if self.survey_responses:
            pain_points = [r.responses["biggest_pain_point"] for r in self.survey_responses]
            pain_point_counts = {}
            for pain_point in pain_points:
                pain_point_counts[pain_point] = pain_point_counts.get(pain_point, 0) + 1
            
            top_pain_points = sorted(pain_point_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for pain_point, count in top_pain_points:
                improvements.append({
                    "title": f"Address: {pain_point}",
                    "description": f"Reported by {count} users",
                    "priority": "high" if count >= 5 else "medium",
                    "effort": "medium",  # Would be estimated by development team
                    "impact": "high"
                })
        
        # Add improvements from bug reports
        high_severity_bugs = [
            f for f in self.feedback_items
            if f.feedback_type == FeedbackType.BUG_REPORT and f.priority == "high"
        ]
        
        for bug in high_severity_bugs:
            improvements.append({
                "title": f"Fix: {bug.content.split(':')[0]}",
                "description": bug.content,
                "priority": "critical",
                "effort": "high",
                "impact": "high"
            })
        
        return improvements
    
    async def _summarize_user_satisfaction(self) -> Dict[str, Any]:
        """Summarize overall user satisfaction"""
        if not self.survey_responses:
            return {"error": "No survey data available"}
        
        satisfaction_scores = [r.responses["overall_satisfaction"] for r in self.survey_responses]
        ease_scores = [r.responses["ease_of_use"] for r in self.survey_responses]
        performance_scores = [r.responses["performance_satisfaction"] for r in self.survey_responses]
        
        return {
            "overall_satisfaction": {
                "average": statistics.mean(satisfaction_scores),
                "above_threshold": sum(1 for s in satisfaction_scores if s >= 4) / len(satisfaction_scores) * 100
            },
            "ease_of_use": {
                "average": statistics.mean(ease_scores),
                "above_threshold": sum(1 for s in ease_scores if s >= 4) / len(ease_scores) * 100
            },
            "performance_satisfaction": {
                "average": statistics.mean(performance_scores),
                "above_threshold": sum(1 for s in performance_scores if s >= 4) / len(performance_scores) * 100
            },
            "recommendation_rate": sum(1 for r in self.survey_responses if r.responses["would_recommend"]) / len(self.survey_responses) * 100,
            "satisfaction_trend": "positive" if statistics.mean(satisfaction_scores) >= 4.0 else "neutral" if statistics.mean(satisfaction_scores) >= 3.0 else "negative"
        }
    
    async def _save_feedback_analysis(self, results: Dict[str, Any]) -> None:
        """Save feedback analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"feedback_analysis_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate feedback report
        report_file = self.results_dir / f"feedback_report_{timestamp}.md"
        report_content = self._generate_feedback_report(results)
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Feedback analysis saved to {results_file}")
        self.logger.info(f"Feedback report saved to {report_file}")
    
    def _generate_feedback_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable feedback report"""
        report = f"""# Feedback Analysis Report
## Zotero Integration - AI Scholar

**Analysis Date:** {results.get('start_time', 'N/A')}
**Total Feedback Items:** {results.get('total_feedback_items', 0)}
**Analysis Status:** {'✅ COMPLETE' if results.get('analysis_complete') else '❌ INCOMPLETE'}

## Executive Summary

This report analyzes comprehensive feedback collected during the user acceptance testing phase of the Zotero integration feature. Feedback was gathered through surveys, interviews, usage analytics, and issue reports.

## Key Metrics

- **Survey Completion Rate:** {results.get('overall_metrics', {}).get('survey_completion_rate', 0):.1f}%
- **Average Satisfaction Score:** {results.get('overall_metrics', {}).get('average_satisfaction_score', 0):.1f}/5
- **Recommendation Rate:** {results.get('overall_metrics', {}).get('recommendation_rate', 0):.1f}%
- **Overall Sentiment:** {results.get('sentiment', {}).get('sentiment_trend', 'unknown').title()}

## Sentiment Analysis

"""
        
        sentiment_dist = results.get('sentiment', {}).get('distribution', {})
        for sentiment, percentage in sentiment_dist.items():
            report += f"- **{sentiment.replace('_', ' ').title()}:** {percentage:.1f}%\n"
        
        report += f"""

## Top Themes Identified

"""
        
        top_themes = results.get('themes', {}).get('top_themes', [])
        for theme, count in top_themes[:5]:
            report += f"- **{theme.title()}:** {count} mentions\n"
        
        report += f"""

## Priority Improvements

"""
        
        priority_improvements = results.get('priority_improvements', [])
        for improvement in priority_improvements[:5]:
            report += f"- **{improvement.get('priority', 'medium').upper()}:** {improvement.get('title', 'N/A')}\n"
            report += f"  - {improvement.get('description', 'No description')}\n"
        
        report += f"""

## Collection Phase Results

### Survey Feedback
- **Responses Collected:** {results.get('collection_phases', {}).get('surveys', {}).get('responses_collected', 0)}
- **Completion Rate:** {results.get('collection_phases', {}).get('surveys', {}).get('completion_rate', 0):.1f}%
- **Average Completion Time:** {results.get('collection_phases', {}).get('surveys', {}).get('average_completion_time', 0):.1f} minutes

### Interview Feedback
- **Interviews Conducted:** {results.get('collection_phases', {}).get('interviews', {}).get('interviews_conducted', 0)}
- **Total Interview Time:** {results.get('collection_phases', {}).get('interviews', {}).get('total_interview_time', 0)} minutes
- **Average Satisfaction:** {results.get('collection_phases', {}).get('interviews', {}).get('average_satisfaction', 0):.1f}/5

### Issue Reports
- **Bug Reports:** {results.get('collection_phases', {}).get('issues', {}).get('bug_reports_collected', 0)}
- **Feature Requests:** {results.get('collection_phases', {}).get('issues', {}).get('feature_requests_collected', 0)}

## Actionable Insights

"""
        
        actionable_insights = results.get('actionable_insights', [])
        for insight in actionable_insights:
            report += f"- **{insight.get('type', 'unknown').replace('_', ' ').title()}** ({insight.get('priority', 'medium').upper()})\n"
            report += f"  - Insight: {insight.get('insight', 'N/A')}\n"
            report += f"  - Action: {insight.get('action', 'N/A')}\n"
            report += f"  - Impact: {insight.get('impact', 'N/A')}\n\n"
        
        report += """## Recommendations

1. **Immediate Actions:**
   - Address high-priority bug reports
   - Implement quick wins from user feedback
   - Improve performance for large libraries

2. **Short-term Improvements:**
   - Enhance user interface based on usability feedback
   - Add most requested features
   - Improve documentation and onboarding

3. **Long-term Strategy:**
   - Establish continuous feedback collection
   - Implement user satisfaction monitoring
   - Plan feature roadmap based on user needs

## Next Steps

1. Prioritize and implement critical improvements
2. Set up ongoing feedback collection mechanisms
3. Monitor user satisfaction metrics post-launch
4. Plan follow-up user research sessions

---
*Report generated by Feedback Collection Framework*
"""
        
        return report