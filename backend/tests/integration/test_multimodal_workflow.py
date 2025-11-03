"""End-to-end integration tests for multi-modal learning workflow."""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any, List

from backend.rl.multimodal.visual_content_processor import VisualContentProcessor
from backend.rl.multimodal.feature_integrator import MultiModalFeatureIntegrator
from backend.rl.multimodal.learning_model import MultiModalLearningModel
from backend.rl.multimodal.data_models import (
    VisualElement, MultiModalFeatures, MultiModalContext,
    VisualElementType, Document
)
from backend.rl.utils import multimodal_logger, handle_errors
from backend.rl.exceptions.advanced_exceptions import MultiModalProcessingError


class TestMultiModalWorkflowIntegration:
    """Integration tests for complete multi-modal learning workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visual_processor = VisualContentProcessor()
        self.feature_integrator = MultiModalFeatureIntegrator()
        self.learning_model = MultiModalLearningModel()
    
    @pytest.mark.asyncio
    async def test_complete_multimodal_workflow_success(self):
        """Test complete multi-modal workflow from document to recommendations."""
        # Create test document with visual content
        document = Document(
            id="test_doc_001",
            title="Test Research Paper",
            content="This paper presents novel findings in machine learning.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"mock_chart_data",
                    "caption": "Performance comparison chart"
                },
                {
                    "type": "diagram",
                    "data": b"mock_diagram_data",
                    "caption": "System architecture diagram"
                }
            ]
        )
        
        # Step 1: Visual content processing
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        assert visual_features is not None
        assert len(visual_features.elements) == 2
        assert visual_features.elements[0].element_type == VisualElementType.CHART
        assert visual_features.elements[1].element_type == VisualElementType.DIAGRAM
        
        # Step 2: Feature integration
        text_features = Mock()
        text_features.embeddings = np.random.rand(512)
        text_features.keywords = ["machine learning", "novel findings"]
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        assert integrated_features is not None
        assert integrated_features.text_features == text_features
        assert integrated_features.visual_features == visual_features
        assert integrated_features.integrated_embedding is not None
        assert len(integrated_features.cross_modal_relationships) > 0
        
        # Step 3: Multi-modal learning
        context = MultiModalContext(
            document_content=document,
            visual_elements=visual_features.elements,
            user_interaction_history=[],
            research_context={"domain": "machine_learning", "task": "literature_review"}
        )
        
        recommendations = await self.learning_model.generate_multimodal_recommendations(context)
        
        assert recommendations is not None
        assert len(recommendations) > 0
        assert all(hasattr(rec, 'content') for rec in recommendations)
        assert all(hasattr(rec, 'confidence') for rec in recommendations)
        assert all(hasattr(rec, 'reasoning') for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_with_chart_analysis(self):
        """Test multi-modal workflow with detailed chart analysis."""
        # Create document with chart data
        document = Document(
            id="chart_doc_001",
            title="Performance Analysis Paper",
            content="This paper analyzes performance metrics across different algorithms.",
            visual_elements=[
                {
                    "type": "chart",
                    "chart_type": "bar_chart",
                    "data": b"mock_bar_chart_data",
                    "caption": "Algorithm performance comparison"
                }
            ]
        )
        
        # Process visual content with chart analysis
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        # Verify chart-specific processing
        chart_element = visual_features.elements[0]
        assert chart_element.element_type == VisualElementType.CHART
        
        # Extract quantitative data from chart
        quantitative_data = await self.visual_processor.extract_quantitative_data(
            document.visual_elements[0]["data"]
        )
        
        assert quantitative_data is not None
        assert quantitative_data.data_points is not None
        assert len(quantitative_data.data_points) > 0
        assert quantitative_data.chart_type == "bar_chart"
        
        # Integrate with text features
        text_features = Mock()
        text_features.embeddings = np.random.rand(512)
        text_features.keywords = ["performance", "algorithms", "comparison"]
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        # Verify quantitative data integration
        assert any(
            rel.relationship_type == "text_chart_correlation"
            for rel in integrated_features.cross_modal_relationships
        )
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_with_diagram_analysis(self):
        """Test multi-modal workflow with diagram structure analysis."""
        # Create document with diagram
        document = Document(
            id="diagram_doc_001",
            title="System Architecture Paper",
            content="This paper describes a novel system architecture.",
            visual_elements=[
                {
                    "type": "diagram",
                    "diagram_type": "flowchart",
                    "data": b"mock_flowchart_data",
                    "caption": "System component flowchart"
                }
            ]
        )
        
        # Process visual content with diagram analysis
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        # Verify diagram-specific processing
        diagram_element = visual_features.elements[0]
        assert diagram_element.element_type == VisualElementType.DIAGRAM
        
        # Analyze diagram structure
        structural_relationships = await self.visual_processor.analyze_diagram_structure(
            document.visual_elements[0]["data"]
        )
        
        assert structural_relationships is not None
        assert structural_relationships.nodes is not None
        assert structural_relationships.edges is not None
        assert len(structural_relationships.nodes) > 0
        assert structural_relationships.diagram_type == "flowchart"
        
        # Integrate with text features
        text_features = Mock()
        text_features.embeddings = np.random.rand(512)
        text_features.keywords = ["system", "architecture", "components"]
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        # Verify structural relationship integration
        assert any(
            rel.relationship_type == "text_diagram_structure"
            for rel in integrated_features.cross_modal_relationships
        )
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_error_recovery(self):
        """Test multi-modal workflow error handling and recovery."""
        # Create document that will cause processing error
        document = Document(
            id="error_doc_001",
            title="Problematic Document",
            content="This document has corrupted visual elements.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"corrupted_data",
                    "caption": "Corrupted chart"
                }
            ]
        )
        
        # Mock visual processor to raise error
        with patch.object(
            self.visual_processor, 
            'extract_visual_features',
            side_effect=MultiModalProcessingError("Visual processing failed")
        ):
            # Test error handling
            with pytest.raises(MultiModalProcessingError):
                await self.visual_processor.extract_visual_features(document)
        
        # Test recovery with fallback processing
        with patch.object(
            self.visual_processor,
            'extract_visual_features'
        ) as mock_extract:
            # First call fails, second succeeds (retry scenario)
            mock_extract.side_effect = [
                MultiModalProcessingError("Temporary failure"),
                Mock(elements=[], confidence_scores={})
            ]
            
            # Use error handler decorator for retry
            @handle_errors(component="multimodal", max_retries=1, retry_delay=0.01)
            async def process_with_retry():
                return await self.visual_processor.extract_visual_features(document)
            
            result = await process_with_retry()
            assert result is not None
            assert mock_extract.call_count == 2
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_performance_tracking(self):
        """Test multi-modal workflow with performance tracking."""
        document = Document(
            id="perf_doc_001",
            title="Performance Test Document",
            content="Document for performance testing.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"performance_test_chart",
                    "caption": "Test chart"
                }
            ]
        )
        
        # Track processing times
        start_time = datetime.now()
        
        # Step 1: Visual processing
        visual_start = datetime.now()
        visual_features = await self.visual_processor.extract_visual_features(document)
        visual_time = (datetime.now() - visual_start).total_seconds()
        
        # Step 2: Feature integration
        integration_start = datetime.now()
        text_features = Mock()
        text_features.embeddings = np.random.rand(512)
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        integration_time = (datetime.now() - integration_start).total_seconds()
        
        # Step 3: Learning model
        learning_start = datetime.now()
        context = MultiModalContext(
            document_content=document,
            visual_elements=visual_features.elements,
            user_interaction_history=[],
            research_context={"domain": "test"}
        )
        
        recommendations = await self.learning_model.generate_multimodal_recommendations(context)
        learning_time = (datetime.now() - learning_start).total_seconds()
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Verify performance metrics
        assert visual_time > 0
        assert integration_time > 0
        assert learning_time > 0
        assert total_time > 0
        
        # Log performance metrics
        multimodal_logger.info(
            "Multi-modal workflow performance",
            visual_processing_time=visual_time,
            integration_time=integration_time,
            learning_time=learning_time,
            total_time=total_time,
            document_id=document.id
        )
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_with_user_feedback(self):
        """Test multi-modal workflow incorporating user feedback."""
        document = Document(
            id="feedback_doc_001",
            title="User Feedback Test Document",
            content="Document for testing user feedback integration.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"feedback_test_chart",
                    "caption": "User feedback test chart"
                }
            ]
        )
        
        # Simulate user interaction history
        user_interactions = [
            {
                "type": "visual_element_click",
                "element_id": "chart_001",
                "timestamp": datetime.now(),
                "feedback": "positive"
            },
            {
                "type": "recommendation_rating",
                "recommendation_id": "rec_001",
                "rating": 4.5,
                "timestamp": datetime.now()
            }
        ]
        
        # Process document with user feedback context
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        text_features = Mock()
        text_features.embeddings = np.random.rand(512)
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        # Create context with user feedback
        context = MultiModalContext(
            document_content=document,
            visual_elements=visual_features.elements,
            user_interaction_history=user_interactions,
            research_context={"domain": "user_study", "feedback_enabled": True}
        )
        
        # Generate recommendations with feedback consideration
        recommendations = await self.learning_model.generate_multimodal_recommendations(context)
        
        # Verify feedback integration
        assert recommendations is not None
        assert len(recommendations) > 0
        
        # Check that recommendations consider user feedback
        for rec in recommendations:
            assert hasattr(rec, 'feedback_score')
            assert rec.feedback_score is not None
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_batch_processing(self):
        """Test multi-modal workflow with batch document processing."""
        # Create multiple test documents
        documents = [
            Document(
                id=f"batch_doc_{i:03d}",
                title=f"Batch Test Document {i}",
                content=f"Content for batch document {i}.",
                visual_elements=[
                    {
                        "type": "chart",
                        "data": f"batch_chart_data_{i}".encode(),
                        "caption": f"Chart {i}"
                    }
                ]
            )
            for i in range(5)
        ]
        
        # Process documents in batch
        batch_results = []
        
        for document in documents:
            # Visual processing
            visual_features = await self.visual_processor.extract_visual_features(document)
            
            # Feature integration
            text_features = Mock()
            text_features.embeddings = np.random.rand(512)
            
            integrated_features = await self.feature_integrator.integrate_features(
                text_features, visual_features
            )
            
            # Learning model
            context = MultiModalContext(
                document_content=document,
                visual_elements=visual_features.elements,
                user_interaction_history=[],
                research_context={"domain": "batch_processing"}
            )
            
            recommendations = await self.learning_model.generate_multimodal_recommendations(context)
            
            batch_results.append({
                'document_id': document.id,
                'visual_features': visual_features,
                'integrated_features': integrated_features,
                'recommendations': recommendations
            })
        
        # Verify batch processing results
        assert len(batch_results) == 5
        
        for result in batch_results:
            assert result['visual_features'] is not None
            assert result['integrated_features'] is not None
            assert result['recommendations'] is not None
            assert len(result['recommendations']) > 0
        
        # Verify consistency across batch
        feature_dimensions = [
            len(result['integrated_features'].integrated_embedding)
            for result in batch_results
        ]
        assert all(dim == feature_dimensions[0] for dim in feature_dimensions)
    
    @pytest.mark.asyncio
    async def test_multimodal_workflow_memory_efficiency(self):
        """Test multi-modal workflow memory efficiency."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large document for memory testing
        large_document = Document(
            id="memory_test_doc",
            title="Large Document for Memory Testing",
            content="Large content " * 1000,  # Simulate large text
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"large_chart_data" * 100,  # Simulate large visual data
                    "caption": "Large chart for memory testing"
                }
                for _ in range(10)  # Multiple visual elements
            ]
        )
        
        # Process large document
        visual_features = await self.visual_processor.extract_visual_features(large_document)
        
        text_features = Mock()
        text_features.embeddings = np.random.rand(2048)  # Larger embeddings
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        context = MultiModalContext(
            document_content=large_document,
            visual_elements=visual_features.elements,
            user_interaction_history=[],
            research_context={"domain": "memory_test"}
        )
        
        recommendations = await self.learning_model.generate_multimodal_recommendations(context)
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Log memory usage
        multimodal_logger.info(
            "Multi-modal workflow memory usage",
            initial_memory_mb=initial_memory,
            final_memory_mb=final_memory,
            memory_increase_mb=memory_increase,
            document_size=len(large_document.content),
            visual_elements_count=len(large_document.visual_elements)
        )
        
        # Verify reasonable memory usage (should not exceed 100MB increase)
        assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"
        
        # Verify processing completed successfully
        assert visual_features is not None
        assert integrated_features is not None
        assert recommendations is not None


class TestMultiModalWorkflowEdgeCases:
    """Test edge cases and boundary conditions in multi-modal workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visual_processor = VisualContentProcessor()
        self.feature_integrator = MultiModalFeatureIntegrator()
        self.learning_model = MultiModalLearningModel()
    
    @pytest.mark.asyncio
    async def test_workflow_with_empty_document(self):
        """Test workflow with empty document."""
        empty_document = Document(
            id="empty_doc",
            title="",
            content="",
            visual_elements=[]
        )
        
        visual_features = await self.visual_processor.extract_visual_features(empty_document)
        
        # Should handle empty document gracefully
        assert visual_features is not None
        assert len(visual_features.elements) == 0
        
        text_features = Mock()
        text_features.embeddings = np.array([])
        text_features.keywords = []
        
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        assert integrated_features is not None
        # Should have minimal integrated features for empty content
    
    @pytest.mark.asyncio
    async def test_workflow_with_unsupported_visual_elements(self):
        """Test workflow with unsupported visual element types."""
        document = Document(
            id="unsupported_doc",
            title="Document with Unsupported Elements",
            content="This document has unsupported visual elements.",
            visual_elements=[
                {
                    "type": "unsupported_type",
                    "data": b"unsupported_data",
                    "caption": "Unsupported element"
                }
            ]
        )
        
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        # Should handle unsupported elements gracefully
        assert visual_features is not None
        # Unsupported elements should be skipped or marked as unknown
        if len(visual_features.elements) > 0:
            assert visual_features.elements[0].element_type == VisualElementType.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_workflow_with_corrupted_visual_data(self):
        """Test workflow with corrupted visual data."""
        document = Document(
            id="corrupted_doc",
            title="Document with Corrupted Visual Data",
            content="This document has corrupted visual data.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"corrupted_binary_data_that_cannot_be_processed",
                    "caption": "Corrupted chart"
                }
            ]
        )
        
        # Should handle corrupted data gracefully
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        assert visual_features is not None
        # Corrupted elements should be marked with low confidence or skipped
        if len(visual_features.elements) > 0:
            assert visual_features.confidence_scores.get("overall", 0) < 0.5
    
    @pytest.mark.asyncio
    async def test_workflow_with_extremely_large_embeddings(self):
        """Test workflow with extremely large feature embeddings."""
        document = Document(
            id="large_embedding_doc",
            title="Document for Large Embedding Test",
            content="Test document.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"test_chart_data",
                    "caption": "Test chart"
                }
            ]
        )
        
        visual_features = await self.visual_processor.extract_visual_features(document)
        
        # Create extremely large text embeddings
        text_features = Mock()
        text_features.embeddings = np.random.rand(10000)  # Very large embedding
        
        # Should handle large embeddings efficiently
        integrated_features = await self.feature_integrator.integrate_features(
            text_features, visual_features
        )
        
        assert integrated_features is not None
        assert integrated_features.integrated_embedding is not None
        # Integrated embedding should be reasonably sized
        assert len(integrated_features.integrated_embedding) <= 2048


if __name__ == "__main__":
    pytest.main([__file__])