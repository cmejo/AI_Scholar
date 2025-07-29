#!/usr/bin/env python3
"""
Comprehensive System Validation and User Acceptance Testing Suite
for AI Scholar RAG Advanced Features
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SystemValidator:
    """Comprehensive system validation suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.test_results: List[TestResult] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            if result is True or (isinstance(result, dict) and result.get('success', False)):
                self.test_results.append(TestResult(test_name, True, duration, details=result if isinstance(result, dict) else None))
                logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            else:
                self.test_results.append(TestResult(test_name, False, duration, error_message="Test returned False"))
                logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(test_name, False, duration, error_message=str(e)))
            logger.error(f"❌ {test_name} - ERROR ({duration:.2f}s): {str(e)}")
    
    async def authenticate(self) -> bool:
        """Authenticate with the system"""
        try:
            # Register test user
            register_data = {
                "email": "test@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            
            async with self.session.post(f"{self.base_url}/api/auth/register", json=register_data) as response:
                if response.status not in [200, 400]:  # 400 might mean user already exists
                    return False
            
            # Login
            login_data = aiohttp.FormData()
            login_data.add_field('email', 'test@example.com')
            login_data.add_field('password', 'testpassword123')
            
            async with self.session.post(f"{self.base_url}/api/auth/login", data=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
    
    # Core System Tests
    async def test_health_check(self) -> bool:
        """Test basic system health"""
        async with self.session.get(f"{self.base_url}/") as response:
            return response.status == 200
    
    async def test_authentication_flow(self) -> bool:
        """Test complete authentication flow"""
        return await self.authenticate()
    
    # Document Management Tests
    async def test_document_upload(self) -> Dict[str, Any]:
        """Test document upload functionality"""
        # Create a test document
        test_content = """
        # Test Document
        
        This is a test document for validating the AI Scholar RAG system.
        
        ## Machine Learning
        Machine learning is a subset of artificial intelligence that focuses on algorithms.
        
        ## Neural Networks
        Neural networks are computing systems inspired by biological neural networks.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            data = aiohttp.FormData()
            data.add_field('file', open(temp_file, 'rb'), filename='test_document.txt', content_type='text/plain')
            data.add_field('chunking_strategy', 'hierarchical')
            
            async with self.session.post(
                f"{self.base_url}/api/documents/upload",
                data=data,
                headers=self.auth_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'document_id': result.get('id'),
                        'chunks_count': result.get('chunks_count', 0)
                    }
                return {'success': False, 'status': response.status}
                
        finally:
            os.unlink(temp_file)
    
    async def test_batch_upload(self) -> Dict[str, Any]:
        """Test batch document upload"""
        test_files = []
        
        # Create multiple test files
        for i in range(3):
            content = f"Test document {i+1}\n\nThis is content for document {i+1}."
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                test_files.append(f.name)
        
        try:
            data = aiohttp.FormData()
            for i, file_path in enumerate(test_files):
                data.add_field('files', open(file_path, 'rb'), filename=f'test_doc_{i+1}.txt', content_type='text/plain')
            data.add_field('chunking_strategy', 'hierarchical')
            
            async with self.session.post(
                f"{self.base_url}/api/documents/batch-upload",
                data=data,
                headers=self.auth_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'successful_uploads': len(result.get('successful_uploads', [])),
                        'failed_uploads': len(result.get('failed_uploads', []))
                    }
                return {'success': False, 'status': response.status}
                
        finally:
            for file_path in test_files:
                os.unlink(file_path)
    
    async def test_document_list(self) -> Dict[str, Any]:
        """Test document listing"""
        async with self.session.get(
            f"{self.base_url}/api/documents",
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                documents = await response.json()
                return {
                    'success': True,
                    'document_count': len(documents)
                }
            return {'success': False, 'status': response.status}
    
    # Chat and RAG Tests
    async def test_basic_chat(self) -> Dict[str, Any]:
        """Test basic chat functionality"""
        chat_request = {
            "message": "What is machine learning?",
            "conversation_id": "test-conversation-1",
            "use_chain_of_thought": False,
            "citation_mode": "inline"
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat/message",
            json=chat_request,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'success': True,
                    'response_length': len(result.get('response', '')),
                    'sources_count': len(result.get('sources', [])),
                    'processing_time': result.get('processing_time', 0)
                }
            return {'success': False, 'status': response.status}
    
    async def test_enhanced_chat(self) -> Dict[str, Any]:
        """Test enhanced chat with advanced features"""
        chat_request = {
            "message": "Explain the relationship between neural networks and deep learning",
            "conversation_id": "test-conversation-enhanced",
            "use_chain_of_thought": True,
            "citation_mode": "detailed",
            "enable_reasoning": True,
            "enable_memory": True,
            "personalization_level": 0.5,
            "max_sources": 5
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat/enhanced",
            json=chat_request,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'success': True,
                    'response_length': len(result.get('response', '')),
                    'sources_count': len(result.get('sources', [])),
                    'reasoning_steps': len(result.get('reasoning_steps', [])),
                    'uncertainty_score': result.get('uncertainty_score'),
                    'knowledge_graph_used': result.get('knowledge_graph_used', False),
                    'memory_context_used': result.get('memory_context_used', False),
                    'processing_time': result.get('processing_time', 0)
                }
            return {'success': False, 'status': response.status}
    
    async def test_semantic_search(self) -> Dict[str, Any]:
        """Test semantic search functionality"""
        params = {
            'query': 'machine learning algorithms',
            'limit': 5,
            'enable_personalization': True
        }
        
        async with self.session.get(
            f"{self.base_url}/api/search/semantic",
            params=params,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'success': True,
                    'results_count': len(result.get('results', [])),
                    'personalization_applied': result.get('personalization_applied', False),
                    'search_strategy': result.get('search_strategy', 'unknown')
                }
            return {'success': False, 'status': response.status}
    
    # Knowledge Graph Tests
    async def test_knowledge_graph(self) -> Dict[str, Any]:
        """Test knowledge graph functionality"""
        # First get a document ID
        async with self.session.get(
            f"{self.base_url}/api/documents",
            headers=self.auth_headers
        ) as response:
            if response.status != 200:
                return {'success': False, 'error': 'Could not get documents'}
            
            documents = await response.json()
            if not documents:
                return {'success': False, 'error': 'No documents available'}
            
            document_id = documents[0]['id']
        
        # Test knowledge graph retrieval
        params = {
            'include_relationships': True,
            'max_depth': 2,
            'min_confidence': 0.5
        }
        
        async with self.session.get(
            f"{self.base_url}/api/knowledge-graph/{document_id}",
            params=params,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'success': True,
                    'entities_count': len(result.get('nodes', [])),
                    'relationships_count': len(result.get('edges', [])),
                    'has_visualization': 'visualization' in result
                }
            return {'success': False, 'status': response.status}
    
    # Analytics Tests
    async def test_analytics_dashboard(self) -> Dict[str, Any]:
        """Test analytics dashboard"""
        params = {
            'time_range': '7d',
            'include_insights': True
        }
        
        async with self.session.get(
            f"{self.base_url}/api/analytics/dashboard",
            params=params,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'success': True,
                    'has_query_analytics': 'query_analytics' in result,
                    'has_document_analytics': 'document_analytics' in result,
                    'has_insights': 'insights' in result,
                    'has_knowledge_graph_stats': 'knowledge_graph_stats' in result
                }
            return {'success': False, 'status': response.status}
    
    # Advanced Features Tests
    async def test_document_comparison(self) -> Dict[str, Any]:
        """Test document comparison feature"""
        # Get available documents
        async with self.session.get(
            f"{self.base_url}/api/documents",
            headers=self.auth_headers
        ) as response:
            if response.status != 200:
                return {'success': False, 'error': 'Could not get documents'}
            
            documents = await response.json()
            if len(documents) < 2:
                return {'success': False, 'error': 'Need at least 2 documents for comparison'}
            
            document_ids = [doc['id'] for doc in documents[:2]]
        
        # Test comparison
        comparison_request = {
            "document_ids": document_ids,
            "query": "Compare the main concepts",
            "comparison_type": "detailed"
        }
        
        async with self.session.post(
            f"{self.base_url}/api/documents/compare",
            json=comparison_request,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'success': True,
                    'has_summary': 'comparison_summary' in result,
                    'similarities_count': len(result.get('similarities', [])),
                    'differences_count': len(result.get('differences', []))
                }
            return {'success': False, 'status': response.status}
    
    # Performance Tests
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test system under concurrent load"""
        async def make_request():
            chat_request = {
                "message": "What is artificial intelligence?",
                "conversation_id": f"test-concurrent-{time.time()}",
                "use_chain_of_thought": False,
                "citation_mode": "inline"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/chat/message",
                json=chat_request,
                headers=self.auth_headers
            ) as response:
                return response.status == 200
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        successful = sum(1 for r in results if r is True)
        
        return {
            'success': successful >= 8,  # At least 80% success rate
            'successful_requests': successful,
            'total_requests': len(tasks),
            'duration': duration,
            'requests_per_second': len(tasks) / duration
        }
    
    async def test_memory_persistence(self) -> Dict[str, Any]:
        """Test conversation memory persistence"""
        conversation_id = "test-memory-persistence"
        
        # First message
        chat_request_1 = {
            "message": "My name is Alice and I'm interested in machine learning",
            "conversation_id": conversation_id,
            "enable_memory": True,
            "personalization_level": 0.5
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat/enhanced",
            json=chat_request_1,
            headers=self.auth_headers
        ) as response:
            if response.status != 200:
                return {'success': False, 'error': 'First message failed'}
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Second message referencing the first
        chat_request_2 = {
            "message": "What did I tell you my name was?",
            "conversation_id": conversation_id,
            "enable_memory": True,
            "personalization_level": 0.5
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat/enhanced",
            json=chat_request_2,
            headers=self.auth_headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                response_text = result.get('response', '').lower()
                memory_used = result.get('memory_context_used', False)
                
                # Check if the response mentions Alice
                mentions_name = 'alice' in response_text
                
                return {
                    'success': memory_used and mentions_name,
                    'memory_context_used': memory_used,
                    'mentions_name': mentions_name,
                    'response_preview': response_text[:100]
                }
            return {'success': False, 'status': response.status}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("Starting comprehensive system validation...")
        
        # Core system tests
        await self.run_test("Health Check", self.test_health_check)
        await self.run_test("Authentication Flow", self.test_authentication_flow)
        
        # Document management tests
        await self.run_test("Document Upload", self.test_document_upload)
        await self.run_test("Batch Upload", self.test_batch_upload)
        await self.run_test("Document List", self.test_document_list)
        
        # Chat and RAG tests
        await self.run_test("Basic Chat", self.test_basic_chat)
        await self.run_test("Enhanced Chat", self.test_enhanced_chat)
        await self.run_test("Semantic Search", self.test_semantic_search)
        
        # Advanced features tests
        await self.run_test("Knowledge Graph", self.test_knowledge_graph)
        await self.run_test("Analytics Dashboard", self.test_analytics_dashboard)
        await self.run_test("Document Comparison", self.test_document_comparison)
        
        # Performance and reliability tests
        await self.run_test("Concurrent Requests", self.test_concurrent_requests)
        await self.run_test("Memory Persistence", self.test_memory_persistence)
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        avg_duration = sum(r.duration for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'average_duration': avg_duration,
            'test_results': [
                {
                    'name': r.test_name,
                    'passed': r.passed,
                    'duration': r.duration,
                    'error': r.error_message,
                    'details': r.details
                }
                for r in self.test_results
            ]
        }
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        report = f"""
# AI Scholar RAG System Validation Report

## Summary
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed_tests']}
- **Failed**: {summary['failed_tests']}
- **Success Rate**: {summary['success_rate']:.1f}%
- **Average Duration**: {summary['average_duration']:.2f}s

## Test Results

"""
        
        for result in summary['test_results']:
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            report += f"### {result['name']} - {status}\n"
            report += f"- **Duration**: {result['duration']:.2f}s\n"
            
            if result['error']:
                report += f"- **Error**: {result['error']}\n"
            
            if result['details']:
                report += f"- **Details**: {json.dumps(result['details'], indent=2)}\n"
            
            report += "\n"
        
        # Add recommendations
        if summary['success_rate'] < 100:
            report += "## Recommendations\n\n"
            
            failed_tests = [r for r in summary['test_results'] if not r['passed']]
            for test in failed_tests:
                report += f"- **{test['name']}**: {test['error'] or 'Investigation required'}\n"
        
        report += f"\n## Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report

async def main():
    """Main validation function"""
    base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    async with SystemValidator(base_url) as validator:
        summary = await validator.run_all_tests()
        
        # Generate and save report
        report = validator.generate_report(summary)
        
        report_file = f"system_validation_report_{int(time.time())}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n{report}")
        print(f"\nReport saved to: {report_file}")
        
        # Exit with appropriate code
        if summary['success_rate'] < 80:
            print("\n❌ System validation failed - success rate below 80%")
            exit(1)
        else:
            print(f"\n✅ System validation passed - {summary['success_rate']:.1f}% success rate")
            exit(0)

if __name__ == "__main__":
    asyncio.run(main())