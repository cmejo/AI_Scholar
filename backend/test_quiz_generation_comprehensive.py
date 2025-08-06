"""
Comprehensive test for Quiz Generation Service - AI-powered features
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
    DifficultyLevel,
    QuizQuestion,
    Quiz
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_powered_question_generation():
    """Test AI-powered question generation from content"""
    try:
        logger.info("Testing AI-powered question generation...")
        
        service = QuizGenerationService()
        
        # Sample content for testing
        sample_content = """
        Machine learning is a subset of artificial intelligence that focuses on algorithms 
        and statistical models that enable computer systems to improve their performance 
        on a specific task through experience. Deep learning is a specialized form of 
        machine learning that uses neural networks with multiple layers to model and 
        understand complex patterns in data. Natural language processing enables computers 
        to understand, interpret, and generate human language in a valuable way.
        """
        
        # Test multiple choice question generation
        mc_question = await service.generate_multiple_choice_question(
            content=sample_content,
            key_concept="machine learning",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        logger.info(f"Generated MC Question: {mc_question.question_text}")
        logger.info(f"Options: {mc_question.options}")
        logger.info(f"Correct Answer: {mc_question.correct_answer}")
        logger.info(f"Confidence Score: {mc_question.confidence_score}")
        
        # Test short answer question generation
        sa_question = await service.generate_short_answer_question(
            content=sample_content,
            key_concept="deep learning",
            difficulty_level=DifficultyLevel.ADVANCED
        )
        
        logger.info(f"Generated SA Question: {sa_question.question_text}")
        logger.info(f"Model Answer: {sa_question.correct_answer}")
        logger.info(f"Explanation: {sa_question.explanation[:100]}...")
        
        # Test essay question generation
        essay_question = await service.generate_essay_question(
            content=sample_content,
            key_concepts=["machine learning", "deep learning", "neural networks"],
            difficulty_level=DifficultyLevel.ADVANCED
        )
        
        logger.info(f"Generated Essay Question: {essay_question.question_text}")
        logger.info(f"Essay Outline: {essay_question.correct_answer[:150]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"AI-powered question generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_difficulty_assessment():
    """Test difficulty assessment functionality"""
    try:
        logger.info("Testing difficulty assessment...")
        
        service = QuizGenerationService()
        
        sample_content = "Machine learning algorithms learn from data to make predictions."
        
        # Create questions with different complexity levels
        simple_question = QuizQuestion(
            id="test_simple",
            question_text="What is machine learning?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            difficulty_level=DifficultyLevel.BEGINNER,
            correct_answer="A type of AI",
            explanation="Basic definition"
        )
        
        complex_question = QuizQuestion(
            id="test_complex",
            question_text="Analyze the implications of gradient descent optimization in neural network training and evaluate its effectiveness compared to alternative optimization algorithms.",
            question_type=QuestionType.ESSAY,
            difficulty_level=DifficultyLevel.ADVANCED,
            correct_answer="Complex analysis required",
            explanation="Advanced analysis"
        )
        
        # Assess difficulty
        simple_assessed = await service.assess_question_difficulty(simple_question, sample_content)
        complex_assessed = await service.assess_question_difficulty(complex_question, sample_content)
        
        logger.info(f"Simple question assessed as: {simple_assessed.value}")
        logger.info(f"Complex question assessed as: {complex_assessed.value}")
        
        # Verify assessments make sense
        if simple_assessed in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]:
            logger.info("✓ Simple question correctly assessed")
        else:
            logger.warning("⚠ Simple question assessment may be incorrect")
        
        if complex_assessed in [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]:
            logger.info("✓ Complex question correctly assessed")
        else:
            logger.warning("⚠ Complex question assessment may be incorrect")
        
        return True
        
    except Exception as e:
        logger.error(f"Difficulty assessment test failed: {str(e)}")
        return False

async def test_content_analysis():
    """Test content complexity analysis"""
    try:
        logger.info("Testing content complexity analysis...")
        
        service = QuizGenerationService()
        
        # Test with different types of content
        simple_content = "Cats are animals. They have fur. They like to play."
        
        complex_content = """
        The implementation of convolutional neural networks in computer vision applications 
        demonstrates significant improvements in feature extraction and pattern recognition 
        capabilities. Advanced architectures such as ResNet and DenseNet utilize skip 
        connections and dense connectivity patterns to mitigate the vanishing gradient 
        problem inherent in deep network topologies.
        """
        
        # Analyze content complexity
        simple_analysis = await service.analyze_content_complexity(simple_content)
        complex_analysis = await service.analyze_content_complexity(complex_content)
        
        logger.info(f"Simple content analysis:")
        logger.info(f"  - Readability: {simple_analysis['readability_score']:.2f}")
        logger.info(f"  - Concept density: {simple_analysis['concept_density']:.2f}")
        logger.info(f"  - Content type: {simple_analysis['content_type']}")
        logger.info(f"  - Recommended difficulty: {simple_analysis['recommended_difficulty'].value}")
        
        logger.info(f"Complex content analysis:")
        logger.info(f"  - Readability: {complex_analysis['readability_score']:.2f}")
        logger.info(f"  - Concept density: {complex_analysis['concept_density']:.2f}")
        logger.info(f"  - Content type: {complex_analysis['content_type']}")
        logger.info(f"  - Recommended difficulty: {complex_analysis['recommended_difficulty'].value}")
        logger.info(f"  - Technical terms: {complex_analysis['technical_terms'][:5]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Content analysis test failed: {str(e)}")
        return False

async def test_answer_key_generation():
    """Test comprehensive answer key generation"""
    try:
        logger.info("Testing answer key generation...")
        
        service = QuizGenerationService()
        
        # Create a sample quiz
        questions = [
            QuizQuestion(
                id="q1",
                question_text="What is machine learning?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                difficulty_level=DifficultyLevel.BEGINNER,
                options=["AI subset", "Programming language", "Database", "Operating system"],
                correct_answer="AI subset",
                explanation="Machine learning is a subset of artificial intelligence.",
                learning_objectives=["Understand ML basics"]
            ),
            QuizQuestion(
                id="q2",
                question_text="Explain the concept of neural networks.",
                question_type=QuestionType.SHORT_ANSWER,
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                correct_answer="Neural networks are computing systems inspired by biological neural networks.",
                explanation="Short answer rubric for neural networks.",
                learning_objectives=["Explain neural networks"]
            )
        ]
        
        quiz = Quiz(
            id="test_quiz",
            title="Test Quiz",
            description="A test quiz",
            document_id="doc_123",
            questions=questions,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_time_minutes=10,
            learning_objectives=["Understand AI concepts"],
            created_at=datetime.now()
        )
        
        # Generate answer key
        answer_key = await service.generate_answer_key(quiz)
        
        logger.info(f"Generated answer key for quiz: {answer_key['quiz_title']}")
        logger.info(f"Total questions: {answer_key['total_questions']}")
        logger.info(f"Scoring guide: {answer_key['scoring_guide']}")
        
        for answer in answer_key['answers']:
            logger.info(f"Q{answer['question_number']}: {answer['question_type']} - {answer['points']} points")
        
        return True
        
    except Exception as e:
        logger.error(f"Answer key generation test failed: {str(e)}")
        return False

async def test_adaptive_question_selection():
    """Test adaptive question selection based on user performance"""
    try:
        logger.info("Testing adaptive question selection...")
        
        service = QuizGenerationService()
        
        sample_content = """
        Machine learning algorithms can be categorized into supervised, unsupervised, 
        and reinforcement learning. Supervised learning uses labeled data to train 
        models for prediction tasks. Unsupervised learning finds patterns in unlabeled 
        data. Reinforcement learning learns through interaction with an environment.
        """
        
        key_concepts = ["supervised learning", "unsupervised learning", "reinforcement learning"]
        
        # Test with different performance histories
        high_performer = {'average_score': 0.9, 'total_attempts': 10}
        low_performer = {'average_score': 0.4, 'total_attempts': 5}
        
        # Generate adaptive questions for high performer
        high_questions = await service.adaptive_question_selection(
            user_id="high_user",
            content=sample_content,
            key_concepts=key_concepts,
            user_performance_history=high_performer
        )
        
        # Generate adaptive questions for low performer
        low_questions = await service.adaptive_question_selection(
            user_id="low_user",
            content=sample_content,
            key_concepts=key_concepts,
            user_performance_history=low_performer
        )
        
        logger.info(f"High performer questions:")
        for i, q in enumerate(high_questions):
            logger.info(f"  Q{i+1}: {q.difficulty_level.value} - {q.question_type.value}")
        
        logger.info(f"Low performer questions:")
        for i, q in enumerate(low_questions):
            logger.info(f"  Q{i+1}: {q.difficulty_level.value} - {q.question_type.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Adaptive question selection test failed: {str(e)}")
        return False

async def main():
    """Run all comprehensive tests"""
    logger.info("=== Quiz Generation Service Comprehensive Tests ===")
    
    # Test AI-powered question generation
    ai_generation_success = await test_ai_powered_question_generation()
    
    # Test difficulty assessment
    difficulty_success = await test_difficulty_assessment()
    
    # Test content analysis
    content_analysis_success = await test_content_analysis()
    
    # Test answer key generation
    answer_key_success = await test_answer_key_generation()
    
    # Test adaptive question selection
    adaptive_success = await test_adaptive_question_selection()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"AI-powered question generation: {'PASSED' if ai_generation_success else 'FAILED'}")
    logger.info(f"Difficulty assessment: {'PASSED' if difficulty_success else 'FAILED'}")
    logger.info(f"Content analysis: {'PASSED' if content_analysis_success else 'FAILED'}")
    logger.info(f"Answer key generation: {'PASSED' if answer_key_success else 'FAILED'}")
    logger.info(f"Adaptive question selection: {'PASSED' if adaptive_success else 'FAILED'}")
    
    all_passed = all([
        ai_generation_success,
        difficulty_success,
        content_analysis_success,
        answer_key_success,
        adaptive_success
    ])
    
    if all_passed:
        logger.info("🎉 All comprehensive tests PASSED!")
        return 0
    else:
        logger.error("❌ Some tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)