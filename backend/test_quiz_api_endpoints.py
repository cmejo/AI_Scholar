"""
Test Quiz API Endpoints
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.quiz_generation_service import (
    QuizGenerationService,
    QuestionType, 
    DifficultyLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quiz_service_integration():
    """Test quiz service integration with mock data"""
    try:
        logger.info("Testing quiz service integration...")
        
        service = QuizGenerationService()
        
        # Test document content retrieval (mock)
        document_content = await service._get_document_content("test_doc_123")
        logger.info(f"Retrieved document content: {document_content[:100]}...")
        
        # Test key concept extraction
        key_concepts = await service._extract_key_concepts(document_content)
        logger.info(f"Extracted key concepts: {key_concepts}")
        
        # Test question generation for each type
        question_types = [
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.SHORT_ANSWER,
            QuestionType.TRUE_FALSE,
            QuestionType.FILL_IN_BLANK
        ]
        
        for question_type in question_types:
            if question_type == QuestionType.MULTIPLE_CHOICE:
                question = await service.generate_multiple_choice_question(
                    content=document_content,
                    key_concept=key_concepts[0] if key_concepts else "machine learning",
                    difficulty_level=DifficultyLevel.INTERMEDIATE
                )
            elif question_type == QuestionType.SHORT_ANSWER:
                question = await service.generate_short_answer_question(
                    content=document_content,
                    key_concept=key_concepts[0] if key_concepts else "machine learning",
                    difficulty_level=DifficultyLevel.INTERMEDIATE
                )
            elif question_type == QuestionType.TRUE_FALSE:
                question = await service._generate_true_false_question(
                    content=document_content,
                    key_concept=key_concepts[0] if key_concepts else "machine learning",
                    difficulty_level=DifficultyLevel.INTERMEDIATE
                )
            elif question_type == QuestionType.FILL_IN_BLANK:
                question = await service._generate_fill_in_blank_question(
                    content=document_content,
                    key_concept=key_concepts[0] if key_concepts else "machine learning",
                    difficulty_level=DifficultyLevel.INTERMEDIATE
                )
            
            logger.info(f"Generated {question_type.value} question:")
            logger.info(f"  Question: {question.question_text}")
            logger.info(f"  Answer: {question.correct_answer}")
            logger.info(f"  Confidence: {question.confidence_score}")
        
        return True
        
    except Exception as e:
        logger.error(f"Quiz service integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_quiz_validation():
    """Test quiz question validation"""
    try:
        logger.info("Testing quiz question validation...")
        
        service = QuizGenerationService()
        
        # Create test questions with different quality levels
        good_question = await service.generate_multiple_choice_question(
            content="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
            key_concept="machine learning",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        # Validate question quality
        quality_metrics = await service.validate_question_quality(
            question=good_question,
            content="Machine learning is a subset of artificial intelligence that enables computers to learn from data."
        )
        
        logger.info(f"Question quality metrics:")
        logger.info(f"  Overall score: {quality_metrics['overall_score']:.2f}")
        logger.info(f"  Clarity score: {quality_metrics['clarity_score']:.2f}")
        logger.info(f"  Relevance score: {quality_metrics['relevance_score']:.2f}")
        logger.info(f"  Answer quality: {quality_metrics['answer_quality']:.2f}")
        
        if quality_metrics['issues']:
            logger.info(f"  Issues: {quality_metrics['issues']}")
        
        if quality_metrics['suggestions']:
            logger.info(f"  Suggestions: {quality_metrics['suggestions']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Quiz validation test failed: {str(e)}")
        return False

async def test_comprehensive_answer_key():
    """Test comprehensive answer key generation"""
    try:
        logger.info("Testing comprehensive answer key generation...")
        
        service = QuizGenerationService()
        
        # Generate a sample quiz
        sample_content = "Machine learning algorithms learn from data to make predictions and decisions."
        key_concepts = ["machine learning", "algorithms", "data"]
        
        questions = []
        
        # Generate different types of questions
        mc_question = await service.generate_multiple_choice_question(
            content=sample_content,
            key_concept="machine learning",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        questions.append(mc_question)
        
        sa_question = await service.generate_short_answer_question(
            content=sample_content,
            key_concept="algorithms",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        questions.append(sa_question)
        
        # Create quiz
        from services.quiz_generation_service import Quiz
        quiz = Quiz(
            id="comprehensive_test_quiz",
            title="Comprehensive Test Quiz",
            description="A test quiz for comprehensive answer key",
            document_id="test_doc",
            questions=questions,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_time_minutes=service._estimate_completion_time(questions),
            learning_objectives=await service._generate_learning_objectives(key_concepts),
            created_at=datetime.now()
        )
        
        # Generate comprehensive answer key
        comprehensive_key = await service.generate_comprehensive_answer_key(quiz)
        
        logger.info(f"Comprehensive answer key generated:")
        logger.info(f"  Quiz: {comprehensive_key['quiz_title']}")
        logger.info(f"  Total questions: {comprehensive_key['total_questions']}")
        logger.info(f"  Learning outcomes: {len(comprehensive_key.get('learning_outcomes', []))}")
        logger.info(f"  Detailed explanations: {len(comprehensive_key.get('detailed_explanations', []))}")
        
        if 'quiz_statistics' in comprehensive_key:
            stats = comprehensive_key['quiz_statistics']
            logger.info(f"  Quiz statistics:")
            logger.info(f"    Total points: {stats.get('total_points', 0)}")
            logger.info(f"    Question types: {stats.get('question_type_distribution', {})}")
            logger.info(f"    Difficulty distribution: {stats.get('difficulty_distribution', {})}")
        
        return True
        
    except Exception as e:
        logger.error(f"Comprehensive answer key test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all API endpoint tests"""
    logger.info("=== Quiz API Endpoints Tests ===")
    
    # Test service integration
    integration_success = await test_quiz_service_integration()
    
    # Test quiz validation
    validation_success = await test_quiz_validation()
    
    # Test comprehensive answer key
    answer_key_success = await test_comprehensive_answer_key()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Service integration: {'PASSED' if integration_success else 'FAILED'}")
    logger.info(f"Quiz validation: {'PASSED' if validation_success else 'FAILED'}")
    logger.info(f"Comprehensive answer key: {'PASSED' if answer_key_success else 'FAILED'}")
    
    all_passed = all([
        integration_success,
        validation_success,
        answer_key_success
    ])
    
    if all_passed:
        logger.info("🎉 All API endpoint tests PASSED!")
        return 0
    else:
        logger.error("❌ Some tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)