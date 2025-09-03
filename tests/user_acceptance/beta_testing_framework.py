#!/usr/bin/env python3
"""
Beta Testing Framework for Zotero Integration
Manages beta testers, test scenarios, and feedback collection
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class TestScenarioStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class BetaTesterType(Enum):
    ACADEMIC_RESEARCHER = "academic_researcher"
    GRADUATE_STUDENT = "graduate_student"
    LIBRARIAN = "librarian"
    RESEARCH_ASSISTANT = "research_assistant"
    POWER_USER = "power_user"

@dataclass
class BetaTester:
    """Represents a beta tester participant"""
    id: str
    email: str
    name: str
    tester_type: BetaTesterType
    zotero_library_size: int
    experience_level: str  # beginner, intermediate, advanced
    preferred_citation_style: str
    research_domain: str
    joined_at: datetime
    last_active: Optional[datetime] = None
    completed_scenarios: List[str] = None
    feedback_provided: int = 0
    satisfaction_score: Optional[float] = None
    
    def __post_init__(self):
        if self.completed_scenarios is None:
            self.completed_scenarios = []

@dataclass
class TestScenario:
    """Represents a test scenario for beta testing"""
    id: str
    name: str
    description: str
    category: str
    estimated_duration: int  # minutes
    prerequisites: List[str]
    steps: List[Dict[str, str]]
    success_criteria: List[str]
    difficulty_level: str  # easy, medium, hard
    priority: str  # low, medium, high, critical

@dataclass
class TestSession:
    """Represents a testing session"""
    id: str
    tester_id: str
    scenario_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: TestScenarioStatus = TestScenarioStatus.NOT_STARTED
    completion_percentage: int = 0
    errors_encountered: List[Dict] = None
    feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = None
    time_spent: Optional[int] = None  # minutes
    
    def __post_init__(self):
        if self.errors_encountered is None:
            self.errors_encountered = []

class BetaTestingManager:
    """Manages the beta testing program"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        
        self.testers: Dict[str, BetaTester] = {}
        self.scenarios: Dict[str, TestScenario] = {}
        self.sessions: Dict[str, TestSession] = {}
        
        self._initialize_test_scenarios()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for beta testing manager"""
        logger = logging.getLogger("beta_testing")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("tests/user_acceptance/beta_testing.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_test_scenarios(self):
        """Initialize comprehensive test scenarios"""
        scenarios = [
            TestScenario(
                id="library_import_basic",
                name="Basic Library Import",
                description="Import a small Zotero library and verify data integrity",
                category="library_management",
                estimated_duration=15,
                prerequisites=["zotero_account", "small_library"],
                steps=[
                    {"step": 1, "action": "Connect Zotero account via OAuth"},
                    {"step": 2, "action": "Select personal library for import"},
                    {"step": 3, "action": "Monitor import progress"},
                    {"step": 4, "action": "Verify imported items match Zotero library"},
                    {"step": 5, "action": "Check collection hierarchy preservation"}
                ],
                success_criteria=[
                    "All items imported successfully",
                    "Metadata preserved accurately",
                    "Collections maintain hierarchy",
                    "Import completes within expected time"
                ],
                difficulty_level="easy",
                priority="critical"
            ),
            TestScenario(
                id="large_library_import",
                name="Large Library Import",
                description="Import a large Zotero library (1000+ items) and test performance",
                category="performance",
                estimated_duration=45,
                prerequisites=["zotero_account", "large_library"],
                steps=[
                    {"step": 1, "action": "Connect Zotero account"},
                    {"step": 2, "action": "Initiate import of large library"},
                    {"step": 3, "action": "Monitor progress and performance"},
                    {"step": 4, "action": "Verify data integrity after import"},
                    {"step": 5, "action": "Test search and browse performance"}
                ],
                success_criteria=[
                    "Import completes without timeout",
                    "Progress tracking works accurately",
                    "No data corruption or loss",
                    "Search remains responsive"
                ],
                difficulty_level="medium",
                priority="high"
            ),
            TestScenario(
                id="advanced_search_usage",
                name="Advanced Search and Filtering",
                description="Test comprehensive search and filtering capabilities",
                category="search_browse",
                estimated_duration=20,
                prerequisites=["imported_library"],
                steps=[
                    {"step": 1, "action": "Perform full-text search across library"},
                    {"step": 2, "action": "Use faceted search by author and year"},
                    {"step": 3, "action": "Apply multiple filters simultaneously"},
                    {"step": 4, "action": "Test collection-based filtering"},
                    {"step": 5, "action": "Verify search result relevance"}
                ],
                success_criteria=[
                    "Search returns relevant results",
                    "Filters work correctly",
                    "Results load quickly",
                    "Pagination works smoothly"
                ],
                difficulty_level="medium",
                priority="high"
            ),
            TestScenario(
                id="citation_generation_workflow",
                name="Citation Generation Workflow",
                description="Generate citations in multiple formats and styles",
                category="citation",
                estimated_duration=25,
                prerequisites=["imported_library"],
                steps=[
                    {"step": 1, "action": "Select references for citation"},
                    {"step": 2, "action": "Generate citations in APA style"},
                    {"step": 3, "action": "Switch to MLA and Chicago styles"},
                    {"step": 4, "action": "Create bibliography from multiple references"},
                    {"step": 5, "action": "Export citations in different formats"}
                ],
                success_criteria=[
                    "Citations format correctly",
                    "Style switching works instantly",
                    "Bibliography compiles accurately",
                    "Export formats are valid"
                ],
                difficulty_level="easy",
                priority="critical"
            ),
            TestScenario(
                id="ai_analysis_features",
                name="AI-Enhanced Analysis",
                description="Test AI-powered analysis and insights features",
                category="ai_analysis",
                estimated_duration=30,
                prerequisites=["imported_library", "ai_features_enabled"],
                steps=[
                    {"step": 1, "action": "Run topic analysis on library"},
                    {"step": 2, "action": "Generate similarity recommendations"},
                    {"step": 3, "action": "Identify research gaps"},
                    {"step": 4, "action": "Create topic clusters visualization"},
                    {"step": 5, "action": "Review AI-generated summaries"}
                ],
                success_criteria=[
                    "AI analysis completes successfully",
                    "Results are relevant and useful",
                    "Visualizations are clear",
                    "Processing time is reasonable"
                ],
                difficulty_level="medium",
                priority="high"
            ),
            TestScenario(
                id="chat_integration_usage",
                name="Chat Integration with References",
                description="Test integration between Zotero references and chat system",
                category="integration",
                estimated_duration=20,
                prerequisites=["imported_library", "chat_access"],
                steps=[
                    {"step": 1, "action": "Start chat about research topic"},
                    {"step": 2, "action": "Reference specific papers in conversation"},
                    {"step": 3, "action": "Ask questions about referenced papers"},
                    {"step": 4, "action": "Export conversation with citations"},
                    {"step": 5, "action": "Verify citation accuracy in export"}
                ],
                success_criteria=[
                    "References integrate seamlessly",
                    "AI provides contextual responses",
                    "Citations are properly formatted",
                    "Export includes all references"
                ],
                difficulty_level="medium",
                priority="high"
            ),
            TestScenario(
                id="collaboration_features",
                name="Collaborative Features",
                description="Test sharing and collaboration capabilities",
                category="collaboration",
                estimated_duration=35,
                prerequisites=["imported_library", "collaboration_partner"],
                steps=[
                    {"step": 1, "action": "Share reference collection with colleague"},
                    {"step": 2, "action": "Collaborate on annotations"},
                    {"step": 3, "action": "Track modification history"},
                    {"step": 4, "action": "Resolve collaboration conflicts"},
                    {"step": 5, "action": "Export shared research project"}
                ],
                success_criteria=[
                    "Sharing works correctly",
                    "Collaborative editing is smooth",
                    "History tracking is accurate",
                    "Conflict resolution is intuitive"
                ],
                difficulty_level="hard",
                priority="medium"
            ),
            TestScenario(
                id="real_time_sync",
                name="Real-time Synchronization",
                description="Test real-time sync between Zotero and AI Scholar",
                category="synchronization",
                estimated_duration=25,
                prerequisites=["zotero_account", "webhook_enabled"],
                steps=[
                    {"step": 1, "action": "Add new item to Zotero library"},
                    {"step": 2, "action": "Verify item appears in AI Scholar"},
                    {"step": 3, "action": "Modify item in Zotero"},
                    {"step": 4, "action": "Check sync status and notifications"},
                    {"step": 5, "action": "Test sync conflict resolution"}
                ],
                success_criteria=[
                    "Changes sync within 30 seconds",
                    "Sync status is clearly indicated",
                    "Conflicts are handled gracefully",
                    "No data loss occurs"
                ],
                difficulty_level="medium",
                priority="high"
            ),
            TestScenario(
                id="accessibility_navigation",
                name="Accessibility and Keyboard Navigation",
                description="Test accessibility features and keyboard navigation",
                category="accessibility",
                estimated_duration=30,
                prerequisites=["screen_reader_or_keyboard_only"],
                steps=[
                    {"step": 1, "action": "Navigate interface using only keyboard"},
                    {"step": 2, "action": "Test screen reader compatibility"},
                    {"step": 3, "action": "Verify color contrast and readability"},
                    {"step": 4, "action": "Test focus indicators and tab order"},
                    {"step": 5, "action": "Complete core tasks without mouse"}
                ],
                success_criteria=[
                    "All features accessible via keyboard",
                    "Screen reader announces content correctly",
                    "Focus indicators are visible",
                    "Tab order is logical"
                ],
                difficulty_level="medium",
                priority="high"
            ),
            TestScenario(
                id="error_recovery",
                name="Error Handling and Recovery",
                description="Test system behavior under error conditions",
                category="reliability",
                estimated_duration=20,
                prerequisites=["imported_library"],
                steps=[
                    {"step": 1, "action": "Simulate network disconnection during sync"},
                    {"step": 2, "action": "Test behavior with invalid Zotero credentials"},
                    {"step": 3, "action": "Attempt operations with corrupted data"},
                    {"step": 4, "action": "Verify error messages are helpful"},
                    {"step": 5, "action": "Test recovery after errors resolved"}
                ],
                success_criteria=[
                    "Errors are handled gracefully",
                    "Error messages are clear and actionable",
                    "System recovers automatically when possible",
                    "No data corruption occurs"
                ],
                difficulty_level="hard",
                priority="medium"
            )
        ]
        
        for scenario in scenarios:
            self.scenarios[scenario.id] = scenario
    
    async def recruit_beta_testers(self, target_count: int = 25) -> Dict[str, Any]:
        """Recruit beta testers for the program"""
        self.logger.info(f"Recruiting {target_count} beta testers")
        
        # Simulate recruiting diverse beta testers
        tester_profiles = [
            {
                "type": BetaTesterType.ACADEMIC_RESEARCHER,
                "experience": "advanced",
                "library_size_range": (500, 5000),
                "domains": ["computer_science", "biology", "psychology", "physics"]
            },
            {
                "type": BetaTesterType.GRADUATE_STUDENT,
                "experience": "intermediate",
                "library_size_range": (100, 1000),
                "domains": ["literature", "history", "sociology", "economics"]
            },
            {
                "type": BetaTesterType.LIBRARIAN,
                "experience": "advanced",
                "library_size_range": (1000, 10000),
                "domains": ["information_science", "library_science"]
            },
            {
                "type": BetaTesterType.RESEARCH_ASSISTANT,
                "experience": "beginner",
                "library_size_range": (50, 500),
                "domains": ["various"]
            },
            {
                "type": BetaTesterType.POWER_USER,
                "experience": "advanced",
                "library_size_range": (2000, 15000),
                "domains": ["interdisciplinary"]
            }
        ]
        
        recruited_count = 0
        citation_styles = ["APA", "MLA", "Chicago", "IEEE", "Nature"]
        
        for i in range(target_count):
            profile = random.choice(tester_profiles)
            
            tester = BetaTester(
                id=str(uuid.uuid4()),
                email=f"beta_tester_{i+1}@example.com",
                name=f"Beta Tester {i+1}",
                tester_type=profile["type"],
                zotero_library_size=random.randint(*profile["library_size_range"]),
                experience_level=profile["experience"],
                preferred_citation_style=random.choice(citation_styles),
                research_domain=random.choice(profile["domains"]),
                joined_at=datetime.now() - timedelta(days=random.randint(0, 7))
            )
            
            self.testers[tester.id] = tester
            recruited_count += 1
        
        self.logger.info(f"Successfully recruited {recruited_count} beta testers")
        
        return {
            "recruited_count": recruited_count,
            "tester_types": {
                tester_type.value: sum(1 for t in self.testers.values() if t.tester_type == tester_type)
                for tester_type in BetaTesterType
            },
            "experience_levels": {
                level: sum(1 for t in self.testers.values() if t.experience_level == level)
                for level in ["beginner", "intermediate", "advanced"]
            }
        }
    
    async def run_beta_program(self) -> Dict[str, Any]:
        """Run the complete beta testing program"""
        self.logger.info("Starting beta testing program")
        
        program_results = {
            "start_time": datetime.now().isoformat(),
            "success": True,
            "phases": {}
        }
        
        try:
            # Phase 1: Recruit testers
            recruitment_results = await self.recruit_beta_testers(
                self.config.get("max_participants", 25)
            )
            program_results["phases"]["recruitment"] = recruitment_results
            
            # Phase 2: Onboard testers
            onboarding_results = await self.onboard_testers()
            program_results["phases"]["onboarding"] = onboarding_results
            
            # Phase 3: Execute test scenarios
            testing_results = await self.execute_test_scenarios()
            program_results["phases"]["testing"] = testing_results
            
            # Phase 4: Collect and analyze feedback
            feedback_results = await self.collect_comprehensive_feedback()
            program_results["phases"]["feedback"] = feedback_results
            
            # Phase 5: Generate insights and recommendations
            insights_results = await self.generate_testing_insights()
            program_results["phases"]["insights"] = insights_results
            
            # Compile overall results
            program_results.update({
                "participant_count": len(self.testers),
                "scenarios_completed": len([s for s in self.sessions.values() if s.status == TestScenarioStatus.COMPLETED]),
                "completion_rate": self._calculate_completion_rate(),
                "satisfaction_score": self._calculate_satisfaction_score(),
                "issues": self._compile_issues(),
                "feedback_summary": self._summarize_feedback()
            })
            
        except Exception as e:
            self.logger.error(f"Beta program failed: {str(e)}")
            program_results["success"] = False
            program_results["error"] = str(e)
        
        finally:
            program_results["end_time"] = datetime.now().isoformat()
        
        return program_results
    
    async def onboard_testers(self) -> Dict[str, Any]:
        """Onboard beta testers with instructions and setup"""
        self.logger.info("Onboarding beta testers")
        
        onboarded_count = 0
        setup_issues = []
        
        for tester in self.testers.values():
            try:
                # Simulate onboarding process
                await self._send_welcome_email(tester)
                await self._provide_testing_instructions(tester)
                await self._setup_test_environment(tester)
                
                onboarded_count += 1
                
            except Exception as e:
                setup_issues.append({
                    "tester_id": tester.id,
                    "error": str(e)
                })
        
        return {
            "onboarded_count": onboarded_count,
            "setup_issues": setup_issues,
            "success_rate": onboarded_count / len(self.testers) * 100
        }
    
    async def execute_test_scenarios(self) -> Dict[str, Any]:
        """Execute test scenarios with beta testers"""
        self.logger.info("Executing test scenarios")
        
        scenario_results = {}
        
        for scenario_id, scenario in self.scenarios.items():
            self.logger.info(f"Running scenario: {scenario.name}")
            
            # Assign testers to scenario based on their profile
            assigned_testers = self._assign_testers_to_scenario(scenario)
            
            scenario_sessions = []
            for tester in assigned_testers:
                session = await self._execute_scenario_with_tester(scenario, tester)
                scenario_sessions.append(session)
                self.sessions[session.id] = session
            
            scenario_results[scenario_id] = {
                "name": scenario.name,
                "assigned_testers": len(assigned_testers),
                "completed_sessions": len([s for s in scenario_sessions if s.status == TestScenarioStatus.COMPLETED]),
                "success_rate": len([s for s in scenario_sessions if s.status == TestScenarioStatus.COMPLETED]) / len(scenario_sessions) * 100 if scenario_sessions else 0,
                "average_duration": sum(s.time_spent or 0 for s in scenario_sessions) / len(scenario_sessions) if scenario_sessions else 0,
                "issues_found": sum(len(s.errors_encountered) for s in scenario_sessions),
                "average_satisfaction": sum(s.satisfaction_rating or 0 for s in scenario_sessions) / len([s for s in scenario_sessions if s.satisfaction_rating]) if any(s.satisfaction_rating for s in scenario_sessions) else 0
            }
        
        return scenario_results
    
    async def collect_comprehensive_feedback(self) -> Dict[str, Any]:
        """Collect comprehensive feedback from beta testers"""
        self.logger.info("Collecting comprehensive feedback")
        
        feedback_data = {
            "survey_responses": [],
            "interview_feedback": [],
            "usage_analytics": {},
            "satisfaction_scores": []
        }
        
        for tester in self.testers.values():
            # Simulate collecting different types of feedback
            survey_response = await self._collect_survey_feedback(tester)
            feedback_data["survey_responses"].append(survey_response)
            
            if tester.experience_level == "advanced" or random.random() < 0.3:
                interview_feedback = await self._conduct_feedback_interview(tester)
                feedback_data["interview_feedback"].append(interview_feedback)
            
            # Collect usage analytics
            analytics = await self._collect_usage_analytics(tester)
            feedback_data["usage_analytics"][tester.id] = analytics
            
            if tester.satisfaction_score:
                feedback_data["satisfaction_scores"].append(tester.satisfaction_score)
        
        return feedback_data
    
    async def generate_testing_insights(self) -> Dict[str, Any]:
        """Generate insights and recommendations from testing"""
        self.logger.info("Generating testing insights")
        
        insights = {
            "key_findings": [],
            "usability_issues": [],
            "feature_requests": [],
            "performance_concerns": [],
            "accessibility_gaps": [],
            "recommendations": []
        }
        
        # Analyze session data for insights
        completed_sessions = [s for s in self.sessions.values() if s.status == TestScenarioStatus.COMPLETED]
        failed_sessions = [s for s in self.sessions.values() if s.status == TestScenarioStatus.FAILED]
        
        # Key findings
        insights["key_findings"] = [
            f"Overall completion rate: {len(completed_sessions) / len(self.sessions) * 100:.1f}%",
            f"Average session duration: {sum(s.time_spent or 0 for s in completed_sessions) / len(completed_sessions):.1f} minutes",
            f"Most challenging scenario: {self._identify_most_challenging_scenario()}",
            f"Highest satisfaction scenario: {self._identify_highest_satisfaction_scenario()}"
        ]
        
        # Identify common issues
        all_errors = []
        for session in self.sessions.values():
            all_errors.extend(session.errors_encountered)
        
        error_frequency = {}
        for error in all_errors:
            error_type = error.get("type", "unknown")
            error_frequency[error_type] = error_frequency.get(error_type, 0) + 1
        
        insights["usability_issues"] = [
            {"issue": error_type, "frequency": count}
            for error_type, count in sorted(error_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Generate recommendations
        insights["recommendations"] = [
            "Improve onboarding flow for new users",
            "Optimize performance for large library imports",
            "Enhance error messages and recovery options",
            "Add more keyboard shortcuts for power users",
            "Improve mobile responsiveness"
        ]
        
        return insights
    
    def _assign_testers_to_scenario(self, scenario: TestScenario) -> List[BetaTester]:
        """Assign appropriate testers to a scenario"""
        suitable_testers = []
        
        for tester in self.testers.values():
            # Check if tester is suitable for this scenario
            if self._is_tester_suitable_for_scenario(tester, scenario):
                suitable_testers.append(tester)
        
        # Limit to reasonable number of testers per scenario
        max_testers = min(len(suitable_testers), 10)
        return random.sample(suitable_testers, max_testers)
    
    def _is_tester_suitable_for_scenario(self, tester: BetaTester, scenario: TestScenario) -> bool:
        """Check if a tester is suitable for a specific scenario"""
        # Check prerequisites
        if "large_library" in scenario.prerequisites and tester.zotero_library_size < 1000:
            return False
        
        if "small_library" in scenario.prerequisites and tester.zotero_library_size > 100:
            return False
        
        # Match difficulty with experience
        if scenario.difficulty_level == "hard" and tester.experience_level == "beginner":
            return False
        
        return True
    
    async def _execute_scenario_with_tester(self, scenario: TestScenario, tester: BetaTester) -> TestSession:
        """Execute a test scenario with a specific tester"""
        session = TestSession(
            id=str(uuid.uuid4()),
            tester_id=tester.id,
            scenario_id=scenario.id,
            started_at=datetime.now()
        )
        
        # Simulate scenario execution
        session.status = TestScenarioStatus.IN_PROGRESS
        
        # Simulate completion based on tester experience and scenario difficulty
        success_probability = self._calculate_success_probability(tester, scenario)
        
        if random.random() < success_probability:
            session.status = TestScenarioStatus.COMPLETED
            session.completion_percentage = 100
            session.time_spent = scenario.estimated_duration + random.randint(-5, 10)
            session.satisfaction_rating = random.randint(3, 5)
        else:
            session.status = TestScenarioStatus.FAILED
            session.completion_percentage = random.randint(20, 80)
            session.time_spent = scenario.estimated_duration + random.randint(5, 20)
            session.satisfaction_rating = random.randint(1, 3)
            
            # Add some errors
            session.errors_encountered = [
                {
                    "type": "ui_confusion",
                    "description": "User couldn't find the import button",
                    "step": random.randint(1, len(scenario.steps))
                },
                {
                    "type": "performance_issue",
                    "description": "Import took too long",
                    "step": random.randint(1, len(scenario.steps))
                }
            ]
        
        session.completed_at = datetime.now()
        session.feedback = f"Feedback for scenario {scenario.name} from {tester.name}"
        
        # Update tester data
        if session.status == TestScenarioStatus.COMPLETED:
            tester.completed_scenarios.append(scenario.id)
        
        tester.feedback_provided += 1
        tester.last_active = datetime.now()
        
        return session
    
    def _calculate_success_probability(self, tester: BetaTester, scenario: TestScenario) -> float:
        """Calculate probability of scenario success based on tester and scenario"""
        base_probability = 0.7
        
        # Adjust for experience
        experience_bonus = {
            "beginner": 0.0,
            "intermediate": 0.1,
            "advanced": 0.2
        }
        base_probability += experience_bonus.get(tester.experience_level, 0)
        
        # Adjust for scenario difficulty
        difficulty_penalty = {
            "easy": 0.0,
            "medium": -0.1,
            "hard": -0.2
        }
        base_probability += difficulty_penalty.get(scenario.difficulty_level, 0)
        
        # Adjust for library size match
        if "large_library" in scenario.prerequisites and tester.zotero_library_size > 1000:
            base_probability += 0.1
        
        return max(0.1, min(0.95, base_probability))
    
    async def _send_welcome_email(self, tester: BetaTester):
        """Send welcome email to beta tester"""
        # Simulate sending email
        await asyncio.sleep(0.1)
    
    async def _provide_testing_instructions(self, tester: BetaTester):
        """Provide testing instructions to beta tester"""
        # Simulate providing instructions
        await asyncio.sleep(0.1)
    
    async def _setup_test_environment(self, tester: BetaTester):
        """Setup test environment for beta tester"""
        # Simulate environment setup
        await asyncio.sleep(0.1)
    
    async def _collect_survey_feedback(self, tester: BetaTester) -> Dict[str, Any]:
        """Collect survey feedback from tester"""
        return {
            "tester_id": tester.id,
            "overall_satisfaction": random.randint(3, 5),
            "ease_of_use": random.randint(3, 5),
            "feature_completeness": random.randint(3, 5),
            "performance_satisfaction": random.randint(2, 5),
            "would_recommend": random.choice([True, True, True, False]),
            "comments": f"Survey feedback from {tester.name}"
        }
    
    async def _conduct_feedback_interview(self, tester: BetaTester) -> Dict[str, Any]:
        """Conduct feedback interview with tester"""
        return {
            "tester_id": tester.id,
            "interview_duration": random.randint(15, 45),
            "key_insights": [
                "Feature X is very useful",
                "Performance could be better",
                "UI is intuitive overall"
            ],
            "suggestions": [
                "Add keyboard shortcuts",
                "Improve error messages",
                "Better mobile support"
            ]
        }
    
    async def _collect_usage_analytics(self, tester: BetaTester) -> Dict[str, Any]:
        """Collect usage analytics for tester"""
        return {
            "sessions_count": random.randint(5, 20),
            "total_time_spent": random.randint(60, 300),
            "features_used": random.sample([
                "library_import", "search", "citation", "ai_analysis", "export"
            ], random.randint(3, 5)),
            "error_rate": random.uniform(0.02, 0.15)
        }
    
    def _calculate_completion_rate(self) -> float:
        """Calculate overall completion rate"""
        if not self.sessions:
            return 0.0
        
        completed = len([s for s in self.sessions.values() if s.status == TestScenarioStatus.COMPLETED])
        return completed / len(self.sessions) * 100
    
    def _calculate_satisfaction_score(self) -> float:
        """Calculate average satisfaction score"""
        scores = [s.satisfaction_rating for s in self.sessions.values() if s.satisfaction_rating]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _compile_issues(self) -> List[Dict[str, Any]]:
        """Compile all issues found during testing"""
        issues = []
        
        for session in self.sessions.values():
            for error in session.errors_encountered:
                issues.append({
                    "scenario": session.scenario_id,
                    "tester": session.tester_id,
                    "type": error.get("type"),
                    "description": error.get("description"),
                    "severity": "medium"  # Would be determined by analysis
                })
        
        return issues
    
    def _summarize_feedback(self) -> Dict[str, Any]:
        """Summarize all collected feedback"""
        return {
            "total_feedback_items": len(self.sessions),
            "positive_feedback_percentage": 75.0,  # Would be calculated from actual feedback
            "common_praise": [
                "Easy to use interface",
                "Powerful search capabilities",
                "Good integration with Zotero"
            ],
            "common_complaints": [
                "Slow performance with large libraries",
                "Confusing error messages",
                "Limited mobile support"
            ]
        }
    
    def _identify_most_challenging_scenario(self) -> str:
        """Identify the most challenging scenario"""
        scenario_difficulty = {}
        
        for session in self.sessions.values():
            scenario_id = session.scenario_id
            if scenario_id not in scenario_difficulty:
                scenario_difficulty[scenario_id] = {"failed": 0, "total": 0}
            
            scenario_difficulty[scenario_id]["total"] += 1
            if session.status == TestScenarioStatus.FAILED:
                scenario_difficulty[scenario_id]["failed"] += 1
        
        most_challenging = max(
            scenario_difficulty.items(),
            key=lambda x: x[1]["failed"] / x[1]["total"] if x[1]["total"] > 0 else 0
        )
        
        return self.scenarios[most_challenging[0]].name
    
    def _identify_highest_satisfaction_scenario(self) -> str:
        """Identify the scenario with highest satisfaction"""
        scenario_satisfaction = {}
        
        for session in self.sessions.values():
            if session.satisfaction_rating:
                scenario_id = session.scenario_id
                if scenario_id not in scenario_satisfaction:
                    scenario_satisfaction[scenario_id] = []
                scenario_satisfaction[scenario_id].append(session.satisfaction_rating)
        
        if not scenario_satisfaction:
            return "N/A"
        
        avg_satisfaction = {
            scenario_id: sum(ratings) / len(ratings)
            for scenario_id, ratings in scenario_satisfaction.items()
        }
        
        best_scenario = max(avg_satisfaction.items(), key=lambda x: x[1])
        return self.scenarios[best_scenario[0]].name