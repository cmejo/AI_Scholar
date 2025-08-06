"""
Task 4.1 Core Functionality Test

This test verifies the core AI-powered quiz generation functionality without database dependencies.
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

async def test_core_question_generation():
    """Test core AI-powered question generation functionality"""
    try:
        logger.info("✓ Testing core AI-powered question generation...")
        
        service = QuizGenerationService()
        
        # Test content for question generation
        research_content = """
        Machine learning is a subset of artificial intelligence that focuses on algorithms 
        and statistical models that enable computer systems to improve their performance 
        on a specific task through experience. Deep learning is a specialized form of 
        machine learning that uses neural networks with multiple layers to model and 
        understand complex patterns in data. Natural language processing enables computers 
        to understand, interpret, and generate human language in a valuable way. Computer 
        vision allows machines to interpret and understand visual information from the world.
        """
        
        # Test key concept extraction
        key_concepts = await service._extract_key_concepts(research_content)
        logger.info(f"  Extracted key concepts: {key_concepts}")
        assert len(key_concepts) > 0, "Should extract key concepts from content"
        
        # Test content complexity analysis
        complexity = await service.analyze_content_complexity(research_content)
        logger.info(f"  Content complexity: {complexity['content_type']} - {complexity['recommended_difficulty'].value}")
        assert 'readability_score' in complexity, "Should analyze readability"
        assert 'concept_density' in complexity, "Should analyze concept density"
        
        # Test multiple choice question generation
        mc_question = await service.generate_multiple_choice_question(
            content=research_content,
            key_concept="machine learning",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        assert mc_question.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(mc_question.options) == 4
        assert mc_question.correct_answer in mc_question.options
        assert len(mc_question.explanation) > 10
        logger.info(f"  ✓ Multiple choice question: {mc_question.question_text[:50]}...")
        
        # Test short answer question generation
        sa_question = await service.generate_short_answer_question(
            content=research_content,
            key_concept="deep learning",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        assert sa_question.question_type == QuestionType.SHORT_ANSWER
        assert len(sa_question.correct_answer) > 10
        assert len(sa_question.explanation) > 20
        logger.info(f"  ✓ Short answer question: {sa_question.question_text[:50]}...")
        
        # Test essay question generation
        essay_question = await service.generate_essay_question(
            content=research_content,
            key_concepts=["machine learning", "deep learning"],
            difficulty_level=DifficultyLevel.ADVANCED
        )
        
        assert essay_question.question_type == QuestionType.ESSAY
        assert len(essay_question.correct_answer) > 50
        assert len(essay_question.explanation) > 50
        logger.info(f"  ✓ Essay question: {essay_question.question_text[:50]}...")
        
        # Test true/false question generation
        tf_question = await service._generate_true_false_question(
            content=research_content,
            key_concept="natural language processing",
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        assert tf_question.question_type == QuestionType.TRUE_FALSE
        assert tf_question.correct_answer in ["True", "False"]
        logger.info(f"  ✓ True/False question: {tf_question.question_text[:50]}...")
        
        # Test fill-in-blank question generation
        fib_question = await service._generate_fill_in_blank_question(
            content=research_content,
            key_concept="computer vision",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        assert fib_question.question_type == QuestionType.FILL_IN_BLANK
        assert "_____" in fib_question.question_text
        logger.info(f"  ✓ Fill-in-blank question: {fib_question.question_text[:50]}...")
        
        logger.info("  ✓ All question types generated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Core question generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_difficulty_assessment():
    """Test difficulty assessment functionality"""
    try:
        logger.info("✓ Testing difficulty assessment...")
        
        service = QuizGenerationService()
        
        sample_content = "Machine learning algorithms learn from data to make predictions."
        
        # Create questions with different complexity levels
        questions = [
            QuizQuestion(
                id="simple",
                question_text="What is machine learning?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                difficulty_level=DifficultyLevel.BEGINNER,
                correct_answer="A type of AI"
            ),
            QuizQuestion(
                id="intermediate",
                question_text="How do machine learning algorithms improve their performance?",
                question_type=QuestionType.SHORT_ANSWER,
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                correct_answer="Through experience and training on data"
            ),
            QuizQuestion(
                id="advanced",
                question_text="Analyze the epistemological implications of machine learning algorithms in automated decision-making systems.",
                question_type=QuestionType.ESSAY,
                difficulty_level=DifficultyLevel.ADVANCED,
                correct_answer="Complex philosophical analysis required"
            )
        ]
        
        # Test difficulty assessment for each question
        for question in questions:
            assessed_difficulty = await service.assess_question_difficulty(question, sample_content)
            logger.info(f"  Question '{question.question_text[:30]}...' assessed as: {assessed_difficulty.value}")
        
        logger.info("  ✓ Difficulty assessment working")
        return True
        
    except Exception as e:
        logger.error(f"Difficulty assessment test failed: {str(e)}")
        return False

async def test_adaptive_selection():
    """Test adaptive question selection"""
    try:
        logger.info("✓ Testing adaptive question selection...")
        
        service = QuizGenerationService()
        
        sample_content = """
        Machine learning algorithms can be categorized into supervised, unsupervised, 
        and reinforcement learning. Each category has different applications and methodologies.
        """
        
        key_concepts = ["supervised learning", "unsupervised learning", "reinforcement learning"]
        
        # Test with different performance histories
        high_performer = {'average_score': 0.9, 'total_attempts': 10}
        low_performer = {'average_score': 0.3, 'total_attempts': 5}
        
        # Generate adaptive questions
        high_questions = await service.adaptive_question_selection(
            user_id="high_user",
            content=sample_content,
            key_concepts=key_concepts,
            user_performance_history=high_performer
        )
        
        low_questions = await service.adaptive_question_selection(
            user_id="low_user",
            content=sample_content,
            key_concepts=key_concepts,
            user_performance_history=low_performer
        )
        
        # Verify adaptive selection
        high_difficulties = [q.difficulty_level for q in high_questions]
        low_difficulties = [q.difficulty_level for q in low_questions]
        
        logger.info(f"  High performer difficulties: {[d.value for d in high_difficulties]}")
        logger.info(f"  Low performer difficulties: {[d.value for d in low_difficulties]}")
        
        # Check that high performers get more challenging questions
        high_avg = sum(3 if d == DifficultyLevel.ADVANCED else 2 if d == DifficultyLevel.INTERMEDIATE else 1 for d in high_difficulties) / len(high_difficulties)
        low_avg = sum(3 if d == DifficultyLevel.ADVANCED else 2 if d == DifficultyLevel.INTERMEDIATE else 1 for d in low_difficulties) / len(low_difficulties)
        
        assert high_avg >= low_avg, "High performers should get more difficult questions on average"
        logger.info("  ✓ Adaptive question selection working correctly")
        return True
        
    except Exception as e:
        logger.error(f"Adaptive selection test failed: {str(e)}")
        return False

async def test_answer_key_generation():
    """Test answer key generation"""
    try:
        logger.info("✓ Testing answer key generation...")
        
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
                learning_objectives=["Understand ML basics"],
                metadata={"key_concept": "machine learning"}
            ),
            QuizQuestion(
                id="q2",
                question_text="Explain neural networks.",
                question_type=QuestionType.SHORT_ANSWER,
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                correct_answer="Neural networks are computing systems inspired by biological neural networks.",
                explanation="Short answer rubric for neural networks.",
                learning_objectives=["Explain neural networks"],
                metadata={"key_concept": "neural networks"}
            ),
            QuizQuestion(
                id="q3",
                question_text="Analyze the impact of AI on society.",
                question_type=QuestionType.ESSAY,
                difficulty_level=DifficultyLevel.ADVANCED,
                correct_answer="Essay outline covering AI impact on various sectors.",
                explanation="Essay rubric with detailed criteria.",
                learning_objectives=["Analyze AI impact"],
                metadata={"key_concepts": ["artificial intelligence", "society"]}
            )
        ]
        
        quiz = Quiz(
            id="test_quiz",
            title="Test Quiz",
            description="A test quiz for answer key generation",
            document_id="test_doc",
            questions=questions,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_time_minutes=20,
            learning_objectives=["Understand AI concepts"],
            created_at=datetime.now()
        )
        
        # Test basic answer key generation
        basic_key = await service.generate_answer_key(quiz)
        
        assert basic_key['quiz_id'] == quiz.id
        assert basic_key['total_questions'] == len(questions)
        assert len(basic_key['answers']) == len(questions)
        assert 'scoring_guide' in basic_key
        
        logger.info(f"  ✓ Basic answer key generated with {len(basic_key['answers'])} answers")
        
        # Test comprehensive answer key generation
        comprehensive_key = await service.generate_comprehensive_answer_key(quiz)
        
        assert 'detailed_explanations' in comprehensive_key
        assert 'learning_outcomes' in comprehensive_key
        assert 'quiz_statistics' in comprehensive_key
        
        stats = comprehensive_key['quiz_statistics']
        logger.info(f"  ✓ Comprehensive answer key with {stats['total_points']} total points")
        logger.info(f"  ✓ Question distribution: {stats['question_type_distribution']}")
        
        # Test question quality validation
        quality = await service.validate_question_quality(questions[0], "Machine learning content")
        
        assert 'overall_score' in quality
        assert 'suggestions' in quality
        logger.info(f"  ✓ Question quality validation (score: {quality['overall_score']:.2f})")
        
        return True
        
    except Exception as e:
        logger.error(f"Answer key generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_requirements_compliance():
    """Test compliance with task requirements"""
    try:
        logger.info("✓ Testing requirements compliance...")
        
        service = QuizGenerationService()
        
        # Requirement: AI-powered question generation from research documents
        research_content = "Artificial intelligence and machine learning are transforming technology."
        
        # Test automatic quiz generation from content
        questions = await service._generate_questions(
            content=research_content,
            key_concepts=["artificial intelligence", "machine learning"],
            num_questions=3,
            question_types=[QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER, QuestionType.ESSAY],
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        assert len(questions) > 0, "Should generate questions from content"
        logger.info("  ✓ AI-powered question generation from documents")
        
        # Requirement: Multiple question types support
        question_types_generated = set(q.question_type for q in questions)
        required_types = {QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER, QuestionType.ESSAY}
        
        assert len(question_types_generated.intersection(required_types)) >= 2, "Should support multiple question types"
        logger.info(f"  ✓ Multiple question types: {[t.value for t in question_types_generated]}")
        
        # Requirement: Difficulty assessment
        for question in questions:
            assessed_difficulty = await service.assess_question_difficulty(question, research_content)
            assert assessed_difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
        
        logger.info("  ✓ Difficulty assessment implemented")
        
        # Requirement: Adaptive question selection
        adaptive_questions = await service.adaptive_question_selection(
            user_id="test_user",
            content=research_content,
            key_concepts=["artificial intelligence"],
            user_performance_history={'average_score': 0.8, 'total_attempts': 5}
        )
        
        assert len(adaptive_questions) > 0, "Should generate adaptive questions"
        logger.info("  ✓ Adaptive question selection implemented")
        
        # Requirement: Automatic answer key generation
        quiz = Quiz(
            id="req_test_quiz",
            title="Requirements Test Quiz",
            description="Test quiz for requirements",
            document_id="req_doc",
            questions=questions,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_time_minutes=15,
            learning_objectives=["Test objectives"],
            created_at=datetime.now()
        )
        
        answer_key = await service.generate_answer_key(quiz)
        assert len(answer_key['answers']) == len(questions), "Should generate answer key"
        logger.info("  ✓ Automatic answer key generation implemented")
        
        # Requirement: Explanation creation
        for question in questions:
            assert len(question.explanation) > 0, "Should have explanations"
        
        logger.info("  ✓ Explanation creation implemented")
        
        return True
        
    except Exception as e:
        logger.error(f"Requirements compliance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all core functionality tests"""
    logger.info("=== Task 4.1 Core Functionality Verification ===")
    logger.info("Testing AI-powered quiz generation service implementation")
    logger.info("")
    
    # Run all tests
    tests = [
        ("Core question generation", test_core_question_generation()),
        ("Difficulty assessment", test_difficulty_assessment()),
        ("Adaptive selection", test_adaptive_selection()),
        ("Answer key generation", test_answer_key_generation()),
        ("Requirements compliance", test_requirements_compliance())
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"Running: {test_name}")
        result = await test_coro
        results.append((test_name, result))
        logger.info(f"Result: {'PASSED' if result else 'FAILED'}")
        logger.info("")
    
    # Summary
    logger.info("=== Core Functionality Summary ===")
    passed_count = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"\nTotal: {passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        logger.info("🎉 Task 4.1 CORE FUNCTIONALITY VERIFIED!")
        logger.info("✅ AI-powered question generation from research documents")
        logger.info("✅ Multiple question types (multiple choice, short answer, essay)")
        logger.info("✅ Difficulty assessment and adaptive question selection")
        logger.info("✅ Automatic answer key generation and explanation creation")
        return 0
    else:
        logger.error("❌ Some core functionality tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)