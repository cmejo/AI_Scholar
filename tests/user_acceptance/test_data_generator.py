#!/usr/bin/env python3
"""
Test Data Generator for User Acceptance Testing
Generates realistic test data for comprehensive UAT scenarios
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import string

@dataclass
class TestUser:
    """Represents a test user for UAT"""
    id: str
    name: str
    email: str
    user_type: str
    experience_level: str
    research_domain: str
    library_size: int
    preferred_citation_style: str
    created_at: datetime

@dataclass
class TestLibrary:
    """Represents a test Zotero library"""
    id: str
    name: str
    owner_id: str
    item_count: int
    collection_count: int
    library_type: str  # personal, group
    created_at: datetime
    items: List[Dict[str, Any]]
    collections: List[Dict[str, Any]]

class TestDataGenerator:
    """Generates comprehensive test data for UAT scenarios"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        
        self.output_dir = Path("tests/user_acceptance/test_data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data templates
        self._init_data_templates()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for test data generator"""
        logger = logging.getLogger("test_data_generator")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("tests/user_acceptance/test_data_generation.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_data_templates(self):
        """Initialize data templates for generation"""
        self.research_domains = [
            "Computer Science", "Biology", "Psychology", "Physics", "Chemistry",
            "Literature", "History", "Sociology", "Economics", "Medicine",
            "Engineering", "Mathematics", "Philosophy", "Political Science",
            "Environmental Science", "Neuroscience", "Linguistics", "Anthropology"
        ]
        
        self.citation_styles = ["APA", "MLA", "Chicago", "IEEE", "Nature", "Harvard"]
        
        self.user_types = [
            "academic_researcher", "graduate_student", "undergraduate_student",
            "librarian", "research_assistant", "professor", "postdoc"
        ]
        
        self.experience_levels = ["beginner", "intermediate", "advanced"]
        
        self.item_types = [
            "journalArticle", "book", "bookSection", "thesis", "conferencePaper",
            "report", "webpage", "patent", "manuscript", "presentation"
        ]
        
        # Sample academic data
        self.sample_authors = [
            "Smith, John", "Johnson, Mary", "Williams, David", "Brown, Sarah",
            "Jones, Michael", "Garcia, Maria", "Miller, Robert", "Davis, Jennifer",
            "Rodriguez, Carlos", "Martinez, Ana", "Anderson, James", "Taylor, Lisa",
            "Thomas, Christopher", "Jackson, Patricia", "White, Matthew", "Harris, Susan"
        ]
        
        self.sample_journals = [
            "Nature", "Science", "Cell", "The Lancet", "NEJM", "PNAS",
            "Journal of Computer Science", "IEEE Transactions", "ACM Computing Surveys",
            "Psychological Science", "American Psychologist", "Cognitive Science",
            "Physical Review Letters", "Journal of Physics", "Chemical Reviews",
            "Journal of Biological Chemistry", "Molecular Biology", "Genetics"
        ]
        
        self.sample_publishers = [
            "Elsevier", "Springer", "Wiley", "Taylor & Francis", "SAGE",
            "Cambridge University Press", "Oxford University Press", "MIT Press",
            "Harvard University Press", "University of Chicago Press"
        ]
        
        self.research_keywords = [
            "machine learning", "artificial intelligence", "neural networks",
            "climate change", "sustainability", "renewable energy",
            "gene therapy", "CRISPR", "protein folding", "cancer research",
            "quantum computing", "blockchain", "cybersecurity", "data mining",
            "social media", "digital humanities", "cognitive psychology",
            "behavioral economics", "public policy", "urban planning"
        ]
    
    async def generate_comprehensive_test_data(self) -> Dict[str, Any]:
        """Generate comprehensive test data for UAT"""
        self.logger.info("Starting comprehensive test data generation")
        
        generation_results = {
            "start_time": datetime.now().isoformat(),
            "data_sets": {},
            "generation_complete": False
        }
        
        try:
            # Generate test users
            self.logger.info("Generating test users")
            users = await self._generate_test_users(50)
            generation_results["data_sets"]["users"] = {
                "count": len(users),
                "file": "test_users.json"
            }
            await self._save_data(users, "test_users.json")
            
            # Generate test libraries
            self.logger.info("Generating test libraries")
            libraries = await self._generate_test_libraries(users, 75)
            generation_results["data_sets"]["libraries"] = {
                "count": len(libraries),
                "file": "test_libraries.json"
            }
            await self._save_data(libraries, "test_libraries.json")
            
            # Generate test scenarios
            self.logger.info("Generating test scenarios")
            scenarios = await self._generate_test_scenarios()
            generation_results["data_sets"]["scenarios"] = {
                "count": len(scenarios),
                "file": "test_scenarios.json"
            }
            await self._save_data(scenarios, "test_scenarios.json")
            
            # Generate performance test data
            self.logger.info("Generating performance test data")
            performance_data = await self._generate_performance_test_data()
            generation_results["data_sets"]["performance"] = {
                "datasets": len(performance_data),
                "file": "performance_test_data.json"
            }
            await self._save_data(performance_data, "performance_test_data.json")
            
            # Generate accessibility test data
            self.logger.info("Generating accessibility test data")
            accessibility_data = await self._generate_accessibility_test_data()
            generation_results["data_sets"]["accessibility"] = {
                "test_cases": len(accessibility_data),
                "file": "accessibility_test_data.json"
            }
            await self._save_data(accessibility_data, "accessibility_test_data.json")
            
            # Generate mock API responses
            self.logger.info("Generating mock API responses")
            api_responses = await self._generate_mock_api_responses()
            generation_results["data_sets"]["api_responses"] = {
                "endpoints": len(api_responses),
                "file": "mock_api_responses.json"
            }
            await self._save_data(api_responses, "mock_api_responses.json")
            
            generation_results["generation_complete"] = True
            
        except Exception as e:
            self.logger.error(f"Test data generation failed: {str(e)}")
            generation_results["error"] = str(e)
            generation_results["generation_complete"] = False
        
        finally:
            generation_results["end_time"] = datetime.now().isoformat()
            await self._save_data(generation_results, "generation_summary.json")
        
        return generation_results
    
    async def _generate_test_users(self, count: int) -> List[TestUser]:
        """Generate test users with diverse profiles"""
        users = []
        
        for i in range(count):
            user_type = random.choice(self.user_types)
            experience = random.choice(self.experience_levels)
            domain = random.choice(self.research_domains)
            
            # Adjust library size based on user type and experience
            if user_type in ["professor", "academic_researcher"]:
                library_size = random.randint(1000, 10000)
            elif user_type in ["graduate_student", "postdoc"]:
                library_size = random.randint(200, 2000)
            elif user_type == "librarian":
                library_size = random.randint(5000, 20000)
            else:
                library_size = random.randint(50, 500)
            
            user = TestUser(
                id=str(uuid.uuid4()),
                name=f"Test User {i+1}",
                email=f"testuser{i+1}@example.com",
                user_type=user_type,
                experience_level=experience,
                research_domain=domain,
                library_size=library_size,
                preferred_citation_style=random.choice(self.citation_styles),
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            
            users.append(user)
        
        return users
    
    async def _generate_test_libraries(self, users: List[TestUser], library_count: int) -> List[TestLibrary]:
        """Generate test libraries with realistic content"""
        libraries = []
        
        for i in range(library_count):
            # Select a random user as owner
            owner = random.choice(users)
            
            # Determine library type and size
            library_type = random.choices(
                ["personal", "group"],
                weights=[80, 20]
            )[0]
            
            item_count = owner.library_size + random.randint(-100, 200)
            item_count = max(10, item_count)  # Minimum 10 items
            
            collection_count = max(1, item_count // 50)  # Roughly 1 collection per 50 items
            
            # Generate library items
            items = await self._generate_library_items(item_count, owner.research_domain)
            
            # Generate collections
            collections = await self._generate_library_collections(collection_count, owner.research_domain)
            
            library = TestLibrary(
                id=str(uuid.uuid4()),
                name=f"{owner.name}'s Library" if library_type == "personal" else f"Research Group {i+1}",
                owner_id=owner.id,
                item_count=item_count,
                collection_count=collection_count,
                library_type=library_type,
                created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
                items=items,
                collections=collections
            )
            
            libraries.append(library)
        
        return libraries
    
    async def _generate_library_items(self, count: int, research_domain: str) -> List[Dict[str, Any]]:
        """Generate realistic library items"""
        items = []
        
        for i in range(count):
            item_type = random.choice(self.item_types)
            
            # Generate basic item data
            item = {
                "key": f"ITEM_{uuid.uuid4().hex[:8].upper()}",
                "version": random.randint(1, 10),
                "itemType": item_type,
                "title": self._generate_realistic_title(research_domain),
                "creators": self._generate_creators(),
                "abstractNote": self._generate_abstract(research_domain),
                "tags": self._generate_tags(research_domain),
                "dateAdded": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
                "dateModified": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            
            # Add type-specific fields
            if item_type == "journalArticle":
                item.update({
                    "publicationTitle": random.choice(self.sample_journals),
                    "volume": str(random.randint(1, 50)),
                    "issue": str(random.randint(1, 12)),
                    "pages": f"{random.randint(1, 500)}-{random.randint(501, 600)}",
                    "date": str(random.randint(2010, 2024)),
                    "DOI": f"10.{random.randint(1000, 9999)}/{uuid.uuid4().hex[:8]}",
                    "ISSN": f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
                })
            elif item_type == "book":
                item.update({
                    "publisher": random.choice(self.sample_publishers),
                    "place": random.choice(["New York", "London", "Cambridge", "Oxford", "Berlin"]),
                    "date": str(random.randint(2000, 2024)),
                    "ISBN": f"978-{random.randint(0, 9)}-{random.randint(100, 999)}-{random.randint(10000, 99999)}-{random.randint(0, 9)}",
                    "numPages": str(random.randint(100, 800))
                })
            elif item_type == "thesis":
                item.update({
                    "university": f"University of {random.choice(['California', 'Michigan', 'Texas', 'Florida', 'Illinois'])}",
                    "thesisType": random.choice(["PhD thesis", "Master's thesis"]),
                    "date": str(random.randint(2015, 2024))
                })
            
            items.append(item)
        
        return items
    
    async def _generate_library_collections(self, count: int, research_domain: str) -> List[Dict[str, Any]]:
        """Generate realistic library collections"""
        collections = []
        
        collection_names = [
            f"{research_domain} - Core Papers",
            f"{research_domain} - Recent Research",
            "Literature Review",
            "Methodology Papers",
            "Background Reading",
            "Key References",
            "Conference Papers",
            "Book Chapters",
            "Review Articles",
            "Theoretical Framework"
        ]
        
        for i in range(count):
            collection = {
                "key": f"COLL_{uuid.uuid4().hex[:8].upper()}",
                "version": random.randint(1, 5),
                "name": random.choice(collection_names) if i < len(collection_names) else f"Collection {i+1}",
                "parentCollection": None if random.random() < 0.7 else f"COLL_{uuid.uuid4().hex[:8].upper()}",
                "relations": {}
            }
            
            collections.append(collection)
        
        return collections
    
    def _generate_realistic_title(self, research_domain: str) -> str:
        """Generate realistic academic paper titles"""
        domain_keywords = {
            "Computer Science": ["algorithm", "machine learning", "neural network", "optimization", "data mining"],
            "Biology": ["protein", "gene expression", "cell", "molecular", "evolution"],
            "Psychology": ["cognitive", "behavioral", "social", "developmental", "clinical"],
            "Physics": ["quantum", "particle", "electromagnetic", "thermodynamic", "relativistic"],
            "Chemistry": ["synthesis", "catalysis", "molecular", "organic", "inorganic"]
        }
        
        keywords = domain_keywords.get(research_domain, ["research", "analysis", "study", "investigation"])
        
        title_templates = [
            "A {adjective} approach to {keyword} in {context}",
            "{keyword} and {keyword2}: {adjective} perspectives",
            "Understanding {keyword} through {method} analysis",
            "The role of {keyword} in {context}: a {adjective} study",
            "{adjective} {keyword} for {application}",
            "Advances in {keyword}: {adjective} methods and applications"
        ]
        
        adjectives = ["novel", "comprehensive", "systematic", "comparative", "experimental", "theoretical"]
        contexts = ["modern applications", "clinical settings", "real-world scenarios", "complex systems"]
        methods = ["computational", "statistical", "experimental", "theoretical", "empirical"]
        applications = ["healthcare", "industry", "education", "research", "technology"]
        
        template = random.choice(title_templates)
        
        return template.format(
            adjective=random.choice(adjectives),
            keyword=random.choice(keywords),
            keyword2=random.choice(keywords),
            context=random.choice(contexts),
            method=random.choice(methods),
            application=random.choice(applications)
        ).title()
    
    def _generate_creators(self) -> List[Dict[str, str]]:
        """Generate realistic author lists"""
        author_count = random.choices([1, 2, 3, 4, 5, 6], weights=[20, 30, 25, 15, 7, 3])[0]
        creators = []
        
        for _ in range(author_count):
            author = random.choice(self.sample_authors)
            last_name, first_name = author.split(", ")
            
            creators.append({
                "creatorType": "author",
                "firstName": first_name,
                "lastName": last_name
            })
        
        return creators
    
    def _generate_abstract(self, research_domain: str) -> str:
        """Generate realistic abstracts"""
        abstract_templates = [
            "This study investigates {topic} using {method}. We analyzed {sample} and found {finding}. The results suggest {implication}. These findings have important implications for {application}.",
            "Background: {background}. Methods: {method} was used to {action}. Results: {finding} was observed. Conclusions: {conclusion}.",
            "We present a {adjective} approach to {problem}. Our method {action} and demonstrates {benefit}. Experimental results show {finding}. This work contributes to {field} by {contribution}."
        ]
        
        topics = [f"{research_domain.lower()} applications", "novel methodologies", "system optimization"]
        methods = ["computational analysis", "experimental design", "statistical modeling", "machine learning"]
        findings = ["significant improvements", "novel insights", "important correlations", "unexpected results"]
        
        template = random.choice(abstract_templates)
        
        return template.format(
            topic=random.choice(topics),
            method=random.choice(methods),
            sample="a large dataset",
            finding=random.choice(findings),
            implication="important theoretical implications",
            application=f"{research_domain.lower()} research",
            background=f"Recent advances in {research_domain.lower()}",
            action="examine the relationship between key variables",
            conclusion="our approach provides valuable insights",
            adjective="novel",
            problem=f"challenges in {research_domain.lower()}",
            benefit="superior performance",
            field=research_domain.lower(),
            contribution="providing new theoretical frameworks"
        )
    
    def _generate_tags(self, research_domain: str) -> List[Dict[str, str]]:
        """Generate realistic tags"""
        domain_tags = {
            "Computer Science": ["machine learning", "algorithms", "data science", "AI", "programming"],
            "Biology": ["genetics", "molecular biology", "cell biology", "evolution", "biochemistry"],
            "Psychology": ["cognition", "behavior", "social psychology", "development", "clinical"],
            "Physics": ["quantum mechanics", "thermodynamics", "optics", "particle physics", "relativity"]
        }
        
        general_tags = ["research", "methodology", "analysis", "theory", "experimental", "review"]
        specific_tags = domain_tags.get(research_domain, general_tags)
        
        tag_count = random.randint(2, 6)
        selected_tags = random.sample(specific_tags + general_tags, min(tag_count, len(specific_tags + general_tags)))
        
        return [{"tag": tag} for tag in selected_tags]
    
    async def _generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate comprehensive test scenarios"""
        scenarios = [
            {
                "id": "small_library_import",
                "name": "Small Library Import Test",
                "description": "Test import of small library (< 100 items)",
                "library_size": "small",
                "expected_duration": "< 2 minutes",
                "success_criteria": ["All items imported", "Metadata preserved", "Collections maintained"],
                "test_data": {
                    "item_count": random.randint(20, 100),
                    "collection_count": random.randint(2, 5),
                    "has_attachments": True
                }
            },
            {
                "id": "medium_library_import",
                "name": "Medium Library Import Test",
                "description": "Test import of medium library (100-1000 items)",
                "library_size": "medium",
                "expected_duration": "< 10 minutes",
                "success_criteria": ["All items imported", "Progress tracking works", "No timeouts"],
                "test_data": {
                    "item_count": random.randint(100, 1000),
                    "collection_count": random.randint(5, 20),
                    "has_attachments": True
                }
            },
            {
                "id": "large_library_import",
                "name": "Large Library Import Test",
                "description": "Test import of large library (1000+ items)",
                "library_size": "large",
                "expected_duration": "< 30 minutes",
                "success_criteria": ["Import completes", "Memory usage acceptable", "System remains responsive"],
                "test_data": {
                    "item_count": random.randint(1000, 5000),
                    "collection_count": random.randint(20, 100),
                    "has_attachments": True
                }
            },
            {
                "id": "search_performance",
                "name": "Search Performance Test",
                "description": "Test search functionality across different library sizes",
                "test_type": "performance",
                "expected_duration": "< 5 minutes",
                "success_criteria": ["Search results < 2 seconds", "Relevant results", "Pagination works"],
                "test_data": {
                    "search_queries": [
                        "machine learning",
                        "climate change",
                        "neural networks",
                        "quantum computing",
                        "gene therapy"
                    ],
                    "expected_results": random.randint(10, 100)
                }
            },
            {
                "id": "citation_generation",
                "name": "Citation Generation Test",
                "description": "Test citation generation in multiple formats",
                "test_type": "functionality",
                "expected_duration": "< 3 minutes",
                "success_criteria": ["Citations format correctly", "All styles supported", "Export works"],
                "test_data": {
                    "citation_styles": ["APA", "MLA", "Chicago", "IEEE"],
                    "item_types": ["journalArticle", "book", "thesis", "conferencePaper"],
                    "export_formats": ["BibTeX", "RIS", "EndNote"]
                }
            },
            {
                "id": "concurrent_users",
                "name": "Concurrent Users Test",
                "description": "Test system behavior with multiple simultaneous users",
                "test_type": "load",
                "expected_duration": "< 15 minutes",
                "success_criteria": ["System remains stable", "Response times acceptable", "No data corruption"],
                "test_data": {
                    "concurrent_users": [5, 10, 15, 20],
                    "operations": ["import", "search", "citation", "export"],
                    "duration_minutes": 10
                }
            },
            {
                "id": "accessibility_compliance",
                "name": "Accessibility Compliance Test",
                "description": "Test WCAG compliance and screen reader compatibility",
                "test_type": "accessibility",
                "expected_duration": "< 20 minutes",
                "success_criteria": ["WCAG AA compliant", "Screen reader compatible", "Keyboard navigable"],
                "test_data": {
                    "wcag_level": "AA",
                    "screen_readers": ["NVDA", "JAWS", "VoiceOver"],
                    "test_pages": ["library", "search", "citations", "settings"]
                }
            }
        ]
        
        return scenarios
    
    async def _generate_performance_test_data(self) -> Dict[str, Any]:
        """Generate performance test datasets"""
        return {
            "load_test_configurations": [
                {
                    "name": "Light Load",
                    "concurrent_users": 5,
                    "duration_minutes": 5,
                    "ramp_up_time": 30,
                    "operations": {
                        "library_browse": 0.4,
                        "search": 0.3,
                        "citation": 0.2,
                        "export": 0.1
                    }
                },
                {
                    "name": "Medium Load",
                    "concurrent_users": 15,
                    "duration_minutes": 10,
                    "ramp_up_time": 60,
                    "operations": {
                        "library_browse": 0.35,
                        "search": 0.35,
                        "citation": 0.2,
                        "export": 0.1
                    }
                },
                {
                    "name": "Heavy Load",
                    "concurrent_users": 25,
                    "duration_minutes": 15,
                    "ramp_up_time": 120,
                    "operations": {
                        "library_browse": 0.3,
                        "search": 0.4,
                        "citation": 0.2,
                        "export": 0.1
                    }
                }
            ],
            "library_size_tests": [
                {"size": 100, "expected_import_time": 30, "expected_search_time": 0.5},
                {"size": 500, "expected_import_time": 120, "expected_search_time": 0.8},
                {"size": 1000, "expected_import_time": 300, "expected_search_time": 1.2},
                {"size": 5000, "expected_import_time": 900, "expected_search_time": 2.0},
                {"size": 10000, "expected_import_time": 1800, "expected_search_time": 3.0}
            ],
            "memory_usage_benchmarks": {
                "idle": {"expected_mb": 150, "max_mb": 200},
                "small_import": {"expected_mb": 200, "max_mb": 300},
                "large_import": {"expected_mb": 400, "max_mb": 600},
                "ai_analysis": {"expected_mb": 350, "max_mb": 500}
            }
        }
    
    async def _generate_accessibility_test_data(self) -> List[Dict[str, Any]]:
        """Generate accessibility test cases"""
        return [
            {
                "test_id": "keyboard_navigation",
                "name": "Keyboard Navigation Test",
                "description": "Test full keyboard navigation through interface",
                "wcag_criteria": ["2.1.1", "2.1.2", "2.4.3"],
                "test_steps": [
                    "Navigate to library page using Tab key",
                    "Access all interactive elements via keyboard",
                    "Verify focus indicators are visible",
                    "Test skip links functionality"
                ],
                "expected_results": [
                    "All elements reachable via keyboard",
                    "Focus indicators clearly visible",
                    "Logical tab order maintained",
                    "Skip links work correctly"
                ]
            },
            {
                "test_id": "screen_reader_compatibility",
                "name": "Screen Reader Compatibility",
                "description": "Test compatibility with major screen readers",
                "wcag_criteria": ["1.3.1", "2.4.6", "4.1.2"],
                "screen_readers": ["NVDA", "JAWS", "VoiceOver"],
                "test_steps": [
                    "Navigate interface using screen reader",
                    "Verify all content is announced",
                    "Test form labels and instructions",
                    "Verify ARIA labels and roles"
                ],
                "expected_results": [
                    "All content properly announced",
                    "Form elements have clear labels",
                    "Navigation structure is clear",
                    "Interactive elements identified correctly"
                ]
            },
            {
                "test_id": "color_contrast",
                "name": "Color Contrast Compliance",
                "description": "Test color contrast ratios meet WCAG standards",
                "wcag_criteria": ["1.4.3", "1.4.6"],
                "test_elements": [
                    "Body text", "Link text", "Button text", "Form labels",
                    "Error messages", "Success messages", "Navigation items"
                ],
                "minimum_ratios": {
                    "normal_text": 4.5,
                    "large_text": 3.0,
                    "ui_components": 3.0
                }
            },
            {
                "test_id": "text_scaling",
                "name": "Text Scaling Test",
                "description": "Test interface usability at 200% zoom",
                "wcag_criteria": ["1.4.4"],
                "zoom_levels": ["150%", "200%", "250%"],
                "test_criteria": [
                    "No horizontal scrolling required",
                    "All content remains visible",
                    "Interactive elements remain usable",
                    "Text doesn't overlap or get cut off"
                ]
            }
        ]
    
    async def _generate_mock_api_responses(self) -> Dict[str, Any]:
        """Generate mock API responses for testing"""
        return {
            "zotero_library_response": {
                "endpoint": "/api/zotero/library",
                "method": "GET",
                "response": {
                    "libraries": [
                        {
                            "id": "12345",
                            "name": "My Library",
                            "type": "user",
                            "links": {
                                "self": {"href": "https://api.zotero.org/users/12345"},
                                "alternate": {"href": "https://www.zotero.org/users/12345"}
                            }
                        }
                    ]
                },
                "status_code": 200
            },
            "zotero_items_response": {
                "endpoint": "/api/zotero/items",
                "method": "GET",
                "response": [
                    {
                        "key": "ABCD1234",
                        "version": 1,
                        "itemType": "journalArticle",
                        "title": "Sample Research Paper",
                        "creators": [
                            {"creatorType": "author", "firstName": "John", "lastName": "Doe"}
                        ],
                        "abstractNote": "This is a sample abstract for testing purposes.",
                        "publicationTitle": "Journal of Testing",
                        "volume": "1",
                        "issue": "1",
                        "pages": "1-10",
                        "date": "2024",
                        "DOI": "10.1234/test.2024.001"
                    }
                ],
                "status_code": 200
            },
            "citation_generation_response": {
                "endpoint": "/api/zotero/citations",
                "method": "POST",
                "response": {
                    "citations": {
                        "APA": "Doe, J. (2024). Sample research paper. Journal of Testing, 1(1), 1-10. https://doi.org/10.1234/test.2024.001",
                        "MLA": "Doe, John. \"Sample Research Paper.\" Journal of Testing, vol. 1, no. 1, 2024, pp. 1-10.",
                        "Chicago": "Doe, John. \"Sample Research Paper.\" Journal of Testing 1, no. 1 (2024): 1-10."
                    }
                },
                "status_code": 200
            },
            "search_response": {
                "endpoint": "/api/zotero/search",
                "method": "GET",
                "response": {
                    "results": [
                        {
                            "key": "ABCD1234",
                            "title": "Sample Research Paper",
                            "creators": ["John Doe"],
                            "date": "2024",
                            "relevance_score": 0.95
                        }
                    ],
                    "total_count": 1,
                    "page": 1,
                    "per_page": 25
                },
                "status_code": 200
            },
            "error_responses": {
                "unauthorized": {
                    "status_code": 401,
                    "response": {
                        "error": "Unauthorized",
                        "message": "Invalid or expired access token"
                    }
                },
                "rate_limited": {
                    "status_code": 429,
                    "response": {
                        "error": "Rate Limited",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60
                    }
                },
                "server_error": {
                    "status_code": 500,
                    "response": {
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred"
                    }
                }
            }
        }
    
    async def _save_data(self, data: Any, filename: str) -> None:
        """Save generated data to file"""
        file_path = self.output_dir / filename
        
        # Convert dataclasses to dictionaries for JSON serialization
        if isinstance(data, list) and data and hasattr(data[0], '__dataclass_fields__'):
            data = [asdict(item) for item in data]
        elif hasattr(data, '__dataclass_fields__'):
            data = asdict(data)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Saved test data to {file_path}")

if __name__ == "__main__":
    async def main():
        generator = TestDataGenerator({})
        results = await generator.generate_comprehensive_test_data()
        print(f"Test data generation completed: {results['generation_complete']}")
        print(f"Generated datasets: {list(results['data_sets'].keys())}")
    
    asyncio.run(main())