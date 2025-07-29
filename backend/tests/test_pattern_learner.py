"""
Tests for Pattern Learning Service.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from collections import Counter

from services.pattern_learner import (
    PatternLearner, 
    QueryPattern, 
    DocumentUsagePattern, 
    UserBehaviorPattern,
    SystemOptimization
)

@pytest.fixture
async def pattern_learner():
    """Create a PatternLearner instance for testing."""
    learner = PatternLearner()
    
    # Mock dependencies
    learner.redis_client = AsyncMock()
    learner.db_connection = AsyncMock()
    learner.db_connection.cursor = AsyncMock()
    
    return learner

@pytest.fixture
def sample_query_data():
    """Sample query data for testing."""
    base_time = datetime.now()
    return [
        {
            'query': 'machine learning algorithms',
            'timestamp': base_time - timedelta(hours=1),
            'user_id': 'user1',
            'metadata': {'query': 'machine learning algorithms'}
        },
        {
            'query': 'deep learning neural networks',
            'timestamp': base_time - timedelta(hours=2),
            'user_id': 'user2',
            'metadata': {'query': 'deep learning neural networks'}
        },
        {
            'query': 'machine learning applications',
            'timestamp': base_time - timedelta(hours=3),
            'user_id': 'user1',
            'metadata': {'query': 'machine learning applications'}
        },
        {
            'query': 'what is artificial intelligence?',
            'timestamp': base_time - timedelta(hours=4),
            'user_id': 'user3',
            'metadata': {'query': 'what is artificial intelligence?'}
        },
        {
            'query': 'how does machine learning work?',
            'timestamp': base_time - timedelta(hours=5),
            'user_id': 'user2',
            'metadata': {'query': 'how does machine learning work?'}
        }
    ]

@pytest.fixture
def sample_document_usage():
    """Sample document usage data for testing."""
    base_time = datetime.now()
    return {
        'doc1': {
            'access_count': 25,
            'access_times': [base_time - timedelta(hours=i) for i in range(25)],
            'queries': ['machine learning', 'algorithms', 'neural networks'],
            'users': ['user1', 'user2', 'user3']
        },
        'doc2': {
            'access_count': 10,
            'access_times': [base_time - timedelta(hours=i*2) for i in range(10)],
            'queries': ['deep learning', 'AI'],
            'users': ['user2', 'user4']
        }
    }

@pytest.fixture
def sample_user_data():
    """Sample user interaction data for testing."""
    base_time = datetime.now()
    return {
        'events': [
            {
                'type': 'query_submitted',
                'data': {'query': 'machine learning basics'},
                'timestamp': base_time - timedelta(minutes=30)
            },
            {
                'type': 'document_accessed',
                'data': {'document_id': 'doc1', 'document_domain': 'technology'},
                'timestamp': base_time - timedelta(minutes=25)
            },
            {
                'type': 'feedback_provided',
                'data': {'rating': 4, 'response_length_rating': 4},
                'timestamp': base_time - timedelta(minutes=20)
            },
            {
                'type': 'query_submitted',
                'data': {'query': 'advanced neural networks'},
                'timestamp': base_time - timedelta(minutes=10)
            }
        ]
    }

class TestPatternLearner:
    """Test cases for PatternLearner service."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test PatternLearner initialization."""
        learner = PatternLearner()
        
        with patch('services.pattern_learner.get_redis_client') as mock_redis, \
             patch('services.pattern_learner.get_db_connection') as mock_db:
            
            mock_redis.return_value = AsyncMock()
            mock_db.return_value = AsyncMock()
            
            await learner.initialize()
            
            assert learner.redis_client is not None
            assert learner.db_connection is not None
    
    @pytest.mark.asyncio
    async def test_analyze_query_patterns(self, pattern_learner, sample_query_data):
        """Test query pattern analysis."""
        # Mock database query
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            (item['metadata'], item['timestamp'], item['user_id'])
            for item in sample_query_data
        ]
        pattern_learner.db_connection.cursor.return_value.__aenter__.return_value = cursor_mock
        
        # Mock Redis cache
        pattern_learner.redis_client.setex = AsyncMock()
        
        patterns = await pattern_learner.analyze_query_patterns(time_window_days=30)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Check for frequent term patterns
        frequent_patterns = [p for p in patterns if p.pattern_type == "frequent_terms"]
        assert len(frequent_patterns) > 0
        
        # Verify pattern structure
        for pattern in patterns:
            assert isinstance(pattern, QueryPattern)
            assert pattern.pattern_id
            assert pattern.pattern_type in ["frequent_terms", "temporal", "semantic"]
            assert pattern.frequency > 0
            assert 0 <= pattern.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_frequent_terms(self, pattern_learner, sample_query_data):
        """Test frequent term analysis."""
        patterns = await pattern_learner._analyze_frequent_terms(sample_query_data)
        
        assert isinstance(patterns, list)
        
        # Should find "machine" and "learning" as frequent terms
        pattern_terms = [p.metadata['term'] for p in patterns]
        assert 'machine' in pattern_terms
        assert 'learning' in pattern_terms
        
        # Check pattern properties
        for pattern in patterns:
            assert pattern.pattern_type == "frequent_terms"
            assert pattern.frequency >= pattern_learner.min_pattern_frequency
            assert len(pattern.examples) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns(self, pattern_learner, sample_query_data):
        """Test temporal pattern analysis."""
        patterns = await pattern_learner._analyze_temporal_patterns(sample_query_data)
        
        assert isinstance(patterns, list)
        
        # Check pattern structure
        for pattern in patterns:
            assert pattern.pattern_type == "temporal"
            assert 'hour' in pattern.metadata
            assert pattern.frequency > 0
    
    @pytest.mark.asyncio
    async def test_analyze_semantic_patterns(self, pattern_learner, sample_query_data):
        """Test semantic pattern analysis."""
        patterns = await pattern_learner._analyze_semantic_patterns(sample_query_data)
        
        assert isinstance(patterns, list)
        
        # Check pattern structure
        for pattern in patterns:
            assert pattern.pattern_type == "semantic"
            assert 'cluster_id' in pattern.metadata
            assert pattern.frequency >= pattern_learner.min_pattern_frequency
    
    @pytest.mark.asyncio
    async def test_analyze_document_usage_patterns(self, pattern_learner, sample_document_usage):
        """Test document usage pattern analysis."""
        # Mock database query
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        pattern_learner.db_connection.cursor.return_value.__aenter__.return_value = cursor_mock
        
        # Mock the _get_document_usage_data method
        pattern_learner._get_document_usage_data = AsyncMock(return_value=sample_document_usage)
        
        # Mock Redis cache
        pattern_learner.redis_client.setex = AsyncMock()
        
        patterns = await pattern_learner.analyze_document_usage_patterns(time_window_days=30)
        
        assert isinstance(patterns, list)
        assert len(patterns) == 2  # Two documents in sample data
        
        # Check pattern structure
        for pattern in patterns:
            assert isinstance(pattern, DocumentUsagePattern)
            assert pattern.document_id in ['doc1', 'doc2']
            assert pattern.access_frequency > 0
            assert isinstance(pattern.peak_usage_times, list)
            assert isinstance(pattern.common_query_contexts, list)
            assert isinstance(pattern.user_segments, list)
            assert 0 <= pattern.effectiveness_score <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_patterns(self, pattern_learner, sample_user_data):
        """Test user behavior pattern analysis."""
        # Mock database query
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            (event['type'], event['data'], event['timestamp'])
            for event in sample_user_data['events']
        ]
        pattern_learner.db_connection.cursor.return_value.__aenter__.return_value = cursor_mock
        
        # Mock Redis cache
        pattern_learner.redis_client.setex = AsyncMock()
        
        pattern = await pattern_learner.analyze_user_behavior_patterns('user1', time_window_days=90)
        
        assert isinstance(pattern, UserBehaviorPattern)
        assert pattern.user_id == 'user1'
        assert pattern.session_duration_avg >= 0
        assert pattern.query_complexity_preference in ['simple', 'moderate', 'complex']
        assert pattern.preferred_response_length in ['brief', 'detailed', 'comprehensive']
        assert isinstance(pattern.domain_preferences, list)
        assert pattern.interaction_style in ['exploratory', 'targeted', 'research']
        assert pattern.feedback_tendency in ['positive', 'critical', 'neutral']
    
    @pytest.mark.asyncio
    async def test_generate_system_optimizations(self, pattern_learner):
        """Test system optimization generation."""
        # Create sample patterns
        query_patterns = [
            QueryPattern(
                pattern_id="freq_ml",
                pattern_type="frequent_terms",
                description="Frequent term: machine learning",
                frequency=10,
                confidence=0.8,
                examples=["machine learning basics"],
                metadata={"term": "machine"}
            )
        ]
        
        document_patterns = [
            DocumentUsagePattern(
                document_id="doc1",
                access_frequency=60,
                peak_usage_times=["09:00", "14:00"],
                common_query_contexts=["machine", "learning"],
                user_segments=["large_group"],
                effectiveness_score=0.8
            )
        ]
        
        user_patterns = [
            UserBehaviorPattern(
                user_id="user1",
                session_duration_avg=15.0,
                query_complexity_preference="complex",
                preferred_response_length="detailed",
                domain_preferences=["technology"],
                interaction_style="research",
                feedback_tendency="positive"
            )
        ]
        
        patterns = {
            'query_patterns': query_patterns,
            'document_patterns': document_patterns,
            'user_patterns': user_patterns
        }
        
        optimizations = await pattern_learner.generate_system_optimizations(patterns)
        
        assert isinstance(optimizations, list)
        assert len(optimizations) > 0
        
        # Check optimization structure
        for opt in optimizations:
            assert isinstance(opt, SystemOptimization)
            assert opt.optimization_type
            assert opt.target_component in ['retrieval', 'caching', 'personalization']
            assert opt.recommendation
            assert 0 <= opt.expected_improvement <= 1
            assert 0 <= opt.confidence <= 1
            assert opt.implementation_priority in ['high', 'medium', 'low']
    
    @pytest.mark.asyncio
    async def test_apply_pattern_based_optimization(self, pattern_learner):
        """Test applying pattern-based optimizations."""
        optimization = SystemOptimization(
            optimization_type="term_boosting",
            target_component="retrieval",
            recommendation="Boost relevance for term 'machine'",
            expected_improvement=0.15,
            confidence=0.8,
            implementation_priority="medium"
        )
        
        # Mock Redis for retrieval optimization
        pattern_learner.redis_client.setex = AsyncMock(return_value=True)
        
        success = await pattern_learner.apply_pattern_based_optimization(optimization)
        
        assert success is True
        pattern_learner.redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_identify_peak_times(self, pattern_learner):
        """Test peak time identification."""
        base_time = datetime.now()
        access_times = [
            base_time.replace(hour=9) + timedelta(minutes=i*10) for i in range(6)  # 9 AM peak
        ] + [
            base_time.replace(hour=14) + timedelta(minutes=i*10) for i in range(4)  # 2 PM peak
        ] + [
            base_time.replace(hour=20) + timedelta(minutes=i*10) for i in range(2)  # 8 PM normal
        ]
        
        peak_times = await pattern_learner._identify_peak_times(access_times)
        
        assert isinstance(peak_times, list)
        assert "09:00" in peak_times  # Should identify 9 AM as peak
        assert "14:00" in peak_times  # Should identify 2 PM as peak
    
    @pytest.mark.asyncio
    async def test_extract_query_contexts(self, pattern_learner):
        """Test query context extraction."""
        queries = [
            "machine learning algorithms",
            "machine learning applications",
            "deep learning neural networks",
            "artificial intelligence basics"
        ]
        
        contexts = await pattern_learner._extract_query_contexts(queries)
        
        assert isinstance(contexts, list)
        assert "machine" in contexts
        assert "learning" in contexts
    
    @pytest.mark.asyncio
    async def test_calculate_effectiveness_score(self, pattern_learner):
        """Test effectiveness score calculation."""
        data = {
            'access_count': 50,
            'users': ['user1', 'user2', 'user3', 'user4', 'user5']
        }
        
        score = await pattern_learner._calculate_effectiveness_score('doc1', data)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
        assert score > 0  # Should be positive for active document
    
    @pytest.mark.asyncio
    async def test_calculate_avg_session_duration(self, pattern_learner, sample_user_data):
        """Test average session duration calculation."""
        duration = await pattern_learner._calculate_avg_session_duration(sample_user_data)
        
        assert isinstance(duration, float)
        assert duration >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_query_complexity(self, pattern_learner, sample_user_data):
        """Test query complexity analysis."""
        complexity = await pattern_learner._analyze_query_complexity(sample_user_data)
        
        assert complexity in ['simple', 'moderate', 'complex']
    
    @pytest.mark.asyncio
    async def test_analyze_response_preferences(self, pattern_learner, sample_user_data):
        """Test response preference analysis."""
        preference = await pattern_learner._analyze_response_preferences(sample_user_data)
        
        assert preference in ['brief', 'detailed', 'comprehensive']
    
    @pytest.mark.asyncio
    async def test_identify_domain_preferences(self, pattern_learner, sample_user_data):
        """Test domain preference identification."""
        domains = await pattern_learner._identify_domain_preferences(sample_user_data)
        
        assert isinstance(domains, list)
        # Should identify 'technology' from sample data
        assert 'technology' in domains
    
    @pytest.mark.asyncio
    async def test_classify_interaction_style(self, pattern_learner, sample_user_data):
        """Test interaction style classification."""
        style = await pattern_learner._classify_interaction_style(sample_user_data)
        
        assert style in ['exploratory', 'targeted', 'research']
    
    @pytest.mark.asyncio
    async def test_analyze_feedback_tendency(self, pattern_learner, sample_user_data):
        """Test feedback tendency analysis."""
        tendency = await pattern_learner._analyze_feedback_tendency(sample_user_data)
        
        assert tendency in ['positive', 'critical', 'neutral']
        # Should be positive based on sample data (rating: 4)
        assert tendency == 'positive'
    
    @pytest.mark.asyncio
    async def test_error_handling(self, pattern_learner):
        """Test error handling in pattern analysis."""
        # Test with database error
        pattern_learner.db_connection.cursor.side_effect = Exception("Database error")
        
        patterns = await pattern_learner.analyze_query_patterns()
        assert patterns == []  # Should return empty list on error
        
        # Test with empty data
        pattern_learner.db_connection.cursor.side_effect = None
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = []
        pattern_learner.db_connection.cursor.return_value.__aenter__.return_value = cursor_mock
        
        patterns = await pattern_learner.analyze_query_patterns()
        assert isinstance(patterns, list)
    
    @pytest.mark.asyncio
    async def test_pattern_caching(self, pattern_learner, sample_query_data):
        """Test pattern result caching."""
        # Mock database query
        cursor_mock = AsyncMock()
        cursor_mock.fetchall.return_value = [
            (item['metadata'], item['timestamp'], item['user_id'])
            for item in sample_query_data
        ]
        pattern_learner.db_connection.cursor.return_value.__aenter__.return_value = cursor_mock
        
        # Mock Redis cache
        pattern_learner.redis_client.setex = AsyncMock()
        
        await pattern_learner.analyze_query_patterns(user_id='user1', time_window_days=30)
        
        # Verify cache was called
        pattern_learner.redis_client.setex.assert_called()
        
        # Check cache key format
        call_args = pattern_learner.redis_client.setex.call_args
        cache_key = call_args[0][0]
        assert cache_key.startswith("query_patterns:")
        assert "user1" in cache_key
        assert "30" in cache_key

if __name__ == "__main__":
    pytest.main([__file__])