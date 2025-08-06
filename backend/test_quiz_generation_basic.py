"""
Basic test for Quiz Generation Service
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.quiz_generation_service import (
    QuestionType, 
    DifficultyLevel,
    QuizQuestion,
    Quiz
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quiz_data_structures():
    """Test quiz data structures and basic functionality"""
    try:
        logger.info("Testing quiz data structures...")
        
        # Test QuizQuestion creation
        question = QuizQuestion(
            id="test_q1",
            question_text="What is machine learning?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            options=["AI subset", "Programming language", "Database", "Operating system"],
            correct_answer="AI subset",
            explanation="Machine learning is a subset of artificial intelligence.",
            source_content="Machine learning is a subset of AI...",
            confidence_score=0.8,
            learning_objectives=["Understand ML basics"],
            metadata={"key_concept": "machine learning"}
        )
        
        logger.info(f"Created question: {question.question_text}")
        logger.info(f"Question type: {question.question_type.value}")
        logger.info(f"Difficulty: {question.difficulty_level.value}")
        logger.info(f"Options: {question.options}")
        
        # Test Quiz creation
        quiz = Quiz(
            id="test_quiz_1",
            title="Machine Learning Basics",
            description="A quiz about ML fundamentals",
            document_id="doc_123",
            questions=[question],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_time_minutes=10,
            learning_objectives=["Understand ML", "Apply ML concepts"],
            created_at=datetime.now()
        )
        
        logger.info(f"Created quiz: {quiz.title}")
        logger.info(f"Quiz has {len(quiz.questions)} questions")
        logger.info(f"Estimated time: {quiz.estimated_time_minutes} minutes")
        
        return True
        
    except Exception as e:
        logger.error(f"Data structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_question_types():
    """Test question type enumeration"""
    try:
        logger.info("Testing question types...")
        
        # Test all question types
        question_types = [
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.SHORT_ANSWER,
            QuestionType.ESSAY,
            QuestionType.TRUE_FALSE,
            QuestionType.FILL_IN_BLANK
        ]
        
        logger.info("Available question types:")
        for qt in question_types:
            logger.info(f"  - {qt.value}")
        
        # Test difficulty levels
        difficulty_levels = [
            DifficultyLevel.BEGINNER,
            DifficultyLevel.INTERMEDIATE,
            DifficultyLevel.ADVANCED
        ]
        
        logger.info("Available difficulty levels:")
        for dl in difficulty_levels:
            logger.info(f"  - {dl.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Question types test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    logger.info("=== Quiz Generation Service Tests ===")
    
    # Test question types
    types_success = await test_question_types()
    
    # Test data structures
    structures_success = await test_quiz_data_structures()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Question types test: {'PASSED' if types_success else 'FAILED'}")
    logger.info(f"Data structures test: {'PASSED' if structures_success else 'FAILED'}")
    
    if types_success and structures_success:
        logger.info("All tests PASSED!")
        return 0
    else:
        logger.error("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)